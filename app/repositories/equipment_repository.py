from sqlalchemy.orm import Session

from app.models.equipment import Equipment


class EquipmentRepository:
    def exists_by_codigo_inventario(self, db: Session, codigo_inventario: str) -> bool:
        return (
            db.query(Equipment)
            .filter(Equipment.codigo_inventario == codigo_inventario)
            .first()
            is not None
        )

    def create(self, db: Session, equipment_data: dict) -> Equipment:
        equipment = Equipment(**equipment_data)
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        return equipment