from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.equipment_schema import EquipmentCreate, EquipmentRead, EquipmentUpdate
from app.services.equipment_service import EquipmentService
from database import get_db

router = APIRouter()
service = EquipmentService()


@router.post("/equipment", response_model=EquipmentRead, status_code=201)
def create_equipment(
    payload: EquipmentCreate,
    db: Session = Depends(get_db),
):
    return service.create_equipment(db, payload)


@router.get("/equipment", response_model=list[EquipmentRead])
def list_equipment(db: Session = Depends(get_db)):
    return service.list_equipment(db)


@router.get("/equipment/{equipment_id}", response_model=EquipmentRead)
def get_equipment(equipment_id: int, db: Session = Depends(get_db)):
    return service.get_equipment(db, equipment_id)


@router.put("/equipment/{equipment_id}", response_model=EquipmentRead)
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
):
    return service.update_equipment(db, equipment_id, payload)


@router.delete("/equipment/{equipment_id}")
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)):
    service.delete_equipment(db, equipment_id)
    return {"detail": "equipment deleted"}