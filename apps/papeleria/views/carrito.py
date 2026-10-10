import json
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic.base import TemplateView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from extra_views import SearchableListMixin

from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.mixins.responsive_view import ResponsiveViewModeMixin
from apps.core.mixins.session_filter_state import SessionFilterStateMixin
from apps.core.mixins.title import PageTitleMixin
from apps.papeleria.cart import PapeleriaCart
from apps.papeleria.forms.carrito import CheckoutForm
from apps.papeleria.models.articulos import Articulo
from apps.papeleria.models.requisiciones import DetalleRequisicion
from apps.papeleria.tables.carrito import ArticuloCarritoTable


class CatalogoListView(
    PermissionRequiredMixin,
    SessionFilterStateMixin,
    ResponsiveViewModeMixin,
    SearchableListMixin,
    PageTitleMixin,
    SingleTableMixin,
    BreadcrumbsMixin,
    FilterView
):
    permission_required = 'papeleria.view_articulo'
    template_name = 'apps/papeleria/carrito/list.html'
    page_title = 'Catalago De Papelería'
    model = Articulo
    table_class = ArticuloCarritoTable
    paginate_by = 12
    search_fields = ['codigo_vs_dp', 'numero_papeleria', 'nombre', 'descripcion']
    filterset_fields = ['unidad', 'es_cuadro_basico']

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Catalogo De Papelería'},
        ]

    def get_queryset(self):
        qs = super().get_queryset()

        usuario = self.request.user

        if not usuario.is_superuser and not usuario.groups.filter(name='ADMINISTRADOR PAPELERÍA').exists():
            qs = qs.filter(mostrar_en_sitio=True)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cart = PapeleriaCart(self.request)
        cart_items, total = cart.get_items()

        context['cart'] = {
            'items': cart_items,
            'total': total,
            'total_count': sum(item['cantidad'] for item in cart_items),
        }
        return context


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
    return redirect(f"{url_base}?{params}#cart-drawer")


@login_required
def cart_remove(request):
    """Elimina completamente un producto del carrito"""
    articulo_id = request.POST.get('articulo_id')

    if articulo_id:
        cart = PapeleriaCart(request)
        cart.remove(articulo_id)

    # Redirige a la vista previa del referrer o por defecto al catálogo
    return redirect(request.META.get('HTTP_REFERER', 'papeleria:carrito__catalogo') + '#cart-drawer')


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
    url_base = reverse('papeleria:carrito__catalogo') + '#cart-drawer'
    return redirect(f"{url_base}?{params}")


class CheckoutView(PermissionRequiredMixin, BreadcrumbsMixin, TemplateView):
    permission_required = 'papeleria.acceder_papeleria'
    template_name = 'apps/papeleria/carrito/checkout.html'

    def get_context_data(self, **kwargs):
        cart = PapeleriaCart(self.request)
        cart_items, total = cart.get_items()

        if not cart_items:
            return redirect('papeleria:carrito__catalogo')

        form = CheckoutForm(user=self.request.user)

        context = super().get_context_data(**kwargs)

        context.update({
            'form': form,
            'cart_items': cart_items,
            'total': total,
            'total_count': sum(item['cantidad'] for item in cart_items),
        })
        return context

    def post(self, request, *args, **kwargs):
        cart = PapeleriaCart(request)
        cart_items, total = cart.get_items()

        if not cart_items:
            return redirect('papeleria:carrito__catalogo')

        # Manejo de peticiones form-data o payload JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        form = CheckoutForm(data, user=request.user)

        if form.is_valid():
            requisicion = form.save()

            # Creación masiva del detalle a partir del carrito
            detalles = [
                DetalleRequisicion(
                    requisicion=requisicion,
                    articulo_id=item['articulo'].id,
                    cantidad=item['cantidad'],
                    precio_unitario=item['articulo'].importe,
                )
                for item in cart_items
            ]
            DetalleRequisicion.objects.bulk_create(detalles)

            # Limpiar sesión del carrito
            cart.clear()

            return redirect('papeleria:requisiciones__detail', requisicion.pk)

        return render(request, self.template_name, {
            'form': form,
            'cart_items': cart_items,
            'total': total,
            'total_count': sum(item['cantidad'] for item in cart_items),
        })

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Papelería', 'url': reverse('papeleria:index')},
            {'title': 'Catalogo De Papelería', 'url': reverse('papeleria:carrito__catalogo')},
            {'title': 'Checkout'},
        ]
