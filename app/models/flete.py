from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class FleteRegistro(Base):
    __tablename__ = "fletes_registro"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cod_vehiculo = Column(String(20), nullable=False)
    origen = Column(String(100), nullable=False)
    destino = Column(String(100), nullable=False)
    tarifa = Column(Integer, nullable=False)
    tipo_flete = Column(String(20), nullable=False)
    fuente = Column(String(100), nullable=False)
    agencia = Column(String(100), nullable=False)
    creado_en = Column(DateTime, default=datetime.now)

    def dict(self) -> dict:
        return {
            "id": self.id,
            "cod_vehiculo": self.cod_vehiculo,
            "origen": self.origen,
            "destino": self.destino,
            "tarifa": self.tarifa,
            "tipo_flete": self.tipo_flete,
            "fuente": self.fuente,
            "agencia": self.agencia,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
