from datetime import date, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.controllers.loan_controller import router
from app.models.borrower import Borrower
from app.models.equipment import Equipment
from app.models.loan import Loan
from database import Base, get_db


@pytest.fixture()
def client_and_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'loan_test.db'}",
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


def seed_equipment(db, code: str, status: str = "DISPONIBLE") -> Equipment:
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


def seed_borrower(db, dni: str = "12345678") -> Borrower:
    borrower = Borrower(
        dni=dni,
        full_name="Juan Pérez",
        email="juan@example.com",
        phone="999888777",
        department="Sistemas",
        created_at=datetime.utcnow(),
    )
    db.add(borrower)
    db.commit()
    db.refresh(borrower)
    return borrower


def test_tl1_registrar_prestamo_con_equipo_disponible_y_borrower_existente(
    client_and_session_factory,
):
    client, SessionLocal = client_and_session_factory

    db = SessionLocal()
    try:
        equipment = seed_equipment(db, "EQ-101", "DISPONIBLE")
        borrower = seed_borrower(db, "11112222")
    finally:
        db.close()

    response = client.post(
        "/loans",
        json={
            "equipment_id": equipment.id,
            "borrower_id": borrower.id,
            "loan_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "return_date": None,
            "status": "ACTIVO",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["equipment_id"] == equipment.id
    assert data["borrower_id"] == borrower.id
    assert data["status"] == "ACTIVO"

    db = SessionLocal()
    try:
        updated_equipment = db.query(Equipment).filter(Equipment.id == equipment.id).first()
        assert updated_equipment.status == "PRESTADO"
    finally:
        db.close()


def test_tl2_registrar_prestamo_con_equipo_no_disponible(client_and_session_factory):
    client, SessionLocal = client_and_session_factory

    db = SessionLocal()
    try:
        equipment = seed_equipment(db, "EQ-102", "PRESTADO")
        borrower = seed_borrower(db, "22223333")
    finally:
        db.close()

    response = client.post(
        "/loans",
        json={
            "equipment_id": equipment.id,
            "borrower_id": borrower.id,
            "loan_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=5)),
            "return_date": None,
            "status": "ACTIVO",
        },
    )

    assert response.status_code == 409


def test_tl3_registrar_prestamo_con_borrower_inexistente(client_and_session_factory):
    client, SessionLocal = client_and_session_factory

    db = SessionLocal()
    try:
        equipment = seed_equipment(db, "EQ-103", "DISPONIBLE")
    finally:
        db.close()

    response = client.post(
        "/loans",
        json={
            "equipment_id": equipment.id,
            "borrower_id": 9999,
            "loan_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=5)),
            "return_date": None,
            "status": "ACTIVO",
        },
    )

    assert response.status_code == 404


def test_tl4_registrar_prestamo_con_fecha_limite_invalida(client_and_session_factory):
    client, SessionLocal = client_and_session_factory

    db = SessionLocal()
    try:
        equipment = seed_equipment(db, "EQ-104", "DISPONIBLE")
        borrower = seed_borrower(db, "33334444")
    finally:
        db.close()

    response = client.post(
        "/loans",
        json={
            "equipment_id": equipment.id,
            "borrower_id": borrower.id,
            "loan_date": str(date.today()),
            "due_date": str(date.today() - timedelta(days=1)),
            "return_date": None,
            "status": "ACTIVO",
        },
    )

    assert response.status_code == 422


def test_tl5_registrar_devolucion_de_prestamo_activo(client_and_session_factory):
    client, SessionLocal = client_and_session_factory

    db = SessionLocal()
    try:
        equipment = seed_equipment(db, "EQ-105", "DISPONIBLE")
        borrower = seed_borrower(db, "44445555")
    finally:
        db.close()

    created = client.post(
        "/loans",
        json={
            "equipment_id": equipment.id,
            "borrower_id": borrower.id,
            "loan_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "return_date": None,
            "status": "ACTIVO",
        },
    )
    assert created.status_code == 201
    loan_id = created.json()["id"]

    returned = client.post(f"/loans/{loan_id}/return")
    assert returned.status_code == 200
    data = returned.json()
    assert data["status"] == "DEVUELTO"
    assert data["return_date"] is not None

    db = SessionLocal()
    try:
        updated_equipment = db.query(Equipment).filter(Equipment.id == equipment.id).first()
        assert updated_equipment.status == "DISPONIBLE"
    finally:
        db.close()


def test_tl6_registrar_devolucion_de_prestamo_ya_devuelto(client_and_session_factory):
    client, _ = client_and_session_factory

    db = client_and_session_factory[1]()
    try:
        equipment = seed_equipment(db, "EQ-106", "DISPONIBLE")
        borrower = seed_borrower(db, "55556666")
    finally:
        db.close()

    created = client.post(
        "/loans",
        json={
            "equipment_id": equipment.id,
            "borrower_id": borrower.id,
            "loan_date": str(date.today()),
            "due_date": str(date.today() + timedelta(days=7)),
            "return_date": None,
            "status": "ACTIVO",
        },
    )
    assert created.status_code == 201
    loan_id = created.json()["id"]

    first_return = client.post(f"/loans/{loan_id}/return")
    assert first_return.status_code == 200

    second_return = client.post(f"/loans/{loan_id}/return")
    assert second_return.status_code == 409


def test_tl7_listar_equipos_disponibles(client_and_session_factory):
    client, SessionLocal = client_and_session_factory

    db = SessionLocal()
    try:
        available_equipment = seed_equipment(db, "EQ-107", "DISPONIBLE")
        _loaned_equipment = seed_equipment(db, "EQ-108", "PRESTADO")
    finally:
        db.close()

    response = client.get("/loans/available-equipment")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == available_equipment.id
    assert data[0]["status"] == "DISPONIBLE"