import time
from datetime import datetime
from django.core.management.base import BaseCommand

from apps.noi.db import noi_session
from apps.noi.exportar.excel import generar_reporte_empleados_excel
from apps.noi.services import (
    obtener_catalogo_puestos,
    obtener_ultimos_recibos_trabajadores,  # <--- Usamos la nueva función orientada a la última nómina
    obtener_tablas_noi_por_rango,
    get_dynamic_trabajador_model,
)


class Command(BaseCommand):
    help = "Genera el Reporte General considerando el salario libre exacto de la última nómina."

    def add_arguments(self, parser):
        parser.add_argument("--desde", type=str, default="2026-09-01", help="Fecha inicio (YYYY-MM-DD)")
        parser.add_argument("--hasta", type=str, default="2026-11-13", help="Fecha fin (YYYY-MM-DD)")
        parser.add_argument("--empresa", type=str, default="abocosa", help="Clave de empresa")

    def handle(self, *args, **options):
        fecha_inicio = datetime.strptime(options["desde"], "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(options["hasta"], "%Y-%m-%d").date()
        empresa = options["empresa"]
        anio_sufijo = fecha_inicio.strftime("%y")  # Ej: "26"

        self.stdout.write(
            self.style.NOTICE(f"Generando reportes para la empresa '{empresa}' del {fecha_inicio} al {fecha_fin}...")
        )

        tiempo_inicio_global = time.time()

        with noi_session(empresa) as (session, empresa_num):
            # 1. Cargar catálogo global de puestos
            self.stdout.write(f"Cargando catálogo global de puestos (PUESTOS{empresa_num})...")
            puestos_dict = obtener_catalogo_puestos(session, empresa_num)

            # 2. Cargar el ÚLTIMO recibo fiscal del año por trabajador
            self.stdout.write(f"Cargando últimos recibos de nómina (RECIBOSNOI{anio_sufijo}{empresa_num})...")
            ultimos_recibos_dict = obtener_ultimos_recibos_trabajadores(session, anio_sufijo, empresa_num)
            self.stdout.write(f"Se obtuvieron los datos de la última nómina para {len(ultimos_recibos_dict)} trabajadores.")

            # 3. Obtener tablas de periodo en el rango solicitado
            tablas_periodo = obtener_tablas_noi_por_rango(
                session, empresa_num=empresa_num, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
            )

            if not tablas_periodo:
                self.stdout.write(self.style.WARNING("No hay tablas de periodo en el rango especificado."))
                return

            self.stdout.write(f"Se analizarán {len(tablas_periodo)} tablas de periodo.")

            trabajadores_maestro = {}
            metricas_por_mes = {}

            for tabla in tablas_periodo:
                cuerpo_fecha = tabla[2:-len(empresa_num)]
                mes_anio_key = f"{cuerpo_fecha[2:4]}/20{cuerpo_fecha[4:6]}"  # Ej: "09/2026"

                if mes_anio_key not in metricas_por_mes:
                    metricas_por_mes[mes_anio_key] = {
                        "activos_inicio": set(),
                        "activos_fin": set(),
                        "bajas_mes": set(),
                        "primer_periodo_procesado": False,
                    }

                TrabajadorModel = get_dynamic_trabajador_model(tabla)
                registros_trabajadores = session.query(TrabajadorModel).all()
                activos_este_periodo = set()

                for trabajador in registros_trabajadores:
                    nombre_completo = f"{trabajador.nombre or ''} {trabajador.apellido_p or ''} {trabajador.apellido_m or ''}".strip()

                    salario_diario = trabajador.sal_diario or 0.0
                    salario_mensual_bruto = round(salario_diario * 30.4, 2)

                    # Obtener estrictamente el NETO de su última nómina registrada
                    datos_ultimo_recibo = ultimos_recibos_dict.get(trabajador.num_trab, {})
                    salario_libre_semanal = datos_ultimo_recibo.get("neto_pagado", 0.0)

                    # Si por alguna razón no tiene recibo fiscal timbrado en esa tabla, caemos a un estimado seguro del sueldo diario
                    if salario_libre_semanal <= 0:
                        salario_libre_semanal = round((salario_diario * 7) * 0.85, 2)

                    salario_mensual_libre = round(salario_libre_semanal * 4.33, 2)

                    # Validación de fecha de baja
                    es_baja = False
                    fecha_baja_limpia = None
                    if trabajador.fecha_baja:
                        str_baja = str(trabajador.fecha_baja)
                        if not (str_baja.startswith("1899") or str_baja.startswith("1900")):
                            es_baja = True
                            fecha_baja_limpia = trabajador.fecha_baja

                    # Resolución de puesto
                    puesto_id = trabajador.puesto or 0
                    puesto_nombre = puestos_dict.get(puesto_id, f"Desconocido ({puesto_id})")

                    # Consolidación del maestro de trabajadores (foto más reciente / última nómina)
                    trabajadores_maestro[trabajador.num_trab] = {
                        "num_trab": trabajador.num_trab,
                        "nombre": nombre_completo,
                        "fecha_ingreso": trabajador.fecha_alt,
                        "fecha_baja": fecha_baja_limpia,
                        "puesto": puesto_nombre,
                        "salario_diario": salario_diario,
                        "salario_mensual_bruto": salario_mensual_bruto,
                        "salario_libre_semanal": salario_libre_semanal,
                        "salario_mensual_libre": salario_mensual_libre,
                        "estatus": "BAJA" if es_baja else "ACTIVO", # o directo estatus
                    }
                    # Corrección limpia para el estatus en el diccionario:
                    trabajadores_maestro[trabajador.num_trab]["estatus"] = "BAJA" if es_baja else "ACTIVO"

                    # Acumulador de rotación mensual
                    if not es_baja:
                        activos_este_periodo.add(trabajador.num_trab)
                    else:
                        if fecha_baja_limpia and fecha_baja_limpia.strftime("%m/%Y") == mes_anio_key:
                            metricas_por_mes[mes_anio_key]["bajas_mes"].add(trabajador.num_trab)

                if not metricas_por_mes[mes_anio_key]["primer_periodo_procesado"]:
                    metricas_por_mes[mes_anio_key]["activos_inicio"] = activos_este_periodo
                    metricas_por_mes[mes_anio_key]["primer_periodo_procesado"] = True

                metricas_por_mes[mes_anio_key]["activos_fin"] = activos_este_periodo

            # 4. Exportación a Excel
            ruta_excel = generar_reporte_empleados_excel(
                empresa=empresa,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                trabajadores=list(trabajadores_maestro.values()),
                metricas_mes=metricas_por_mes,
            )

            tiempo_total = time.time() - tiempo_inicio_global
            self.stdout.write(self.style.SUCCESS(f"\n¡Proceso completado en {tiempo_total:.2f} segundos!"))
            self.stdout.write(self.style.SUCCESS(f"Archivo Excel guardado en: {ruta_excel}"))