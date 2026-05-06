from django.urls import path

from apps.cumpleanios.views import CumpleaniosView, CumpleaniosDiapositivasView

app_name = 'cumpleanios'

urlpatterns = [
    path('', CumpleaniosView.as_view(), name='list'),
    path('diapositivas', CumpleaniosDiapositivasView.as_view(), name='diapositivas'),
]
