from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

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