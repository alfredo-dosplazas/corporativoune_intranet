from django.urls import path

from . import views

app_name = 'resguardos'

urlpatterns = [
    path('', views.ResguardoListView.as_view(), name='list'),
    path('crear/', views.ResguardoCreateView.as_view(), name='create'),
    path('<int:pk>/editar/', views.ResguardoUpdateView.as_view(), name='update'),
    path('<int:pk>/detalle/', views.ResguardoUpdateView.as_view(), name='detail'),
    path('<int:pk>/eliminar/', views.ResguardoDeleteView.as_view(), name='delete'),
    path('<int:pk>/pdf/', views.ResguardoPdfView.as_view(), name='pdf'),

    path('equipos/', views.EquipoListView.as_view(), name='equipos__list'),
    path('equipos/crear/', views.EquipoCreateView.as_view(), name='equipos__create'),
    path('equipos/<int:pk>/editar/', views.EquipoUpdateView.as_view(), name='equipos__update'),
    path('equipos/<int:pk>/eliminar/', views.EquipoDeleteView.as_view(), name='equipos__delete'),
    path('equipos/autocomplete/', views.EquipoAutocompleteView.as_view(), name='equipos__autocomplete'),
]
