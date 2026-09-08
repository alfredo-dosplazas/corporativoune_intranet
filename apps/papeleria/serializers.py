from rest_framework import serializers

from apps.core.serializers import EmpresaSerializer
from apps.papeleria.models.articulos import Articulo
from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion


class ArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articulo
        fields = [
            'id', 'codigo_vs_dp', 'es_cuadro_basico', 'mostrar_en_sitio', 'nombre', 'descripcion', 'precio',
            'imagen', 'numero_papeleria', 'unidad', 'impuesto', 'importe',
        ]


class UserSimpleSerializer(serializers.Serializer):
    """Serializa la información básica del usuario evitando métodos complejos."""
    id = serializers.IntegerField()
    full_name = serializers.CharField(source='get_full_name')
    email = serializers.CharField()
    contacto = serializers.SerializerMethodField()

    def get_contacto(self, obj):
        contacto = getattr(obj, 'contacto', None)
        return contacto.to_dict() if contacto and hasattr(contacto, 'to_dict') else None


class DetalleRequisicionSerializer(serializers.ModelSerializer):
    articulo = ArticuloSerializer(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = DetalleRequisicion
        fields = [
            'id', 'articulo', 'cantidad', 'cantidad_autorizada',
            'precio_unitario', 'subtotal', 'notas'
        ]


class RequisicionSerializer(serializers.ModelSerializer):
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    solicitante = UserSimpleSerializer(read_only=True)
    aprobador = UserSimpleSerializer(read_only=True)
    compras = UserSimpleSerializer(read_only=True)
    contraloria = UserSimpleSerializer(read_only=True)
    estado_ui = serializers.SerializerMethodField()
    empresa = EmpresaSerializer(read_only=True)
    url = serializers.URLField(source='get_absolute_url')
    can = serializers.SerializerMethodField()

    detalles = DetalleRequisicionSerializer(
        source='detalle_requisicion',
        many=True,
        read_only=True
    )

    class Meta:
        model = Requisicion
        fields = [
            'id', 'folio', 'folio_consecutivo', 'empresa', 'estado', 'estado_ui', 'estado_display',
            'solicitante', 'aprobador', 'compras', 'contraloria',
            'total', 'can', 'created_at', 'updated_at', 'url',
            'detalles',
        ]

    # --- OMITIR O INCLUIR DINÁMICAMENTE ---
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si en el context viene include_detalles=False, removemos el campo
        if not self.context.get('include_detalles', True):
            self.fields.pop('detalles', None)

    def get_estado_ui(self, obj):
        return obj.estado_ui

    def get_can(self, obj):
        user = self.context.get('user')
        if not user:
            return {}
        return {
            'ver': obj.puede_ver(user),
            'editar': obj.puede_editar(user),
            'eliminar': obj.puede_eliminar(user),
            'confirmar': obj.puede_confirmar(user),
            'enviar_aprobador': obj.puede_enviar_al_aprobador(user),
            'aprobar': obj.puede_aprobar(user),
            'autorizar': obj.puede_autorizar(user),
        }
