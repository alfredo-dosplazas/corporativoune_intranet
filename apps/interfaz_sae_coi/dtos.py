from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class MovimientoPolizaDTO:
    nombre_cuenta: str
    cuenta: str
    concepto: str
    debe: float = 0.0
    haber: float = 0.0


@dataclass
class PolizaDTO:
    tipo_poliza: str  # 'Dr', 'Ig', 'Eg'
    fecha: str  # 'YYYY-MM-DD'
    concepto: str
    uuid_sae: Optional[str] = ''
    uuid_xml: Optional[str] = ''
    referencia: Optional[str] = ''
    movimientos: List[MovimientoPolizaDTO] = field(default_factory=list)

    @property
    def total_debe(self) -> float:
        return round(sum(m.debe for m in self.movimientos), 2)

    @property
    def total_haber(self) -> float:
        return round(sum(m.haber for m in self.movimientos), 2)

    @property
    def esta_cuadrada(self) -> bool:
        return abs(self.total_debe - self.total_haber) < 0.01

    def to_dict(self):
        d = asdict(self)
        d['total_debe'] = self.total_debe
        d['total_haber'] = self.total_haber
        d['esta_cuadrada'] = self.esta_cuadrada
        return d
