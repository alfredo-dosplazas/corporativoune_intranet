from dal import autocomplete
from django import forms

from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models


class FiltroListasPreciosForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered input-sm w-full',
            'placeholder': 'Ej: PROD-01 o Nombre...'
        })
    )

    linea = forms.MultipleChoiceField(
        required=False,
        widget=autocomplete.Select2Multiple(
            url='listas_precios:lineas_autocomplete',
            attrs={
                'data-placeholder': 'Selecciona una o varias líneas...',
                'class': 'select select-bordered select-sm w-full'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Recuperar claves desde data (GET) o initial, truncando a 5 caracteres
        selected_lineas = [
            l.strip()[:5] for l in self.data.getlist('linea') if l and l.strip()
        ] if self.data else self.initial.get('linea', [])

        if selected_lineas:
            choices = []
            try:
                with sae_session() as (db_sae, suffix):
                    m = get_sae_models(suffix)
                    rows = db_sae.query(m.Linea.clave, m.Linea.descripcion) \
                        .filter(m.Linea.clave.in_(selected_lineas)).all()

                    found = {r.clave.strip(): r.descripcion.strip() for r in rows}
                    for cve in selected_lineas:
                        label = cve
                        choices.append((cve, label))
            except Exception:
                # Fallback por si falla la sesión de BD al instanciar el form
                choices = [(cve, cve) for cve in selected_lineas]

            self.fields['linea'].choices = choices