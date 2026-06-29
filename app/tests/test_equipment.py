from datetime import date, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.controllers.equipment_controller import router
from app.models.borrower import Borrower
from app.models.equipment import Equipment
from app.models.loan import Loan
from database import Base, get_db


@pytest.fixture()
def client_and_session_factory(tmp_path, monkeypatch):
    db_path = tmp_path / "techloan_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    import database as database_module

    monkeypatch.setattr(database_module, "SessionLocal", TestingSessionLocal)

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


def test_t1_registrar_equipo_valido(client_and_session_factory):
    client, _ = client_and_session_factory

    response = client.post(
        "/equipment",
        json={
            "code": "EQ-001",
            "name": "Laptop Dell",
            "category": "Computadora",
            "description": "Equipo portátil",
            "status": "AVAILABLE",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "EQ-001"
    assert data["name"] == "Laptop Dell"
    assert data["status"] == "AVAILABLE"
    assert "id" in data


def test_t2_registrar_equipo_con_codigo_duplicado(client_and_session_factory):
    client, _ = client_and_session_factory

    payload = {
        "code": "EQ-002",
        "name": "Proyector",
        "category": "Presentación",
        "description": "Proyector HD",
        "status": "AVAILABLE",
    }

    first = client.post("/equipment", json=payload)
    assert first.status_code == 201

    second = client.post("/equipment", json=payload)
    assert second.status_code == 409


def test_t3_registrar_equipo_sin_nombre(client_and_session_factory):
    client, _ = client_and_session_factory

    response = client.post(
        "/equipment",
        json={
            "code": "EQ-003",
            "category": "Periférico",
            "description": "Sin nombre",
            "status": "AVAILABLE",
        },
    )

    assert response.status_code == 422


def test_t4_registrar_equipo_con_estado_no_permitido(client_and_session_factory):
    client, _ = client_and_session_factory

    response = client.post(
        "/equipment",
        json={
            "code": "EQ-004",
            "name": "Monitor",
            "category": "Pantalla",
            "description": "Estado inválido",
            "status": "MAINTENANCE",
        },
    )

    assert response.status_code == 422


def test_t5_actualizar_equipo_valido(client_and_session_factory):
    client, _ = client_and_session_factory

    created = client.post(
        "/equipment",
        json={
            "code": "EQ-005",
            "name": "Tablet",
            "category": "Dispositivo móvil",
            "description": "Tablet inicial",
            "status": "AVAILABLE",
        },
    )
    assert created.status_code == 201
    equipment_id = created.json()["id"]

    response = client.put(
        f"/equipment/{equipment_id}",
        json={
            "code": "EQ-005-UPDATED",
            "name": "Tablet Pro",
            "category": "Dispositivo móvil",
            "description": "Descripción actualizada",
            "status": "LOANED",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "EQ-005-UPDATED"
    assert data["name"] == "Tablet Pro"
    assert data["status"] == "LOANED"
    assert data["description"] == "Descripción actualizada"


def test_t6_eliminar_equipo_sin_prestamos_activos(client_and_session_factory):
    client, _ = client_and_session_factory

    created = client.post(
        "/equipment",
        json={
            "code": "EQ-006",
            "name": "Teclado",
            "category": "Periférico",
            "description": "Para oficina",
            "status": "AVAILABLE",
        },
    )
    assert created.status_code == 201
    equipment_id = created.json()["id"]

    deleted = client.delete(f"/equipment/{equipment_id}")
    assert deleted.status_code == 200

    get_deleted = client.get(f"/equipment/{equipment_id}")
    assert get_deleted.status_code == 404


def test_t7_eliminar_equipo_con_prestamos_activos(client_and_session_factory):
    client, SessionLocal = client_and_session_factory

    created = client.post(
        "/equipment",
        json={
            "code": "EQ-007",
            "name": "Laptop de prueba",
            "category": "Computadora",
            "description": "Con préstamo activo",
            "status": "LOANED",
        },
    )
    assert created.status_code == 201
    equipment_id = created.json()["id"]

    db = SessionLocal()
    try:
        borrower = Borrower(
            dni="12345678",
            full_name="Juan Pérez",
            email="juan.perez@example.com",
            phone="999888777",
            department="Sistemas",
            created_at=datetime.utcnow(),
        )
        db.add(borrower)
        db.commit()
        db.refresh(borrower)

        loan = Loan(
            equipment_id=equipment_id,
            borrower_id=borrower.id,
            loan_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            return_date=None,
            status="ACTIVE",
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        db.add(loan)
        db.commit()
    finally:
        db.close()

    deleted = client.delete(f"/equipment/{equipment_id}")
    assert deleted.status_code == 409