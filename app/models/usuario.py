from sqlalchemy import Column, String
from sqlalchemy.orm import DeclarativeBase

from app.models.flete import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"extend_existing": True}

    usr_nick = Column(String(50), primary_key=True)
    usr_nombres = Column(String(100), nullable=False)
    usr_apellidos = Column(String(100), nullable=False)
    usr_password = Column(String(4000), nullable=False)
    usr_role = Column(String(50), nullable=False)


Link: https://www.impocoma.com.co:8084/cotizacion
Usuario: p2adqwe
Contraseña: XSam7RGMJf