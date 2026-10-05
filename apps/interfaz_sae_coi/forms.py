from django import forms

from apps.interfaz_sae_coi.constants import TIPOS_DOCUMENTOS


class DocumentoFilterForm(forms.Form):
    """Formulario puro para el modal de filtros (sin depender de django-filters)"""
    tipo_documento = forms.ChoiceField(choices=[(t['value'], t['label']) for t in TIPOS_DOCUMENTOS], required=False)
    estado_conta = forms.ChoiceField(
        choices=[('todos', 'Todos'), ('contabilizados', 'Contabilizados'), ('pendientes', 'Pendientes')],
        required=False
    )
    almacen = forms.CharField(required=False)
    dia = forms.CharField(required=False)
    mes = forms.CharField(required=False)
    anio = forms.CharField(required=False)
