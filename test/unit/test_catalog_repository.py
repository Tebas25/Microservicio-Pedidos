from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.models.cobot_menu_item import CobotMenuItem, MenuItem
from app.models.db_exceptions import ItemAlreadyExistsError, ItemNotFoundError
from app.repositories import catalog_respository
from app.repositories.catalog_respository import CatalogRepository

pytestmark = pytest.mark.asyncio


# ---------- ayudas ----------

def make_session(rows=None):
    """AsyncSession falsa: execute() devuelve un resultado cuyas filas son `rows`."""
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows if rows is not None else []
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def sql_of(db) -> str:
    return str(db.execute.await_args.args[0])


def params_of(db) -> dict:
    return db.execute.await_args.args[1]


def db_error(mensaje: str) -> DBAPIError:
    return DBAPIError("CALL algo()", {}, Exception(mensaje))


FILA_MENU = {
    "nombre_item": "Mojito",
    "ingredientes": "Ron, menta",
    "imagen": "http://img/mojito.png",
    "codigo_modbus": 1,
    "estado": True,
    "precio_item": Decimal("5.50"),
}

FILA_ITEM = {
    "id_item": 7,
    "nombre_item": "Mojito",
    "ingredientes": "Ron, menta",
    "imagen": "http://img/mojito.png",
    "codigo_modbus": 1,
}


# ---------- constructor ----------

async def test_guarda_la_sesion():
    db = make_session()

    assert CatalogRepository(db).db is db


# ---------- get_cobot ----------

async def test_get_cobot_convierte_cada_fila_con_cobot_dto(monkeypatch):
    class FakeDto:
        @classmethod
        def model_validate(cls, datos):
            return ("dto", datos)

    monkeypatch.setattr(catalog_respository, "CobotDto", FakeDto)
    db = make_session([{"id_cobot": "c1"}, {"id_cobot": "c2"}])

    resultado = await CatalogRepository(db).get_cobot()

    assert resultado == [("dto", {"id_cobot": "c1"}), ("dto", {"id_cobot": "c2"})]
    assert sql_of(db) == "SELECT * FROM cobots"


async def test_get_cobot_sin_filas_devuelve_lista_vacia():
    db = make_session([])

    assert await CatalogRepository(db).get_cobot() == []


# ---------- get_menu ----------

async def test_get_menu_devuelve_los_items_del_cobot_en_orden():
    otra = {**FILA_MENU, "nombre_item": "Daiquiri", "precio_item": Decimal("6.00")}
    db = make_session([FILA_MENU, otra])

    items = await CatalogRepository(db).get_menu("cobot-1")

    assert all(isinstance(i, CobotMenuItem) for i in items)
    assert [i.nombre_item for i in items] == ["Mojito", "Daiquiri"]
    assert items[0].precio_item == Decimal("5.50")


async def test_get_menu_llama_a_la_funcion_con_el_id_del_cobot():
    db = make_session([])

    await CatalogRepository(db).get_menu("cobot-1")

    assert "get_cobot_menu(:p_id_cobot)" in sql_of(db)
    assert params_of(db) == {"p_id_cobot": "cobot-1"}


async def test_get_menu_sin_filas_devuelve_lista_vacia():
    assert await CatalogRepository(make_session([])).get_menu("cobot-1") == []


async def test_get_menu_ignora_columnas_extra():
    db = make_session([{**FILA_MENU, "id_cobot": "cobot-1"}])

    items = await CatalogRepository(db).get_menu("cobot-1")

    assert len(items) == 1


async def test_get_menu_con_una_fila_incompleta_lanza_validation_error():
    fila = {k: v for k, v in FILA_MENU.items() if k != "precio_item"}
    db = make_session([fila])

    with pytest.raises(ValidationError):
        await CatalogRepository(db).get_menu("cobot-1")


async def test_get_menu_es_solo_lectura():
    db = make_session([FILA_MENU])

    await CatalogRepository(db).get_menu("cobot-1")

    db.commit.assert_not_awaited()
    db.rollback.assert_not_awaited()


# ---------- get_all_items ----------

async def test_get_all_items_devuelve_menu_items():
    db = make_session([FILA_ITEM, {**FILA_ITEM, "id_item": 8, "nombre_item": "Daiquiri"}])

    items = await CatalogRepository(db).get_all_items()

    assert all(isinstance(i, MenuItem) for i in items)
    assert [(i.id_item, i.nombre_item) for i in items] == [(7, "Mojito"), (8, "Daiquiri")]


