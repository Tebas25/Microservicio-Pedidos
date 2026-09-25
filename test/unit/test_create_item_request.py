from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.create_item_request import CreateItemRequest


def test_crea_request_valido():
    payload = CreateItemRequest(
        nombre_item="Mojito",
        precio_item=Decimal("5.50"),
        estado=True,
        ingredientes="ron, menta, limón",
        codigo_modbus="M010",
        id_cobot="CBT001",
    )

    assert payload.nombre_item == "Mojito"
    assert payload.precio_item == Decimal("5.50")
    assert payload.id_cobot == "CBT001"


def test_convierte_precio_numerico_a_decimal():
    payload = CreateItemRequest(
        nombre_item="Agua",
        precio_item=1.5,  # viene como float/int desde JSON
        estado=True,
        ingredientes="agua",
        codigo_modbus="M020",
        id_cobot="CBT002",
    )

    assert isinstance(payload.precio_item, Decimal)


@pytest.mark.parametrize(
    "campo_faltante",
    ["nombre_item", "precio_item", "estado", "ingredientes", "codigo_modbus", "id_cobot"],
)
def test_falla_si_falta_algun_campo_obligatorio(campo_faltante):
    datos = {
        "nombre_item": "Mojito",
        "precio_item": Decimal("5.50"),
        "estado": True,
        "ingredientes": "ron",
        "codigo_modbus": "M010",
        "id_cobot": "CBT001",
    }
    del datos[campo_faltante]

    with pytest.raises(ValidationError):
        CreateItemRequest(**datos)


def test_falla_si_precio_no_es_numerico():
    with pytest.raises(ValidationError):
        CreateItemRequest(
            nombre_item="Mojito",
            precio_item="no-es-un-numero",
            estado=True,
            ingredientes="ron",
            codigo_modbus="M010",
            id_cobot="CBT001",
        )