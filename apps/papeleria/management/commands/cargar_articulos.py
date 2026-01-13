from collections import defaultdict

from django.core.management import BaseCommand
from django.db import connections

from apps.core.models import Empresa
from apps.papeleria.models.articulos import Unidad, Articulo


class Command(BaseCommand):
    help = 'Cargar artículos de papelería'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Iniciando migración...")

        intranet_cursor = connections['intranet'].cursor()

        # ======================
        # UNIDADES
        # ======================
        intranet_cursor.execute("""
            SELECT id, nombre, clave
            FROM papeleria_unidad
        """)
        unidades = intranet_cursor.fetchall()

        for row in unidades:
            Unidad.objects.update_or_create(
                id=row[0],
                defaults={
                    'nombre': row[1],
                    'clave': row[2],
                }
            )

        self.stdout.write(f"✅ Unidades migradas: {len(unidades)}")

        # ======================
        # ARTÍCULOS
        # ======================
        intranet_cursor.execute("""
            SELECT id, foto, codigo_vs_dp, numero, nombre,
                   precio, impuesto, unidad_id, es_cuadro_basico
            FROM papeleria_articulo
        """)
        articulos = intranet_cursor.fetchall()

        # ======================
        # RELACIONES ARTICULO-EMPRESA
        # ======================
        intranet_cursor.execute("""
            SELECT articulo_id, empresa_id
            FROM papeleria_articulo_empresas
        """)
        relaciones = intranet_cursor.fetchall()

        # Agrupar por articulo_id
        empresas_por_articulo = defaultdict(list)
        for articulo_id, empresa_id in relaciones:
            empresas_por_articulo[articulo_id].append(empresa_id)

        # ======================
        # MIGRACIÓN FINAL
        # ======================
        for row in articulos:
            articulo_id = row[0]

            articulo, _ = Articulo.objects.update_or_create(
                id=articulo_id,
                defaults={
                    'imagen': row[1],
                    'codigo_vs_dp': row[2],
                    'numero_papeleria': row[3],
                    'nombre': row[4],
                    'precio': row[5],
                    'impuesto': row[6],
                    'unidad_id': row[7],
                    'es_cuadro_basico': row[8],
                    'mostrar_en_sitio': row[8],
                }
            )

            # Agregar empresas relacionadas
            empresa_ids = empresas_por_articulo.get(articulo_id, [])
            if empresa_ids:
                articulo.empresas.set(
                    Empresa.objects.filter(id__in=empresa_ids)
                )

        self.stdout.write(f"✅ Artículos migrados: {len(articulos)}")
        self.stdout.write("🎉 Migración finalizada correctamente")
