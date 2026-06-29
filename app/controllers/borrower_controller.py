from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.borrower_schema import BorrowerCreate, BorrowerRead, BorrowerUpdate
from app.services.borrower_service import BorrowerService
from database import get_db

router = APIRouter()
service = BorrowerService()


@router.post("/borrowers", response_model=BorrowerRead, status_code=201)
def create_borrower(payload: BorrowerCreate, db: Session = Depends(get_db)):
    return service.create_borrower(db, payload)


@router.get("/borrowers", response_model=list[BorrowerRead])
def list_borrowers(db: Session = Depends(get_db)):
    return service.list_borrowers(db)


@router.get("/borrowers/{borrower_id}", response_model=BorrowerRead)
def get_borrower(borrower_id: int, db: Session = Depends(get_db)):
    return service.get_borrower(db, borrower_id)


@router.put("/borrowers/{borrower_id}", response_model=BorrowerRead)
def update_borrower(
    borrower_id: int,
    payload: BorrowerUpdate,
    db: Session = Depends(get_db),
):
    return service.update_borrower(db, borrower_id, payload)