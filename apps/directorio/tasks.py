import logging
from celery import shared_task
from django.db import connections, transaction

from apps.core.models import Empresa, RazonSocial
from apps.directorio.models import Contacto, EmailContacto, TelefonoContacto
from apps.noi.db_router import get_or_create_noi_connection_alias
from apps.noi.models import EmpresaNOI, MapeoDepartamentoNOI
from apps.noi.services import listar_periodos_disponibles
from apps.rrhh.models.areas import Area
from apps.rrhh.models.puestos import Puesto
from apps.rrhh.models.sedes import Sede

logger = logging.getLogger(__name__)


def _separar_nombre_completo(nombre_raw: str):
    partes = (nombre_raw or "").strip().split()
    if not partes:
        return "", None
    primer_nombre = partes[0].title()
    segundo_nombre = " ".join(partes[1:]).title() if len(partes) > 1 else None
    return primer_nombre, segundo_nombre


def _limpiar_str(val, max_len: int | None = None):
    if val is None:
        return None
    s = " ".join(str(val).strip().split())
    if not s:
        return None
    return s[:max_len] if max_len else s


def _normalizar_texto(val):
    if not val:
        return ""
    return " ".join(str(val).strip().lower().split())


def _normalizar_fecha(val):
    if not val:
        return None
    if hasattr(val, "date"):
        return val.date()
    return val


def _obtener_mapa_departamentos_noi(empresa_noi_obj: EmpresaNOI) -> dict[str, Empresa]:
    """
    Devuelve {departamento_normalizado: Empresa} a partir de los mapeos activos
    configurados en MapeoDepartamentoNOI para la EmpresaNOI indicada.
    """
    mapeos = (
        MapeoDepartamentoNOI.objects.filter(
            empresa_noi=empresa_noi_obj,
            activo=True,
        )
        .select_related("empresa_destino")
    )

    mapa = {}
    for m in mapeos:
        clave_norm = _normalizar_texto(m.departamento_noi)
        if clave_norm and m.empresa_destino:
            mapa[clave_norm] = m.empresa_destino
    return mapa


def _obtener_nombre_catalogo_noi(cursor, tabla: str, clave: str | None) -> str | None:
    """
    Consulta el campo NOMBRE en una tabla de catálogo de NOI (ej. DEPTOS08 o PUESTOS08)
    por su CLAVE.
    """
    if not clave:
        return None

    sql = f"""
        SELECT FIRST 1 NOMBRE
        FROM {tabla}
        WHERE TRIM(CLAVE) = %s
    """
    try:
        cursor.execute(sql, [str(clave).strip()])
        row = cursor.fetchone()
        if row and row[0]:
            return _limpiar_str(row[0])
    except Exception as exc:
        logger.debug("No se pudo consultar %s para clave %s: %s", tabla, clave, exc)

    return None


def _obtener_nombre_departamento_noi(cursor, num_empresa: str, clave_depto: str | None) -> str | None:
    if not clave_depto:
        return None
    tabla_deptos = f"DEPTOS{str(num_empresa).strip()}"
    return _obtener_nombre_catalogo_noi(cursor, tabla_deptos, clave_depto)


def _obtener_nombre_puesto_noi(cursor, num_empresa: str, clave_puesto: str | None) -> str | None:
    if not clave_puesto:
        return None
    tabla_puestos = f"PUESTOS{str(num_empresa).strip()}"
    return _obtener_nombre_catalogo_noi(cursor, tabla_puestos, clave_puesto)

def _obtener_o_vincular_catalogo(modelo, empresa: Empresa, valor_noi: str):
    """
    1. Busca si ya existe por `nombre_noi` (ej. nombre='PROGRAMAS', nombre_noi='DOS').
       Lo devuelve intacto sin tocar `nombre`.
    2. Si no existe por `nombre_noi`, busca si existe un registro previo por `nombre`
       (migración de registros viejos donde `nombre_noi` era NULL/vacío) y le llena `nombre_noi`.
    3. Si no existe de ninguna forma, lo crea con `nombre` y `nombre_noi` iguales.
    """
    # 1. Coincidencia exacta/insensible por nombre_noi
    instancia = modelo.objects.filter(
        empresa=empresa,
        nombre_noi__iexact=valor_noi
    ).first()

    if instancia:
        return instancia

    # 2. Coincidencia por nombre interno (para registros creados antes de añadir nombre_noi)
    instancia = modelo.objects.filter(
        empresa=empresa,
        nombre__iexact=valor_noi
    ).first()

    if instancia:
        instancia.nombre_noi = valor_noi
        instancia.save(update_fields=['nombre_noi'])
        return instancia

    # 3. No existe: crear ambos campos con el valor de NOI
    return modelo.objects.create(
        empresa=empresa,
        nombre=valor_noi,
        nombre_noi=valor_noi,
    )

