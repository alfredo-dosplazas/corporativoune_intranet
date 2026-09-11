from typing import Generator, List, Dict, Optional, Tuple

from apps.interfaz_sae_coi.config import get_cuenta_cliente, get_cuenta_ventas, CUENTAS_CONFIG, get_cuenta_caja_banco, \
    get_nombre_cuenta
from apps.interfaz_sae_coi.dtos import PolizaDTO, MovimientoPolizaDTO


class PolizaVentaGenerator:
    """Genera la Póliza de Venta (Ingreso/Facturación)"""

    @staticmethod
    def generate(factura_data: dict) -> PolizaDTO:
        folio = factura_data.get('folio', '').strip()
        fecha = str(factura_data.get('fecha'))
        cliente_nombre = factura_data.get('cliente', '')
        almacen = factura_data.get('almacen', '')

        uuid_sat = factura_data.get('uuid_xml', '') or ''
        uuid_sae = factura_data.get('uuid_sae', '') or ''

        subtotal = float(factura_data.get('subtotal') or 0.0)
        iva = float(factura_data.get('total_impuesto4') or 0.0)
        total = float(factura_data.get('total') or 0.0)

        concepto_head = f"POLIZA DE Venta / Factura / {folio} / {cliente_nombre} / {almacen}"[:100]

        poliza = PolizaDTO(
            tipo_poliza='Dr',
            fecha=fecha,
            concepto=concepto_head,
            uuid_sae=uuid_sae,
            uuid_xml=uuid_sat,
            referencia=folio
        )

        # Partida 1: Clientes (DEBE)
        cuenta_cliente = get_cuenta_cliente(cliente_nombre)
        poliza.movimientos.append(MovimientoPolizaDTO(
            nombre_cuenta=get_nombre_cuenta(cuenta_cliente),
            cuenta=cuenta_cliente,
            concepto=f"CLIENTE {cliente_nombre} | FACTURA {folio}",
            debe=total,
            haber=0.0
        ))

        # Partida 2: Ventas por Almacén (HABER)
        cuenta_ventas = get_cuenta_ventas(almacen)
        poliza.movimientos.append(MovimientoPolizaDTO(
            nombre_cuenta=get_nombre_cuenta(cuenta_ventas),
            cuenta=cuenta_ventas,
            concepto=f"VENTAS | ALMACEN {almacen} | FACTURA {folio}",
            debe=0.0,
            haber=subtotal
        ))

        # Partida 3: IVA Trasladado Pendiente (HABER)
        if iva > 0:
            cuenta_iva = CUENTAS_CONFIG['IVA_16_TRASLADADO']
            poliza.movimientos.append(MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_iva),
                cuenta=cuenta_iva,
                concepto=f"IVA | FACTURA {folio}",
                debe=0.0,
                haber=iva
            ))

        return poliza


class PolizaCostoVentaGenerator:
    """Genera la Póliza de Costo de Ventas"""

    @staticmethod
    def generate(factura_data: dict, partidas_sae: list) -> PolizaDTO:
        folio = factura_data.get('folio', '').strip()
        fecha = str(factura_data.get('fecha'))
        cliente_nombre = factura_data.get('cliente', '')
        rfc = factura_data.get('rfc', '')
        clave_cliente = factura_data.get('clave_cliente', '')

        uuid_sat = factura_data.get('uuid_xml', '') or ''
        uuid_sae = factura_data.get('uuid_sae', '') or ''

        concepto_head = f"POLIZA DE COSTO - {folio} / CLIENTE {clave_cliente} / {cliente_nombre} / {rfc}"[:100]

        poliza = PolizaDTO(
            tipo_poliza='Dr',
            fecha=fecha,
            concepto=concepto_head,
            uuid_xml=uuid_sat,
            uuid_sae=uuid_sae,
            referencia=f"COSTO-{folio}"
        )

        cuenta_costo = CUENTAS_CONFIG['COSTO_VENTAS_GENERAL']
        cuenta_inventario = CUENTAS_CONFIG['INVENTARIO_GENERAL']

        for p in partidas_sae:
            descripcion_prod = p.get('descripcion', 'PRODUCTO').strip()
            cantidad = float(p.get('cantidad') or 0.0)
            costo_unitario = float(p.get('costo') or 0.0)
            costo_total = round(cantidad * costo_unitario, 2)

            if costo_total <= 0:
                continue

            concepto_mov = f"COSTO DE VENTA DEL {descripcion_prod}"[:100]

            # CARGO: Costo de Ventas
            poliza.movimientos.append(MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_costo),
                cuenta=cuenta_costo,
                concepto=concepto_mov,
                debe=costo_total,
                haber=0.0
            ))

            # ABONO: Inventario
            poliza.movimientos.append(MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_inventario),
                cuenta=cuenta_inventario,
                concepto=concepto_mov,
                debe=0.0,
                haber=costo_total
            ))

        return poliza


