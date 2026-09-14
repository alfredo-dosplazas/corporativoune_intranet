from rest_framework import serializers

from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto
from apps.rrhh.models.sedes import Sede


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'


class PuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Puesto
        fields = '__all__'


class SedeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sede
        fields = '__all__'
