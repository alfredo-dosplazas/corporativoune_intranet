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

        view = self.view
        if getattr(view, 'orden', None):
            total = view.orden.detalle_orden.count()
            kwargs['extra'] = total - 1
        else:
            kwargs['extra'] = 1

        return kwargs

    def get_initial(self):
        view = self.view
        if not getattr(view, 'orden', None):
            return []

        return [
            {
                "descripcion": d.descripcion,
                "cantidad": d.cantidad,
            }
            for d in view.orden.detalle_orden.all()
        ]