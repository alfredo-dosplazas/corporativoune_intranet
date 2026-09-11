from rest_framework import serializers

from apps.compras.models import Proveedor, Orden, DetalleOrden
from apps.core.serializers import RazonSocialSerializer, UserSerializer
from apps.directorio.serializers import ContactoSerializer


class ProveedorSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='compras:proveedores__detail',
        lookup_field='pk'
    )

    class Meta:
        model = Proveedor
        fields = '__all__'


class DetalleOrdenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleOrden
        fields = '__all__'


class OrdenSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='compras:ordenes__detail',
        lookup_field='pk'
    )
    proveedor = ProveedorSerializer(read_only=True)
    razon_social = RazonSocialSerializer(read_only=True)
    solicitante = ContactoSerializer(read_only=True)
    autoriza = ContactoSerializer(read_only=True)
    total = serializers.DecimalField(decimal_places=6, max_digits=20, read_only=True)
    detalles = DetalleOrdenSerializer(many=True, read_only=True, source='detalle_orden')

    class Meta:
        model = Orden
        fields = '__all__'
