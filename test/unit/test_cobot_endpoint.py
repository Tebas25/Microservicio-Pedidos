"""Pruebas unitarias de los endpoints REST del catálogo (router /catalog).

El repositorio se reemplaza por un mock (dependency_overrides): se verifica
solo la capa HTTP: rutas, validación de entrada, códigos de estado, cuerpos de
respuesta y traducción de excepciones a errores HTTP.

Endpoints cubiertos: /cobots, /get/{id}, /all-items, /check-update/{id},
/add-item y /update-item/new. (/update-state y /update-price usan CatalogService.)
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_cobot_repository
from app.api.endpoints import router
from app.models.cobot_menu_item import CobotMenuItem, MenuItem
from app.models.db_exceptions import (
    CobotNotFoundError,
    ItemAlreadyExistsError,
    ItemNotFoundError,
)
from app.repositories.catalog_respository import CatalogRepository


@pytest.fixture
def repo():
    return MagicMock(spec=CatalogRepository)   # los métodos async pasan a ser AsyncMock


@pytest.fixture
def client(repo):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cobot_repository] = lambda: repo
    return TestClient(app)


@pytest.fixture
def client_sin_propagar_errores(repo):
    """Para comprobar los 500: los errores no capturados se convierten en respuesta."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cobot_repository] = lambda: repo
    return TestClient(app, raise_server_exceptions=False)


def cobot_item(nombre="Mojito", precio="5.50", estado=True, ingredientes="Ron, menta"):
    return CobotMenuItem(
        nombre_item=nombre,
        ingredientes=ingredientes,
        imagen="http://img/x.png",
        codigo_modbus=1,
        estado=estado,
        precio_item=Decimal(precio),
    )


def menu_item(id_item=7, nombre="Mojito"):
    return MenuItem(
        id_item=id_item,
        nombre_item=nombre,
        ingredientes="Ron, menta",
        imagen="http://img/x.png",
        codigo_modbus=1,
    )


# ---------- router ----------

def test_el_router_usa_el_prefijo_catalog():
    assert router.prefix == "/catalog"
    assert "catalog" in router.tags


def test_el_router_expone_las_rutas_esperadas():
    rutas = {(m, r.path) for r in router.routes for m in r.methods}

    assert rutas >= {
        ("GET", "/catalog/cobots"),
        ("GET", "/catalog/get/{id_cobot}"),
        ("GET", "/catalog/all-items"),
        ("GET", "/catalog/check-update/{id_cobot}"),
        ("POST", "/catalog/add-item"),
        ("POST", "/catalog/update-item/new"),
        # ("PATCH", "/catalog/update-state"),
        # ("PATCH", "/catalog/update-price"),
    }


def test_un_metodo_no_permitido_devuelve_405(client):
    assert client.get("/catalog/add-item").status_code == 405


def test_una_ruta_inexistente_devuelve_404(client):
    assert client.get("/catalog/no-existe").status_code == 404


# ---------- GET /catalog/cobots ----------

def test_obtener_cobots_sin_cobots_devuelve_lista_vacia(client, repo):
    repo.get_cobot.return_value = []

    respuesta = client.get("/catalog/cobots")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": []}
    repo.get_cobot.assert_awaited_once_with()


# ---------- GET /catalog/get/{id_cobot} ----------

def test_obtener_menu_devuelve_los_items_y_el_total(client, repo):
    repo.get_menu.return_value = [cobot_item("Mojito", "5.50"), cobot_item("Daiquiri", "6.00")]

    respuesta = client.get("/catalog/get/cobot-1")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 2
    assert [i["nombre_item"] for i in cuerpo["items"]] == ["Mojito", "Daiquiri"]
    assert Decimal(str(cuerpo["items"][0]["precio_item"])) == Decimal("5.50")


