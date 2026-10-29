from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.add_item_to_catalog_request import AddItemToCtlgRequest

VALIDO = {"id_cobot": "cobot-1", "nombre_item": "Mojito", "precio_item": "5.50"}


def crear(**cambios):
    return AddItemToCtlgRequest(**{**VALIDO, **cambios})


def error_de(**cambios):
    """Ejecuta la validación esperando un fallo y devuelve la lista de errores."""
    with pytest.raises(ValidationError) as exc:
        crear(**cambios)
    return exc.value.errors()


# ---------- construcción ----------

def test_crea_la_peticion_con_sus_campos():
    peticion = crear()

    assert peticion.id_cobot == "cobot-1"
    assert peticion.nombre_item == "Mojito"
    assert peticion.precio_item == Decimal("5.50")


def test_el_precio_se_guarda_como_decimal():
    assert isinstance(crear().precio_item, Decimal)


def test_el_precio_en_texto_conserva_sus_decimales():
    assert str(crear(precio_item="5.50").precio_item) == "5.50"


@pytest.mark.parametrize("entrada, esperado", [
    ("5.50", Decimal("5.50")),
    ("6", Decimal("6")),
    (6, Decimal("6")),
    (5.5, Decimal("5.5")),
    (0.1, Decimal("0.1")),     # un float no arrastra su error binario
    (Decimal("7.25"), Decimal("7.25")),
    ("0", Decimal("0")),
])
def test_el_precio_acepta_texto_enteros_floats_y_decimales(entrada, esperado):
    assert crear(precio_item=entrada).precio_item == esperado


# ---------- precio inválido ----------

@pytest.mark.parametrize("precio", ["abc", "", "5,50", "NaN", "Infinity", "-Infinity", None, [], {}])
def test_precio_invalido_es_rechazado(precio):
    errores = error_de(precio_item=precio)

    assert [e["loc"] for e in errores] == [("precio_item",)]


@pytest.mark.parametrize("precio", ["NaN", "Infinity"])
def test_precio_no_finito_es_rechazado_con_el_motivo(precio):
    errores = error_de(precio_item=precio)

    assert errores[0]["type"] == "finite_number"


# ---------- campos obligatorios y tipos ----------

@pytest.mark.parametrize("campo", ["id_cobot", "nombre_item", "precio_item"])
def test_cada_campo_es_obligatorio(campo):
    datos = {k: v for k, v in VALIDO.items() if k != campo}

    with pytest.raises(ValidationError) as exc:
        AddItemToCtlgRequest(**datos)

    errores = exc.value.errors()
    assert [(e["loc"], e["type"]) for e in errores] == [((campo,), "missing")]


def test_sin_ningun_campo_reporta_los_tres():
    with pytest.raises(ValidationError) as exc:
        AddItemToCtlgRequest()

    assert {e["loc"][0] for e in exc.value.errors()} == {"id_cobot", "nombre_item", "precio_item"}


@pytest.mark.parametrize("campo", ["id_cobot", "nombre_item"])
@pytest.mark.parametrize("valor", [123, 4.5, True, [], None])
def test_los_campos_de_texto_no_aceptan_otros_tipos(campo, valor):
    errores = error_de(**{campo: valor})

    assert [e["loc"] for e in errores] == [(campo,)]


def test_los_campos_desconocidos_se_ignoran():
    peticion = crear(extra="no importa")

    assert not hasattr(peticion, "extra")
    assert "extra" not in peticion.model_dump()


# ---------- serialización ----------

def test_model_dump_conserva_el_decimal():
    datos = crear().model_dump()

    assert datos == {"id_cobot": "cobot-1", "nombre_item": "Mojito", "precio_item": Decimal("5.50")}


def test_model_dump_en_modo_json_serializa_el_precio_como_texto():
    datos = crear().model_dump(mode="json")

    assert datos["precio_item"] == "5.50"


def test_model_dump_json_incluye_exactamente_los_tres_campos():
    assert crear().model_dump_json() == (
        '{"id_cobot":"cobot-1","nombre_item":"Mojito","precio_item":"5.50"}'
    )


def test_ida_y_vuelta_por_json_conserva_la_peticion():
    original = crear(precio_item="12.30")

    recuperada = AddItemToCtlgRequest.model_validate_json(original.model_dump_json())

    assert recuperada == original
    assert str(recuperada.precio_item) == "12.30"


def test_valida_un_json_con_precio_numerico():
    raw = '{"id_cobot":"cobot-1","nombre_item":"Mojito","precio_item":5.5}'

    peticion = AddItemToCtlgRequest.model_validate_json(raw)

    assert peticion.precio_item == Decimal("5.5")


def test_valida_un_json_con_precio_en_texto():
    raw = '{"id_cobot":"cobot-1","nombre_item":"Mojito","precio_item":"5.50"}'

    assert AddItemToCtlgRequest.model_validate_json(raw).precio_item == Decimal("5.50")


def test_json_malformado_es_rechazado():
    with pytest.raises(ValidationError):
        AddItemToCtlgRequest.model_validate_json("no es json")


# ---------- igualdad y esquema ----------

def test_dos_peticiones_con_los_mismos_datos_son_iguales():
    assert crear() == crear()


def test_peticiones_con_distinto_precio_no_son_iguales():
    assert crear(precio_item="5.50") != crear(precio_item="6.00")


def test_el_esquema_declara_los_tres_campos_como_obligatorios():
    esquema = AddItemToCtlgRequest.model_json_schema()

    assert sorted(esquema["required"]) == ["id_cobot", "nombre_item", "precio_item"]
    assert set(esquema["properties"]) == {"id_cobot", "nombre_item", "precio_item"}