from django.urls import path

from apps.custom_auth import views

app_name = 'custom_auth'

urlpatterns = [
    path('usuarios/', views.UsuarioListView.as_view(), name='usuario__list'),
    path('usuarios/crear/', views.UsuarioCreateView.as_view(), name='usuario__create'),
    path('usuarios/editar/<int:pk>/', views.UsuarioUpdateView.as_view(), name='usuario__update'),

    path('impersonate/<int:user_id>/', views.impersonate_user, name='impersonate_user'),
    path('impersonate/stop/', views.stop_impersonating, name='impersonate_stop'),
]