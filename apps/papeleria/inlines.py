from extra_views import InlineFormSetFactory

from apps.papeleria.forms.requisiciones import DetalleRequisicionForm
from apps.papeleria.models.requisiciones import DetalleRequisicion


class DetalleRequisicionInline(InlineFormSetFactory):
    model = DetalleRequisicion
    form_class = DetalleRequisicionForm

    factory_kwargs = {
        'min_num': 1,
        'validate_min': True,
    }

    def get_factory_kwargs(self):
        kwargs = super().get_factory_kwargs()

        view = self.view
        if getattr(view, 'requisicion', None):
            total = view.requisicion.detalle_requisicion.count()
            kwargs['extra'] = total - 1
        else:
            kwargs['extra'] = 1

        return kwargs

    def get_initial(self):
        view = self.view
        if not getattr(view, 'requisicion', None):
            return []

        return [
            {
                "articulo": d.articulo,
                "cantidad": d.cantidad,
            }
            for d in view.requisicion.detalle_requisicion.all()
        ]
