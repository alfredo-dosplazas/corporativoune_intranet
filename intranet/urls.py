from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('cumpleanios/', include('apps.cumpleanios.urls')),
    path('destajos/', include('apps.destajos.urls')),
    path('papeleria/', include('apps.papeleria.urls')),
    path('directorio/', include('apps.directorio.urls')),
    path('rrhh/', include('apps.rrhh.urls')),
    path('fotos/', include('apps.fotos.urls')),
    path('monitoreo-servicios/', include('apps.monitoreo_servicios.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
