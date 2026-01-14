from django.urls import path

from apps.destajos.views.destajos import DestajosView

app_name = 'destajos'

urlpatterns = [
    path('', DestajosView.as_view(), name='index'),
]