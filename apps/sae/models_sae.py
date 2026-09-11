from types import SimpleNamespace
from sqlalchemy import Column, String, Date, Float, Integer, ForeignKey, BLOB
from sqlalchemy.orm import relationship, aliased

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
    uuid_sae = Column('UUID', String(50))
    act_coi = Column('ACT_COI', String(1))


class CFDIMixin:
    folio = Column('CVE_DOC', String(20), primary_key=True)
    tipo_doc = Column('TIPO_DOC', String(1))
    uuid_sat = Column('UUID', String(50))
    xml_doc = Column('XML_DOC', BLOB())


class CoiXmlMixin:
    folio = Column('CVE_DOC', String(20), primary_key=True)
    id_xml_sat = Column('UUID', String(50), primary_key=True)
    fecha = Column('FECHA_SINC', Date)
    xml_doc = Column('XML_DOC', BLOB())
    status = Column('STATUS', String(1))
    tipodoc = Column('TIPODOC', String(1))
    uuid_cfdi_sae = Column('ID_SINC', String(50))


class ArticuloMixin:
    clave = Column('CVE_ART', String(10), primary_key=True)
    descripcion = Column('DESCR', String(254))


class PartidaFacturaMixin:
    num_partida = Column('NUM_PAR', Integer, primary_key=True)
    cantidad = Column('CANT', Float)
    costo = Column('COST', Float)


class CuenDetMixin:
    cve_clie = Column('CVE_CLIE', String(10), primary_key=True)
    refer = Column('REFER', String(20), primary_key=True)
    id_mov = Column('ID_MOV', Integer, primary_key=True)
    num_cpto = Column('NUM_CPTO', Integer)
    num_cargo = Column('NUM_CARGO', Integer)
    no_factura = Column('NO_FACTURA', String(20))
    docto = Column('DOCTO', String(20))
    importe = Column('IMPORTE', Float)
    fecha_apli = Column('FECHA_APLI', Date)
    fecha_venc = Column('FECHA_VENC', Date)
    num_moned = Column('NUM_MONED', Integer)
    tcambio = Column('TCAMBIO', Float)
    strcvevend = Column('STRCVEVEND', String(5))
    impmon_ext = Column('IMPMON_EXT', Float)
    fechaelab = Column('FECHAELAB', Date)
    cve_folio = Column('CVE_FOLIO', String(10))
    tipo_mov = Column('TIPO_MOV', String(1))  # 'C' Cargo, 'A' Abono
    signo = Column('SIGNO', Integer)  # -1 Abono, 1 Cargo
    cve_doc_comppago = Column('CVE_DOC_COMPPAGO', String(20))


class ConceptoPorCobrarMixin:
    num_cpto = Column('NUM_CPTO', Integer, primary_key=True)
    descr = Column('DESCR', String(50))
    tipo = Column('TIPO', String(1))  # 'C' o 'A'
    status = Column('STATUS', String(1))  # 'A' Activo
    es_forma_pago = Column('ES_FMA_PAG', String(1))  # S o N


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

    class NotaVenta(FacturaMixin, Base):
        __tablename__ = f'FACTV{suffix}'
        __table_args__ = {'extend_existing': True}

        num_alma = Column('NUM_ALMA', ForeignKey(f'ALMACENES{suffix}.CVE_ALM'))
        almacen = relationship(Almacen, backref=f"notas_venta_{suffix}")
        clave_cliente = Column('CVE_CLPV', ForeignKey(f'CLIE{suffix}.CLAVE'))
        cliente = relationship(Cliente, backref=f"notas_venta_{suffix}")

    class NotaCredito(FacturaMixin, Base):
        __tablename__ = f'FACTE{suffix}'
        __table_args__ = {'extend_existing': True}

        num_alma = Column('NUM_ALMA', ForeignKey(f'ALMACENES{suffix}.CVE_ALM'))
        almacen = relationship(Almacen, backref=f"notas_credito_{suffix}")
        clave_cliente = Column('CVE_CLPV', ForeignKey(f'CLIE{suffix}.CLAVE'))
        cliente = relationship(Cliente, backref=f"notas_credito_{suffix}")

    class NotaDevolucion(FacturaMixin, Base):
        __tablename__ = f'FACTD{suffix}'
        __table_args__ = {'extend_existing': True}

        num_alma = Column('NUM_ALMA', ForeignKey(f'ALMACENES{suffix}.CVE_ALM'))
        almacen = relationship(Almacen, backref=f"notas_devolucion_{suffix}")
        clave_cliente = Column('CVE_CLPV', ForeignKey(f'CLIE{suffix}.CLAVE'))
        cliente = relationship(Cliente, backref=f"notas_devolucion_{suffix}")

    class CFDI(CFDIMixin, Base):
        __tablename__ = f'CFDI{suffix}'
        __table_args__ = {'extend_existing': True}

        folio = Column('CVE_DOC', ForeignKey(f'FACTF{suffix}.CVE_DOC'), primary_key=True)
        factura = relationship(Factura, backref=f"cfdi_{suffix}")

    class CoiXml(CoiXmlMixin, Base):
        __tablename__ = f'COI_XML{suffix}'
        __table_args__ = {'extend_existing': True}

        folio = Column('CVE_DOC', ForeignKey(f'FACTF{suffix}.CVE_DOC'), primary_key=True)
        factura = relationship(Factura, backref=f"coi_xml_{suffix}")

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

    class PartidaNotaDevolucion(PartidaFacturaMixin, Base):
        __tablename__ = f'PAR_FACTD{suffix}'
        __table_args__ = {'extend_existing': True}

        # Llave compuesta: folio + num_partida
        folio = Column('CVE_DOC', ForeignKey(f'FACTD{suffix}.CVE_DOC'), primary_key=True)
        nota_devolucion = relationship(NotaDevolucion, backref=f"partidas_devolucion_{suffix}")

        cve_art = Column('CVE_ART', ForeignKey(f'INVE{suffix}.CVE_ART'))
        producto = relationship(Producto, backref=f"partidas_devolucion_{suffix}")

    class CuenDet(CuenDetMixin, Base):
        __tablename__ = f'CUEN_DET{suffix}'
        __table_args__ = {'extend_existing': True}

    class ConceptoPorCobrar(ConceptoPorCobrarMixin, Base):
        __tablename__ = f'CONC{suffix}'
        __table_args__ = {'extend_existing': True}

    AlmacenFactura = aliased(Almacen, name=f'AlmacenFactura_{suffix}')
    AlmacenNota = aliased(Almacen, name=f'AlmacenNota_{suffix}')

    models = SimpleNamespace(
        Cliente=Cliente,
        Almacen=Almacen,
        AlmacenFactura=AlmacenFactura,
        AlmacenNota=AlmacenNota,
        Factura=Factura,
        NotaVenta=NotaVenta,
        NotaCredito=NotaCredito,
        NotaDevolucion=NotaDevolucion,
        CFDI=CFDI,
        CoiXml=CoiXml,
        PartidaFactura=PartidaFactura,
        PartidaNotaDevolucion=PartidaNotaDevolucion,
        Producto=Producto,
        CuenDet=CuenDet,
        Concepto=ConceptoPorCobrar,
    )

    _MODEL_CACHE[suffix] = models
    return models
