from rest_framework import serializers
from apps.resguardos.models import Resguardo, Equipo, EvidenciaResguardo


class EquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipo
        fields = '__all__'


class EvidenciaResguardoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaResguardo
        fields = '__all__'


class ResguardoSerializer(serializers.ModelSerializer):
    equipo = EquipoSerializer(read_only=True)
    evidencias = EvidenciaResguardoSerializer(many=True, read_only=True)
    created_by_username = serializers.ReadOnlyField(source='created_by.username')
    url = serializers.HyperlinkedIdentityField(
        view_name='resguardos:detail',
        lookup_field='pk'
    )

    class Meta:
        model = Resguardo
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'required': False}
        }
