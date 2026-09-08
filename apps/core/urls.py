from django.urls import path

from apps.core.autocompletes import UsuarioAutocomplete, EmpresaAutocomplete, RazonSocialAutocomplete
from apps.core.views import LogoutView, PerfilView, home, login_view

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('perfil/', PerfilView.as_view(), name='perfil'),

    path('usuario/autocomplete/', UsuarioAutocomplete.as_view(), name='usuario__autocomplete'),
    path('empresa/autocomplete/', EmpresaAutocomplete.as_view(), name='empresa__autocomplete'),
    path('razon-social/autocomplete/', RazonSocialAutocomplete.as_view(), name='razon_social__autocomplete'),
]
