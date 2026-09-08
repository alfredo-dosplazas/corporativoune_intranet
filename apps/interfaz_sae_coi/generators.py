from typing import Generator

from apps.interfaz_sae_coi.config import get_cuenta_cliente, get_cuenta_ventas, CUENTAS_CONFIG
from apps.interfaz_sae_coi.dtos import PolizaDTO, MovimientoPolizaDTO


class PolizaVentaGenerator(Generator):
    """Genera la Póliza de Venta (Ingreso/Facturación)"""

    @staticmethod
    def generate(factura_data: dict) -> PolizaDTO:
        folio = factura_data.get('folio', '').strip()
        fecha = str(factura_data.get('fecha'))
        cliente_nombre = factura_data.get('cliente', '')
        almacen = factura_data.get('almacen', '')
        uuid = factura_data.get('uuid', '')

        subtotal = float(factura_data.get('subtotal') or 0.0)
        iva = float(factura_data.get('total_impuesto4') or 0.0)
        total = float(factura_data.get('total') or 0.0)

        # 1. Concepto Encabezado
        concepto_head = f"POLIZA DE Venta / Factura / {folio} / {cliente_nombre} / {almacen}"[:100]

        poliza = PolizaDTO(
            tipo_poliza='Dr',
            fecha=fecha,
            concepto=concepto_head,
            uuid_xml=uuid,
            referencia=folio
        )

        # Partida 1: CARGO a Clientes (DEBE) -> Total de la Factura
        cuenta_cliente = get_cuenta_cliente(cliente_nombre)
        poliza.movimientos.append(MovimientoPolizaDTO(
            cuenta=cuenta_cliente,
            concepto=f"CLIENTE {cliente_nombre} | FACTURA {folio}",
            debe=total,
            haber=0.0
        ))

        # Partida 2: ABONO a Ventas por Almacén (HABER) -> Subtotal
        cuenta_ventas = get_cuenta_ventas(almacen)
        poliza.movimientos.append(MovimientoPolizaDTO(
            cuenta=cuenta_ventas,
            concepto=f"VENTAS | ALMACEN {almacen} | FACTURA {folio}",
            debe=0.0,
            haber=subtotal
        ))

        # Partida 3: ABONO a IVA Trasladado Pendiente (HABER) -> IVA
        if iva > 0:
            poliza.movimientos.append(MovimientoPolizaDTO(
                cuenta=CUENTAS_CONFIG['IVA_16_TRASLADADO'],
                concepto=f"IVA | FACTURA {folio}",
                debe=0.0,
                haber=iva
            ))

        return poliza


class PolizaCostoVentaGenerator:
    """Genera la Póliza de Costo de Ventas a partir de las partidas/artículos del documento SAE"""

    @staticmethod
    def generate(factura_data: dict, partidas_sae: list) -> PolizaDTO:
        folio = factura_data.get('folio', '').strip()
        fecha = str(factura_data.get('fecha'))
        cliente_nombre = factura_data.get('cliente', '')
        rfc = factura_data.get('rfc', '')
        clave_cliente = factura_data.get('clave_cliente', '')
        uuid = factura_data.get('uuid', '')

        # Concepto Encabezado
        concepto_head = f"POLIZA DE COSTO - {folio} / CLIENTE {clave_cliente} / {cliente_nombre} / {rfc}"[:100]

        poliza = PolizaDTO(
            tipo_poliza='Dr',
            fecha=fecha,
            concepto=concepto_head,
            uuid_xml=uuid,
            referencia=f"COSTO-{folio}"
        )

        # Generar movimientos por cada producto/partida de la factura
        for p in partidas_sae:
            descripcion_prod = p.get('descripcion', 'PRODUCTO').strip()
            cantidad = float(p.get('cantidad') or 0.0)
            costo_unitario = float(p.get('costo') or 0.0)
            costo_total = round(cantidad * costo_unitario, 2)

            if costo_total <= 0:
                continue

            concepto_mov = f"COSTO DE VENTA DEL {descripcion_prod}"[:100]

            # CARGO: Costo de Ventas (DEBE)
            poliza.movimientos.append(MovimientoPolizaDTO(
                cuenta=CUENTAS_CONFIG['COSTO_VENTAS_GENERAL'],
                concepto=concepto_mov,
                debe=costo_total,
                haber=0.0
            ))

            # ABONO: Inventario (HABER)
            poliza.movimientos.append(MovimientoPolizaDTO(
                cuenta=CUENTAS_CONFIG['INVENTARIO_GENERAL'],
                concepto=concepto_mov,
                debe=0.0,
                haber=costo_total
            ))

        return poliza
