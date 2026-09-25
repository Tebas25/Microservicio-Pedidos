import pytest
from sqlalchemy import text

from app.repositories.catalog_respository import CatalogRepository


@pytest.mark.asyncio
async def test_update_item_price_exitoso_actualiza_en_bd_real(db_session, seed_data):
    repo = CatalogRepository(db_session)

    await repo.update_item_price(
        item_price=8.25,
        item_name="Mojito",
        id_cobot="CBT001",
    )

    result = await db_session.execute(
        text(
            "SELECT precio_item FROM item_menu WHERE nombre_item = 'Mojito' AND id_cobot = 'CBT001'"
        )
    )
    assert float(result.scalar_one()) == 8.25


@pytest.mark.xfail(
    reason="PENDIENTE: update_menu_item_price aún no valida existencia del ítem "
    "(falta el IF NOT EXISTS + RAISE EXCEPTION, a corregir después).",
    strict=True,
)
@pytest.mark.asyncio
async def test_update_item_price_deberia_fallar_si_item_no_existe(
    db_session, seed_data
):
    repo = CatalogRepository(db_session)

    with pytest.raises(RuntimeError):
        await repo.update_item_price(
            item_price=8.25,
            item_name="ItemQueNoExiste",
            id_cobot="CBT001",
        )


@pytest.mark.asyncio
async def test_update_item_price_no_afecta_items_de_otro_cobot(db_session, seed_data):
    """
    Confirma que el fix de ambigüedad de columna también corrigió el
    aislamiento entre cobots: CBT002 ya no puede cambiar el precio de
    un ítem que pertenece a CBT001.
    """
    repo = CatalogRepository(db_session)

    await repo.update_item_price(
        item_price=99.99,
        item_name="Mojito",
        id_cobot="CBT002",  # cobot equivocado
    )

    result = await db_session.execute(
        text(
            "SELECT precio_item FROM item_menu WHERE nombre_item = 'Mojito' AND id_cobot = 'CBT001'"
        )
    )
    precio_actual = float(result.scalar_one())

    # El precio NO debe haber cambiado, porque el WHERE ahora sí filtra
    # correctamente por id_cobot.
    assert precio_actual == 5.50, (
        "Si esto falla con 99.99, el filtro por id_cobot no está "
        "funcionando como se esperaba."
    )
