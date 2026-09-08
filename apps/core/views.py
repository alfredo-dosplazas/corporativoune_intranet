import calendar
import json
from collections import defaultdict

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from inertia import render

from apps.core.forms import LoginForm
from apps.core.mixins.breadcrumbs import BreadcrumbsMixin
from apps.core.querysets import modulos_visibles


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'GET':
        return render(request, 'Auth/Login')

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            data = request.POST

        username = data.get('username', '').strip()
        password = data.get('password', '')

        errors = {}

        if not username:
            errors['username'] = 'El usuario o correo es obligatorio.'
        if not password:
            errors['password'] = 'La contraseña es obligatoria.'

        if not errors:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                errors['username'] = 'Las credenciales ingresadas son incorrectas.'

        return render(
            request,
            'Auth/Login',
            props={'errors': errors},
        )


class LogoutView(BaseLogoutView):
    pass


@login_required()
def home(request):
    empresa = getattr(getattr(request.user, 'contacto', None), 'empresa', None)

    modulos_disponibles = []
    modulos_empresa = modulos_visibles(request, empresa)

    for modulo in modulos_empresa:
        if modulo.puede_acceder(request, empresa):
            url = reverse(modulo.url_name) if modulo.url_name else (modulo.url or '#')
            modulos_disponibles.append({
                "nombre": modulo.nombre,
                "icono": modulo.icono,
                "descripcion": modulo.descripcion,
                "url": url,
            })

    props = {
        'modulos': modulos_disponibles,
    }
    return render(request, 'Home', props)


class PerfilView(LoginRequiredMixin, BreadcrumbsMixin, TemplateView):
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
        context = super().get_context_data(**kwargs)

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

        context.update({
            "month_days": month_days,
            "asistencias_por_dia": asistencias_por_dia,
            "year": year,
            "month": month,
            'months': self.MONTHS,
            'years': [i for i in range(2014, hoy.year + 1)],
        })

        return context

    def get_breadcrumbs(self):
        return [
            {'title': 'Inicio', 'url': reverse('home')},
            {'title': 'Perfil'},
        ]


def handler_404(request, exception=None):
    is_inertia = request.headers.get('x-inertia')

    description = str(exception) if exception else 'La página que buscas no existe o fue movida.'

    return render(
        request,
        'Error',
        props={
            'status': 404,
            'title': 'Página no encontrada',
            'description': description,
        },
    )


def handler_403(request, exception=None):
    description = str(exception) if exception else 'No tienes permisos para acceder a este recurso.'

    return render(
        request,
        'Error',
        props={
            'status': 403,
            'title': 'Acceso Denegado',
            'description': description,
        },
    )
