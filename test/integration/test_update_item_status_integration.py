import pytest
from sqlalchemy import text

from app.repositories.catalog_respository import CatalogRepository


@pytest.mark.asyncio
async def test_update_item_status_exitoso_actualiza_en_bd_real(db_session, seed_data):
    repo = CatalogRepository(db_session)

    await repo.update_item_status(
        item_state=True,
        item_name="Mojito",
        id_cobot="CBT001",
    )

    result = await db_session.execute(text("""
            SELECT cc.estado 
            FROM cobot_catalog cc
            JOIN catalog_item ci ON cc.id_item = ci.id_item
            WHERE ci.nombre_item = 'Mojito' AND cc.id_cobot = 'CBT001'
        """))
    assert result.scalar_one() is True


@pytest.mark.asyncio
async def test_update_item_status_deberia_fallar_si_item_no_existe(
    db_session, seed_data
):
    repo = CatalogRepository(db_session)

    with pytest.raises(RuntimeError):
        await repo.update_item_status(
            item_state=True,
            item_name="ItemInexistente",
            id_cobot="CBT001",
        )


@pytest.mark.asyncio
async def test_update_item_status_deberia_fallar_si_item_no_existe(
    db_session, seed_data
):
    repo = CatalogRepository(db_session)

    with pytest.raises(RuntimeError):
        await repo.update_item_status(
            item_state=True,
            item_name="ItemQueNoExiste",
            id_cobot="CBT001",
        )


@pytest.mark.asyncio
async def test_update_item_status_no_afecta_items_de_otro_cobot(db_session, seed_data):
    repo = CatalogRepository(db_session)

    with pytest.raises(RuntimeError):
        await repo.update_item_status(
            item_state=True,
            item_name="Mojito",
            id_cobot="CBT002",
        )

    result = await db_session.execute(text("""
        SELECT cc.estado
        FROM public.cobot_catalog cc
        JOIN public.catalog_item ci ON cc.id_item = ci.id_item
        WHERE ci.nombre_item = 'Mojito'
          AND cc.id_cobot = 'CBT001'
    """))

    assert result.scalar_one() is False
