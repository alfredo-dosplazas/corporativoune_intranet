from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django_js_reverse.views import urls_json

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
    path('compras/', include('apps.compras.urls')),
    path('vs-erp/', include('apps.vs_erp.urls')),
    path('evidencias-moldes/', include('apps.evidencias_moldes.urls')),
    path('listas-precios/', include('apps.listas_precios.urls')),
    path('interfaz-sae-coi/', include('apps.interfaz_sae_coi.urls')),
    path('', include('pwa.urls')),
    path("jsreverse.json", urls_json, name="js_reverse"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
