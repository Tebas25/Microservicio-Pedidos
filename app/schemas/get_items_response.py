from pydantic import BaseModel

from app.models.cobot_menu_item import MenuItem


class GetItemsResponse(BaseModel):
    items: list[MenuItem]
    total: int
