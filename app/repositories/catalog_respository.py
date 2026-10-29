from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cobot_menu_item import CobotMenuItem, MenuItem
from app.models.db_exceptions import (
    CobotNotFoundError,
    ItemAlreadyExistsError,
    ItemNotFoundError,
)
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

    async def get_all_items(self) -> list[MenuItem]:
        result = await self.db.execute(text("SELECT * FROM get_all_items()"))
        rows = result.mappings().all()
        return [MenuItem.model_validate(dict(row)) for row in rows]

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
        ingredientes: str,
        imagen: str,
        codigo_modbus: int,
    ) -> None:
        try:
            await self.db.execute(
                text(
                    "CALL create_item("
                    ":p_nombre_item, :p_ingredientes, :p_imagen, :p_codigo_modbus)"
                ),
                {
                    "p_nombre_item": nombre_item,
                    "p_ingredientes": ingredientes,
                    "p_imagen": imagen,
                    "p_codigo_modbus": codigo_modbus,
                },
            )
            await self.db.commit()
        except DBAPIError as exc:
            await self.db.rollback()
            mensaje = str(exc.orig) if exc.orig else str(exc)

            if "already exists" in mensaje:
                raise ItemAlreadyExistsError(nombre_item) from exc

            raise

    async def add_item_to_catalog(
        self, id_cobot: str, nombre_item: str, precio_item: Decimal
    ) -> None:
        try:
            await self.db.execute(
                text(
                    "CALL add_item_to_cobot_catalog(:p_id_cobot, :p_nombre_item, :p_precio_item)"
                ),
                {
                    "p_id_cobot": id_cobot,
                    "p_nombre_item": nombre_item,
                    "p_precio_item": precio_item,
                },
            )
            await self.db.commit()
        except DBAPIError as exc:
            await self.db.rollback()
            mensaje = str(exc.orig) if exc.orig else str(exc)

            if "no existe" in mensaje:
                raise ItemNotFoundError(nombre_item) from exc
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
