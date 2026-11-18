class NOIDatabaseRouter:
    route_app_labels = {'noi_raw'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'noi_snb_01'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return None
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'noi_snb_01' or app_label in self.route_app_labels:
            return False
        return None
