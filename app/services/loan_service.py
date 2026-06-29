from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.models.equipment import Equipment
from app.models.loan import Loan
from app.repositories.loan_repository import LoanRepository
from app.schemas.loan_schema import LoanCreate


class LoanService:
    def __init__(self) -> None:
        self.repository = LoanRepository()

    def list_loans(self, db: Session) -> list[Loan]:
        return self.repository.list(db)

    def get_loan(self, db: Session, loan_id: int) -> Loan:
        loan = self.repository.get_by_id(db, loan_id)
        if loan is None:
            raise HTTPException(status_code=404, detail="loan not found")
        return loan

    def get_available_equipment(self, db: Session) -> list[Equipment]:
        return self.repository.get_available_equipment(db)

    def create_loan(self, db: Session, payload: LoanCreate) -> Loan:
        equipment = db.query(Equipment).filter(Equipment.id == payload.equipment_id).first()
        if equipment is None:
            raise HTTPException(status_code=404, detail="equipment not found")

        borrower = db.query(Borrower).filter(Borrower.id == payload.borrower_id).first()
        if borrower is None:
            raise HTTPException(status_code=404, detail="borrower not found")

        if payload.status != "ACTIVO":
            raise HTTPException(status_code=422, detail="invalid loan status")
        if payload.return_date is not None:
            raise HTTPException(status_code=422, detail="return_date must be null for an active loan")
        if payload.due_date <= payload.loan_date:
            raise HTTPException(status_code=422, detail="due_date must be later than loan_date")

        if equipment.status != "DISPONIBLE":
            raise HTTPException(status_code=409, detail="equipment is not available")

        active_loan = (
            db.query(Loan)
            .filter(
                Loan.equipment_id == equipment.id,
                Loan.status == "ACTIVO",
                Loan.return_date.is_(None),
            )
            .first()
        )
        if active_loan is not None:
            raise HTTPException(status_code=409, detail="equipment already has an active loan")

        now = datetime.utcnow()
        loan = Loan(
            equipment_id=payload.equipment_id,
            borrower_id=payload.borrower_id,
            loan_date=payload.loan_date,
            due_date=payload.due_date,
            return_date=None,
            status="ACTIVO",
            created_at=now,
            updated_at=None,
        )
        equipment.status = "PRESTADO"
        equipment.updated_at = now

        self.repository.create(db, loan)
        db.add(equipment)
        db.commit()
        db.refresh(loan)
        db.refresh(equipment)
        return loan

    def return_loan(self, db: Session, loan_id: int) -> Loan:
        loan = self.repository.get_by_id(db, loan_id)
        if loan is None:
            raise HTTPException(status_code=404, detail="loan not found")

        if self.repository.is_loan_returned(db, loan_id):
            raise HTTPException(status_code=409, detail="loan already returned")

        if loan.status != "ACTIVO" or loan.return_date is not None:
            raise HTTPException(status_code=409, detail="loan is not active")

        equipment = db.query(Equipment).filter(Equipment.id == loan.equipment_id).first()
        if equipment is None:
            raise HTTPException(status_code=404, detail="equipment not found")

        now = datetime.utcnow()
        data = {
            "return_date": date.today(),
            "status": "DEVUELTO",
            "updated_at": now,
        }
        equipment.status = "DISPONIBLE"
        equipment.updated_at = now

        self.repository.register_return(db, loan, data)
        db.add(equipment)
        db.commit()
        db.refresh(loan)
        db.refresh(equipment)
        return loan