from rest_framework import serializers

from apps.core.models import Empresa
from apps.directorio.models import Contacto
from apps.rrhh.serializers import AreaSerializer, PuestoSerializer, SedeSerializer


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'


class ContactoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    iniciales = serializers.CharField(read_only=True)
    empresa = EmpresaSerializer(read_only=True)
    area = AreaSerializer(read_only=True)
    puesto = PuestoSerializer(read_only=True)
    sede = SedeSerializer(read_only=True)

    class Meta:
        model = Contacto
        fields = '__all__'
