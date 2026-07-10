from extra_views import InlineFormSetFactory

from apps.refacciones_servicios.forms import DetalleOrdenCompraForm
from apps.refacciones_servicios.models import DetalleOrdenCompra


class DetalleOrdenCompraInline(InlineFormSetFactory):
    model = DetalleOrdenCompra
    form_class = DetalleOrdenCompraForm

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