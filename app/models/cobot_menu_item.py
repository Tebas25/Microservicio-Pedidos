from decimal import Decimal
from pydantic import BaseModel


class CobotMenuItem(BaseModel):
    nombre_item: str
    ingredientes: str | None
    imagen: str | None
    codigo_modbus: int
    estado: bool
    precio_item: Decimal

    model_config = {"from_attributes": True}


class MenuItem(BaseModel):
    id_item: int
    nombre_item: str
    ingredientes: str
    imagen: str
    codigo_modbus: int

    model_config = {"from_attributes": True}
