from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cobot_menu_item import CobotMenuItem
from app.models.db_exceptions import CobotNotFoundError, ItemAlreadyExistsError


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

    async def add_item(
        self,
        nombre_item: str,
        precio_item: Decimal,
        estado: bool,
        ingredientes: str,
        codigo_modbus: str,
        id_cobot: str,
    ) -> None:
        try:
            await self.db.execute(
                text(
                    "CALL add_menu_item("
                    ":p_nombre_item, :p_precio_item, :p_estado, "
                    ":p_ingredientes, :p_codigo_modbus, :p_id_cobot)"
                ),
                {
                    "p_nombre_item": nombre_item,
                    "p_precio_item": precio_item,
                    "p_estado": estado,
                    "p_ingredientes": ingredientes,
                    "p_codigo_modbus": codigo_modbus,
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
