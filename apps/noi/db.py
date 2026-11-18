from contextlib import contextmanager
import fdb
from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Carga de la API de Firebird (Firebird 2.5)
FB_CLIENT_PATH = getattr(settings, 'FIREBIRD_CLIENT_PATH', r"C:/Program Files/Firebird/Firebird_2_5/bin/fbclient.dll")
fdb.load_api(FB_CLIENT_PATH)

# Caché global en memoria para los engines de SQLAlchemy por empresa y evitar reconexiones pesadas
_ENGINE_CACHE = {}


def obtener_o_crear_engine_firebird(host, db_path, user, password):
    """Crea o recupera de caché un engine de SQLAlchemy para una ruta de Firebird específica."""
    connection_key = f"{host}:{db_path}:{user}"
    if connection_key in _ENGINE_CACHE:
        return _ENGINE_CACHE[connection_key]

    engine = create_engine(
        f"firebird+fdb://{user}:{password}@{host}:3050/{db_path}?charset=UTF8",
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )
    _ENGINE_CACHE[connection_key] = engine
    return engine


@contextmanager
def noi_session(empresa_clave_o_obj):
    """
    Context manager híbrido para sesiones SQLAlchemy con Firebird en Aspel NOI.
    Soporta recibir tanto un string (ej. "abocosa", "snb") como una instancia del modelo Django `EmpresaNoi`.

    Uso:
        with noi_session("abocosa") as (session, empresa_num):
            ...
    """
    from apps.noi.models import EmpresaNOI  # Importación local para evitar dependencias circulares

    host = getattr(settings, "DPSERVER_HOST", "localhost")
    user = getattr(settings, "FIREBIRD_DB_USER", "SYSDBA")
    password = getattr(settings, "FIREBIRD_DB_PASSWORD", "masterkey")

    db_path = None
    num_empresa = "08"

    # Caso 1: El parámetro es una instancia del modelo de Django `EmpresaNoi`
    if isinstance(empresa_clave_o_obj, EmpresaNOI):
        empresa_obj = empresa_clave_o_obj
        host = empresa_obj.db_host or host
        db_path = empresa_obj.db_path
        user = empresa_obj.db_user or user
        password = empresa_obj.db_password or password
        num_empresa = empresa_obj.numero_empresa

    # Caso 2: El parámetro es un string (clave corta como "abocosa" o "snb")
    elif isinstance(empresa_clave_o_obj, str):
        clave = empresa_clave_o_obj.lower()

        # Intentar buscar primero en la base de datos de Django
        empresa_db = EmpresaNOI.objects.filter(nombre_corto=clave, activa=True).first()
        if empresa_db:
            host = empresa_db.db_host or host
            db_path = empresa_db.db_path
            user = empresa_db.db_user or user
            password = empresa_db.db_password or password
            num_empresa = empresa_db.numero_empresa
        else:
            # Fallback a settings / configuración estática si aún no está en la BD
            if clave == "snb":
                db_path = getattr(settings, "FIREBIRD_DB_NOI_SNB_PATH", "")
                num_empresa = "01"
            elif clave == "abocosa":
                db_path = getattr(settings, "FIREBIRD_DB_NOI_ABOCOSA_PATH", "")
                num_empresa = "08"
            else:
                raise ValueError(
                    f"Empresa NOI '{clave}' no encontrada en la base de datos ni en la configuración estática.")
    else:
        raise TypeError("El parámetro de empresa debe ser una cadena (string) o una instancia de EmpresaNoi.")

    if not db_path:
        raise ValueError(
            f"La ruta de la base de datos Firebird para la empresa '{empresa_clave_o_obj}' no está configurada.")

    # Crear engine y sessionmaker dinámico
    engine = obtener_o_crear_engine_firebird(host, db_path, user, password)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()

    try:
        yield session, num_empresa
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()