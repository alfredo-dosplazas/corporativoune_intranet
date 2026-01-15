from import_export import resources

from apps.directorio.models import Contacto


class ContactoResource(resources.ModelResource):
    class Meta:
        model = Contacto