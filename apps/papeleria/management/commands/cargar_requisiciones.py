from django.core.management import BaseCommand
from django.db import connections, transaction
from django.contrib.auth import get_user_model
from apps.core.models import Empresa
from apps.papeleria.models.articulos import Articulo
from apps.papeleria.models.requisiciones import Requisicion, DetalleRequisicion

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrar usuarios y requisiciones de papelería desde la BD legacy intranet'

    TABLA_EMPLEADOS_LEGACY = 'core_empleado'
    TABLA_USUARIOS_LEGACY = 'auth_user'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando proceso de migración...")

        cursor = connections['intranet'].cursor()

        # ==========================================
        # PASO -1: MIGRAR / CREAR USUARIOS LEGACY EN DESTINO
        # ==========================================
        self.stdout.write("👤 Migrando / Creando usuarios desde la BD legacy...")

        # Leemos los datos clave de auth_user en la BD legacy
        cursor.execute(f"""
            SELECT id, username, first_name, last_name, email, is_active, is_staff, is_superuser
            FROM {self.TABLA_USUARIOS_LEGACY}
            WHERE username IS NOT NULL AND username != ''
        """)
        usuarios_legacy_rows = cursor.fetchall()

        usuarios_creados = 0
        with transaction.atomic():
            for u_row in usuarios_legacy_rows:
                username_clean = str(u_row[1]).strip().lower()
                if not username_clean:
                    continue

                user_obj, created = User.objects.get_or_create(
                    username=username_clean,
                    defaults={
                        'first_name': u_row[2] or '',
                        'last_name': u_row[3] or '',
                        'email': u_row[4] or '',
                        'is_active': bool(u_row[5]),
                        'is_staff': bool(u_row[6]),
                        'is_superuser': bool(u_row[7]),
                    }
                )
                if created:
                    # Asignar una contraseña inusable por seguridad para obligar a resetearla o usar SSO
                    user_obj.set_unusable_password()
                    user_obj.save()
                    usuarios_creados += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Usuarios creados/verificados: {usuarios_creados} nuevos."))

        # Aseguramos fallback tras sincronizar usuarios
        usuario_fallback = User.objects.filter(is_superuser=True).first()
        empresa_fallback = Empresa.objects.first()

        if not usuario_fallback or not empresa_fallback:
            self.stderr.write("❌ Error: Se requiere al menos un superusuario y una Empresa en el destino.")
            return

        # ==========================================
        # PASO 0: MAPEO EMPLEADO LEGACY -> USERNAME
        # ==========================================
        self.stdout.write("🔍 Mapeando relaciones Empleado -> Usuario en BD legacy...")

        cursor.execute(f"""
            SELECT e.id, u.username
            FROM {self.TABLA_EMPLEADOS_LEGACY} e
            JOIN {self.TABLA_USUARIOS_LEGACY} u ON e.usuario_id = u.id
            WHERE u.username IS NOT NULL AND u.username != ''
        """)

        empleado_to_username = {
            row[0]: str(row[1]).strip().lower()
            for row in cursor.fetchall()
        }

        # Refrescamos el diccionario de usuarios en destino (ya incluye los recién importados)
        dest_users_by_username = {
            u.username.strip().lower(): u
            for u in User.objects.all() if u.username
        }

        empresas_dict = {e.id: e for e in Empresa.objects.all()}

        def obtener_usuario_por_empleado_id(empleado_id):
            if not empleado_id:
                return usuario_fallback

            username = empleado_to_username.get(empleado_id)
            if not username:
                return usuario_fallback

            return dest_users_by_username.get(username, usuario_fallback)

        # ==========================================
        # PASO 1: MIGRACIÓN DE REQUISICIONES
        # ==========================================
        self.stdout.write("📋 Cargando requisiciones desde BD legacy...")
        cursor.execute("""
            SELECT 
                id,                     -- 0
                folio,                  -- 1
                estado,                 -- 2
                fecha_solicitud,        -- 3
                fecha_actualizacion,    -- 4
                autoriza_solicitante,   -- 5
                autoriza_jefe_area,     -- 6
                autoriza_compras,       -- 7
                autoriza_contraloria,   -- 8
                observaciones,          -- 9
                aprobador_id,           -- 10 (Empleado ID)
                empresa_id,             -- 11
                encargado_compras_id,   -- 12 (Empleado ID)
                solicitante_id,         -- 13 (Empleado ID)
                contraloria_id,         -- 14 (Empleado ID)
                es_urgente,             -- 15
                notas                   -- 16
            FROM papeleria_requisicion
        """)

        requisiciones_legacy = cursor.fetchall()
        req_creadas = 0

        with transaction.atomic():
            for row in requisiciones_legacy:
                req_id = row[0]
                folio_legacy = row[1] or f"REQ-LEGACY-{req_id}"

                solicitante = obtener_usuario_por_empleado_id(row[13])
                aprobador = obtener_usuario_por_empleado_id(row[10])
                compras = obtener_usuario_por_empleado_id(row[12])
                contraloria = obtener_usuario_por_empleado_id(row[14])

                empresa = empresas_dict.get(row[11], empresa_fallback)

                consecutivo = req_id
                if folio_legacy and '-' in folio_legacy:
                    try:
                        consecutivo = int(folio_legacy.split('-')[-1])
                    except ValueError:
                        pass

                req, _ = Requisicion.objects.update_or_create(
                    id=req_id,
                    defaults={
                        'folio': folio_legacy,
                        'folio_consecutivo': consecutivo,
                        'estado': str(row[2]).lower() if row[2] else 'borrador',
                        'solicitante': solicitante,
                        'aprobador': aprobador,
                        'compras': compras,
                        'contraloria': contraloria,
                        'creada_por': solicitante,
                        'empresa': empresa,
                        'aprobo_solicitante': bool(row[5]),
                        'aprobo_aprobador': bool(row[6]),
                        'aprobo_compras': bool(row[7]),
                        'aprobo_contraloria': bool(row[8]),
                        'notas': row[16] or row[9] or '',
                        'es_papeleria_stock': bool(row[15]),
                    }
                )

                fecha_creacion = row[3]
                fecha_modificacion = row[4]

                if fecha_creacion or fecha_modificacion:
                    Requisicion.objects.filter(pk=req.pk).update(
                        created_at=fecha_creacion or req.created_at,
                        updated_at=fecha_modificacion or fecha_creacion or req.updated_at
                    )

                req_creadas += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Requisiciones migradas: {req_creadas}"))

        # ==========================================
        # PASO 2: MIGRACIÓN DE DETALLES
        # ==========================================
        cursor.execute("""
            SELECT id, cantidad, concepto, articulo_id, requisicion_id
            FROM papeleria_detallerequisicion
        """)
        detalles_legacy = cursor.fetchall()

        articulos_dict = {a.id: a for a in Articulo.objects.all()}
        requisiciones_dict = {r.id: r for r in Requisicion.objects.all()}

        detalles_creados = 0

        with transaction.atomic():
            for row in detalles_legacy:
                det_id = row[0]
                cantidad = row[1] or 1
                articulo_id = row[3]
                requisicion_id = row[4]

                articulo_obj = articulos_dict.get(articulo_id)
                requisicion_obj = requisiciones_dict.get(requisicion_id)

                if not articulo_obj or not requisicion_obj:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️ Omite detalle #{det_id}: Requisición {requisicion_id} o Artículo {articulo_id} no existen en destino.")
                    )
                    continue

                precio_unitario = getattr(articulo_obj, 'precio', 0.0)

                DetalleRequisicion.objects.update_or_create(
                    id=det_id,
                    defaults={
                        'requisicion': requisicion_obj,
                        'articulo': articulo_obj,
                        'cantidad': cantidad,
                        'cantidad_autorizada': cantidad if requisicion_obj.estado in ['completada',
                                                                                      'autorizada_contraloria'] else 0,
                        'precio_unitario': precio_unitario,
                        'notas': row[2] or '',
                    }
                )
                detalles_creados += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Detalles de requisición migrados: {detalles_creados}"))
        self.stdout.write(self.style.SUCCESS("🎉 ¡Migración finalizada correctamente!"))