async def test_get_all_items_llama_a_la_funcion_sin_parametros():
    db = make_session([])

    await CatalogRepository(db).get_all_items()

    assert "get_all_items()" in sql_of(db)
    assert len(db.execute.await_args.args) == 1   # sin diccionario de parámetros


async def test_get_all_items_sin_filas_devuelve_lista_vacia():
    assert await CatalogRepository(make_session([])).get_all_items() == []


async def test_get_all_items_con_una_fila_invalida_lanza_validation_error():
    db = make_session([{**FILA_ITEM, "id_item": "no-numero"}])

    with pytest.raises(ValidationError):
        await CatalogRepository(db).get_all_items()


# ---------- get_last_update_date ----------

async def test_get_last_update_date_devuelve_la_fecha_como_texto():
    db = make_session([{"ultima_actualizacion_catalogo": "2026-10-22T10:00:00"}])

    fecha = await CatalogRepository(db).get_last_update_date("cobot-1")

    assert fecha == "2026-10-22T10:00:00"


async def test_get_last_update_date_convierte_un_datetime_a_texto():
    momento = datetime(2026, 10, 22, 10, 0, 0)
    db = make_session([{"ultima_actualizacion_catalogo": momento}])

    fecha = await CatalogRepository(db).get_last_update_date("cobot-1")

    assert isinstance(fecha, str)
    assert fecha == str(momento)


async def test_get_last_update_date_llama_a_la_funcion_con_el_id_del_cobot():
    db = make_session([{"ultima_actualizacion_catalogo": "x"}])

    await CatalogRepository(db).get_last_update_date("cobot-9")

    assert "check_catalog_update(:p_id_cobot)" in sql_of(db)
    assert params_of(db) == {"p_id_cobot": "cobot-9"}


async def test_get_last_update_date_usa_solo_la_primera_fila():
    db = make_session([
        {"ultima_actualizacion_catalogo": "primera"},
        {"ultima_actualizacion_catalogo": "segunda"},
    ])

    assert await CatalogRepository(db).get_last_update_date("cobot-1") == "primera"


# ---------- add_item ----------

async def test_add_item_ejecuta_el_procedimiento_con_sus_parametros():
    db = make_session()

    await CatalogRepository(db).add_item("Mojito", "Ron, menta", "http://img/m.png", 3)

    assert "CALL create_item(" in sql_of(db)
    assert params_of(db) == {
        "p_nombre_item": "Mojito",
        "p_ingredientes": "Ron, menta",
        "p_imagen": "http://img/m.png",
        "p_codigo_modbus": 3,
    }


async def test_add_item_hace_commit_y_no_devuelve_nada():
    db = make_session()

    resultado = await CatalogRepository(db).add_item("Mojito", "Ron", "img", 3)

    assert resultado is None
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


async def test_add_item_duplicado_lanza_item_already_exists_y_hace_rollback():
    db = make_session()
    original = db_error('duplicate key: item "Mojito" already exists')
    db.execute.side_effect = original

    with pytest.raises(ItemAlreadyExistsError) as exc:
        await CatalogRepository(db).add_item("Mojito", "Ron", "img", 3)

    assert exc.value.nombre_item == "Mojito"
    assert exc.value.__cause__ is original
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


async def test_add_item_con_otro_error_de_base_de_datos_lo_relanza_tal_cual():
    db = make_session()
    original = db_error("connection reset by peer")
    db.execute.side_effect = original

    with pytest.raises(DBAPIError) as exc:
        await CatalogRepository(db).add_item("Mojito", "Ron", "img", 3)

    assert exc.value is original
    db.rollback.assert_awaited_once()


async def test_add_item_sin_orig_usa_el_texto_completo_del_error():
    """Si el error no trae `orig`, el mensaje se toma de str(exc) (incluye el SQL)."""
    db = make_session()
    db.execute.side_effect = DBAPIError("CALL create_item: already exists", {}, None)

    with pytest.raises(ItemAlreadyExistsError):
        await CatalogRepository(db).add_item("Mojito", "Ron", "img", 3)


# ---------- add_item_to_catalog ----------

async def test_add_item_to_catalog_ejecuta_el_procedimiento_con_sus_parametros():
    db = make_session()

    await CatalogRepository(db).add_item_to_catalog("cobot-1", "Mojito", Decimal("5.50"))

    assert "CALL add_item_to_cobot_catalog(" in sql_of(db)
    assert params_of(db) == {
        "p_id_cobot": "cobot-1",
        "p_nombre_item": "Mojito",
        "p_precio_item": Decimal("5.50"),
    }


