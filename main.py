from fastapi import FastAPI

from app.controllers.equipment_controller import router as equipment_router

app = FastAPI(title="TechLoan", version="0.1.0")

app.include_router(equipment_router)