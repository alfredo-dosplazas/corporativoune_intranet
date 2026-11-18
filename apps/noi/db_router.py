from django.conf import settings


def get_or_create_noi_connection_alias(empresa_obj):
    """
    Registra o recupera dinámicamente el alias de conexión en Django
    para la base de datos Firebird específica de la EmpresaNOI.
    """
    alias = f"noi_empresa_{empresa_obj.id}"

    if alias not in settings.DATABASES:
        settings.DATABASES[alias] = {
            'ENGINE': 'django_firebird',
            'NAME': empresa_obj.db_path,
            'USER': settings.FIREBIRD_DB_USER or 'SYSDBA',
            'PASSWORD': settings.FIREBIRD_DB_PASSWORD or '',
            'HOST': empresa_obj.db_host or 'localhost',
            'PORT': '3050',
            'OPTIONS': {
                'charset': 'UTF8',
                'lock_timeout': 10,
            },
            'TIME_ZONE': None,
            'CONN_HEALTH_CHECKS': False,
            'CONN_MAX_AGE': 0,
            'AUTOCOMMIT': True,
            'ATOMIC_REQUESTS': False,
        }
    return alias
