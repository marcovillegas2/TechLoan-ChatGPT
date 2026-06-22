from sqlalchemy.orm import Session

from app.repositories.equipment_repository import EquipmentRepository


class EquipmentService:
    def __init__(self, repository: EquipmentRepository | None = None):
        self.repository = repository or EquipmentRepository()

    def create_equipment(self, db: Session, equipment_data: dict):
        nombre = (equipment_data.get("nombre") or "").strip()
        codigo_inventario = (equipment_data.get("codigo_inventario") or "").strip()
        descripcion = (equipment_data.get("descripcion") or "").strip()
        categoria = (equipment_data.get("categoria") or "").strip()
        ubicacion = (equipment_data.get("ubicacion") or "").strip()

        if not nombre:
            raise ValueError("El nombre del equipo es obligatorio.")

        if len(nombre) > 150:
            raise ValueError("El nombre del equipo no puede superar 150 caracteres.")

        if not codigo_inventario:
            raise ValueError("El código de inventario es obligatorio.")

        if len(codigo_inventario) > 50:
            raise ValueError("El código de inventario no puede superar 50 caracteres.")

        if self.repository.exists_by_codigo_inventario(db, codigo_inventario):
            raise ValueError("Ya existe un equipo con ese código de inventario.")

        payload = {
            "nombre": nombre,
            "codigo_inventario": codigo_inventario,
            "descripcion": descripcion or None,
            "categoria": categoria or None,
            "ubicacion": ubicacion or None,
            "estado": "Disponible",
        }

        return self.repository.create(db, payload)