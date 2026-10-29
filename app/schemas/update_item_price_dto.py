from decimal import Decimal

from pydantic import BaseModel


class UpdateItemPriceDTO(BaseModel):
    item_price: Decimal
    item_name: str
    id_cobot: str
