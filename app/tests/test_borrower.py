from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.controllers.borrower_controller import router
from app.models.borrower import Borrower
from database import Base, get_db


@pytest.fixture()
def client_and_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'borrower_test.db'}",
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


def test_tb1_registrar_solicitante_valido(client_and_session_factory):
    client, _ = client_and_session_factory

    response = client.post(
        "/borrowers",
        json={
            "dni": "12345678",
            "full_name": "Juan Pérez",
            "email": "juan@example.com",
            "phone": "999888777",
            "department": "Sistemas",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["dni"] == "12345678"
    assert data["full_name"] == "Juan Pérez"


def test_tb2_registrar_solicitante_con_dni_duplicado(client_and_session_factory):
    client, _ = client_and_session_factory

    payload = {
        "dni": "87654321",
        "full_name": "Ana Torres",
        "email": "ana@example.com",
        "phone": "900111222",
        "department": "TI",
    }

    first = client.post("/borrowers", json=payload)
    assert first.status_code == 201

    second = client.post("/borrowers", json=payload)
    assert second.status_code == 409


def test_tb3_registrar_solicitante_con_campo_obligatorio_faltante(client_and_session_factory):
    client, _ = client_and_session_factory

    response = client.post(
        "/borrowers",
        json={
            "dni": "11112222",
            "email": "sin_nombre@example.com",
            "phone": "900000000",
            "department": "Soporte",
        },
    )

    assert response.status_code == 422


def test_tb4_actualizar_solicitante_valido(client_and_session_factory):
    client, _ = client_and_session_factory

    created = client.post(
        "/borrowers",
        json={
            "dni": "55556666",
            "full_name": "Carlos Ruiz",
            "email": "carlos@example.com",
            "phone": "988776655",
            "department": "Infraestructura",
        },
    )
    assert created.status_code == 201
    borrower_id = created.json()["id"]

    response = client.put(
        f"/borrowers/{borrower_id}",
        json={
            "dni": "55556667",
            "full_name": "Carlos Ruiz Actualizado",
            "email": "carlos.actualizado@example.com",
            "phone": "900123456",
            "department": "Mesa de ayuda",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dni"] == "55556667"
    assert data["full_name"] == "Carlos Ruiz Actualizado"
    assert data["department"] == "Mesa de ayuda"