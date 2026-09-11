from contextlib import contextmanager
import fdb
from django.conf import settings

FB_CLIENT_PATH = r"C:/Program Files/Firebird/Firebird_2_5/bin/fbclient.dll"
fdb.load_api(FB_CLIENT_PATH)

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

engine_test = create_engine(
    f"firebird+fdb://{settings.FIREBIRD_DB_USER}:{settings.FIREBIRD_DB_PASSWORD}@127.0.0.1:3050/C:/Program Files (x86)/Common Files/Aspel/Sistemas Aspel/COI10.00/Datos/Empresa1/COI10EMPRE1.FDB?charset=UTF8",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

engine_dominum = create_engine(
    f"firebird+fdb://{settings.FIREBIRD_DB_USER}:{settings.FIREBIRD_DB_PASSWORD}@{settings.DPSERVER_HOST}:3050/{settings.FIREBIRD_DB_COI_PATH}?charset=UTF8",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

EMPRESAS_CONFIG = {
    "test": {
        "suffix": "01",
        "SessionFactory": sessionmaker(bind=engine_test),
    },
    "dominum": {
        "suffix": "23",
        "SessionFactory": sessionmaker(bind=engine_dominum),
    },
}


@contextmanager
def coi_session(empresa="dominum"):
    if getattr(settings, 'DEBUG', False):
        empresa = "test"

    config = EMPRESAS_CONFIG.get(empresa)
    if not config:
        raise ValueError(f"Empresa '{empresa}' no soportada.")

    session = config["SessionFactory"]()
    try:
        yield session, config["suffix"]
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
