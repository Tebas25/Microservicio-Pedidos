from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import router
from app.api.dependencies import get_cobot_repository
from app.models.db_exceptions import CobotNotFoundError, ItemAlreadyExistsError

PAYLOAD_VALIDO = {
    "nombre_item": "Mojito Clásico",
    "ingredientes": "Ron, limón, menta, azúcar",
    "imagen": "imagenGenerica",
    "codigo_modbus": 1,
}


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def client(mock_repo):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cobot_repository] = lambda: mock_repo
    return TestClient(app)


def test_crear_item_exitoso_responde_201(client, mock_repo):
    mock_repo.add_item.return_value = None

    response = client.post("/catalog/add-item", json=PAYLOAD_VALIDO)

    assert response.status_code == 201
    assert response.json() == {"mensaje": "Item creado correctamente"}


def test_crear_item_llama_al_repositorio_con_los_datos_correctos(client, mock_repo):
    mock_repo.add_item.return_value = None

    client.post("/catalog/add-item", json=PAYLOAD_VALIDO)

    mock_repo.add_item.assert_awaited_once_with(
        nombre_item="Mojito Clásico",
        ingredientes="Ron, limón, menta, azúcar",
        imagen="imagenGenerica",
        codigo_modbus=1,
    )


def test_crear_item_responde_404_si_cobot_no_existe(client, mock_repo):
    mock_repo.add_item.side_effect = CobotNotFoundError("CBT999")

    payload = {**PAYLOAD_VALIDO, "id_cobot": "CBT999"}
    response = client.post("/catalog/add-item", json=payload)

    assert response.status_code == 404
    assert "CBT999" in response.json()["detail"]


def test_crear_item_responde_409_si_item_ya_existe(client, mock_repo):
    mock_repo.add_item.side_effect = ItemAlreadyExistsError(
        f"El ítem 'Mojito' ya existe en CBT001"
    )

    response = client.post("/catalog/add-item", json=PAYLOAD_VALIDO)

    assert response.status_code == 409
    assert "Mojito" in response.json()["detail"]


def test_crear_item_responde_422_si_falta_campo_obligatorio(client, mock_repo):
    payload_incompleto = {**PAYLOAD_VALIDO}
    del payload_incompleto["nombre_item"]

    response = client.post("/catalog/add-item", json=payload_incompleto)

    assert response.status_code == 422
    mock_repo.add_item.assert_not_awaited()


def test_crear_item_responde_500_si_error_no_manejado(client, mock_repo):
    mock_repo.add_item.side_effect = RuntimeError("error inesperado")

    with pytest.raises(RuntimeError):
        client.post("/catalog/add-item", json=PAYLOAD_VALIDO)
