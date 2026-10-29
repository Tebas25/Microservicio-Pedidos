import pytest
from pydantic import ValidationError

from app.schemas.create_item_request import CreateItemRequest

VALIDO = {
    "nombre_item": "Mojito",
    "ingredientes": "Ron, menta, lima",
    "imagen": "http://img/mojito.png",
    "codigo_modbus": 1,
}


def crear(**cambios):
    return CreateItemRequest(**{**VALIDO, **cambios})


def error_de(**cambios):
    with pytest.raises(ValidationError) as exc:
        crear(**cambios)
    return exc.value.errors()


# ---------- construcción ----------

def test_crea_la_peticion_con_sus_campos():
    peticion = crear()

    assert peticion.nombre_item == "Mojito"
    assert peticion.ingredientes == "Ron, menta, lima"
    assert peticion.imagen == "http://img/mojito.png"
    assert peticion.codigo_modbus == 1


def test_codigo_modbus_se_guarda_como_entero():
    assert isinstance(crear().codigo_modbus, int)


@pytest.mark.parametrize("entrada", ["5", 5, 5.0])
def test_codigo_modbus_acepta_valores_equivalentes_a_un_entero(entrada):
    assert crear(codigo_modbus=entrada).codigo_modbus == 5


@pytest.mark.parametrize("entrada", ["abc", "", "0x01", 5.5, None, [], {}])
def test_codigo_modbus_invalido_es_rechazado(entrada):
    errores = error_de(codigo_modbus=entrada)

    assert [e["loc"] for e in errores] == [("codigo_modbus",)]


def test_codigo_modbus_en_hexadecimal_como_texto_no_se_interpreta():
    """El código debe llegar como número: "0x01" se rechaza (envíalo como 1)."""
    assert error_de(codigo_modbus="0x01")[0]["type"] == "int_parsing"


# ---------- campos obligatorios y tipos ----------

@pytest.mark.parametrize("campo", ["nombre_item", "ingredientes", "imagen", "codigo_modbus"])
def test_cada_campo_es_obligatorio(campo):
    datos = {k: v for k, v in VALIDO.items() if k != campo}

    with pytest.raises(ValidationError) as exc:
        CreateItemRequest(**datos)

    assert [(e["loc"], e["type"]) for e in exc.value.errors()] == [((campo,), "missing")]


def test_sin_ningun_campo_reporta_los_cuatro():
    with pytest.raises(ValidationError) as exc:
        CreateItemRequest()

    assert {e["loc"][0] for e in exc.value.errors()} == set(VALIDO)


@pytest.mark.parametrize("campo", ["nombre_item", "ingredientes", "imagen"])
@pytest.mark.parametrize("valor", [123, 4.5, True, [], None])
def test_los_campos_de_texto_no_aceptan_otros_tipos_ni_none(campo, valor):
    errores = error_de(**{campo: valor})

    assert [e["loc"] for e in errores] == [(campo,)]


def test_los_campos_desconocidos_se_ignoran():
    peticion = crear(extra="no importa")

    assert not hasattr(peticion, "extra")


# ---------- serialización y esquema ----------

def test_model_dump_devuelve_los_cuatro_campos():
    assert crear().model_dump() == VALIDO


def test_ida_y_vuelta_por_json_conserva_la_peticion():
    original = crear(nombre_item="Piña colada")

    recuperada = CreateItemRequest.model_validate_json(original.model_dump_json())

    assert recuperada == original


def test_dos_peticiones_con_los_mismos_datos_son_iguales():
    assert crear() == crear()
    assert crear() != crear(codigo_modbus=2)


def test_el_esquema_declara_los_cuatro_campos_como_obligatorios():
    esquema = CreateItemRequest.model_json_schema()

    assert sorted(esquema["required"]) == sorted(VALIDO)
    assert esquema["properties"]["codigo_modbus"]["type"] == "integer"