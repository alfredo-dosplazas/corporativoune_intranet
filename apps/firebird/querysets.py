from datetime import datetime, timedelta
from django.db import models, connections


class FirebirdQuerySet(models.QuerySet):
    """
    QuerySet que inyecta FIRST/SKIP en la consulta compilada por Django
    y precarga en lote puestos y recibos del periodo para máximo rendimiento.
    """

    def _get_sql_with_first_skip(self, limit: int, offset: int):
        compiler = self.query.get_compiler(self.db)
        sql, params = compiler.as_sql()

        # Inyectar FIRST / SKIP justo después del SELECT principal
        sql_upper = sql.upper()
        if "SELECT " in sql_upper:
            idx = sql_upper.find("SELECT ") + 7
            sql_paginado = f"SELECT FIRST {limit} SKIP {offset} {sql[idx:]}"
        else:
            sql_paginado = sql

        return sql_paginado, params

    def __getitem__(self, k):
        if isinstance(k, slice):
            start = int(k.start) if k.start is not None else 0
            stop = int(k.stop) if k.stop is not None else 10
            limit = stop - start

            if limit <= 0:
                return []

            db_alias = self.db
            model = self.model

            # 1. Obtenemos el SQL generado por Django con FIRST/SKIP
            sql, params = self._get_sql_with_first_skip(limit, start)

            # 2. Ejecución con cursor directo para mapear de forma segura attname (puesto_id)
            with connections[db_alias].cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0].lower() for col in cursor.description]
                raw_rows = cursor.fetchall()

            if not raw_rows:
                return []

            items = []
            puestos_ids = set()

            for row in raw_rows:
                obj = model()
                for i, col_name in enumerate(columns):
                    attr_name = col_name

                    # Buscamos el campo en el modelo
                    for field in model._meta.fields:
                        if (field.db_column and field.db_column.lower() == col_name) or (
                                field.name.lower() == col_name):
                            # field.attname nos da 'puesto_id' para ForeignKeys
                            # evitando el ValueError
                            attr_name = field.attname
                            break

                    val = row[i]
                    if isinstance(val, str):
                        val = val.strip()

                    # Si es puesto_id, guardamos el ID para precargarlo en lote
                    if attr_name == 'puesto_id' and val is not None:
                        try:
                            val = int(val)
                            puestos_ids.add(val)
                        except (ValueError, TypeError):
                            pass

                    setattr(obj, attr_name, val)

                obj._state.adding = False
                obj._state.db = db_alias
                items.append(obj)

            # 3. PRECARGA EN LOTE DE PUESTOS (Resuelve obj.puesto sin queries extra)
            if puestos_ids and hasattr(model, 'puesto'):
                try:
                    PuestoModel = model.puesto.field.remote_field.model
                    puestos_map = {
                        p.pk: p for p in PuestoModel.objects.using(db_alias).filter(pk__in=puestos_ids)
                    }
                    for obj in items:
                        pid = getattr(obj, 'puesto_id', None)
                        if pid in puestos_map:
                            model.puesto.field.set_cached_value(obj, puestos_map[pid])
                except Exception:
                    pass

            # 4. PRECARGA EN LOTE DE RECIBOS DE NÓMINA DEL PERIODO
            table_name = model._meta.db_table
            if table_name.startswith("TB") and len(table_name) >= 8 and items:
                self._prefetch_recibos_en_lote(items, table_name, db_alias)

            return items

        return super().__getitem__(k)

    def _prefetch_recibos_en_lote(self, items, table_name, db_alias):
        """
        Precarga los recibos de todos los trabajadores obtenidos en una sola consulta.
        """
        try:
            dd = int(table_name[2:4])
            mm = int(table_name[4:6])
            yy_short = int(table_name[6:8])
            sufijo_anio = table_name[6:8]
            num_empresa = "".join(filter(str.isdigit, table_name))[-2:]
            f_periodo = datetime(yy_short + 2000, mm, dd).date()

            claves = [str(obj.clave).strip() for obj in items if getattr(obj, 'clave', None)]
            if not claves:
                return

            from apps.noi.models import get_noi_dynamic_model, ReciboNOIBase

            tabla_recibos = f"RECIBOSNOI{sufijo_anio}{num_empresa}"
            ReciboModel = get_noi_dynamic_model(ReciboNOIBase, tabla_recibos, num_empresa)

            fecha_min = f_periodo - timedelta(days=3)
            fecha_max = f_periodo + timedelta(days=3)

            recibos = ReciboModel.objects.using(db_alias).filter(
                cve_trab__in=claves,
                f_nomina__range=(fecha_min, fecha_max)
            )

            recibos_map = {}
            for r in recibos:
                cve = str(r.cve_trab).strip()
                recibos_map.setdefault(cve, []).append(r)

            for obj in items:
                cve = str(obj.clave).strip()
                obj._recibos_periodo_cache = recibos_map.get(cve, [])

        except Exception as e:
            pass

    def count(self):
        if self._result_cache is not None:
            return len(self._result_cache)

        compiler = self.query.get_compiler(self.db)
        sql, params = compiler.as_sql()

        sql_upper = sql.upper()
        if " ORDER BY " in sql_upper:
            sql = sql[:sql_upper.rfind(" ORDER BY ")]

        count_sql = f"SELECT COUNT(*) FROM ({sql}) AS count_subquery"

        with connections[self.db].cursor() as cursor:
            cursor.execute(count_sql, params)
            row = cursor.fetchone()
            return row[0] if row else 0


class FirebirdManager(models.Manager):
    def get_queryset(self):
        return FirebirdQuerySet(self.model, using=self._db)
