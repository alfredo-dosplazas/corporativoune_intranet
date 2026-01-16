from django.utils.safestring import mark_safe
from django_tables2 import Column


class ContactoColumn(Column):
    empty_values = ()

    def render(self, value):
        contacto = value
        empresa = contacto.empresa

        theme_attr = f'data-theme="{empresa.theme}"' if empresa and empresa.theme else ""

        if contacto.foto:
            foto_html = f"""
                        <div {theme_attr} class="avatar">
                            <div class="w-10 h-10 rounded-full ring ring-primary ring-offset-2 ring-offset-base-100">
                                <img src="{contacto.foto.url}" alt="{contacto.nombre_completo}" />
                            </div>
                        </div>
                    """
        else:
            foto_html = f"""
                <div {theme_attr} class="avatar avatar-placeholder">
                    <div class="w-10 h-10 rounded-full bg-primary text-primary-content">
                        <span class="text-xl">{contacto.iniciales}</span>
                    </div>
                </div>
            """

        estado_html = ""
        if contacto.usuario and not contacto.usuario.is_active:
            estado_html = """
                        <span class="badge badge-xs">Inactivo</span>
                    """

        empresa_html = ""
        if empresa:
            empresa_html = f"""
                        <span class="text-xs uppercase tracking-wide opacity-60">
                            {empresa.nombre_corto}
                        </span>
                    """

        return mark_safe(f"""
                    <div class="flex items-center gap-3 min-w-[220px]">

                        {foto_html}

                        <div class="min-w-0">
                            <div class="font-medium truncate">
                                {contacto.nombre_completo}
                            </div>

                            <div class="text-xs opacity-70 truncate">
                                {contacto.area.nombre if contacto.area else "Área no asignada"}
                            </div>

                            <div class="flex items-center gap-2 mt-0.5">
                                {empresa_html}
                                {estado_html}
                            </div>
                        </div>
                    </div>
                """)
