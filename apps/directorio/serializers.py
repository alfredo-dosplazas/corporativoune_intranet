from rest_framework import serializers

from apps.directorio.models import Contacto


class ContactoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)

    class Meta:
        model = Contacto
        fields = '__all__'
