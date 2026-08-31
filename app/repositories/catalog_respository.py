from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cobot_menu_item import CobotMenuItem


class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_menu(self, id_cobot: str) -> list[CobotMenuItem]:
        result = await self.db.execute(
            text("SELECT * FROM get_cobot_menu(:p_id_cobot)"),
            {"p_id_cobot": id_cobot},
        )
        rows = result.mappings().all()
        return [CobotMenuItem.model_validate(dict(row)) for row in rows]
