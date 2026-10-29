from decimal import Decimal

from pydantic import BaseModel


class AddItemToCtlgRequest(BaseModel):
    id_cobot: str
    nombre_item: str
    precio_item: Decimal
