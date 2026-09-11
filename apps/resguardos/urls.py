from django.urls import path

from apps.resguardos.views.equipos import equipos_list, equipo_create, equipo_update, equipo_delete, \
    equipos_autocomplete
from apps.resguardos.views.resguardos import resguardos_list, resguardo_create, ResguardoPdfView, resguardo_update, \
    resguardo_delete

app_name = 'resguardos'

urlpatterns = [
    path('', resguardos_list, name='list'),
    path('crear/', resguardo_create, name='create'),
    path('<int:pk>/editar/', resguardo_update, name='update'),
    path('<int:pk>/detalle/', resguardo_update, name='detail'),
    path('<int:pk>/eliminar/', resguardo_delete, name='delete'),
    path('<int:pk>/pdf/', ResguardoPdfView.as_view(), name='pdf'),

    path('equipos/', equipos_list, name='equipos__list'),
    path('equipos/crear/', equipo_create, name='equipos__create'),
    path('equipos/<int:pk>/editar/', equipo_update, name='equipos__update'),
    path('equipos/<int:pk>/eliminar/', equipo_delete, name='equipos__delete'),
    path('equipos/autocomplete/', equipos_autocomplete, name='equipos__autocomplete'),
]
