from rest_framework import serializers

from apps.core.models import Empresa
from apps.directorio.models import Contacto, EmailContacto, TelefonoContacto
from apps.rrhh.serializers import AreaSerializer, PuestoSerializer, SedeSerializer


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'


class EmailContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailContacto
        fields = ['id', 'email', 'es_principal', 'esta_activo', 'es_slack']


class TelefonoContactoSerializer(serializers.ModelSerializer):
    whatsapp = serializers.ReadOnlyField()

    class Meta:
        model = TelefonoContacto
        fields = ['id', 'telefono', 'extension', 'es_principal', 'esta_activo', 'es_celular', 'whatsapp']


class ContactoSerializer(serializers.ModelSerializer):
    # Campos calculados (@property del modelo)
    nombre_completo = serializers.ReadOnlyField()
    titulo_nombre_completo = serializers.ReadOnlyField()
    iniciales = serializers.ReadOnlyField()
    email_principal = serializers.SerializerMethodField()
    telefono_principal = serializers.SerializerMethodField()

    # Relaciones anidadas de lectura
    empresa = EmpresaSerializer(read_only=True)
    area = AreaSerializer(read_only=True)
    puesto = PuestoSerializer(read_only=True)
    sede_administrativa = SedeSerializer(read_only=True)
    sedes_visibles = SedeSerializer(many=True, read_only=True)
    empresas_relacionadas = EmpresaSerializer(many=True, read_only=True)

    emails = EmailContactoSerializer(many=True, read_only=True)
    telefonos = TelefonoContactoSerializer(many=True, read_only=True)

    class Meta:
        model = Contacto
        fields = [
            'id',
            'foto',
            'numero_empleado',
            'abreviatura_titulo',
            'primer_nombre',
            'segundo_nombre',
            'primer_apellido',
            'segundo_apellido',
            'nombre_completo',
            'titulo_nombre_completo',
            'iniciales',
            'email_principal',
            'telefono_principal',
            'empresa',
            'razon_social',
            'empresas_relacionadas',
            'sede_administrativa',
            'sedes_visibles',
            'area',
            'puesto',
            'es_jefe',
            'jefe_directo',
            'fecha_nacimiento',
            'fecha_ingreso',
            'fecha_egreso',
            'slack_id',
            'slack_url',
            'mostrar_en_directorio',
            'mostrar_en_cumpleanios',
            'esta_archivado',
            'emails',
            'telefonos',
        ]

    def get_email_principal(self, obj):
        email_obj = obj.email_principal
        return email_obj.email if email_obj else None

    def get_telefono_principal(self, obj):
        tel_obj = obj.telefono_principal
        return tel_obj.telefono if tel_obj else None
