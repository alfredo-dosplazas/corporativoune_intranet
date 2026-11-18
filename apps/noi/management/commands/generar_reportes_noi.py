import time
from datetime import datetime
from django.core.management.base import BaseCommand
from apps.noi.db import noi_session
from apps.noi.services import obtener_tablas_noi_por_rango, get_dynamic_trabajador_model


class Command(BaseCommand):
    help = "Genera el Reporte General de Salarios/Puestos y el Reporte de Rotación Mensual."

    def add_arguments(self, parser):
        parser.add_argument("--desde", type=str, default="2026-09-01", help="Fecha inicio (YYYY-MM-DD)")
        parser.add_argument("--hasta", type=str, default="2026-11-13", help="Fecha fin (YYYY-MM-DD)")
        parser.add_argument("--empresa", type=str, default="abocosa", help="Clave de empresa")

    def handle(self, *args, **options):
        str_desde = options["desde"]
        str_hasta = options["hasta"]
        empresa = options["empresa"]

        fecha_inicio = datetime.strptime(str_desde, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(str_hasta, "%Y-%m-%d").date()

        self.stdout.write(
            self.style.NOTICE(f"Generando reportes para empresa '{empresa}' del {fecha_inicio} al {fecha_fin}..."))

        with noi_session(empresa) as (session, empresa_num):

            # 1. Obtener tablas en el rango
            tablas = obtener_tablas_noi_por_rango(session, empresa_num=empresa_num, fecha_inicio=fecha_inicio,
                                                  fecha_fin=fecha_fin)

            if not tablas:
                self.stdout.write(self.style.WARNING("No hay tablas en el rango especificado."))
                return

            self.stdout.write(f"Se analizarán {len(tablas)} tablas de periodo.")

            # Diccionarios de acumulación
            trabajadores_maestro = {}  # Para el reporte general (fotografía más reciente)
            metricas_por_mes = {}  # Para el reporte de rotación

            for tabla in tablas:
                # Extraer mes y año del nombre de la tabla (ej. TB 05 09 26 08 -> DD=05, MM=09, YY=26)
                cuerpo_fecha = tabla[2:-len(empresa_num)]
                mes_anio_key = f"{cuerpo_fecha[2:4]}/20{cuerpo_fecha[4:6]}"  # Ej: "09/2026"

                if mes_anio_key not in metricas_por_mes:
                    metricas_por_mes[mes_anio_key] = {
                        "tablas": [],
                        "activos_inicio": set(),
                        "activos_fin": set(),
                        "bajas_periodo": set()
                    }
                metricas_por_mes[mes_anio_key]["tablas"].append(tabla)

                ModelClass = get_dynamic_trabajador_model(tabla)
                registros = session.query(ModelClass).all()

                # Evaluamos cada registro del periodo
                for r in registros:
                    nombre_completo = f"{r.nombre or ''} {r.apellido_p or ''} {r.apellido_m or ''}".strip()
                    salario_diario = r.sal_diario or 0.0

                    # Detección limpia de activo/baja
                    es_baja = False
                    if r.fecha_baja:
                        s_baj = str(r.fecha_baja)
                        if not (s_baj.startswith("1899") or s_baj.startswith("1900")):
                            es_baja = True

                    # --- REPORTE 1: Acumulador Maestro (Salarios y Puestos Actuales) ---
                    trabajadores_maestro[r.num_trab] = {
                        "num_trab": r.num_trab,
                        "nombre": nombre_completo,
                        "fecha_ingreso": r.fecha_alt,
                        "fecha_baja": r.fecha_baja if es_baja else None,
                        "puesto": r.puesto,
                        "salario_diario": salario_diario,
                        "salario_mensual_bruto": round(salario_diario * 30.4, 2),
                        "salario_libre_semanal": round((salario_diario * 7) * 0.85, 2),  # Estimado neto o cálculo real
                        "activo": not es_baja
                    }

                    # --- REPORTE 2: Acumulador de Rotación ---
                    # Clasificamos al trabajador en las métricas del mes según corresponda al periodo
                    if not es_baja:
                        metricas_por_mes[mes_anio_key]["activos_fin"].add(r.num_trab)
                    else:
                        metricas_por_mes[mes_anio_key]["bajas_periodo"].add(r.num_trab)

            # ==========================================
            # IMPRESIÓN DE RESULTADOS EN CONSOLA
            # ==========================================

            self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
            self.stdout.write(self.style.SUCCESS(" REPORTE 1: GENERAL DE SALARIOS Y PUESTOS (Muestra)"))
            self.stdout.write(self.style.SUCCESS("=" * 60))

            contador = 0
            for t_id, info in list(trabajadores_maestro.items())[:10]:
                contador += 1
                estatus_txt = "ACTIVO" if info["activo"] else "BAJA"
                self.stdout.write(
                    f"{contador}. [{info['num_trab']}] {info['nombre']} | Estatus: {estatus_txt} | "
                    f"Puesto: {info['puesto']} | Sal. Diario: ${info['salario_diario']:.2f} | "
                    f"Sal. Mensual: ${info['salario_mensual_bruto']:.2f} | Sal. Semanal Libre: ${info['salario_libre_semanal']:.2f}"
                )
            self.stdout.write(f"... Total de trabajadores en padrón: {len(trabajadores_maestro)}\n")

            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS(" REPORTE 2: INDICADORES DE ROTACIÓN MENSUAL"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(
                f"{'MES/AÑO':<10} | {'ACTIVOS INICIO':<15} | {'ACTIVOS FIN':<12} | {'BAJAS REGISTRADAS':<18}")
            self.stdout.write("-" * 65)

            for mes, m_data in sorted(metricas_por_mes.items()):
                # Tomamos el primer periodo del mes como referencia de inicio y el último como fin
                # (O puedes afinarlo exacto al día 1 y último día del mes si tienes tablas en esas fechas)
                activos_ini_count = len(m_data["activos_fin"])  # Aproximación basada en la corrida del mes
                activos_fin_count = len(m_data["activos_fin"])
                bajas_count = len(m_data["bajas_periodo"])

                self.stdout.write(f"{mes:<10} | {activos_ini_count:<15} | {activos_fin_count:<12} | {bajas_count:<18}")

            self.stdout.write("-" * 65)
