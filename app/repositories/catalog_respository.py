from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cobot_menu_item import CobotMenuItem
from app.models.db_exceptions import CobotNotFoundError, ItemAlreadyExistsError
from app.schemas.get_cobot_dto import CobotDto


class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cobot(self) -> list[CobotDto]:
        result = await self.db.execute(text("SELECT * FROM cobots"))
        rows = result.mappings().all()
        return [CobotDto.model_validate(dict(row)) for row in rows]

    async def get_menu(self, id_cobot: str) -> list[CobotMenuItem]:
        result = await self.db.execute(
            text("SELECT * FROM get_cobot_menu(:p_id_cobot)"),
            {"p_id_cobot": id_cobot},
        )
        rows = result.mappings().all()
        return [CobotMenuItem.model_validate(dict(row)) for row in rows]

    async def get_last_update_date(self, id_cobot: str) -> str:
        result = await self.db.execute(
            text("SELECT * FROM check_catalog_update(:p_id_cobot)"),
            {"p_id_cobot": id_cobot},
        )
        rows = result.mappings().all()
        return str(rows[0]["ultima_actualizacion_catalogo"])

    async def add_item(
        self,
        nombre_item: str,
        precio_item: Decimal,
        estado: bool,
        ingredientes: str,
        id_cobot: str,
    ) -> None:
        try:
            await self.db.execute(
                text(
                    "CALL add_menu_item("
                    ":p_nombre_item, :p_precio_item, :p_estado, "
                    ":p_ingredientes, :p_id_cobot)"
                ),
                {
                    "p_nombre_item": nombre_item,
                    "p_precio_item": precio_item,
                    "p_estado": estado,
                    "p_ingredientes": ingredientes,
                    "p_id_cobot": id_cobot,
                },
            )
            await self.db.commit()
        except DBAPIError as exc:
            await self.db.rollback()
            mensaje = str(exc.orig) if exc.orig else str(exc)

            if "doesnt exist" in mensaje:
                raise CobotNotFoundError(id_cobot) from exc
            if "already exists" in mensaje:
                raise ItemAlreadyExistsError(nombre_item, id_cobot) from exc

            raise

    async def update_item_status(
        self, item_state: bool, item_name: str, id_cobot: str
    ) -> None:
        try:
            await self.db.execute(
                text(
                    "CALL update_menu_item_state(:p_item_state, :p_item_name, :p_id_cobot)"
                ),
                {
                    "p_item_state": item_state,
                    "p_item_name": item_name,
                    "p_id_cobot": id_cobot,
                },
            )
            await self.db.commit()
        except DBAPIError as exc:
            await self.db.rollback()
            print(f"DBAPIError real: {exc}")
            print(f"Orig: {exc.orig}")
            raise RuntimeError()

    async def update_item_price(
        self, item_price: float, item_name: str, id_cobot: str
    ) -> None:
        try:
            await self.db.execute(
                text(
                    "CALL update_menu_item_price(:p_precio_item, :p_item_name, :p_id_cobot)"
                ),
                {
                    "p_precio_item": item_price,
                    "p_item_name": item_name,
                    "p_id_cobot": id_cobot,
                },
            )
            await self.db.commit()
        except DBAPIError as exc:
            await self.db.rollback()
            raise RuntimeError()
