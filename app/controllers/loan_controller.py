from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.equipment_schema import EquipmentRead
from app.schemas.loan_schema import LoanCreate, LoanRead
from app.services.loan_service import LoanService
from database import get_db

router = APIRouter()
service = LoanService()


@router.post("/loans", response_model=LoanRead, status_code=201)
def create_loan(payload: LoanCreate, db: Session = Depends(get_db)):
    return service.create_loan(db, payload)


@router.get("/loans", response_model=list[LoanRead])
def list_loans(db: Session = Depends(get_db)):
    return service.list_loans(db)

@router.get("/loans/available-equipment", response_model=list[EquipmentRead])
def available_equipment(db: Session = Depends(get_db)):
    return service.get_available_equipment(db)

@router.post("/loans/{loan_id}/return", response_model=LoanRead)
def return_loan(loan_id: int, db: Session = Depends(get_db)):
    return service.return_loan(db, loan_id)

@router.get("/loans/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    return service.get_loan(db, loan_id)