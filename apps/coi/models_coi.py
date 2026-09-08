# apps/coi/models.py
from types import SimpleNamespace
from sqlalchemy import Column, String, Date, Float, DateTime, Integer, SmallInteger
from apps.coi.db import Base

_MODEL_CACHE = {}


class FolioMixin:
    tippol = Column('TIPPOL', String(2), primary_key=True)
    ejercicio = Column('EJERCICIO', Integer, primary_key=True)

    # Folios por periodo (01 al 14)
    folio01 = Column('FOLIO01', Integer, default=0)
    folio02 = Column('FOLIO02', Integer, default=0)
    folio03 = Column('FOLIO03', Integer, default=0)
    folio04 = Column('FOLIO04', Integer, default=0)
    folio05 = Column('FOLIO05', Integer, default=0)
    folio06 = Column('FOLIO06', Integer, default=0)
    folio07 = Column('FOLIO07', Integer, default=0)
    folio08 = Column('FOLIO08', Integer, default=0)
    folio09 = Column('FOLIO09', Integer, default=0)
    folio10 = Column('FOLIO10', Integer, default=0)
    folio11 = Column('FOLIO11', Integer, default=0)
    folio12 = Column('FOLIO12', Integer, default=0)
    folio13 = Column('FOLIO13', Integer, default=0)
    folio14 = Column('FOLIO14', Integer, default=0)

    # Asignaciones (01 al 14)
    asig01 = Column('ASIG01', Integer, default=0)
    asig02 = Column('ASIG02', Integer, default=0)
    asig03 = Column('ASIG03', Integer, default=0)
    asig04 = Column('ASIG04', Integer, default=0)
    asig05 = Column('ASIG05', Integer, default=0)
    asig06 = Column('ASIG06', Integer, default=0)
    asig07 = Column('ASIG07', Integer, default=0)
    asig08 = Column('ASIG08', Integer, default=0)
    asig09 = Column('ASIG09', Integer, default=0)
    asig10 = Column('ASIG10', Integer, default=0)
    asig11 = Column('ASIG11', Integer, default=0)
    asig12 = Column('ASIG12', Integer, default=0)
    asig13 = Column('ASIG13', Integer, default=0)
    asig14 = Column('ASIG14', Integer, default=0)


class DiarioSAEMixin:
    uuid_sinc = Column('UUID_SINC', String(36), primary_key=True)
    fecha_sinc = Column('FECHA_SINC', DateTime)
    origen = Column('ORIGEN', String(10))
    tipo_doc = Column('TIPO_DOC', String(10))
    fecha_docto = Column('FECHA_DOCTO', DateTime)
    estatus = Column('ESTATUS', String(1))
    referencia = Column('REFERENCIA', String(20))
    xml = Column('XML', String(255))
    contabiliz = Column('CONTABILIZ', String(1))  # 'S', 'N'
    fecha_conta = Column('FECHA_CONTA', DateTime)
    poliza = Column('POLIZA', String(20))
    periodo = Column('PERIODO', Integer)
    ejercicio = Column('EJERCICIO', Integer)
    obs = Column('OBS', String(255))
    uuid_xml = Column('UUID_XML', String(36))
    razonsocial = Column('RAZONSOCIAL', String(254))


class PolizaMixin:
    tipo_poli = Column('TIPO_POLI', String(2), primary_key=True)
    num_poliz = Column('NUM_POLIZ', String(5), primary_key=True)
    periodo = Column('PERIODO', SmallInteger, primary_key=True)
    ejercicio = Column('EJERCICIO', Integer, primary_key=True)
    fecha_pol = Column('FECHA_POL', DateTime)
    concep_po = Column('CONCEP_PO', String(120))
    num_part = Column('NUM_PART', Integer)
    logaudita = Column('LOGAUDITA', String(1), default='N')
    contabiliz = Column('CONTABILIZ', String(1), default='S')
    numparcua = Column('NUMPARCUA', SmallInteger, default=0)
    tienedocumentos = Column('TIENEDOCUMENTOS', SmallInteger, default=0)
    proccontab = Column('PROCCONTAB', Integer, default=0)
    origen = Column('ORIGEN', String(15), default='SAE')
    uuid = Column('UUID', String(100))
    espolizaprivada = Column('ESPOLIZAPRIVADA', Integer, default=0)
    uuidop = Column('UUIDOP', String(40))
    doc_sigo = Column('DOC_SIGO', String(20))
    uuidxml = Column('UUIDXML', String(36))
    uuidsae = Column('UUIDSAE', String(36))
    id_pol_ezaudita = Column('ID_POL_EZAUDITA', String(36))
    sinc_ezaudita = Column('SINC_EZAUDITA', Integer, default=0)


class AuxiliarMixin:
    tipo_poli = Column('TIPO_POLI', String(2), primary_key=True)
    num_poliz = Column('NUM_POLIZ', String(5), primary_key=True)
    num_part = Column('NUM_PART', Float, primary_key=True)
    periodo = Column('PERIODO', SmallInteger, primary_key=True)
    ejercicio = Column('EJERCICIO', SmallInteger, primary_key=True)
    num_cta = Column('NUM_CTA', String(21))
    fecha_pol = Column('FECHA_POL', DateTime)
    concep_po = Column('CONCEP_PO', String(120))
    debe_haber = Column('DEBE_HABER', String(1))
    montomov = Column('MONTOMOV', Float)
    numdepto = Column('NUMDEPTO', SmallInteger, default=0)
    tipcambio = Column('TIPCAMBIO', Float, default=1.0)
    contrapar = Column('CONTRAPAR', SmallInteger, default=0)
    orden = Column('ORDEN', Integer)
    ccostos = Column('CCOSTOS', Integer, default=0)
    cgrupos = Column('CGRUPOS', Integer, default=0)
    idinfadipar = Column('IDINFADIPAR', Integer, default=0)
    iduuid = Column('IDUUID', Integer, default=0)


def get_coi_models(anio_suffix="26"):
    """
    Retorna las clases mapeadas según el sufijo de año (ej. 26 para 2026).
    """
    if anio_suffix in _MODEL_CACHE:
        return _MODEL_CACHE[anio_suffix]

    class Folio(FolioMixin, Base):
        __tablename__ = 'FOLIOS'
        __table_args__ = {'extend_existing': True}

    class DiarioSAE(DiarioSAEMixin, Base):
        __tablename__ = 'DIARIOSAE'
        __table_args__ = {'extend_existing': True}

    class Poliza(PolizaMixin, Base):
        __tablename__ = f'POLIZAS{anio_suffix}'
        __table_args__ = {'extend_existing': True}

    class Auxiliar(AuxiliarMixin, Base):
        __tablename__ = f'AUXILIAR{anio_suffix}'
        __table_args__ = {'extend_existing': True}

    models = SimpleNamespace(
        Folio=Folio,
        DiarioSAE=DiarioSAE,
        Poliza=Poliza,
        Auxiliar=Auxiliar,
    )

    _MODEL_CACHE[anio_suffix] = models
    return models
