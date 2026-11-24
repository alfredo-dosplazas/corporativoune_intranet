from django.urls import path
from .views import waha_webhook_view

urlpatterns = [
    path("webhooks/waha/", waha_webhook_view, name="waha_webhook"),
]