class PolizaCorteCajaGenerator:
    """Genera Pólizas de Ingreso/Corte de Caja separadas por Complemento de Pago"""

    @staticmethod
    def _build_poliza(
            tipo_poliza: str,
            prefijo_ref: str,
            etiqueta_concepto: str,
            fecha_corte: str,
            almacen_nombre: str,
            cobros_list: List[Dict]
    ) -> Optional[PolizaDTO]:
        if not cobros_list:
            return None

        concepto_poliza = f"CORTE DE CAJA ({etiqueta_concepto}) / DIA {fecha_corte} / SUCURSAL {almacen_nombre.upper()}"[
            :100]

        fecha_clean = fecha_corte.replace('-', '').replace('/', '')[:8]
        alm_code = almacen_nombre[:3].upper().replace(' ', '')
        referencia_coi = f"{prefijo_ref}-{alm_code}-{fecha_clean}"[:20]

        poliza = PolizaDTO(
            tipo_poliza=tipo_poliza,
            fecha=fecha_corte,
            concepto=concepto_poliza,
            uuid_sae='',
            uuid_xml='',
            referencia=referencia_coi
        )

        cuenta_iva_pend = CUENTAS_CONFIG['IVA_16_TRASLADADO']
        cuenta_iva_cobrado = CUENTAS_CONFIG['IVA_16_COBRADO']

        for cobro in cobros_list:
            monto_pago = float(cobro.get('importe') or 0.0)
            if monto_pago <= 0:
                continue

            concepto_pago = str(cobro.get('concepto_descr', 'PAGO')).strip()
            num_cpto = cobro.get('num_cpto')
            cliente_nombre = cobro.get('cliente_nombre', 'PUBLICO GENERAL')
            doc_referencia = cobro.get('no_factura', cobro.get('refer', ''))
            doc_complemento_pago = cobro.get('cve_doc_comppago', '')

            base_pago = round(monto_pago / 1.16, 2)
            iva_pago = round(monto_pago - base_pago, 2)

            complemento_str = f" | CP: {doc_complemento_pago}" if doc_complemento_pago else ""
            concepto_partida = f"COBRO {concepto_pago} | {doc_referencia} | {cliente_nombre}{complemento_str}"[:100]

            # 1. DEBE: Caja / Banco
            cuenta_caja_banco = get_cuenta_caja_banco(almacen=almacen_nombre, num_cpto=num_cpto)
            poliza.movimientos.append(MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_caja_banco),
                cuenta=cuenta_caja_banco,
                concepto=concepto_partida,
                debe=monto_pago,
                haber=0.0
            ))

            # 2. HABER: Clientes
            cuenta_cliente = get_cuenta_cliente(cliente_nombre)
            poliza.movimientos.append(MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_cliente),
                cuenta=cuenta_cliente,
                concepto=concepto_partida,
                debe=0.0,
                haber=monto_pago
            ))

            # 3. DEBE: Cancelación de IVA Trasladado Pendiente
            if iva_pago > 0:
                poliza.movimientos.append(MovimientoPolizaDTO(
                    nombre_cuenta=get_nombre_cuenta(cuenta_iva_pend),
                    cuenta=cuenta_iva_pend,
                    concepto=f"CANCELACION IVA PEND. | {doc_referencia}"[:100],
                    debe=iva_pago,
                    haber=0.0
                ))

                # 4. HABER: IVA Trasladado Cobrado
                poliza.movimientos.append(MovimientoPolizaDTO(
                    nombre_cuenta=get_nombre_cuenta(cuenta_iva_cobrado),
                    cuenta=cuenta_iva_cobrado,
                    concepto=f"IVA COBRADO | {doc_referencia}"[:100],
                    debe=0.0,
                    haber=iva_pago
                ))

        return poliza

    @classmethod
    def generate_split(
            cls,
            fecha_corte: str,
            almacen_nombre: str,
            cobros_list: List[Dict]
    ) -> Tuple[Optional[PolizaDTO], Optional[PolizaDTO]]:

        cobros_mostrador = []
        cobros_cp = []

        for c in cobros_list:
            cve_cp = str(c.get('cve_doc_comppago') or '').strip()
            if cve_cp:
                cobros_cp.append(c)
            else:
                cobros_mostrador.append(c)

        # 1. Póliza MOSTRADOR -> Prefijo corto 'C-M' (16 caracteres totales)
        # Ejemplo resultante: C-M-CED-20260904
        poliza_mostrador = cls._build_poliza(
            tipo_poliza='Im',
            prefijo_ref='C-M',
            etiqueta_concepto='MOSTRADOR / SIN CP',
            fecha_corte=fecha_corte,
            almacen_nombre=almacen_nombre,
            cobros_list=cobros_mostrador
        )

        # 2. Póliza COMPLEMENTO DE PAGO -> Prefijo corto 'C-CP' (17 caracteres totales)
        # Ejemplo resultante: C-CP-CED-20260904
        poliza_cp = cls._build_poliza(
            tipo_poliza='Ig',
            prefijo_ref='C-CP',
            etiqueta_concepto='CON COMPLEMENTO DE PAGO',
            fecha_corte=fecha_corte,
            almacen_nombre=almacen_nombre,
            cobros_list=cobros_cp
        )

        return poliza_mostrador, poliza_cp


