from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.dashboard_service import DashboardService
from database import get_db

router = APIRouter()
service = DashboardService()


@router.get("/dashboard/summary")
def get_summary(db: Session = Depends(get_db)):
    return service.get_summary(db)


@router.get("/dashboard/charts")
def get_charts(db: Session = Depends(get_db)):
    return service.get_charts(db)


@router.get("/dashboard/overdue-users")
def get_overdue_users(db: Session = Depends(get_db)):
    return service.get_overdue_users(db)