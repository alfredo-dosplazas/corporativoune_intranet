from django.core.paginator import Paginator
from django.urls import reverse


def paginate_queryset(queryset, request, page_size=12, transform_fn=None):
    """
    Pagina un queryset de Django y devuelve la estructura estandarizada para Inertia.
    """
    page_number = request.GET.get('page', 1)
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    # Si se pasa una función transformadora (ej. lambda x: x.to_dict())
    if transform_fn:
        data = [transform_fn(item) for item in page_obj]
    elif hasattr(queryset.model, 'to_dict'):
        data = [item.to_dict() for item in page_obj]
    else:
        data = list(page_obj.object_list.values())

    return {
        'data': data,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': paginator.num_pages,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
    }


def paginate_list(items, request, page_size=12, transform_fn=None):
    """
    Pagina una lista/arreglo de Python y devuelve la estructura estandarizada para Inertia.
    """
    page_number = request.GET.get('page', 1)
    paginator = Paginator(items, page_size)
    page_obj = paginator.get_page(page_number)

    # Si los elementos requieren transformación opcional
    if transform_fn:
        data = [transform_fn(item) for item in page_obj]
    else:
        data = list(page_obj.object_list)

    return {
        'data': data,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': paginator.num_pages,
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
    }


def make_breadcrumbs(crumbs):
    """
    Genera la estructura de breadcrumbs resolviendo nombres de URLs si es necesario.
    Recibe una lista de tuplas: [('Nombre', 'nombre_url'), ('Actual', None)]
    """
    result = []
    for crumb in crumbs:
        label = crumb[0]
        url = crumb[1]

        item = {'label': label}
        if url:
            # Si el string ya empieza con '/', es una URL directa, si no, se resuelve con reverse
            item['url'] = url if url.startswith('/') else reverse(url)

        result.append(item)
    return result
