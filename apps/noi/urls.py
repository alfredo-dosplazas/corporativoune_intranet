from django.urls import path
from . import views

app_name = 'noi'

urlpatterns = [
    path('trabajadores/', views.TrabajadorNOIListView.as_view(), name='trabajadores__list'),
    path('trabajadores/exportar/', views.ExportarExcelNOIView.as_view(), name='trabajadores__exportar'),

    path("departamentos/", views.DepartamentosNOIListView.as_view(), name="departamentos_list"),
]
