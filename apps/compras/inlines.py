from extra_views import InlineFormSetFactory

from apps.compras.forms import DetalleOrdenForm
from apps.compras.models import DetalleOrden


class DetalleOrdenInline(InlineFormSetFactory):
    model = DetalleOrden
    form_class = DetalleOrdenForm

    factory_kwargs = {
        'min_num': 1,
        'validate_min': True,
    }

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()
        view = getattr(self, 'view', None)

        if view and getattr(view, 'orden', None):
            # Asignamos extra exactamente con el número de partidas a duplicar
            kwargs['extra'] = view.orden.detalle_orden.count()
        else:
            kwargs['extra'] = 1

        return kwargs

    def get_initial(self):
        view = getattr(self, 'view', None)
        if not view or not getattr(view, 'orden', None):
            return []

        # Retornamos los diccionarios con los datos duplicados
        return [
            {
                "descripcion": d.descripcion,
                "precio_unitario": d.precio_unitario,
                "cantidad": d.cantidad,
            }
            for d in view.orden.detalle_orden.all()
        ]