def _resolver_area_y_puesto(
        empresa: Empresa,
        nombre_depto: str | None,
        nombre_puesto: str | None,
        contacto_existente: Contacto | None = None,
):
    """
    Resuelve Area y Puesto vinculados a la empresa destino:
    - Si el contacto ya tiene area o puesto asignados, los conserva para no pisar
      ajustes manuales (como puestos definitivos asignados en el directorio).
    - Si no los tiene, vincula por nombre_noi o nombre, o crea el registro nuevo
      poblando tanto `nombre` como `nombre_noi`.
    """
    area = None
    if contacto_existente and contacto_existente.area_id:
        area = contacto_existente.area
    else:
        nombre_area = _limpiar_str(nombre_depto, max_len=100)
        if nombre_area:
            area = _obtener_o_vincular_catalogo(Area, empresa, nombre_area)

    puesto = None
    if contacto_existente and contacto_existente.puesto_id:
        puesto = contacto_existente.puesto
    else:
        nombre_puesto_limpio = _limpiar_str(nombre_puesto, max_len=100)
        if nombre_puesto_limpio:
            puesto = _obtener_o_vincular_catalogo(Puesto, empresa, nombre_puesto_limpio)

    return area, puesto


def _resolver_razon_social_noi(empresa_noi_obj: EmpresaNOI) -> RazonSocial | None:
    """
    Obtiene la RazonSocial de EmpresaNOI; si no tiene FK asignada, intenta
    encontrarla por nombre a partir del campo texto razon_social de EmpresaNOI.
    """
    if empresa_noi_obj.razon_social_destino_id:
        return empresa_noi_obj.razon_social_destino

    nombre_rs = _limpiar_str(empresa_noi_obj.razon_social)
    if nombre_rs:
        return RazonSocial.objects.filter(nombre__iexact=nombre_rs).first()

    return None


def _resolver_sede_administrativa(
        empresa_noi_obj: EmpresaNOI,
        empresa: Empresa,
        sede_actual: Sede | None = None,
) -> Sede | None:
    """
    Resuelve la sede administrativa respetando la sede ya asignada si existe,
    o usando sede_default de EmpresaNOI / sedes asociadas a la empresa.
    """
    if sede_actual:
        return sede_actual

    if empresa_noi_obj.sede_default:
        return empresa_noi_obj.sede_default

    return (
            Sede.objects.filter(empresas=empresa, activa=True, es_principal=True).first()
            or Sede.objects.filter(empresas=empresa).first()
            or Sede.objects.filter(activa=True).first()
            or Sede.objects.first()
    )


def _resolver_destino_empleado(
        empresa_noi_obj: EmpresaNOI,
        razon_social: RazonSocial | None,
        mapa_deptos: dict[str, Empresa],
        clave_depto: str | None = None,
        nombre_depto: str | None = None,
        contacto_existente: Contacto | None = None,
):
    """
    Resuelve (empresa, razon_social, sede_administrativa) para un empleado de NOI:
    1. Si el contacto ya existe y ya tiene empresa asignada, la conserva para no pisar ajustes manuales.
    2. Si es nuevo (o no tiene empresa), busca coincidencia en MapeoDepartamentoNOI por nombre o clave.
    3. Si no hay mapeo para el departamento, usa empresa_noi_obj.empresa_default (o fallback).
    """
    empresa = None
    if contacto_existente and contacto_existente.empresa_id:
        empresa = contacto_existente.empresa
    else:
        for candidato in (nombre_depto, clave_depto):
            norm = _normalizar_texto(candidato)
            if norm and norm in mapa_deptos:
                empresa = mapa_deptos[norm]
                break

        if not empresa:
            empresa = empresa_noi_obj.empresa_default

        if not empresa and razon_social:
            empresa = razon_social.empresas.order_by("nombre_corto").first()

        if not empresa:
            empresa = Empresa.get_default()

        if (nombre_depto or clave_depto) and _normalizar_texto(nombre_depto or clave_depto) not in mapa_deptos:
            logger.debug(
                "Depto NOI sin mapeo en %s (clave='%s', nombre='%s') -> empresa '%s'",
                empresa_noi_obj.nombre_corto,
                clave_depto,
                nombre_depto,
                empresa.nombre_corto,
            )

    if razon_social and not empresa.razones_sociales.filter(pk=razon_social.pk).exists():
        empresa.razones_sociales.add(razon_social)

    sede_admin = _resolver_sede_administrativa(
        empresa_noi_obj=empresa_noi_obj,
        empresa=empresa,
        sede_actual=contacto_existente.sede_administrativa if contacto_existente else None,
    )

    return empresa, razon_social, sede_admin


