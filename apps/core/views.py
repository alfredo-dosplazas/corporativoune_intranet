from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.shortcuts import render
from django.views.generic import TemplateView

from apps.core.forms import LoginForm
from apps.core.models import Modulo


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
        usuario = self.request.user
        context['modulos'] = Modulo.objects.filter()

        return context
