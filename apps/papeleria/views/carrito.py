import json
from email import message
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django.urls import reverse
from inertia import render

from apps.core.models import Empresa
from apps.core.utils.navigation import paginate_queryset, make_breadcrumbs
from apps.papeleria.cart import PapeleriaCart
from apps.papeleria.forms.requisiciones import RequisicionForm
from apps.papeleria.models.articulos import Articulo
from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion


@login_required
@permission_required('papeleria.view_articulo', raise_exception=True)
def catalogo_view(request):
    """Vista principal tipo MercadoLibre para seleccionar papelería"""
    cart = PapeleriaCart(request)
    cart_items, total = cart.get_items()

    articulos = Articulo.objects.filter(mostrar_en_sitio=True)

    return render(request, 'Papeleria/Catalogo/Index', {
        'breadcrumbs': make_breadcrumbs([
            ('Inicio', 'home'),
            ('Papelería', 'papeleria:index'),
            ('Requisiciones', 'papeleria:requisiciones__list'),
            ('Catalogo De Artículos', None),
        ]),
        'paginated_data': paginate_queryset(articulos, request, page_size=12),
        'cart': {
            'items': cart_items,
            'total': total,
            'total_count': sum(item['cantidad'] for item in cart_items),
        }
    })


@login_required
def cart_add(request):
    """Acción Inertia POST para agregar artículo"""
    articulo_id = request.POST.get('articulo_id')
    cantidad = int(request.POST.get('cantidad', 1))
    page = int(request.POST.get('page', 1))

    if articulo_id and cantidad:
        cart = PapeleriaCart(request)
        cart.add(articulo_id, cantidad)

    params = urlencode({'page': page})
    url_base = reverse('papeleria:carrito__catalogo')
    return redirect(f"{url_base}?{params}")


@login_required
def cart_remove(request):
    """Elimina completamente un producto del carrito"""
    articulo_id = request.POST.get('articulo_id')

    if articulo_id:
        cart = PapeleriaCart(request)
        cart.remove(articulo_id)

    # Redirige a la vista previa del referrer o por defecto al catálogo
    return redirect(request.META.get('HTTP_REFERER', 'papeleria:carrito__catalogo'))


@login_required
def cart_update(request):
    """Actualiza la cantidad exacta o decrementa (si cantidad <= 0 elimina)"""
    articulo_id = request.POST.get('articulo_id')
    cantidad = int(request.POST.get('cantidad', 0))
    page = int(request.POST.get('page', 1))

    if articulo_id:
        cart = PapeleriaCart(request)
        if cantidad > 0:
            cart.update(articulo_id, cantidad)
        else:
            cart.remove(articulo_id)

    params = urlencode({'page': page})
    url_base = reverse('papeleria:carrito__catalogo')
    return redirect(f"{url_base}?{params}")


@login_required()
def checkout_view(request):
    cart = PapeleriaCart(request)
    cart_items, total = cart.get_items()

    form = RequisicionForm(user=request.user)

    if not cart_items:
        return redirect('papeleria:carrito__catalogo')

    if request.method == 'POST':
        data = request.POST or json.loads(request.body)
        form = RequisicionForm(data, user=request.user)

        if form.is_valid():
            form.save()
            requisicion = form.instance

            for item in cart_items:
                DetalleRequisicion.objects.create(
                    requisicion=requisicion,
                    articulo_id=item['articulo']['id'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['articulo']['importe'],
                )

            cart.clear()
            return redirect('papeleria:requisiciones__detail', form.instance.pk)

    empresas = Empresa.objects.all()
    return render(request, 'Papeleria/Catalogo/Checkout', {
        'cart_items': cart_items,
        'total': total,
        'empresas': [{'id': e.id, 'nombre': e.nombre} for e in empresas],
        'errors': form.errors,
    })
