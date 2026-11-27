from django.core.exceptions import ValidationError
from import_export import resources, fields, widgets

from apps.core.models import Empresa, RazonSocial
from apps.directorio.models import Contacto, EmailContacto, TelefonoContacto
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto
from apps.rrhh.models.sedes import Sede


class ScopedEmpresaWidget(widgets.ForeignKeyWidget):
    """Valida que la empresa pertenezca al alcance permitido del usuario."""

    def __init__(self, empresas_qs):
        super().__init__(Empresa, field='nombre_corto')
        self.empresas_qs = empresas_qs

    def clean(self, value, row=None, **kwargs):
        val = (str(value).strip() if value is not None else '')
        if not val:
            raise ValidationError("La columna 'empresa' es obligatoria.")

        empresa = (self.empresas_qs.filter(nombre_corto__iexact=val).first())
        if not empresa:
            raise ValidationError(f"La empresa '{val}' no existe o no tienes permiso para importarla.")
        return empresa

    def render(self, value, obj=None, **kwargs):
        if not value:
            return ''
        return getattr(value, 'nombre_corto', '')


class RazonSocialWidget(widgets.ForeignKeyWidget):
    def __init__(self):
        super().__init__(RazonSocial, field='nombre_corto')

    def render(self, value, obj=None, **kwargs):
        if not value:
            return ''
        return getattr(value, 'nombre_corto', '')


class ScopedSedeWidget(widgets.ForeignKeyWidget):
    """Valida que la sede administrativa pertenezca al alcance permitido del usuario."""

    def __init__(self, sedes_qs):
        super().__init__(Sede, field='nombre')
        self.sedes_qs = sedes_qs

    def clean(self, value, row=None, **kwargs):
        val = (str(value).strip() if value is not None else '')
        if not val:
            raise ValidationError("La columna 'sede_administrativa' es obligatoria.")

        sede = self.sedes_qs.filter(nombre__iexact=val).first()
        if not sede:
            raise ValidationError(f"La sede '{val}' no existe o no tienes permiso para importarla.")
        return sede


class ScopedSedesM2MWidget(widgets.ManyToManyWidget):
    """Resuelve sedes separadas por coma filtrando por las sedes permitidas."""

    def __init__(self, sedes_qs):
        super().__init__(Sede, separator=',', field='nombre')
        self.sedes_qs = sedes_qs

    def clean(self, value, row=None, **kwargs):
        if not value:
            return self.model.objects.none()
        nombres = [s.strip() for s in str(value).split(',') if s and s.strip()]
        sedes_encontradas = []
        for nombre in nombres:
            sede = self.sedes_qs.filter(nombre__iexact=nombre).first()
            if not sede:
                raise ValidationError(f"La sede '{nombre}' no existe o no está en tu alcance.")
            sedes_encontradas.append(sede.pk)
        return self.sedes_qs.filter(pk__in=sedes_encontradas)


class AreaIdWidget(widgets.ForeignKeyWidget):
    def __init__(self):
        super().__init__(Area, field='pk')

    def render(self, value, obj=None, **kwargs):
        if not value:
            return ''
        return getattr(value, 'nombre', '')


class PuestoIdWidget(widgets.ForeignKeyWidget):
    def __init__(self):
        super().__init__(Puesto, field='pk')

    def render(self, value, obj=None, **kwargs):
        if not value:
            return ''
        return getattr(value, 'nombre', '')


