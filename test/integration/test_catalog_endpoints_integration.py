from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError

from app.api.dependencies import get_cobot_repository
from app.api.endpoints import router
from app.repositories.catalog_respository import CatalogRepository


@pytest.fixture
def session():
    """AsyncSession falsa; `session.filas` define las filas que devuelve execute()."""
    db = MagicMock()
    resultado = MagicMock()
    resultado.mappings.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=resultado)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.resultado = resultado
    return db


def con_filas(session, filas):
    session.resultado.mappings.return_value.all.return_value = filas


@pytest.fixture
def client(session):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cobot_repository] = lambda: CatalogRepository(session)
    return TestClient(app, raise_server_exceptions=False)


def sql_de(session) -> str:
    return str(session.execute.await_args.args[0])


def parametros_de(session) -> dict:
    return session.execute.await_args.args[1]


def error_bd(mensaje: str) -> DBAPIError:
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

NUEVO_ITEM = {
    "nombre_item": "Mojito",
    "ingredientes": "Ron, menta",
    "imagen": "http://img/mojito.png",
    "codigo_modbus": 3,
}

AGREGAR_AL_MENU = {"id_cobot": "cobot-1", "nombre_item": "Mojito", "precio_item": "5.50"}


# ---------- GET /catalog/get/{id_cobot} ----------

def test_menu_llega_de_la_base_de_datos_al_json(client, session):
    con_filas(session, [FILA_MENU, {**FILA_MENU, "nombre_item": "Daiquiri", "precio_item": Decimal("6.00")}])

    respuesta = client.get("/catalog/get/cobot-1")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 2
    assert [i["nombre_item"] for i in cuerpo["items"]] == ["Mojito", "Daiquiri"]
    assert Decimal(str(cuerpo["items"][1]["precio_item"])) == Decimal("6.00")


def test_menu_consulta_la_funcion_con_el_id_de_la_url(client, session):
    client.get("/catalog/get/cobot-42")

    assert "get_cobot_menu(:p_id_cobot)" in sql_de(session)
    assert parametros_de(session) == {"p_id_cobot": "cobot-42"}


def test_menu_sin_filas_devuelve_lista_vacia(client, session):
    respuesta = client.get("/catalog/get/cobot-1")

    assert respuesta.json() == {"items": [], "total": 0}


def test_menu_con_una_fila_corrupta_devuelve_500(client, session):
    con_filas(session, [{k: v for k, v in FILA_MENU.items() if k != "precio_item"}])

    assert client.get("/catalog/get/cobot-1").status_code == 500


# ---------- GET /catalog/all-items ----------

def test_todos_los_items_llegan_de_la_base_de_datos_al_json(client, session):
    con_filas(session, [FILA_ITEM, {**FILA_ITEM, "id_item": 8, "nombre_item": "Daiquiri"}])

    respuesta = client.get("/catalog/all-items")

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 2
    assert [i["id_item"] for i in respuesta.json()["items"]] == [7, 8]
    assert "get_all_items()" in sql_de(session)


# ---------- GET /catalog/check-update/{id_cobot} ----------

def test_check_update_devuelve_la_fecha_de_la_base_de_datos(client, session):
    momento = datetime(2026, 10, 22, 10, 0, 0)
    con_filas(session, [{"ultima_actualizacion_catalogo": momento}])

    respuesta = client.get("/catalog/check-update/cobot-1")

    assert respuesta.status_code == 200
    assert respuesta.json() == str(momento)
    assert parametros_de(session) == {"p_id_cobot": "cobot-1"}


def test_check_update_de_un_cobot_sin_filas_devuelve_500(client, session):
    """Hoy un cobot sin fila de actualización produce un 500 (IndexError en el repositorio)."""
    assert client.get("/catalog/check-update/cobot-x").status_code == 500


# ---------- POST /catalog/add-item ----------

def test_crear_item_ejecuta_el_procedimiento_y_confirma(client, session):
    respuesta = client.post("/catalog/add-item", json=NUEVO_ITEM)

    assert respuesta.status_code == 201
    assert "CALL create_item(" in sql_de(session)
    assert parametros_de(session) == {
        "p_nombre_item": "Mojito",
        "p_ingredientes": "Ron, menta",
        "p_imagen": "http://img/mojito.png",
        "p_codigo_modbus": 3,
    }
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


def test_crear_item_duplicado_en_la_base_de_datos_devuelve_409(client, session):
    session.execute.side_effect = error_bd('item "Mojito" already exists')

    respuesta = client.post("/catalog/add-item", json=NUEVO_ITEM)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": 'Item "Mojito" already exists'}
    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_crear_item_con_otro_error_de_base_de_datos_devuelve_500_y_hace_rollback(client, session):
    session.execute.side_effect = error_bd("connection reset by peer")

    respuesta = client.post("/catalog/add-item", json=NUEVO_ITEM)

    assert respuesta.status_code == 500
    session.rollback.assert_awaited_once()


def test_crear_item_invalido_no_toca_la_base_de_datos(client, session):
    respuesta = client.post("/catalog/add-item", json={**NUEVO_ITEM, "codigo_modbus": "abc"})

    assert respuesta.status_code == 422
    session.execute.assert_not_awaited()
    session.commit.assert_not_awaited()


# ---------- POST /catalog/update-item/new ----------

def test_agregar_al_menu_ejecuta_el_procedimiento_con_el_precio_decimal(client, session):
    respuesta = client.post("/catalog/update-item/new", json=AGREGAR_AL_MENU)

    assert respuesta.status_code == 201
    assert "CALL add_item_to_cobot_catalog(" in sql_de(session)
    assert parametros_de(session) == {
        "p_id_cobot": "cobot-1",
        "p_nombre_item": "Mojito",
        "p_precio_item": Decimal("5.50"),
    }
    assert isinstance(parametros_de(session)["p_precio_item"], Decimal)
    session.commit.assert_awaited_once()


def test_agregar_al_menu_un_item_que_no_existe_devuelve_404(client, session):
    session.execute.side_effect = error_bd('el item "Mojito" no existe')

    respuesta = client.post("/catalog/update-item/new", json=AGREGAR_AL_MENU)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Item Mojito doesn't exist"}
    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_agregar_al_menu_con_otro_error_de_base_de_datos_devuelve_500(client, session):
    session.execute.side_effect = error_bd("deadlock detected")

    respuesta = client.post("/catalog/update-item/new", json=AGREGAR_AL_MENU)

    assert respuesta.status_code == 500
    session.rollback.assert_awaited_once()


def test_agregar_al_menu_con_precio_invalido_no_toca_la_base_de_datos(client, session):
    respuesta = client.post("/catalog/update-item/new", json={**AGREGAR_AL_MENU, "precio_item": "abc"})

    assert respuesta.status_code == 422
    session.execute.assert_not_awaited()