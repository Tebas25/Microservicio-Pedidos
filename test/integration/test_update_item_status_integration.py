import pytest
from sqlalchemy import text

from app.repositories.catalog_respository import CatalogRepository


@pytest.mark.asyncio
async def test_update_item_status_exitoso_actualiza_en_bd_real(db_session, seed_data):
    """Camino feliz: sí funciona correctamente cuando los datos son válidos."""
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
    reason="BUG CONOCIDO: update_menu_item_state no valida que el ítem exista; "
    "hace UPDATE de 0 filas sin lanzar excepción. Ver ticket #XXX.",
    strict=True,
)
@pytest.mark.asyncio
async def test_update_item_status_deberia_fallar_si_item_no_existe(
    db_session, seed_data
):
    """
    Comportamiento ESPERADO (aún no implementado): actualizar un ítem que
    no existe debería lanzar RuntimeError, igual que add_menu_item lanza
    CobotNotFoundError / ItemAlreadyExistsError.

    Este test está marcado xfail(strict=True) a propósito: si algún día
    se corrige el SP y el test empieza a pasar, pytest fallará el suite
    para forzarnos a quitar el marcador y confirmar la corrección.
    """
    repo = CatalogRepository(db_session)

    with pytest.raises(RuntimeError):
        await repo.update_item_status(
            item_state=True,
            item_name="ItemQueNoExiste",
            id_cobot="CBT001",
        )


@pytest.mark.asyncio
async def test_BUG_update_item_status_ignora_id_cobot_y_afecta_cualquier_item(
    db_session, seed_data
):
    """
    DOCUMENTA UN BUG DE SEGURIDAD DE DATOS (no un xfail: este test PASA
    hoy, confirmando que el bug existe de forma reproducible).

    El SP update_menu_item_state recibe id_cobot como parámetro pero
    nunca lo usa para filtrar el UPDATE (compara cobots.id_cobot contra
    item_menu.id_cobot, ignorando el parámetro de entrada). Esto permite
    que un cobot actualice el ítem de OTRO cobot sin restricción, siempre
    que el nombre del ítem coincida.

    Este test debe eliminarse o invertirse (assert is False) una vez
    que el SP se corrija para validar el cobot correctamente.
    """
    repo = CatalogRepository(db_session)

    await repo.update_item_status(
        item_state=True,
        item_name="Mojito",
        id_cobot="CBT002",
    )

    result = await db_session.execute(
        text(
            "SELECT estado FROM item_menu WHERE nombre_item = 'Mojito' AND id_cobot = 'CBT001'"
        )
    )
    estado_actual = result.scalar_one()

    assert estado_actual is True, (
        "Si este assert falla, el bug fue corregido: el SP ahora sí "
        "valida el id_cobot correctamente. Actualiza este test a "
        "test_update_item_status_no_afecta_items_de_otro_cobot con "
        "pytest.raises(RuntimeError) en su lugar."
    )
