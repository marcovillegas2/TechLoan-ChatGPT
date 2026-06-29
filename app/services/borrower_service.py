from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.borrower import Borrower
from app.repositories.borrower_repository import BorrowerRepository
from app.schemas.borrower_schema import BorrowerCreate, BorrowerUpdate


class BorrowerService:
    def __init__(self) -> None:
        self.repository = BorrowerRepository()

    def create_borrower(self, db: Session, payload: BorrowerCreate) -> Borrower:
        dni = payload.dni.strip()
        full_name = payload.full_name.strip()
        email = payload.email.strip()
        phone = payload.phone.strip()
        department = payload.department.strip()

        if not dni:
            raise HTTPException(status_code=422, detail="dni is required")
        if not full_name:
            raise HTTPException(status_code=422, detail="full_name is required")
        if not email:
            raise HTTPException(status_code=422, detail="email is required")
        if not phone:
            raise HTTPException(status_code=422, detail="phone is required")
        if not department:
            raise HTTPException(status_code=422, detail="department is required")

        existing = self.repository.get_by_dni(db, dni)
        if existing is not None:
            raise HTTPException(status_code=409, detail="dni already exists")

        borrower = Borrower(
            dni=dni,
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
            created_at=datetime.utcnow(),
        )
        self.repository.create(db, borrower)
        db.commit()
        db.refresh(borrower)
        return borrower

    def list_borrowers(self, db: Session) -> list[Borrower]:
        return self.repository.list(db)

    def get_borrower(self, db: Session, borrower_id: int) -> Borrower:
        borrower = self.repository.get_by_id(db, borrower_id)
        if borrower is None:
            raise HTTPException(status_code=404, detail="borrower not found")
        return borrower

    def update_borrower(
        self, db: Session, borrower_id: int, payload: BorrowerUpdate
    ) -> Borrower:
        borrower = self.repository.get_by_id(db, borrower_id)
        if borrower is None:
            raise HTTPException(status_code=404, detail="borrower not found")

        data = payload.model_dump(exclude_unset=True)

        if "dni" in data:
            dni = data["dni"].strip()
            if not dni:
                raise HTTPException(status_code=422, detail="dni is required")
            existing = self.repository.get_by_dni(db, dni)
            if existing is not None and existing.id != borrower_id:
                raise HTTPException(status_code=409, detail="dni already exists")
            data["dni"] = dni

        if "full_name" in data:
            full_name = data["full_name"].strip()
            if not full_name:
                raise HTTPException(status_code=422, detail="full_name is required")
            data["full_name"] = full_name

        if "email" in data:
            email = data["email"].strip()
            if not email:
                raise HTTPException(status_code=422, detail="email is required")
            data["email"] = email

        if "phone" in data:
            phone = data["phone"].strip()
            if not phone:
                raise HTTPException(status_code=422, detail="phone is required")
            data["phone"] = phone

        if "department" in data:
            department = data["department"].strip()
            if not department:
                raise HTTPException(status_code=422, detail="department is required")
            data["department"] = department

        self.repository.update(db, borrower, data)
        db.commit()
        db.refresh(borrower)
        return borrower