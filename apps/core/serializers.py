from rest_framework import serializers

from apps.ad.models import User
from apps.core.models import Empresa, RazonSocial
from apps.directorio.serializers import ContactoSerializer


class UserSerializer(serializers.ModelSerializer):
    contacto = ContactoSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'contacto']


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'


class RazonSocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = RazonSocial
        fields = '__all__'
