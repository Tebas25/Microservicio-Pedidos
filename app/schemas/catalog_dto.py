from pydantic import BaseModel


class UpdateItemStatus(BaseModel):
    item_state: bool
    item_name: str
    id_cobot: str