def test_obtener_menu_incluye_todos_los_campos_de_cada_item(client, repo):
    repo.get_menu.return_value = [cobot_item(estado=False, ingredientes=None)]

    item = client.get("/catalog/get/cobot-1").json()["items"][0]

    assert set(item) == {
        "nombre_item", "ingredientes", "imagen", "codigo_modbus", "estado", "precio_item",
    }
    assert item["estado"] is False
    assert item["ingredientes"] is None
    assert item["codigo_modbus"] == 1


def test_obtener_menu_consulta_el_cobot_de_la_url(client, repo):
    repo.get_menu.return_value = []

    client.get("/catalog/get/cobot-42")

    repo.get_menu.assert_awaited_once_with("cobot-42")


def test_obtener_menu_vacio_devuelve_total_cero(client, repo):
    repo.get_menu.return_value = []

    respuesta = client.get("/catalog/get/cobot-1")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": [], "total": 0}


def test_obtener_menu_con_error_del_repositorio_devuelve_500(client_sin_propagar_errores, repo):
    repo.get_menu.side_effect = RuntimeError("sin conexión")

    assert client_sin_propagar_errores.get("/catalog/get/cobot-1").status_code == 500


# ---------- GET /catalog/all-items ----------

def test_obtener_items_devuelve_los_items_y_el_total(client, repo):
    repo.get_all_items.return_value = [menu_item(7, "Mojito"), menu_item(8, "Daiquiri")]

    respuesta = client.get("/catalog/all-items")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 2
    assert [(i["id_item"], i["nombre_item"]) for i in cuerpo["items"]] == [
        (7, "Mojito"), (8, "Daiquiri"),
    ]
    repo.get_all_items.assert_awaited_once_with()


def test_obtener_items_sin_items_devuelve_total_cero(client, repo):
    repo.get_all_items.return_value = []

    assert client.get("/catalog/all-items").json() == {"items": [], "total": 0}


# ---------- GET /catalog/check-update/{id_cobot} ----------

def test_obtener_ultima_actualizacion_devuelve_la_fecha_como_texto(client, repo):
    repo.get_last_update_date.return_value = "2026-10-22 10:00:00"

    respuesta = client.get("/catalog/check-update/cobot-1")

    assert respuesta.status_code == 200
    assert respuesta.json() == "2026-10-22 10:00:00"
    repo.get_last_update_date.assert_awaited_once_with("cobot-1")


def test_obtener_ultima_actualizacion_con_error_del_repositorio_devuelve_500(
    client_sin_propagar_errores, repo
):
    repo.get_last_update_date.side_effect = IndexError("sin filas")

    assert client_sin_propagar_errores.get("/catalog/check-update/cobot-x").status_code == 500


# ---------- POST /catalog/add-item ----------

NUEVO_ITEM = {
    "nombre_item": "Mojito",
    "ingredientes": "Ron, menta",
    "imagen": "http://img/mojito.png",
    "codigo_modbus": 3,
}


def test_crear_item_devuelve_201_y_el_mensaje(client, repo):
    respuesta = client.post("/catalog/add-item", json=NUEVO_ITEM)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"mensaje": "Item creado correctamente"}


def test_crear_item_pasa_los_datos_al_repositorio(client, repo):
    client.post("/catalog/add-item", json=NUEVO_ITEM)

    repo.add_item.assert_awaited_once_with(
        nombre_item="Mojito",
        imagen="http://img/mojito.png",
        ingredientes="Ron, menta",
        codigo_modbus=3,
    )


def test_crear_item_duplicado_devuelve_409_con_el_motivo(client, repo):
    repo.add_item.side_effect = ItemAlreadyExistsError("Mojito")

    respuesta = client.post("/catalog/add-item", json=NUEVO_ITEM)

    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": 'Item "Mojito" already exists'}


def test_crear_item_con_cobot_inexistente_devuelve_404_con_el_motivo(client, repo):
    repo.add_item.side_effect = CobotNotFoundError("cobot-1")

    respuesta = client.post("/catalog/add-item", json=NUEVO_ITEM)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Cobot cobot-1 doesnt exist"}


