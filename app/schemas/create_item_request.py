from pydantic import BaseModel
from decimal import Decimal


class CreateItemRequest(BaseModel):
    nombre_item: str
    precio_item: Decimal
    estado: bool
    ingredientes: str
    id_cobot: str
