from pydantic import BaseModel


class UpdateItemPriceDTO(BaseModel):
    item_price: float
    item_name: str
    id_cobot: str
