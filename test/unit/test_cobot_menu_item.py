from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.cobot_menu_item import CobotMenuItem, MenuItem

COBOT_ITEM = {
    "nombre_item": "Mojito",
    "ingredientes": "Ron, menta",
    "imagen": "http://img/mojito.png",
    "codigo_modbus": 1,
    "estado": True,
    "precio_item": "5.50",
}

MENU_ITEM = {
    "id_item": 7,
    "nombre_item": "Mojito",
    "ingredientes": "Ron, menta",
    "imagen": "http://img/mojito.png",
    "codigo_modbus": 1,
}


# =====================  CobotMenuItem  =====================

def cobot_item(**cambios):
    return CobotMenuItem(**{**COBOT_ITEM, **cambios})


def test_cobot_menu_item_guarda_todos_sus_campos():
    item = cobot_item()

    assert item.nombre_item == "Mojito"
    assert item.ingredientes == "Ron, menta"
    assert item.imagen == "http://img/mojito.png"
    assert item.codigo_modbus == 1
    assert item.estado is True
    assert item.precio_item == Decimal("5.50")


def test_cobot_menu_item_conserva_los_decimales_del_precio():
    assert str(cobot_item(precio_item="5.50").precio_item) == "5.50"


@pytest.mark.parametrize("campo", ["ingredientes", "imagen"])
def test_cobot_menu_item_acepta_none_en_ingredientes_e_imagen(campo):
    assert getattr(cobot_item(**{campo: None}), campo) is None


@pytest.mark.parametrize("campo", sorted(COBOT_ITEM))
def test_cobot_menu_item_todos_los_campos_son_obligatorios_incluso_los_nulables(campo):
    datos = {k: v for k, v in COBOT_ITEM.items() if k != campo}

    with pytest.raises(ValidationError) as exc:
        CobotMenuItem(**datos)

    assert [(e["loc"], e["type"]) for e in exc.value.errors()] == [((campo,), "missing")]


@pytest.mark.parametrize("valor", ["abc", 5.5, None, ""])
def test_cobot_menu_item_codigo_modbus_invalido(valor):
    with pytest.raises(ValidationError) as exc:
        cobot_item(codigo_modbus=valor)

    assert [e["loc"] for e in exc.value.errors()] == [("codigo_modbus",)]


@pytest.mark.parametrize("valor, esperado", [(True, True), (False, False), ("true", True), ("false", False)])
def test_cobot_menu_item_estado_acepta_booleanos(valor, esperado):
    assert cobot_item(estado=valor).estado is esperado


def test_cobot_menu_item_estado_invalido():
    with pytest.raises(ValidationError):
        cobot_item(estado="quizas")


@pytest.mark.parametrize("valor", ["abc", None, "NaN"])
def test_cobot_menu_item_precio_invalido(valor):
    with pytest.raises(ValidationError) as exc:
        cobot_item(precio_item=valor)

    assert [e["loc"] for e in exc.value.errors()] == [("precio_item",)]


def test_cobot_menu_item_se_crea_desde_una_fila_de_base_de_datos():
    fila = {**COBOT_ITEM, "precio_item": Decimal("5.50"), "columna_extra": "ignorada"}

    item = CobotMenuItem.model_validate(fila)

    assert item.nombre_item == "Mojito"
    assert not hasattr(item, "columna_extra")


def test_cobot_menu_item_se_crea_desde_un_objeto_con_atributos():
    """from_attributes=True permite validar filas/objetos ORM, no solo diccionarios."""
    objeto = SimpleNamespace(**{**COBOT_ITEM, "precio_item": Decimal("5.50")})

    item = CobotMenuItem.model_validate(objeto)

    assert item.nombre_item == "Mojito"
    assert item.precio_item == Decimal("5.50")


def test_cobot_menu_item_serializa_el_precio_como_texto_en_json():
    assert cobot_item().model_dump(mode="json")["precio_item"] == "5.50"


def test_cobot_menu_item_ida_y_vuelta_por_json():
    original = cobot_item(ingredientes=None)

    assert CobotMenuItem.model_validate_json(original.model_dump_json()) == original


def test_cobot_menu_item_tiene_from_attributes_activado():
    assert CobotMenuItem.model_config["from_attributes"] is True


# =====================  MenuItem  =====================

def menu_item(**cambios):
    return MenuItem(**{**MENU_ITEM, **cambios})


def test_menu_item_guarda_todos_sus_campos():
    item = menu_item()

    assert item.id_item == 7
    assert item.nombre_item == "Mojito"
    assert item.ingredientes == "Ron, menta"
    assert item.imagen == "http://img/mojito.png"
    assert item.codigo_modbus == 1


@pytest.mark.parametrize("campo", sorted(MENU_ITEM))
def test_menu_item_todos_los_campos_son_obligatorios(campo):
    datos = {k: v for k, v in MENU_ITEM.items() if k != campo}

    with pytest.raises(ValidationError) as exc:
        MenuItem(**datos)

    assert [(e["loc"], e["type"]) for e in exc.value.errors()] == [((campo,), "missing")]


@pytest.mark.parametrize("campo", ["ingredientes", "imagen"])
def test_menu_item_no_acepta_none_en_ingredientes_ni_imagen(campo):
    """A diferencia de CobotMenuItem, aquí ingredientes e imagen no son nulables."""
    with pytest.raises(ValidationError) as exc:
        menu_item(**{campo: None})

    assert [e["loc"] for e in exc.value.errors()] == [(campo,)]


@pytest.mark.parametrize("campo", ["id_item", "codigo_modbus"])
@pytest.mark.parametrize("valor", ["abc", 1.5, None])
def test_menu_item_los_enteros_invalidos_son_rechazados(campo, valor):
    with pytest.raises(ValidationError) as exc:
        menu_item(**{campo: valor})

    assert [e["loc"] for e in exc.value.errors()] == [(campo,)]


def test_menu_item_se_crea_desde_una_fila_de_base_de_datos():
    item = MenuItem.model_validate({**MENU_ITEM, "columna_extra": 1})

    assert item.id_item == 7


def test_menu_item_se_crea_desde_un_objeto_con_atributos():
    item = MenuItem.model_validate(SimpleNamespace(**MENU_ITEM))

    assert item.nombre_item == "Mojito"


def test_menu_item_ida_y_vuelta_por_json():
    original = menu_item()

    assert MenuItem.model_validate_json(original.model_dump_json()) == original


def test_menu_item_tiene_from_attributes_activado():
    assert MenuItem.model_config["from_attributes"] is True