from django.urls import path

from apps.core.autocompletes import UsuarioAutocomplete, EmpresaAutocomplete
from apps.core.views import LoginView, LogoutView, HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('usuario/autocomplete/', UsuarioAutocomplete.as_view(), name='usuario__autocomplete'),
    path('empresa/autocomplete/', EmpresaAutocomplete.as_view(), name='empresa__autocomplete'),
]