from django.urls import path

from apps.cumpleanios.views import CumpleaniosView

app_name = 'cumpleanios'

urlpatterns = [
    path('', CumpleaniosView.as_view(), name='list'),
]
