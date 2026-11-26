from decimal import Decimal, ROUND_HALF_UP
from django.core.management.base import BaseCommand, CommandError
from apps.sae.db import sae_session
from apps.sae.models_sae import get_sae_models
from apps.listas_precios.models import LineaReglaPrecio, ProductoPrecioOverride


class Command(BaseCommand):
    help = 'Calcula y actualiza directamente los precios en la BD Firebird de SAE (DOMINUM o ABRAHAM).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=str,
            required=True,
            choices=['dominum', 'abraham'],
            help='Empresa destino en SAE (dominum o abraham).'
        )
        parser.add_argument(
            '--lineas',
            nargs='+',
            type=str,
            help='Claves de línea a actualizar separadas por espacio (ej. --lineas KBX HERR). Si se omite, actualiza todas.'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula el proceso y muestra los cambios sin guardar en Firebird.'
        )

    def handle(self, *args, **options):
        empresa = options['empresa'].lower()
        lineas_filtro = [l.strip()[:5] for l in options['lineas']] if options['lineas'] else None
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING(
            f"Iniciando sincronización para {empresa.upper()} (Dry-run: {dry_run})..."
        ))

        # 1. Cargar reglas y overrides desde Django (SQLite/Postgres/MySQL)
        reglas_qs = LineaReglaPrecio.objects.all()
        if lineas_filtro:
            reglas_qs = reglas_qs.filter(cve_lin__in=lineas_filtro)

        reglas_dict = {
            f"{(r.cve_lin or '').strip()}_{r.num_lista}": {
                'desc': Decimal(str(r.porcentaje_descuento or 0)),
                'util': Decimal(str(r.porcentaje_utilidad or 0)),
            }
            for r in reglas_qs
        }

        overrides_dict = {
            o.cve_art.strip(): Decimal(str(o.precio_lista_custom))
            for o in ProductoPrecioOverride.objects.all()
        }

        # 2. Conectar a Firebird SAE
        # Si sae_session acepta un parámetro (ej. sae_session(empresa=target_empresa)), pásalo aquí:
        with sae_session(empresa) as (db_sae, suffix):
            m = get_sae_models(suffix)

            # Obtener listas de precios activas en SAE
            listas_sae = db_sae.query(m.Precio.clave).filter(m.Precio.status == 'A').all()
            claves_listas = [l.clave for l in listas_sae]

            # Consultar productos activos y su precio base (Lista 3)
            query_prods = db_sae.query(
                m.Producto.clave,
                m.Producto.linea,
                m.PrecioPorProducto.precio.label('precio_base_sae')
            ).outerjoin(
                m.PrecioPorProducto,
                (m.Producto.clave == m.PrecioPorProducto.cve_art) & (m.PrecioPorProducto.cve_precio == 3)
            ).filter(m.Producto.status == 'A')

            if lineas_filtro:
                query_prods = query_prods.filter(m.Producto.linea.in_(lineas_filtro))

            productos = query_prods.all()

            if not productos:
                self.stdout.write(self.style.ERROR("No se encontraron productos activos con esos filtros."))
                return

            claves_prods = [p.clave for p in productos]

            # Precargar en memoria todos los registros actuales de PRECIO_X_PROD para evitar miles de SELECTs
            precios_existentes_qs = db_sae.query(m.PrecioPorProducto).filter(
                m.PrecioPorProducto.cve_art.in_(claves_prods)
            ).all()

            mapa_precios_sae = {
                (px.cve_art.strip(), px.cve_precio): px
                for px in precios_existentes_qs
            }

            actualizados = 0
            insertados = 0

            for prod in productos:
                cve_art_raw = prod.clave  # Conservamos el padding original de Firebird para FK
                cve_art = cve_art_raw.strip()
                linea = (prod.linea or '').strip()

                precio_sae = Decimal(str(prod.precio_base_sae or 0))
                precio_custom = overrides_dict.get(cve_art)
                precio_base_final = precio_custom if precio_custom is not None else precio_sae

                # Si hay override, también actualizamos la Lista 3 (Base) en SAE
                if precio_custom is not None:
                    self._upsert_precio(
                        db_sae, m, mapa_precios_sae, cve_art_raw, cve_art, 3, precio_custom,
                        stats={'upd': 0, 'ins': 0}  # Opcional: contar aparte
                    )

                # Calcular y aplicar cada lista de precio según las reglas de la línea
                for num_lista in claves_listas:
                    # Si hay override en Lista 3, ya se asignó arriba; no sobrescribir Lista 3 con fórmula si no aplica
                    if num_lista == 3 and precio_custom is not None:
                        continue

                    regla = reglas_dict.get(f"{linea}_{num_lista}")
                    if not regla:
                        continue

                    desc_pct = regla['desc'] / Decimal('100')
                    util_pct = regla['util'] / Decimal('100')

                    if util_pct >= Decimal('1'):
                        precio_calculado = Decimal('0.00')
                    else:
                        precio_calculado = (precio_base_final * (Decimal('1') - desc_pct)) / (Decimal('1') - util_pct)

                    precio_final = float(precio_calculado.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

                    registro_existente = mapa_precios_sae.get((cve_art, num_lista))

                    if registro_existente:
                        if round(float(registro_existente.precio or 0), 2) != precio_final:
                            registro_existente.precio = precio_final
                            actualizados += 1
                    else:
                        nuevo_precio = m.PrecioPorProducto(
                            cve_art=cve_art_raw,
                            cve_precio=num_lista,
                            precio=precio_final
                        )
                        db_sae.add(nuevo_precio)
                        insertados += 1

            if dry_run:
                db_sae.rollback()
                self.stdout.write(self.style.SUCCESS(
                    f"[SIMULACIÓN] Se habrían actualizado {actualizados} precios e insertado {insertados} nuevos."
                ))
            else:
                try:
                    db_sae.commit()
                    self.stdout.write(self.style.SUCCESS(
                        f"¡Éxito en {empresa.upper()}! Actualizados: {actualizados} | Insertados: {insertados}."
                    ))
                except Exception as e:
                    db_sae.rollback()
                    raise CommandError(f"Error al hacer commit en Firebird: {e}")

    def _upsert_precio(self, db_sae, m, mapa_precios_sae, cve_art_raw, cve_art, num_lista, valor, stats):
        valor_float = float(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        reg = mapa_precios_sae.get((cve_art, num_lista))
        if reg:
            reg.precio = valor_float
        else:
            db_sae.add(m.PrecioPorProducto(
                cve_art=cve_art_raw,
                cve_precio=num_lista,
                precio=valor_float
            ))