from dal import autocomplete
from django.utils.html import format_html

from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models


class LineaAutocompleteView(autocomplete.Select2ListView):
    def get_list(self):
        usuario = self.request.user
        if not usuario.is_authenticated:
            return []

        # 1. Obtener lista desde SAE (SQLAlchemy)
        with sae_session() as (db_sae, suffix):
            m = get_sae_models(suffix)

            query = db_sae.query(m.Linea.clave, m.Linea.descripcion).filter(m.Linea.status == 'A')

            if self.q:
                q_clean = self.q.strip()
                query = query.filter(
                    (m.Linea.clave.ilike(f"%{q_clean}%")) |
                    (m.Linea.descripcion.ilike(f"%{q_clean}%"))
                )

            # Devuelve una lista simple de strings conteniendo solo las claves
            lineas = [l.clave.strip() for l in query.all()]

        return lineas

    def get_result_value(self, result):
        # Como result ya es un string (ej: "L-01"), se retorna directamente
        return result

    def get_result_label(self, result):
        # Renderiza el string formateado dentro del dropdown
        return format_html(
            """
            <div class="py-1 px-2 hover:bg-base-200 rounded">
                <span class="badge badge-primary badge-sm font-mono font-bold">{clave}</span>
            </div>
            """,
            clave=result
        )

    def get_selected_result_label(self, result):
        # La etiqueta del item seleccionado en el input
        return result
