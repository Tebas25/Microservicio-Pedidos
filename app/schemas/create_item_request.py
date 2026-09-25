from pydantic import BaseModel
from decimal import Decimal


class CreateItemRequest(BaseModel):
    nombre_item: str
    precio_item: Decimal
    estado: bool
    ingredientes: str
    codigo_modbus: str
    id_cobot: str
