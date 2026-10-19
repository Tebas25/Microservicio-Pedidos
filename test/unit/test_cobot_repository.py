from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.catalog_respository import CatalogRepository


def make_db(rows: list[dict]) -> AsyncMock:
    """Sesión falsa: execute() devuelve un resultado cuyas filas son `rows`."""
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    db = AsyncMock()
    db.execute.return_value = result
    return db


@pytest.mark.asyncio
async def test_get_cobot_maps_rows_and_ignores_extra_columns():
    db = make_db(
        [
            {
                "id_cobot": "CBT000T",
                "nombre_cobot": "Cobot JAKA",
                "columna_interna": "no debe salir",
            }
        ]
    )
    repo = CatalogRepository(db)

    cobots = await repo.get_cobot()

    assert len(cobots) == 1
    assert cobots[0].id_cobot == "CBT000T"
    assert cobots[0].nombre_cobot == "Cobot JAKA"
    assert not hasattr(cobots[0], "columna_interna")
    db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_cobot_returns_empty_list_when_there_are_no_rows():
    repo = CatalogRepository(make_db([]))

    assert await repo.get_cobot() == []
