class CoreRouter:
    route_app_labels = {'asistencias'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'cetnet'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'cetnet'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Asistencias solo en cetnet
        if app_label in self.route_app_labels:
            return db == 'cetnet'

        # Ninguna app debe migrar en intranet
        if db == 'intranet':
            return False

        # Todo lo demás en default
        return db == 'default'