class ContactoResource(resources.ModelResource):
    numero_empleado = fields.Field(attribute='numero_empleado', column_name='numero_empleado')
    abreviatura_titulo = fields.Field(attribute='abreviatura_titulo', column_name='abreviatura_titulo')
    primer_nombre = fields.Field(attribute='primer_nombre', column_name='primer_nombre')
    segundo_nombre = fields.Field(attribute='segundo_nombre', column_name='segundo_nombre')
    primer_apellido = fields.Field(attribute='primer_apellido', column_name='primer_apellido')
    segundo_apellido = fields.Field(attribute='segundo_apellido', column_name='segundo_apellido')

    empresa = fields.Field(attribute='empresa', column_name='empresa')
    razon_social = fields.Field(attribute='razon_social', column_name='razon_social')
    sede_administrativa = fields.Field(attribute='sede_administrativa', column_name='sede_administrativa')
    sedes_visibles = fields.Field(attribute='sedes_visibles', column_name='sedes_visibles')
    sedes_consulta = fields.Field(attribute='sedes_consulta', column_name='sedes_consulta')

    area = fields.Field(attribute='area', column_name='area', widget=AreaIdWidget())
    puesto = fields.Field(attribute='puesto', column_name='puesto', widget=PuestoIdWidget())

    # Columnas virtuales (no son columnas directas en Contacto, se procesan en after_save_instance)
    emails = fields.Field(column_name='emails')
    telefonos = fields.Field(column_name='telefonos')

    fecha_ingreso = fields.Field(
        attribute='fecha_ingreso',
        column_name='fecha_ingreso',
        widget=widgets.DateWidget(format='%Y-%m-%d')
    )
    fecha_egreso = fields.Field(
        attribute='fecha_egreso',
        column_name='fecha_egreso',
        widget=widgets.DateWidget(format='%Y-%m-%d')
    )
    es_jefe = fields.Field(attribute='es_jefe', column_name='es_jefe', widget=widgets.BooleanWidget())
    mostrar_en_directorio = fields.Field(
        attribute='mostrar_en_directorio',
        column_name='mostrar_en_directorio',
        widget=widgets.BooleanWidget()
    )
    mostrar_en_cumpleanios = fields.Field(
        attribute='mostrar_en_cumpleanios',
        column_name='mostrar_en_cumpleanios',
        widget=widgets.BooleanWidget()
    )

    class Meta:
        model = Contacto
        import_id_fields = ('razon_social', 'numero_empleado')
        skip_unchanged = True
        report_skipped = True
        fields = (
            'numero_empleado',
            'abreviatura_titulo',
            'primer_nombre',
            'segundo_nombre',
            'primer_apellido',
            'segundo_apellido',
            'empresa',
            'razon_social',
            'sede_administrativa',
            'sedes_visibles',
            'sedes_consulta',
            'area',
            'puesto',
            'emails',
            'telefonos',
            'fecha_ingreso',
            'fecha_egreso',
            'es_jefe',
            'mostrar_en_directorio',
            'mostrar_en_cumpleanios',
        )

    def __init__(self, empresas_qs=None, sedes_qs=None, **kwargs):
        super().__init__(**kwargs)
        self.empresas_qs = empresas_qs if empresas_qs is not None else Empresa.objects.all()
        self.sedes_qs = sedes_qs if sedes_qs is not None else Sede.objects.all()

        # Inyectar widgets con el alcance dinámico del usuario
        self.fields['empresa'].widget = ScopedEmpresaWidget(self.empresas_qs)
        self.fields['razon_social'].widget = RazonSocialWidget()
        self.fields['sede_administrativa'].widget = ScopedSedeWidget(self.sedes_qs)
        self.fields['sedes_visibles'].widget = ScopedSedesM2MWidget(self.sedes_qs)
        self.fields['sedes_consulta'].widget = ScopedSedesM2MWidget(self.sedes_qs)

    def dehydrate_area(self, contacto):
        return contacto.area.nombre if contacto.area else ''

    def dehydrate_puesto(self, contacto):
        return contacto.puesto.nombre if contacto.puesto else ''

    def dehydrate_emails(self, contacto):
        if not contacto.pk:
            return ''
        return ', '.join(
            contacto.emails.filter(esta_activo=True)
            .order_by('-es_principal', 'id')
            .values_list('email', flat=True)
        )

    def dehydrate_telefonos(self, contacto):
        if not contacto.pk:
            return ''
        return ', '.join(
            contacto.telefonos.filter(esta_activo=True)
            .order_by('-es_principal', 'id')
            .values_list('telefono', flat=True)
        )

    def before_import_row(self, row, row_number=None, **kwargs):
        # Validar campos mínimos
        if not str(row.get('primer_nombre') or '').strip():
            raise ValidationError("El campo 'primer_nombre' es obligatorio.")
        if not str(row.get('primer_apellido') or '').strip():
            raise ValidationError("El campo 'primer_apellido' es obligatorio.")

        # Resolver empresa para poder buscar/crear Area y Puesto vinculados a esa empresa
        emp_val = str(row.get('empresa') or '').strip()
        empresa = (self.empresas_qs.filter(nombre_corto__iexact=emp_val).first())
        if not empresa:
            raise ValidationError(f"Empresa '{emp_val}' no permitida o inexistente.")

        # Resolver Área (busca por nombre_noi o nombre; si no existe, crea en dry_run=False)
        dry_run = kwargs.get('dry_run', False)
        area_str = str(row.get('area') or '').strip()
        if area_str:
            area_obj = (
                    Area.objects.filter(empresa=empresa, nombre_noi__iexact=area_str).first()
                    or Area.objects.filter(empresa=empresa, nombre__iexact=area_str).first()
            )
            if not area_obj and not dry_run:
                area_obj = Area.objects.create(empresa=empresa, nombre=area_str, nombre_noi=area_str)
            row['area'] = area_obj.pk if area_obj else None
        else:
            row['area'] = None

        # Resolver Puesto
        puesto_str = str(row.get('puesto') or '').strip()
        if puesto_str:
            puesto_obj = (
                    Puesto.objects.filter(empresa=empresa, nombre_noi__iexact=puesto_str).first()
                    or Puesto.objects.filter(empresa=empresa, nombre__iexact=puesto_str).first()
            )
            if not puesto_obj and not dry_run:
                puesto_obj = Puesto.objects.create(empresa=empresa, nombre=puesto_str, nombre_noi=puesto_str)
            row['puesto'] = puesto_obj.pk if puesto_obj else None
        else:
            row['puesto'] = None

        # Defaults para booleanos si vienen vacíos en el Excel
        if row.get('mostrar_en_directorio') in (None, ''):
            row['mostrar_en_directorio'] = True
        if row.get('mostrar_en_cumpleanios') in (None, ''):
            row['mostrar_en_cumpleanios'] = True

    def get_instance(self, instance_loader, row):
        # Si no trae numero_empleado, siempre crea un contacto nuevo en lugar de intentar match por None
        num_emp = str(row.get('numero_empleado') or '').strip()
        if not num_emp:
            return None
        return super().get_instance(instance_loader, row)

    def after_save_instance(self, instance, row, **kwargs):
        if kwargs.get('dry_run', False):
            return

        # 1. Procesar correos separados por coma -> todos activos
        emails_raw = str(row.get('emails') or '').strip()
        if emails_raw:
            correos = [e.strip().lower() for e in emails_raw.split(',') if e and e.strip()]
            tiene_principal = instance.emails.filter(es_principal=True).exists()
            for idx, correo in enumerate(correos):
                email_obj, created = EmailContacto.objects.get_or_create(
                    contacto=instance,
                    email=correo,
                    defaults={
                        'esta_activo': True,
                        'es_principal': (not tiene_principal and idx == 0),
                    }
                )
                if not created and not email_obj.esta_activo:
                    email_obj.esta_activo = True
                    email_obj.save(update_fields=['esta_activo'])

        # 2. Procesar teléfonos separados por coma -> todos activos
        tels_raw = str(row.get('telefonos') or '').strip()
        if tels_raw:
            telefonos = [t.strip() for t in tels_raw.split(',') if t and t.strip()]
            tiene_tel_principal = instance.telefonos.filter(es_principal=True).exists()
            for idx, tel in enumerate(telefonos):
                tel_limpio = ''.join(ch for ch in tel if ch.isdigit())[:11]
                if not tel_limpio:
                    continue
                tel_obj, created = TelefonoContacto.objects.get_or_create(
                    contacto=instance,
                    telefono=tel_limpio,
                    extension=None,
                    defaults={
                        'esta_activo': True,
                        'es_principal': (not tiene_tel_principal and idx == 0),
                    }
                )
                if not created and not tel_obj.esta_activo:
                    tel_obj.esta_activo = True
                    tel_obj.save(update_fields=['esta_activo'])
