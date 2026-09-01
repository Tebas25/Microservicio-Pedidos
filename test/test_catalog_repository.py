from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import DBAPIError

from app.repositories.catalog_respository import CatalogRepository
from app.models.db_exceptions import CobotNotFoundError, ItemAlreadyExistsError

from app.repositories.catalog_respository import CatalogRepository


@pytest.mark.asyncio
async def test_get_menu_retorna_lista_de_items_mapeados():
    fila_simulada = {
        "nombre_item": "Pizza",
        "precio_item": Decimal("10.50"),
        "estado": True,
        "ingredientes": "queso, tomate",
        "codigo_modbus": "M001",
    }

    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [fila_simulada]

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    repo = CatalogRepository(mock_db)
    items = await repo.get_menu("CBT001")

    assert len(items) == 1
    assert items[0].nombre_item == "Pizza"
    assert items[0].precio_item == Decimal("10.50")


@pytest.mark.asyncio
async def test_get_menu_retorna_lista_vacia_si_no_hay_filas():
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    repo = CatalogRepository(mock_db)
    items = await repo.get_menu("CBT_NO_EXISTE")

    assert items == []


@pytest.mark.asyncio
async def test_get_menu_pasa_el_id_cobot_como_parametro():
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    repo = CatalogRepository(mock_db)
    await repo.get_menu("CBT999")

    args, kwargs = mock_db.execute.call_args
    assert args[1] == {"p_id_cobot": "CBT999"}

def _hacer_dbapi_error(mensaje_original: str) -> DBAPIError:
    """Construye un DBAPIError simulando el mensaje que vendría de Postgres."""
    orig = Exception(mensaje_original)
    return DBAPIError("CALL add_menu_item(...)", {}, orig)


@pytest.mark.asyncio
async def test_add_item_exitoso_hace_commit():
    mock_db = AsyncMock()

    repo = CatalogRepository(mock_db)
    await repo.add_item(
        nombre_item="Mojito",
        precio_item=Decimal("5.50"),
        estado=True,
        ingredientes="ron, menta",
        codigo_modbus="M010",
        id_cobot="CBT001",
    )

    mock_db.execute.assert_awaited_once()
    mock_db.commit.assert_awaited_once()
    mock_db.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_item_pasa_los_parametros_correctos():
    mock_db = AsyncMock()

    repo = CatalogRepository(mock_db)
    await repo.add_item(
        nombre_item="Mojito",
        precio_item=Decimal("5.50"),
        estado=True,
        ingredientes="ron, menta",
        codigo_modbus="M010",
        id_cobot="CBT001",
    )

    args, _ = mock_db.execute.call_args
    parametros = args[1]
    assert parametros == {
        "p_nombre_item": "Mojito",
        "p_precio_item": Decimal("5.50"),
        "p_estado": True,
        "p_ingredientes": "ron, menta",
        "p_codigo_modbus": "M010",
        "p_id_cobot": "CBT001",
    }


@pytest.mark.asyncio
async def test_add_item_lanza_cobot_not_found_error():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = _hacer_dbapi_error("Cobot CBT999 doesnt exist")

    repo = CatalogRepository(mock_db)

    with pytest.raises(CobotNotFoundError) as exc_info:
        await repo.add_item(
            nombre_item="Mojito",
            precio_item=Decimal("5.50"),
            estado=True,
            ingredientes="ron",
            codigo_modbus="M010",
            id_cobot="CBT999",
        )

    assert exc_info.value.id_cobot == "CBT999"
    mock_db.rollback.assert_awaited_once()
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_add_item_lanza_item_already_exists_error():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = _hacer_dbapi_error(
        'Item "Mojito" already exists for cobot CBT001'
    )

    repo = CatalogRepository(mock_db)

    with pytest.raises(ItemAlreadyExistsError) as exc_info:
        await repo.add_item(
            nombre_item="Mojito",
            precio_item=Decimal("5.50"),
            estado=True,
            ingredientes="ron",
            codigo_modbus="M010",
            id_cobot="CBT001",
        )

    assert exc_info.value.nombre_item == "Mojito"
    assert exc_info.value.id_cobot == "CBT001"
    mock_db.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_item_propaga_errores_no_reconocidos():
    mock_db = AsyncMock()
    mock_db.execute.side_effect = _hacer_dbapi_error(
        "operator does not exist: ! boolean"
    )

    repo = CatalogRepository(mock_db)

    with pytest.raises(DBAPIError):
        await repo.add_item(
            nombre_item="Mojito",
            precio_item=Decimal("5.50"),
            estado=True,
            ingredientes="ron",
            codigo_modbus="M010",
            id_cobot="CBT001",
        )

    mock_db.rollback.assert_awaited_once()