def test_crear_item_con_error_inesperado_devuelve_500(client_sin_propagar_errores, repo):
    repo.add_item.side_effect = RuntimeError("falla")

    assert client_sin_propagar_errores.post("/catalog/add-item", json=NUEVO_ITEM).status_code == 500


@pytest.mark.parametrize("campo", sorted(NUEVO_ITEM))
def test_crear_item_sin_un_campo_obligatorio_devuelve_422_y_no_llama_al_repositorio(
    client, repo, campo
):
    cuerpo = {k: v for k, v in NUEVO_ITEM.items() if k != campo}

    respuesta = client.post("/catalog/add-item", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"][0]["loc"] == ["body", campo]
    repo.add_item.assert_not_awaited()


@pytest.mark.parametrize("codigo", ["abc", "0x01", 1.5, None])
def test_crear_item_con_codigo_modbus_invalido_devuelve_422(client, repo, codigo):
    respuesta = client.post("/catalog/add-item", json={**NUEVO_ITEM, "codigo_modbus": codigo})

    assert respuesta.status_code == 422
    repo.add_item.assert_not_awaited()


def test_crear_item_sin_cuerpo_devuelve_422(client, repo):
    assert client.post("/catalog/add-item").status_code == 422
    repo.add_item.assert_not_awaited()


# ---------- POST /catalog/update-item/new ----------

AGREGAR_AL_MENU = {"id_cobot": "cobot-1", "nombre_item": "Mojito", "precio_item": "5.50"}


def test_agregar_item_al_menu_devuelve_201_y_el_mensaje(client, repo):
    respuesta = client.post("/catalog/update-item/new", json=AGREGAR_AL_MENU)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"mensaje": "Item agregado a menu correctamente"}


def test_agregar_item_al_menu_pasa_los_datos_al_repositorio_con_el_precio_decimal(client, repo):
    client.post("/catalog/update-item/new", json=AGREGAR_AL_MENU)

    repo.add_item_to_catalog.assert_awaited_once_with(
        nombre_item="Mojito",
        id_cobot="cobot-1",
        precio_item=Decimal("5.50"),
    )
    precio = repo.add_item_to_catalog.await_args.kwargs["precio_item"]
    assert isinstance(precio, Decimal)


def test_agregar_item_al_menu_acepta_el_precio_como_numero_json(client, repo):
    client.post("/catalog/update-item/new", json={**AGREGAR_AL_MENU, "precio_item": 5.5})

    assert repo.add_item_to_catalog.await_args.kwargs["precio_item"] == Decimal("5.5")


def test_agregar_item_inexistente_devuelve_404_con_el_motivo(client, repo):
    repo.add_item_to_catalog.side_effect = ItemNotFoundError("Mojito")

    respuesta = client.post("/catalog/update-item/new", json=AGREGAR_AL_MENU)

    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "Item Mojito doesn't exist"}


def test_agregar_item_al_menu_con_error_inesperado_devuelve_500(client_sin_propagar_errores, repo):
    repo.add_item_to_catalog.side_effect = RuntimeError("falla")

    respuesta = client_sin_propagar_errores.post("/catalog/update-item/new", json=AGREGAR_AL_MENU)

    assert respuesta.status_code == 500


@pytest.mark.parametrize("campo", sorted(AGREGAR_AL_MENU))
def test_agregar_item_al_menu_sin_un_campo_obligatorio_devuelve_422(client, repo, campo):
    cuerpo = {k: v for k, v in AGREGAR_AL_MENU.items() if k != campo}

    respuesta = client.post("/catalog/update-item/new", json=cuerpo)

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"][0]["loc"] == ["body", campo]
    repo.add_item_to_catalog.assert_not_awaited()


@pytest.mark.parametrize("precio", ["abc", "NaN", None, ""])
def test_agregar_item_al_menu_con_precio_invalido_devuelve_422(client, repo, precio):
    respuesta = client.post("/catalog/update-item/new", json={**AGREGAR_AL_MENU, "precio_item": precio})

    assert respuesta.status_code == 422
    repo.add_item_to_catalog.assert_not_awaited()