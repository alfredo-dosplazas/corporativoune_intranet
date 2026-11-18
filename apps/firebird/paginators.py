from django.core.paginator import Paginator, Page
from django.db import connections


class FirebirdSQLPaginator(Paginator):
    """
    Paginador de alto rendimiento para Firebird.
    Ejecuta el FIRST / SKIP y mapea las columnas directamente a las instancias del modelo
    en una sola consulta, evitando lentitud y fallos con el ORM.
    """

    def _get_model_and_db(self):
        obj = self.object_list
        model = getattr(obj, 'model', None)
        db_alias = getattr(obj, 'db', 'noi_snb_01')

        if not model:
            for attr in ('data', 'queryset', '_queryset', 'object_list'):
                inner = getattr(obj, attr, None)
                if inner is not None:
                    m = getattr(inner, 'model', None)
                    if m:
                        model = m
                    db = getattr(inner, 'db', None)
                    if db:
                        db_alias = db
                    if not model and hasattr(inner, 'model'):
                        model = inner.model

        return model, db_alias

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page

        model, db_alias = self._get_model_and_db()

        if not model:
            top = bottom + self.per_page
            if top + self.orphans >= self.count:
                top = self.count
            return self._get_page(list(self.object_list)[bottom:top], number, self)

        table_name = model._meta.db_table

        # Consulta nativa completa para traer la página de registros en un solo viaje
        paginated_sql = f"""
            SELECT FIRST {self.per_page} SKIP {bottom} * 
            FROM {table_name}
        """

        with connections[db_alias].cursor() as cursor:
            cursor.execute(paginated_sql)
            columns = [col[0].lower() for col in cursor.description]
            raw_rows = cursor.fetchall()

        if not raw_rows:
            return Page([], number, self)

        # Mapeo directo y ultrarrápido a los atributos del modelo de Django
        items = []
        for row in raw_rows:
            obj = model()
            for i, col_name in enumerate(columns):
                # Buscamos si el modelo tiene un campo mapeado a esa columna o usamos el nombre directo
                field_name = col_name
                for field in model._meta.fields:
                    if field.db_column and field.db_column.lower() == col_name:
                        field_name = field.name
                        break

                # Asignamos el valor limpio al atributo del modelo
                val = row[i]
                # Limpiar espacios en cadenas si Firebird devuelve CHAR con relleno
                if isinstance(val, str):
                    val = val.strip()
                setattr(obj, field_name, val)

            # Marcamos la instancia como ya guardada/existente en BD para el ORM
            obj._state.adding = False
            obj._state.db = db_alias
            items.append(obj)

        return Page(items, number, self)

    @property
    def count(self):
        model, db_alias = self._get_model_and_db()

        if not model:
            c = getattr(self.object_list, "count", None)
            if callable(c):
                return c()
            return len(self.object_list)

        table_name = model._meta.db_table

        with connections[db_alias].cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row = cursor.fetchone()
            return row[0] if row else 0
