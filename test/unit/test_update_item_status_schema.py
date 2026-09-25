import pytest
from pydantic import ValidationError

from app.schemas.catalog_dto import UpdateItemStatus


def test_crea_request_valido():
    payload = UpdateItemStatus(
        item_state=False,
        item_name="Mojito",
        id_cobot="CBT001",
    )

    assert payload.item_state is False
    assert payload.item_name == "Mojito"
    assert payload.id_cobot == "CBT001"


@pytest.mark.parametrize(
    "campo_faltante",
    ["item_state", "item_name", "id_cobot"],
)
def test_falla_si_falta_algun_campo_obligatorio(campo_faltante):
    datos = {
        "item_state": True,
        "item_name": "Mojito",
        "id_cobot": "CBT001",
    }
    del datos[campo_faltante]

    with pytest.raises(ValidationError):
        UpdateItemStatus(**datos)


def test_falla_si_item_state_no_es_booleano():
    with pytest.raises(ValidationError):
        UpdateItemStatus(
            item_state="no-es-booleano",
            item_name="Mojito",
            id_cobot="CBT001",
        )
