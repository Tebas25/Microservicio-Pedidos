from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.cobot_menu_item import CobotMenuItem


def test_crea_item_desde_diccionario():
    item = CobotMenuItem(
        nombre_item="Pizza",
        precio_item=Decimal("10.50"),
        estado=True,
        ingredientes="queso, tomate",
        codigo_modbus="M001",
    )
    assert item.nombre_item == "Pizza"
    assert item.precio_item == Decimal("10.50")
    assert item.estado is True


def test_permite_ingredientes_y_codigo_modbus_nulos():
    item = CobotMenuItem(
        nombre_item="Agua",
        precio_item=Decimal("1.00"),
        estado=True,
        ingredientes=None,
        codigo_modbus=None,
    )
    assert item.ingredientes is None
    assert item.codigo_modbus is None


def test_falla_si_falta_campo_obligatorio():
    with pytest.raises(ValidationError):
        CobotMenuItem(
            precio_item=Decimal("5.00"),
            estado=True,
            ingredientes=None,
            codigo_modbus=None,
        )


class ObjetoConAtributos:
    def __init__(self):
        self.nombre_item = "Cerveza"
        self.precio_item = Decimal("3.50")
        self.estado = True
        self.ingredientes = None
        self.codigo_modbus = "M002"


def test_model_validate_funciona_con_objeto_por_from_attributes():
    obj = ObjetoConAtributos()
    item = CobotMenuItem.model_validate(obj)
    assert item.nombre_item == "Cerveza"
    assert item.precio_item == Decimal("3.50")