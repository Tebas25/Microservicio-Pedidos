from app.repositories.catalog_respository import CatalogRepository
from app.schemas.catalog_dto import UpdateItemStatus


class CatalogService:
    def __init__(self, catalog_repository: CatalogRepository):
        self.catalog_repository = catalog_repository

    async def update_item_state(self, update_item_status: UpdateItemStatus) -> None:
        return await self.catalog_repository.update_item_status(
            update_item_status.item_state,
            update_item_status.item_name,
            update_item_status.id_cobot,
        )
