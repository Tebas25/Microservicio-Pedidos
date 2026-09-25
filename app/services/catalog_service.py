from app.repositories.catalog_respository import CatalogRepository
from app.schemas.catalog_dto import UpdateItemStatus
from app.schemas.update_item_price_dto import UpdateItemPriceDTO


class CatalogService:
    def __init__(self, catalog_repository: CatalogRepository):
        self.catalog_repository = catalog_repository

    async def update_item_state(self, update_item_status: UpdateItemStatus) -> None:
        return await self.catalog_repository.update_item_status(
            update_item_status.item_state,
            update_item_status.item_name,
            update_item_status.id_cobot,
        )

    async def update_item_price(self, update_item_price: UpdateItemPriceDTO) -> None:
        return await self.catalog_repository.update_item_price(
            update_item_price.item_price,
            update_item_price.item_name,
            update_item_price.id_cobot,
        )
