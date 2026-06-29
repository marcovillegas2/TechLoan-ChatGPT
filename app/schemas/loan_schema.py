from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class LoanCreate(BaseModel):
    equipment_id: int
    borrower_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None
    status: Literal["ACTIVO", "DEVUELTO", "VENCIDO"]


class LoanUpdate(BaseModel):
    equipment_id: Optional[int] = None
    borrower_id: Optional[int] = None
    loan_date: Optional[date] = None
    due_date: Optional[date] = None
    return_date: Optional[date] = None
    status: Optional[Literal["ACTIVO", "DEVUELTO", "VENCIDO"]] = None


class LoanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipment_id: int
    borrower_id: int
    loan_date: date
    due_date: date
    return_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None