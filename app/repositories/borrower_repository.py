from sqlalchemy.orm import Session

from app.models.borrower import Borrower


class BorrowerRepository:
    def create(self, db: Session, borrower: Borrower) -> Borrower:
        db.add(borrower)
        db.flush()
        return borrower

    def get_by_id(self, db: Session, borrower_id: int) -> Borrower | None:
        return db.query(Borrower).filter(Borrower.id == borrower_id).first()

    def get_by_dni(self, db: Session, dni: str) -> Borrower | None:
        return db.query(Borrower).filter(Borrower.dni == dni).first()

    def list(self, db: Session) -> list[Borrower]:
        return db.query(Borrower).order_by(Borrower.id.asc()).all()

    def update(self, db: Session, borrower: Borrower, data: dict) -> Borrower:
        for field, value in data.items():
            setattr(borrower, field, value)
        db.flush()
        return borrower