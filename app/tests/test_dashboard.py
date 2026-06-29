from datetime import date, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.controllers.dashboard_controller import router
from app.models.borrower import Borrower
from app.models.equipment import Equipment
from app.models.loan import Loan
from database import Base, get_db


@pytest.fixture()
def client_and_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'dashboard_test.db'}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client, TestingSessionLocal

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def seed_equipment(db, code: str, status: str) -> Equipment:
    equipment = Equipment(
        code=code,
        name=f"Equipo {code}",
        category="Tecnología",
        description="Equipo de prueba",
        status=status,
        created_at=datetime.utcnow(),
        updated_at=None,
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


def seed_borrower(db, dni: str, full_name: str) -> Borrower:
    borrower = Borrower(
        dni=dni,
        full_name=full_name,
        email=f"{dni}@example.com",
        phone="999888777",
        department="Sistemas",
        created_at=datetime.utcnow(),
    )
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


def seed_dashboard_data(session_factory):
    db = session_factory()
    try:
        equipment_1 = seed_equipment(db, "EQ-201", "DISPONIBLE")
        equipment_2 = seed_equipment(db, "EQ-202", "PRESTADO")
        equipment_3 = seed_equipment(db, "EQ-203", "PRESTADO")

        borrower_1 = seed_borrower(db, "11111111", "Ana Torres")
        borrower_2 = seed_borrower(db, "22222222", "Luis Ramos")
        borrower_3 = seed_borrower(db, "33333333", "Marta Vega")

        loan_1 = Loan(
            equipment_id=equipment_2.id,
            borrower_id=borrower_1.id,
            loan_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=1),
            return_date=None,
            status="ACTIVO",
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        loan_2 = Loan(
            equipment_id=equipment_1.id,
            borrower_id=borrower_2.id,
            loan_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=10),
            return_date=date.today(),
            status="DEVUELTO",
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        loan_3 = Loan(
            equipment_id=equipment_3.id,
            borrower_id=borrower_3.id,
            loan_date=date.today() - timedelta(days=15),
            due_date=date.today() - timedelta(days=3),
            return_date=None,
            status="VENCIDO",
            created_at=datetime.utcnow(),
            updated_at=None,
        )

        db.add_all([loan_1, loan_2, loan_3])
        db.commit()
    finally:
        db.close()


def test_td1_obtener_resumen_con_datos_existentes(client_and_session_factory):
    client, SessionLocal = client_and_session_factory
    seed_dashboard_data(SessionLocal)

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_equipment"] == 3
    assert data["available_equipment"] == 1
    assert data["loaned_equipment"] == 2
    assert data["overdue_loans"] == 2
    assert data["overdue_borrowers"] == 2
    assert data["loan_status_distribution"]["ACTIVO"] == 1
    assert data["loan_status_distribution"]["DEVUELTO"] == 1
    assert data["loan_status_distribution"]["VENCIDO"] == 1


def test_td2_obtener_resumen_sin_datos(client_and_session_factory):
    client, _ = client_and_session_factory

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_equipment"] == 0
    assert data["available_equipment"] == 0
    assert data["loaned_equipment"] == 0
    assert data["overdue_loans"] == 0
    assert data["overdue_borrowers"] == 0
    assert data["loan_status_distribution"]["ACTIVO"] == 0
    assert data["loan_status_distribution"]["DEVUELTO"] == 0
    assert data["loan_status_distribution"]["VENCIDO"] == 0


def test_td3_obtener_usuarios_con_devoluciones_vencidas(client_and_session_factory):
    client, SessionLocal = client_and_session_factory
    seed_dashboard_data(SessionLocal)

    response = client.get("/dashboard/overdue-users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {item["full_name"] for item in data}
    assert names == {"Ana Torres", "Marta Vega"}
    assert all(item["days_overdue"] > 0 for item in data)
    assert all(item["status"] in {"ACTIVO", "VENCIDO"} for item in data)


def test_td4_obtener_usuarios_vencidos_sin_datos(client_and_session_factory):
    client, _ = client_and_session_factory

    response = client.get("/dashboard/overdue-users")

    assert response.status_code == 200
    assert response.json() == []


def test_td5_obtener_datos_de_graficos(client_and_session_factory):
    client, SessionLocal = client_and_session_factory
    seed_dashboard_data(SessionLocal)

    response = client.get("/dashboard/charts")

    assert response.status_code == 200
    data = response.json()
    assert data["equipment_distribution"]["DISPONIBLE"] == 1
    assert data["equipment_distribution"]["PRESTADO"] == 2
    assert data["loan_distribution"]["ACTIVO"] == 1
    assert data["loan_distribution"]["DEVUELTO"] == 1
    assert data["loan_distribution"]["VENCIDO"] == 1