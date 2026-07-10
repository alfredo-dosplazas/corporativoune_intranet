class CoreRouter:
    # Agregamos las aplicaciones y mapeamos qué app va a qué base de datos
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'asistencias':
            return 'cetnet'
        if model._meta.app_label == 'vs_erp':
            return 'vs_dp'  # Redirige las lecturas de vs_erp a la BD del VS Control Total
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'asistencias':
            return 'cetnet'
        if model._meta.app_label == 'vs_erp':
            return 'vs_dp'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Asistencias solo en cetnet
        if app_label == 'asistencias':
            return db == 'cetnet'

        # CRÍTICO: Bloquear CUALQUIER migración en la base de datos del ERP (vs_dp)
        if db == 'vs_dp' or app_label == 'vs_erp':
            return False

        # Ninguna app debe migrar en intranet
        if db == 'intranet':
            return False

        # Todo lo demás en default
        return db == 'default'