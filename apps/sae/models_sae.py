from types import SimpleNamespace
from sqlalchemy import Column, String, Date, Float, Integer, ForeignKey
from sqlalchemy.orm import relationship

from apps.sae.db import Base

_MODEL_CACHE = {}


class ClienteMixin:
    clave = Column('CLAVE', String(10), primary_key=True)
    nombre = Column('NOMBRE', String(254))
    rfc = Column('RFC', String(254))


class AlmacenMixin:
    clave = Column('CVE_ALM', Integer, primary_key=True)
    nombre = Column('DESCR', String(10))


class FacturaMixin:
    folio = Column('CVE_DOC', String(20), primary_key=True)
    fecha = Column('FECHA_DOC', Date)
    clave_vendedor = Column('CVE_VEND', String(5))
    total_impuesto1 = Column('IMP_TOT1', Float)
    total_impuesto2 = Column('IMP_TOT2', Float)
    total_impuesto3 = Column('IMP_TOT3', Float)
    total_impuesto4 = Column('IMP_TOT4', Float)
    subtotal = Column('CAN_TOT', Float)
    total = Column('IMPORTE', Float)
    status = Column('STATUS', String(1))
    uuid = Column('UUID', String(50))
    act_coi = Column('ACT_COI', String(1))


class ArticuloMixin:
    clave = Column('CVE_ART', String(10), primary_key=True)
    descripcion = Column('DESCR', String(254))


class PartidaFacturaMixin:
    num_partida = Column('NUM_PAR', Integer, primary_key=True)
    cantidad = Column('CANT', Float)
    costo = Column('COST', Float)


def get_sae_models(suffix="01"):
    if suffix in _MODEL_CACHE:
        return _MODEL_CACHE[suffix]

    class Almacen(AlmacenMixin, Base):
        __tablename__ = f'ALMACENES{suffix}'
        __table_args__ = {'extend_existing': True}

    class Cliente(ClienteMixin, Base):
        __tablename__ = f'CLIE{suffix}'
        __table_args__ = {'extend_existing': True}

    class Factura(FacturaMixin, Base):
        __tablename__ = f'FACTF{suffix}'
        __table_args__ = {'extend_existing': True}

        num_alma = Column('NUM_ALMA', ForeignKey(f'ALMACENES{suffix}.CVE_ALM'))
        almacen = relationship(Almacen, backref=f"facturas_{suffix}")

        clave_cliente = Column('CVE_CLPV', ForeignKey(f'CLIE{suffix}.CLAVE'))
        cliente = relationship(Cliente, backref=f"facturas_{suffix}")

    class Producto(ArticuloMixin, Base):
        __tablename__ = f'INVE{suffix}'
        __table_args__ = {'extend_existing': True}

    class PartidaFactura(PartidaFacturaMixin, Base):
        __tablename__ = f'PAR_FACTF{suffix}'
        __table_args__ = {'extend_existing': True}

        # Llave compuesta: folio + num_partida
        folio = Column('CVE_DOC', ForeignKey(f'FACTF{suffix}.CVE_DOC'), primary_key=True)
        factura = relationship(Factura, backref=f"partidas_{suffix}")

        cve_art = Column('CVE_ART', ForeignKey(f'INVE{suffix}.CVE_ART'))
        producto = relationship(Producto, backref=f"partidas_{suffix}")

    models = SimpleNamespace(
        Cliente=Cliente,
        Almacen=Almacen,
        Factura=Factura,
        PartidaFactura=PartidaFactura,
        Producto=Producto,
    )

    _MODEL_CACHE[suffix] = models
    return models