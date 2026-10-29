import pytest
from pydantic import ValidationError

from app.models.cobot_menu_item import MenuItem
from app.schemas.get_items_response import GetItemsResponse


@pytest.fixture
def items():
    return [MenuItem.model_construct() for _ in range(3)]


def errores_de(**datos):
    with pytest.raises(ValidationError) as exc:
        GetItemsResponse(**datos)
    return exc.value.errors()


# ---------- construcción ----------

def test_acepta_una_lista_vacia():
    respuesta = GetItemsResponse(items=[], total=0)

    assert respuesta.items == []
    assert respuesta.total == 0


def test_conserva_los_items_y_su_orden(items):
    respuesta = GetItemsResponse(items=items, total=len(items))

    assert len(respuesta.items) == 3
    assert all(a is b for a, b in zip(respuesta.items, items))


def test_guarda_el_total(items):
    assert GetItemsResponse(items=items, total=3).total == 3


def test_los_items_son_instancias_de_menu_item(items):
    respuesta = GetItemsResponse(items=items, total=3)

    assert all(isinstance(i, MenuItem) for i in respuesta.items)


def test_el_campo_items_esta_tipado_como_lista_de_menu_item():
    assert GetItemsResponse.model_fields["items"].annotation == list[MenuItem]


# ---------- campos obligatorios ----------

@pytest.mark.parametrize("faltante", ["items", "total"])
def test_cada_campo_es_obligatorio(faltante, items):
    datos = {"items": items, "total": 3}
    datos.pop(faltante)

    errores = errores_de(**datos)

    assert [(e["loc"], e["type"]) for e in errores] == [((faltante,), "missing")]


def test_sin_ningun_campo_reporta_ambos():
    with pytest.raises(ValidationError) as exc:
        GetItemsResponse()

    assert {e["loc"][0] for e in exc.value.errors()} == {"items", "total"}


# ---------- items inválidos ----------

@pytest.mark.parametrize("valor", ["texto", 5, None, {}])
def test_items_debe_ser_una_lista(valor):
    errores = errores_de(items=valor, total=0)

    assert [e["loc"] for e in errores] == [("items",)]


@pytest.mark.parametrize("elemento", [123, "texto", None])
def test_cada_elemento_debe_ser_un_menu_item(elemento):
    errores = errores_de(items=[elemento], total=1)

    assert [e["loc"] for e in errores] == [("items", 0)]


def test_el_error_indica_la_posicion_del_elemento_invalido(items):
    errores = errores_de(items=[items[0], "malo", items[1]], total=3)

    assert [e["loc"] for e in errores] == [("items", 1)]


# ---------- total ----------

@pytest.mark.parametrize("entrada", ["3", 3.0])
def test_total_acepta_valores_equivalentes_a_un_entero(entrada):
    assert GetItemsResponse(items=[], total=entrada).total == 3


@pytest.mark.parametrize("entrada", ["abc", "", 2.5, None, [], {}])
def test_total_invalido_es_rechazado(entrada):
    errores = errores_de(items=[], total=entrada)

    assert [e["loc"] for e in errores] == [("total",)]


# ---------- igualdad, serialización y esquema ----------

def test_dos_respuestas_vacias_son_iguales():
    assert GetItemsResponse(items=[], total=0) == GetItemsResponse(items=[], total=0)


def test_respuestas_con_distinto_total_no_son_iguales():
    assert GetItemsResponse(items=[], total=0) != GetItemsResponse(items=[], total=1)


def test_serializa_una_lista_vacia():
    respuesta = GetItemsResponse(items=[], total=0)

    assert respuesta.model_dump() == {"items": [], "total": 0}
    assert respuesta.model_dump_json() == '{"items":[],"total":0}'


def test_valida_un_json_con_lista_vacia():
    respuesta = GetItemsResponse.model_validate_json('{"items":[],"total":0}')

    assert respuesta.items == []
    assert respuesta.total == 0


def test_el_esquema_declara_items_y_total_como_obligatorios():
    esquema = GetItemsResponse.model_json_schema()

    assert sorted(esquema["required"]) == ["items", "total"]
    assert esquema["properties"]["items"]["type"] == "array"
    assert esquema["properties"]["total"]["type"] == "integer"