from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class EquipmentCreate(BaseModel):
    code: str
    name: str
    category: str
    description: Optional[str] = None
    status: Literal["DISPONIBLE", "PRESTADO"]


class EquipmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["DISPONIBLE", "PRESTADO"]] = None


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None