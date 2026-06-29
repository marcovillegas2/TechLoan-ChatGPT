from sqlalchemy.orm import Session

from app.models.equipment import Equipment
from app.models.loan import Loan


class LoanRepository:
    def create(self, db: Session, loan: Loan) -> Loan:
        db.add(loan)
        db.flush()
        return loan

    def get_by_id(self, db: Session, loan_id: int) -> Loan | None:
        return db.query(Loan).filter(Loan.id == loan_id).first()

    def list(self, db: Session) -> list[Loan]:
        return db.query(Loan).order_by(Loan.id.asc()).all()

    def register_return(self, db: Session, loan: Loan, data: dict) -> Loan:
        for field, value in data.items():
            setattr(loan, field, value)
        db.flush()
        return loan

    def is_equipment_available(self, db: Session, equipment_id: int) -> bool:
        equipment = (
            db.query(Equipment)
            .filter(
                Equipment.id == equipment_id,
                Equipment.status == "DISPONIBLE",
            )
            .first()
        )
        return equipment is not None

    def get_available_equipment(self, db: Session) -> list[Equipment]:
        return (
            db.query(Equipment)
            .filter(Equipment.status == "DISPONIBLE")
            .order_by(Equipment.id.asc())
            .all()
        )

    def is_loan_returned(self, db: Session, loan_id: int) -> bool:
        loan = self.get_by_id(db, loan_id)
        if loan is None:
            return False
        return loan.status == "DEVUELTO" or loan.return_date is not None