async def test_add_item_to_catalog_envia_el_precio_como_decimal_sin_perder_precision():
    db = make_session()

    await CatalogRepository(db).add_item_to_catalog("cobot-1", "Mojito", Decimal("0.10"))

    enviado = params_of(db)["p_precio_item"]
    assert isinstance(enviado, Decimal)   # un float aquí perdería precisión (0.1 != Decimal("0.10"))
    assert enviado == Decimal("0.10")


async def test_add_item_to_catalog_hace_commit_y_no_devuelve_nada():
    db = make_session()

    resultado = await CatalogRepository(db).add_item_to_catalog("cobot-1", "Mojito", Decimal("5.50"))

    assert resultado is None
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


async def test_add_item_to_catalog_item_inexistente_lanza_item_not_found():
    db = make_session()
    original = db_error('el item "Mojito" no existe')
    db.execute.side_effect = original

    with pytest.raises(ItemNotFoundError) as exc:
        await CatalogRepository(db).add_item_to_catalog("cobot-1", "Mojito", Decimal("5.50"))

    assert exc.value.nombre_item == "Mojito"
    assert exc.value.__cause__ is original
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


async def test_add_item_to_catalog_con_otro_error_lo_relanza_tal_cual():
    db = make_session()
    original = db_error("deadlock detected")
    db.execute.side_effect = original

    with pytest.raises(DBAPIError) as exc:
        await CatalogRepository(db).add_item_to_catalog("cobot-1", "Mojito", Decimal("5.50"))

    assert exc.value is original
    db.rollback.assert_awaited_once()


async def test_add_item_to_catalog_sin_orig_usa_el_texto_completo_del_error():
    db = make_session()
    db.execute.side_effect = DBAPIError("CALL x: el item no existe", {}, None)

    with pytest.raises(ItemNotFoundError):
        await CatalogRepository(db).add_item_to_catalog("cobot-1", "Mojito", Decimal("5.50"))


# ---------- update_item_status ----------

async def test_update_item_status_ejecuta_el_procedimiento_con_sus_parametros():
    db = make_session()

    await CatalogRepository(db).update_item_status(False, "Mojito", "cobot-1")

    assert "CALL update_menu_item_state(" in sql_of(db)
    assert params_of(db) == {
        "p_item_state": False,
        "p_item_name": "Mojito",
        "p_id_cobot": "cobot-1",
    }


async def test_update_item_status_hace_commit_y_no_devuelve_nada():
    db = make_session()

    resultado = await CatalogRepository(db).update_item_status(True, "Mojito", "cobot-1")

    assert resultado is None
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


async def test_update_item_status_con_error_hace_rollback_y_lanza_runtime_error(capsys):
    db = make_session()
    original = db_error("fallo de base de datos")
    db.execute.side_effect = original

    with pytest.raises(RuntimeError) as exc:
        await CatalogRepository(db).update_item_status(True, "Mojito", "cobot-1")

    assert exc.value.__context__ is original   # el error original queda encadenado
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()
    salida = capsys.readouterr().out
    assert "DBAPIError real" in salida
    assert "fallo de base de datos" in salida


# ---------- update_item_price ----------

async def test_update_item_price_ejecuta_el_procedimiento_con_sus_parametros():
    db = make_session()

    await CatalogRepository(db).update_item_price(6.5, "Mojito", "cobot-1")

    assert "CALL update_menu_item_price(" in sql_of(db)
    assert params_of(db) == {
        "p_precio_item": 6.5,
        "p_item_name": "Mojito",
        "p_id_cobot": "cobot-1",
    }


async def test_update_item_price_hace_commit_y_no_devuelve_nada():
    db = make_session()

    resultado = await CatalogRepository(db).update_item_price(6.5, "Mojito", "cobot-1")

    assert resultado is None
    db.commit.assert_awaited_once()
    db.rollback.assert_not_awaited()


async def test_update_item_price_con_error_hace_rollback_y_lanza_runtime_error():
    db = make_session()
    original = db_error("fallo de base de datos")
    db.execute.side_effect = original

    with pytest.raises(RuntimeError) as exc:
        await CatalogRepository(db).update_item_price(6.5, "Mojito", "cobot-1")

    assert exc.value.__context__ is original
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()