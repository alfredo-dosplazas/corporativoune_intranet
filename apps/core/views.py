from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.urls import reverse
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

            if all(user.has_perm(p) for p in permisos):
                modulos_disponibles.append({
                    "nombre": modulo.nombre,
                    "icono": modulo.icono,
                    "descripcion": modulo.descripcion,
                    "url": reverse(modulo.url_name),
                })

        context['modulos'] = modulos_disponibles

        return context
