import calendar
from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from django.views.generic import TemplateView

from apps.core.forms import LoginForm
from apps.core.querysets import modulos_visibles


class LoginView(BaseLoginView):
    template_name = "login.html"
    redirect_authenticated_user = True
    form_class = LoginForm


class LogoutView(BaseLogoutView):
    pass


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        empresa = getattr(getattr(self.request.user, 'contacto', None), 'empresa', None)

        modulos_disponibles = []
        modulos_visibles_empresa = modulos_visibles(self.request, empresa)

        for modulo in modulos_visibles_empresa:
            permisos = modulo.permisos.split(',') if modulo.permisos else []

            url = reverse(modulo.url_name) if modulo.url_name else modulo.url
            if url is None:
                url = '#'

            if all(user.has_perm(p) for p in permisos):
                modulos_disponibles.append({
                    "nombre": modulo.nombre,
                    "icono": modulo.icono,
                    "descripcion": modulo.descripcion,
                    "url": url,
                })

        context['modulos'] = modulos_disponibles

        return context


class PerfilView(LoginRequiredMixin, TemplateView):
    template_name = 'perfil.html'

    MONTHS = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre',
    }

    def get_context_data(self, **kwargs):
        contacto = self.request.user.contacto

        hoy = timezone.localdate()
        year = int(self.request.GET.get("year", hoy.year))
        month = int(self.request.GET.get("month", hoy.month))

        # Calendario del mes
        cal = calendar.Calendar(firstweekday=0)
        month_days = cal.monthdatescalendar(year, month)

        # Asistencias del mes
        asistencias = contacto.asistencias.filter(
            punch_time__year=year,
            punch_time__month=month
        )

        asistencias_por_dia = defaultdict(list)

        for a in asistencias:
            dia = timezone.localtime(a.punch_time).date()
            asistencias_por_dia[dia].append(a)

        context = {
            "month_days": month_days,
            "asistencias_por_dia": asistencias_por_dia,
            "year": year,
            "month": month,
            'months': self.MONTHS,
            'years': [i for i in range(2014, hoy.year + 1)],
        }

        return context