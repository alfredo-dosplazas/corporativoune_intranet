from dal import autocomplete

from apps.core.models import Empresa
from apps.core.utils.network import get_client_ip, get_empresas_from_ip
from apps.directorio.utils import es_frescopack, obtener_sedes_permitidas
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto


class AreaAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Area.objects.all()

        if not self.request.user.is_authenticated:
            ip = get_client_ip(self.request)
            empresas = get_empresas_from_ip(ip)
            return qs.filter(empresa__in=empresas)

        sedes = obtener_sedes_permitidas(self.request)
        if sedes is not None:
            qs = qs.filter(empresa__sedes__id__in=sedes).distinct()

        # Si viene reenviado el campo empresa desde el formulario
        empresa_id = self.forwarded.get('empresa')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return qs


class AreaNombreAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        qs = Area.objects.all()

        if not self.request.user.is_authenticated:
            ip = get_client_ip(self.request)
            empresas = get_empresas_from_ip(ip)
            qs = qs.filter(empresa__in=empresas)
        else:
            sedes = obtener_sedes_permitidas(self.request)
            if sedes is not None:
                qs = qs.filter(empresa__sedes__id__in=sedes).distinct()

        empresa_id = self.forwarded.get('empresa')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return list(set(qs.values_list('nombre', flat=True)))


class PuestoAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Puesto.objects.all()

        if not self.request.user.is_authenticated:
            ip = get_client_ip(self.request)
            empresas = get_empresas_from_ip(ip)
            return qs.filter(empresa__in=empresas)

        sedes = obtener_sedes_permitidas(self.request)
        if sedes is not None:
            qs = qs.filter(empresa__sedes__id__in=sedes).distinct()

        empresa_id = self.forwarded.get('empresa')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return qs


class PuestoNombreAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        qs = Puesto.objects.all()

        if not self.request.user.is_authenticated:
            ip = get_client_ip(self.request)
            empresas = get_empresas_from_ip(ip)
            qs = qs.filter(empresa__in=empresas)
        else:
            sedes = obtener_sedes_permitidas(self.request)
            if sedes is not None:
                qs = qs.filter(empresa__sedes__id__in=sedes).distinct()

        empresa_id = self.forwarded.get('empresa')
        if empresa_id:
            qs = qs.filter(empresa_id=empresa_id)

        if self.q:
            qs = qs.filter(nombre__icontains=self.q)

        return list(set(qs.values_list('nombre', flat=True)))