class PolizaNotaCreditoGenerator:
    """Genera la Póliza de Nota de Crédito (Devoluciones/Descuentos)"""

    @classmethod
    def generate(cls, nc_data: dict) -> PolizaDTO:
        cuenta_descuentos = CUENTAS_CONFIG['DESCUENTOS']
        cuenta_iva_pend = CUENTAS_CONFIG['IVA_16_TRASLADADO']

        folio = nc_data.get("folio", "").strip()
        fecha = str(nc_data.get("fecha"))
        cliente_nombre = nc_data.get("cliente", "")
        almacen = nc_data.get("almacen", "")

        uuid_sat = nc_data.get("uuid_xml", "") or ""
        uuid_sae = nc_data.get("uuid_sae", "") or ""

        subtotal = float(nc_data.get("subtotal") or 0.0)
        iva = float(nc_data.get("total_impuesto4") or 0.0)
        total = float(nc_data.get("total") or 0.0)

        concepto_head = f"POLIZA DE Nota de Credito / {folio} / {cliente_nombre} / {almacen}"[:100]

        poliza = PolizaDTO(
            tipo_poliza="Eg",
            fecha=fecha,
            concepto=concepto_head,
            uuid_sae=uuid_sae,
            uuid_xml=uuid_sat,
            referencia=folio,
        )

        # Partida 1: Descuentos sobre ventas (DEBE - Subtotal sin IVA)
        poliza.movimientos.append(
            MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_descuentos),
                cuenta=cuenta_descuentos,
                concepto=f"DESCUENTOS Y DEVOLUCIONES | NC {folio}",
                debe=subtotal,
                haber=0.0,
            )
        )

        # Partida 2: IVA Trasladado (DEBE)
        if iva > 0:
            poliza.movimientos.append(
                MovimientoPolizaDTO(
                    nombre_cuenta=get_nombre_cuenta(cuenta_iva_pend),
                    cuenta=cuenta_iva_pend,
                    concepto=f"IVA | NC {folio}",
                    debe=iva,
                    haber=0.0,
                )
            )

        # Partida 3: Clientes (HABER - Total)
        cuenta_cliente = get_cuenta_cliente(cliente_nombre)
        poliza.movimientos.append(
            MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_cliente),
                cuenta=cuenta_cliente,
                concepto=f"CLIENTE {cliente_nombre} | NC {folio}",
                debe=0.0,
                haber=total,
            )
        )

        return poliza


