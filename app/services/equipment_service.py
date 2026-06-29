from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.repositories.equipment_repository import EquipmentRepository
from app.schemas.equipment_schema import EquipmentCreate, EquipmentUpdate


class EquipmentService:
    ALLOWED_STATUSES = {
        "DISPONIBLE",
        "PRESTADO"
    }

    def __init__(self) -> None:
        self.repository = EquipmentRepository()

    def create_equipment(self, db: Session, payload: EquipmentCreate) -> Equipment:
        code = payload.code.strip()
        name = payload.name.strip()
        category = payload.category.strip()

        if not code:
            raise HTTPException(status_code=422, detail="code is required")
        if not name:
            raise HTTPException(status_code=422, detail="name is required")
        if not category:
            raise HTTPException(status_code=422, detail="category is required")
        if payload.status not in self.ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail="invalid equipment status")

        existing_equipment = self.repository.get_by_code(db, code)
        if existing_equipment is not None:
            raise HTTPException(status_code=409, detail="equipment code already exists")

        equipment = Equipment(
            code=code,
            name=name,
            category=category,
            description=payload.description,
            status=payload.status,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        return self.repository.create(db, equipment)

    def list_equipment(self, db: Session) -> list[Equipment]:
        return self.repository.list(db)

    def get_equipment(self, db: Session, equipment_id: int) -> Equipment:
        equipment = self.repository.get_by_id(db, equipment_id)
        if equipment is None:
            raise HTTPException(status_code=404, detail="equipment not found")
        return equipment

    def update_equipment(
        self, db: Session, equipment_id: int, payload: EquipmentUpdate
    ) -> Equipment:
        equipment = self.repository.get_by_id(db, equipment_id)
        if equipment is None:
            raise HTTPException(status_code=404, detail="equipment not found")

        data = payload.model_dump(exclude_unset=True)

        if "code" in data:
            code = data["code"].strip()
            if not code:
                raise HTTPException(status_code=422, detail="code is required")
            existing_equipment = self.repository.get_by_code(db, code)
            if existing_equipment is not None and existing_equipment.id != equipment_id:
                raise HTTPException(status_code=409, detail="equipment code already exists")
            data["code"] = code

        if "name" in data:
            name = data["name"].strip()
            if not name:
                raise HTTPException(status_code=422, detail="name is required")
            data["name"] = name

        if "category" in data:
            category = data["category"].strip()
            if not category:
                raise HTTPException(status_code=422, detail="category is required")
            data["category"] = category

        if "status" in data and data["status"] not in self.ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail="invalid equipment status")

        data["updated_at"] = datetime.utcnow()
        return self.repository.update(db, equipment, data)

    def delete_equipment(self, db: Session, equipment_id: int) -> None:
        equipment = self.repository.get_by_id(db, equipment_id)
        if equipment is None:
            raise HTTPException(status_code=404, detail="equipment not found")

        if self.repository.has_active_loans(db, equipment_id):
            raise HTTPException(
                status_code=409,
                detail="equipment has active loans",
            )

        self.repository.delete(db, equipment)