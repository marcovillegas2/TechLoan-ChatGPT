from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.equipment import Base
from app.services.equipment_service import EquipmentService

DATABASE_URL = "sqlite:///./techloan.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

router = APIRouter(tags=["Equipment"])
service = EquipmentService()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/equipments", status_code=status.HTTP_201_CREATED)
def create_equipment(
    nombre: str = Form(...),
    codigo_inventario: str = Form(...),
    descripcion: str = Form(""),
    categoria: str = Form(""),
    ubicacion: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        equipment = service.create_equipment(
            db,
            {
                "nombre": nombre,
                "codigo_inventario": codigo_inventario,
                "descripcion": descripcion,
                "categoria": categoria,
                "ubicacion": ubicacion,
            },
        )
        return {
            "id_equipo": equipment.id_equipo,
            "nombre": equipment.nombre,
            "codigo_inventario": equipment.codigo_inventario,
            "descripcion": equipment.descripcion,
            "categoria": equipment.categoria,
            "ubicacion": equipment.ubicacion,
            "estado": equipment.estado,
            "fecha_registro": equipment.fecha_registro,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))