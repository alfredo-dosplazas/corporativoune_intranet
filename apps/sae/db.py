from contextlib import contextmanager
import fdb
from django.conf import settings

FB_CLIENT_PATH = r"C:/Program Files/Firebird/Firebird_2_5/bin/fbclient.dll"
fdb.load_api(FB_CLIENT_PATH)

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

EMPRESAS_CONFIG = {
    "dominum": {
        "suffix": "01",
        "engine": create_engine(
            f"firebird+fdb://{settings.FIREBIRD_DB_USER}:{settings.FIREBIRD_DB_PASSWORD}@{settings.DOMINUM_HOST}:3050/{settings.FIREBIRD_DB_DOMINUM_PATH}?charset=UTF8",
            pool_pre_ping=True,
        )
    },
    "abraham": {
        "suffix": "03",
        "engine": create_engine(
            f"firebird+fdb://{settings.FIREBIRD_DB_USER}:{settings.FIREBIRD_DB_PASSWORD}@{settings.DOMINUM_HOST}:3050/{settings.FIREBIRD_DB_ABRAHAM_PATH}?charset=UTF8",
            pool_pre_ping=True,
        )
    },
}


@contextmanager
def sae_session(empresa="dominum"):
    config = EMPRESAS_CONFIG.get(empresa)
    if not config:
        raise ValueError(f"Empresa '{empresa}' no soportada.")

    Session = sessionmaker(bind=config["engine"])
    session = Session()
    try:
        yield session, config["suffix"]
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
