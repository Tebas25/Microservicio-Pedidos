from pydantic import BaseModel
from decimal import Decimal


class CreateItemRequest(BaseModel):
    nombre_item: str
    ingredientes: str
    imagen: str
    codigo_modbus: int
