from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.models.loan import Loan


class EquipmentRepository:
    def create(self, db: Session, equipment: Equipment) -> Equipment:
        db.add(equipment)
        db.commit()
        db.refresh(equipment)
        return equipment

    def get_by_id(self, db: Session, equipment_id: int) -> Equipment | None:
        return db.query(Equipment).filter(Equipment.id == equipment_id).first()

    def get_by_code(self, db: Session, code: str) -> Equipment | None:
        return db.query(Equipment).filter(Equipment.code == code).first()

    def list(self, db: Session) -> list[Equipment]:
        return db.query(Equipment).order_by(Equipment.id.asc()).all()

    def update(self, db: Session, equipment: Equipment, data: dict) -> Equipment:
        for field, value in data.items():
            setattr(equipment, field, value)
        db.commit()
        db.refresh(equipment)
        return equipment

    def delete(self, db: Session, equipment: Equipment) -> None:
        db.delete(equipment)
        db.commit()

    def has_active_loans(self, db: Session, equipment_id: int) -> bool:
        active_loan = (
            db.query(Loan)
            .filter(
                Loan.equipment_id == equipment_id,
                Loan.status == "ACTIVE",
                Loan.return_date.is_(None),
            )
            .first()
        )
        return active_loan is not None