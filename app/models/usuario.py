from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import DeclarativeBase

from app.models.flete import Base

# Fuente única de verdad de los roles asignables a un usuario.
# El orden se respeta en los selectores de la interfaz.
# - ADMIN:     acceso total.
# - FLETES:    registro de fletes plaza.
# - COMERCIAL: cotización comercial + reporte.
# - REPORTES:  acceso de solo lectura, únicamente a la vista de Reporte.
ROLES = ["ADMIN", "FLETES", "COMERCIAL", "REPORTES"]


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"extend_existing": True}

    usr_nick = Column(String(50), primary_key=True)
    usr_nombres = Column(String(100), nullable=False)
    usr_apellidos = Column(String(100), nullable=False)
    usr_password = Column(String(4000), nullable=False)
    usr_role = Column(String(50), nullable=False)
    fecha_creacion = Column(DateTime, nullable=True)
    ultima_conexion = Column(DateTime, nullable=True)
    usr_agencia = Column(String(100), nullable=True)
