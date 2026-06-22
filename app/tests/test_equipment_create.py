import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.equipment import Base
from app.repositories.equipment_repository import EquipmentRepository
from app.services.equipment_service import EquipmentService


def test_create_equipment_success():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        service = EquipmentService(EquipmentRepository())

        equipment = service.create_equipment(
            db,
            {
                "nombre": "Laptop Lenovo",
                "codigo_inventario": "TL-001",
                "descripcion": "Equipo para préstamo",
                "categoria": "Laptop",
                "ubicacion": "Almacén",
            },
        )

        assert equipment.id_equipo is not None
        assert equipment.nombre == "Laptop Lenovo"
        assert equipment.codigo_inventario == "TL-001"
        assert equipment.estado == "Disponible"
    finally:
        db.close()