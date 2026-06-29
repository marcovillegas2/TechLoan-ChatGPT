from fastapi import FastAPI
from database import Base, engine
from fastapi.middleware.cors import CORSMiddleware

import app.models.equipment
import app.models.borrower
import app.models.loan

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TechLoan",
    version="0.1.0",
    description="Sistema Administrativo de Control de Préstamos de Equipos Tecnológicos",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # o el puerto exacto de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.controllers.equipment_controller import router as equipment_router
from app.controllers.borrower_controller import router as borrower_router
from app.controllers.loan_controller import router as loan_router
from app.controllers.dashboard_controller import router as dashboard_router

app.include_router(equipment_router)
app.include_router(borrower_router)
app.include_router(loan_router)
app.include_router(dashboard_router)