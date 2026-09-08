from rest_framework import serializers

from apps.core.models import Empresa


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = [
            'id', 'nombre', 'nombre_corto', 'abreviatura', 'codigo', 'theme', 'logo'
        ]