class PolizaNotaDevolucionGenerator:
    """
    Genera la Póliza de Devolución/Nota de Crédito (Tipo Eg).
    Registra tanto la reversión de Inventarios/Costo como el ajuste contable/fiscal del Cliente.
    """

    @classmethod
    def generate(cls, nd_data: dict) -> PolizaDTO:
        cuenta_inventario = CUENTAS_CONFIG['INVENTARIO_GENERAL']
        cuenta_costo_ventas = CUENTAS_CONFIG['COSTO_VENTAS_GENERAL']
        cuenta_devoluciones = CUENTAS_CONFIG['DESCUENTOS']  # Devoluciones / Descuentos s/Ventas
        cuenta_iva_trasladado = CUENTAS_CONFIG['IVA_16_TRASLADADO']

        folio = str(nd_data.get("folio", "")).strip()
        fecha = str(nd_data.get("fecha"))
        cliente_nombre = nd_data.get("cliente", "")
        almacen = nd_data.get("almacen", "")

        uuid_sat = nd_data.get("uuid_xml", "") or ""
        uuid_sae = nd_data.get("uuid_sae", "") or ""

        # Importes comerciales/fiscales
        subtotal = float(nd_data.get("subtotal") or 0.0)
        iva = float(nd_data.get("total_impuesto4") or 0.0)
        total = float(nd_data.get("total") or 0.0)

        # Importe operativo (Costo del material devuelto)
        costo_total = float(nd_data.get("costo_total") or 0.0)

        concepto_head = f"POLIZA DEVOLUCION / NC {folio} / {cliente_nombre} / {almacen}"[:100]

        poliza = PolizaDTO(
            tipo_poliza="Eg",
            fecha=fecha,
            concepto=concepto_head,
            uuid_sae=uuid_sae,
            uuid_xml=uuid_sat,
            referencia=folio,
        )

        # -------------------------------------------------------------
        # 1. PARTE INVENTARIO / COSTO (Ajuste Físico)
        # -------------------------------------------------------------
        # Partida 1: Inventario (DEBE - Reingreso de mercancía al almacén)
        if costo_total > 0:
            poliza.movimientos.append(
                MovimientoPolizaDTO(
                    nombre_cuenta=get_nombre_cuenta(cuenta_inventario),
                    cuenta=cuenta_inventario,
                    concepto=f"REINGRESO INVENTARIO | ND {folio}",
                    debe=costo_total,
                    haber=0.0,
                )
            )

            # Partida 2: Costo de Ventas (HABER - Disminución del costo)
            poliza.movimientos.append(
                MovimientoPolizaDTO(
                    nombre_cuenta=get_nombre_cuenta(cuenta_costo_ventas),
                    cuenta=cuenta_costo_ventas,
                    concepto=f"REVERSION COSTO VENTAS | ND {folio}",
                    debe=0.0,
                    haber=costo_total,
                )
            )

        # -------------------------------------------------------------
        # 2. PARTE COMERCIAL / FISCAL (Ajuste Cliente)
        # -------------------------------------------------------------
        # Partida 3: Devoluciones sobre Ventas (DEBE - Subtotal)
        poliza.movimientos.append(
            MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_devoluciones),
                cuenta=cuenta_devoluciones,
                concepto=f"DEVOLUCIONES S/VENTAS | ND {folio}",
                debe=subtotal,
                haber=0.0,
            )
        )

        # Partida 4: IVA Trasladado (DEBE)
        if iva > 0:
            poliza.movimientos.append(
                MovimientoPolizaDTO(
                    nombre_cuenta=get_nombre_cuenta(cuenta_iva_trasladado),
                    cuenta=cuenta_iva_trasladado,
                    concepto=f"IVA DEVOLUCION | ND {folio}",
                    debe=iva,
                    haber=0.0,
                )
            )

        # Partida 5: Clientes (HABER - Total acreditado)
        cuenta_cliente = get_cuenta_cliente(cliente_nombre)
        poliza.movimientos.append(
            MovimientoPolizaDTO(
                nombre_cuenta=get_nombre_cuenta(cuenta_cliente),
                cuenta=cuenta_cliente,
                concepto=f"ABONO CLIENTE {cliente_nombre} | ND {folio}",
                debe=0.0,
                haber=total,
            )
        )

        return poliza
