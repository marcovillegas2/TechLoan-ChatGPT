from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Equipment(Base):
    __tablename__ = "equipment"

    id_equipo = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    codigo_inventario = Column(String(50), nullable=False, unique=True, index=True)
    descripcion = Column(Text, nullable=True)
    categoria = Column(String(100), nullable=True)
    ubicacion = Column(String(100), nullable=True)
    estado = Column(String(20), nullable=False, default="Disponible")
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)