from datetime import date

from sqlalchemy.orm import Session

from app.repositories.borrower_repository import BorrowerRepository
from app.repositories.equipment_repository import EquipmentRepository
from app.repositories.loan_repository import LoanRepository


class DashboardService:
    EQUIPMENT_AVAILABLE = "DISPONIBLE"
    EQUIPMENT_LOANED = "PRESTADO"
    LOAN_ACTIVE = "ACTIVO"
    LOAN_RETURNED = "DEVUELTO"
    LOAN_OVERDUE = "VENCIDO"

    def __init__(self) -> None:
        self.equipment_repository = EquipmentRepository()
        self.borrower_repository = BorrowerRepository()
        self.loan_repository = LoanRepository()

    def _get_all_equipment(self, db: Session):
        return self.equipment_repository.list(db)

    def _get_all_loans(self, db: Session):
        return self.loan_repository.list(db)

    def _get_overdue_loans(self, db: Session):
        today = date.today()
        loans = self._get_all_loans(db)
        return [
            loan
            for loan in loans
            if loan.return_date is None and loan.due_date < today
        ]

    def get_summary(self, db: Session) -> dict:
        equipments = self._get_all_equipment(db)
        loans = self._get_all_loans(db)
        overdue_loans = self._get_overdue_loans(db)

        return {
            "total_equipment": len(equipments),
            "available_equipment": sum(
                1 for equipment in equipments if equipment.status == self.EQUIPMENT_AVAILABLE
            ),
            "loaned_equipment": sum(
                1 for equipment in equipments if equipment.status == self.EQUIPMENT_LOANED
            ),
            "overdue_loans": len(overdue_loans),
            "overdue_borrowers": len({loan.borrower_id for loan in overdue_loans}),
            "loan_status_distribution": {
                self.LOAN_ACTIVE: sum(1 for loan in loans if loan.status == self.LOAN_ACTIVE),
                self.LOAN_RETURNED: sum(1 for loan in loans if loan.status == self.LOAN_RETURNED),
                self.LOAN_OVERDUE: sum(1 for loan in loans if loan.status == self.LOAN_OVERDUE),
            },
            "equipment_status_distribution": {
                self.EQUIPMENT_AVAILABLE: sum(
                    1 for equipment in equipments if equipment.status == self.EQUIPMENT_AVAILABLE
                ),
                self.EQUIPMENT_LOANED: sum(
                    1 for equipment in equipments if equipment.status == self.EQUIPMENT_LOANED
                ),
            },
        }

    def get_charts(self, db: Session) -> dict:
        equipments = self._get_all_equipment(db)
        loans = self._get_all_loans(db)

        return {
            "equipment_distribution": {
                self.EQUIPMENT_AVAILABLE: sum(
                    1 for equipment in equipments if equipment.status == self.EQUIPMENT_AVAILABLE
                ),
                self.EQUIPMENT_LOANED: sum(
                    1 for equipment in equipments if equipment.status == self.EQUIPMENT_LOANED
                ),
            },
            "loan_distribution": {
                self.LOAN_ACTIVE: sum(1 for loan in loans if loan.status == self.LOAN_ACTIVE),
                self.LOAN_RETURNED: sum(1 for loan in loans if loan.status == self.LOAN_RETURNED),
                self.LOAN_OVERDUE: sum(1 for loan in loans if loan.status == self.LOAN_OVERDUE),
            },
        }

    def get_overdue_users(self, db: Session) -> list[dict]:
        overdue_loans = self._get_overdue_loans(db)
        today = date.today()
        overdue_users: list[dict] = []

        for loan in overdue_loans:
            borrower = self.borrower_repository.get_by_id(db, loan.borrower_id)
            equipment = self.equipment_repository.get_by_id(db, loan.equipment_id)

            overdue_users.append(
                {
                    "borrower_id": borrower.id if borrower else None,
                    "full_name": borrower.full_name if borrower else None,
                    "dni": borrower.dni if borrower else None,
                    "equipment": {
                        "id": equipment.id if equipment else None,
                        "code": equipment.code if equipment else None,
                        "name": equipment.name if equipment else None,
                    },
                    "due_date": loan.due_date.isoformat(),
                    "days_overdue": (today - loan.due_date).days,
                    "status": loan.status,
                }
            )

        return overdue_users