def _buscar_contacto_por_clave_y_razon(clave: str, razon_social: RazonSocial | None) -> Contacto | None:
    """
    Busca un Contacto por la dupla (numero_empleado, razon_social).
    """
    qs = Contacto.objects.select_related(
        "empresa",
        "razon_social",
        "sede_administrativa",
        "area",
        "puesto",
    ).filter(numero_empleado=clave)

    if razon_social is not None:
        return qs.filter(razon_social=razon_social).first()
    return qs.filter(razon_social__isnull=True).first()


def sincronizar_empleados_desde_ultimo_periodo(empresa_noi_obj: EmpresaNOI):
    """
    Lee la tabla TB más reciente del periodo en NOI y crea/actualiza Contactos
    identificados por (numero_empleado, razon_social), resolviendo empresa,
    sede, área y puesto sin enviar notificaciones.
    """
    db_alias = get_or_create_noi_connection_alias(empresa_noi_obj)
    periodos = listar_periodos_disponibles(empresa_noi_obj, db_alias)
    if not periodos:
        logger.warning("No se encontraron tablas TB para %s", empresa_noi_obj)
        return {"procesados": 0, "creados": 0, "actualizados": 0, "omitidos": 0}

    ultimo_periodo = periodos[0]
    tabla_tb = ultimo_periodo["table_name"]

    razon_social_destino = _resolver_razon_social_noi(empresa_noi_obj)
    mapa_deptos = _obtener_mapa_departamentos_noi(empresa_noi_obj)
    cache_nombres_depto = {}
    cache_nombres_puesto = {}

    sql = f"""
        SELECT
            CLAVE,
            NOMBRE,
            AP_PAT_,
            AP_MAT_,
            STATUS,
            DEPTO,
            PUESTO,
            FECH_ALTA,
            FECH_BAJA,
            FECH_NACIM,
            EMAIL,
            TELEFONO
        FROM {tabla_tb}
    """

    with connections[db_alias].cursor() as cursor:
        cursor.execute(sql)
        cols = [c[0].lower() for c in cursor.description]
        filas = cursor.fetchall()

        stats = {"procesados": 0, "creados": 0, "actualizados": 0, "omitidos": 0}

        for fila in filas:
            raw = dict(zip(cols, fila))
            stats["procesados"] += 1

            clave = _limpiar_str(raw.get("clave"))
            if not clave:
                stats["omitidos"] += 1
                continue

            primer_nombre, segundo_nombre = _separar_nombre_completo(raw.get("nombre"))
            primer_apellido = (_limpiar_str(raw.get("ap_pat_")) or "").title()
            segundo_apellido = (_limpiar_str(raw.get("ap_mat_")) or "").title() or None

            if not primer_nombre:
                stats["omitidos"] += 1
                continue

            clave_depto = _limpiar_str(raw.get("depto"))
            nombre_depto = None
            if clave_depto:
                if clave_depto not in cache_nombres_depto:
                    cache_nombres_depto[clave_depto] = _obtener_nombre_departamento_noi(
                        cursor=cursor,
                        num_empresa=empresa_noi_obj.numero_empresa,
                        clave_depto=clave_depto,
                    )
                nombre_depto = cache_nombres_depto[clave_depto]

            clave_puesto = _limpiar_str(raw.get("puesto"))
            nombre_puesto = None
            if clave_puesto:
                if clave_puesto not in cache_nombres_puesto:
                    cache_nombres_puesto[clave_puesto] = _obtener_nombre_puesto_noi(
                        cursor=cursor,
                        num_empresa=empresa_noi_obj.numero_empresa,
                        clave_puesto=clave_puesto,
                    )
                nombre_puesto = cache_nombres_puesto[clave_puesto]

            status_noi = (_limpiar_str(raw.get("status")) or "").upper()
            fecha_ingreso = _normalizar_fecha(raw.get("fech_alta"))
            fecha_egreso = _normalizar_fecha(raw.get("fech_baja"))
            fecha_nacimiento = _normalizar_fecha(raw.get("fech_nacim"))
            email_noi = _limpiar_str(raw.get("email"))
            tel_noi = _limpiar_str(raw.get("telefono"))

            if status_noi == "B" and not fecha_egreso:
                fecha_egreso = ultimo_periodo["fecha"]
            elif status_noi in ("A", "R"):
                fecha_egreso = None

            with transaction.atomic():
                contacto = _buscar_contacto_por_clave_y_razon(clave, razon_social_destino)

                empresa_destino, razon_social_final, sede_admin = _resolver_destino_empleado(
                    empresa_noi_obj=empresa_noi_obj,
                    razon_social=razon_social_destino,
                    mapa_deptos=mapa_deptos,
                    clave_depto=clave_depto,
                    nombre_depto=nombre_depto,
                    contacto_existente=contacto,
                )

                if not empresa_destino or not sede_admin:
                    raise ValueError(
                        f"No se pudo resolver Empresa o Sede administrativa para {empresa_noi_obj} (clave {clave})."
                    )

                area_destino, puesto_destino = _resolver_area_y_puesto(
                    empresa=empresa_destino,
                    nombre_depto=nombre_depto,
                    nombre_puesto=nombre_puesto,
                    contacto_existente=contacto,
                )

                if contacto is None:
                    contacto = Contacto.objects.create(
                        numero_empleado=clave,
                        primer_nombre=primer_nombre,
                        segundo_nombre=segundo_nombre,
                        primer_apellido=primer_apellido,
                        segundo_apellido=segundo_apellido,
                        empresa=empresa_destino,
                        razon_social=razon_social_final,
                        sede_administrativa=sede_admin,
                        area=area_destino,
                        puesto=puesto_destino,
                        fecha_nacimiento=fecha_nacimiento,
                        fecha_ingreso=fecha_ingreso,
                        fecha_egreso=fecha_egreso,
                    )
                    stats["creados"] += 1
                else:
                    contacto.primer_nombre = primer_nombre
                    contacto.segundo_nombre = segundo_nombre
                    contacto.primer_apellido = primer_apellido
                    contacto.segundo_apellido = segundo_apellido
                    if razon_social_final and not contacto.razon_social_id:
                        contacto.razon_social = razon_social_final
                    if area_destino and not contacto.area_id:
                        contacto.area = area_destino
                    if puesto_destino and not contacto.puesto_id:
                        contacto.puesto = puesto_destino
                    if fecha_nacimiento and not contacto.fecha_nacimiento:
                        contacto.fecha_nacimiento = fecha_nacimiento
                    if fecha_ingreso and not contacto.fecha_ingreso:
                        contacto.fecha_ingreso = fecha_ingreso
                    contacto.fecha_egreso = fecha_egreso
                    contacto.save()
                    stats["actualizados"] += 1

                if email_noi and "@" in email_noi:
                    EmailContacto.objects.get_or_create(
                        contacto=contacto,
                        email=email_noi.lower(),
                        defaults={"es_principal": not contacto.emails.exists(), "esta_activo": True},
                    )

                if tel_noi:
                    tel_limpio = "".join(ch for ch in tel_noi if ch.isdigit())[:11]
                    if tel_limpio:
                        TelefonoContacto.objects.get_or_create(
                            contacto=contacto,
                            telefono=tel_limpio,
                            extension=None,
                            defaults={"es_principal": not contacto.telefonos.exists(), "esta_activo": True},
                        )

    logger.info("Sync NOI %s (tabla %s): %s", empresa_noi_obj, tabla_tb, stats)
    return stats


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_contactos_noi_task(self):
    """
    Tarea Celery periódica para cargar/actualizar empleados desde el último periodo NOI
    hacia el modelo Contacto usando (numero_empleado, razon_social) como llave lógica.
    """
    resumen_total = {}
    empresas_noi = EmpresaNOI.objects.filter(
        activa=True,
        sincronizar_con_directorio=True,
    ).select_related("razon_social_destino", "empresa_default", "sede_default")

    for emp_noi in empresas_noi:
        clave_cfg = str(emp_noi.numero_empresa)
        try:
            resumen_total[clave_cfg] = sincronizar_empleados_desde_ultimo_periodo(emp_noi)
        except Exception as exc:
            logger.exception("Error sincronizando EmpresaNOI %s: %s", emp_noi, exc)
            raise self.retry(exc=exc)

    return resumen_total
