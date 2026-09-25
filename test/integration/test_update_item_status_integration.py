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

    result = await db_session.execute(
        text(
            "SELECT estado FROM item_menu WHERE nombre_item = 'Mojito' AND id_cobot = 'CBT001'"
        )
    )
    assert result.scalar_one() is True


@pytest.mark.xfail(
    reason="PENDIENTE: update_menu_item_state aún no valida existencia del ítem "
    "(falta el IF NOT EXISTS + RAISE EXCEPTION, a corregir después).",
    strict=True,
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
    """
    Confirma que el fix de ambigüedad de columna también corrigió el
    aislamiento entre cobots: CBT002 ya no puede cambiar el estado de
    un ítem que pertenece a CBT001.
    """
    repo = CatalogRepository(db_session)

    await repo.update_item_status(
        item_state=True,
        item_name="Mojito",  # pertenece a CBT001
        id_cobot="CBT002",  # cobot equivocado
    )

    result = await db_session.execute(
        text(
            "SELECT estado FROM item_menu WHERE nombre_item = 'Mojito' AND id_cobot = 'CBT001'"
        )
    )
    # El estado original (false, del seed_data) no debe haber cambiado
    assert result.scalar_one() is False, (
        "Si esto falla con True, el filtro por id_cobot no está "
        "funcionando como se esperaba."
    )
