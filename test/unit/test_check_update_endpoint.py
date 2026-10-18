from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_cobot_repository
from app.api.endpoints import router


@pytest.fixture
def repo_mock():
    return AsyncMock()


@pytest.fixture
def client(repo_mock):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cobot_repository] = lambda: repo_mock
    return TestClient(app)


def test_check_update_retorna_200_y_fecha(client, repo_mock):
    repo_mock.get_last_update_date.return_value = "2026-10-17 12:30:00"

    response = client.get("/catalog/check-update/cobot-1")

    assert response.status_code == 200
    assert response.json() == "2026-10-17 12:30:00"


def test_check_update_llama_al_repo_con_el_id_cobot(client, repo_mock):
    repo_mock.get_last_update_date.return_value = "2026-10-17"

    client.get("/catalog/check-update/cobot-99")

    repo_mock.get_last_update_date.assert_awaited_once_with("cobot-99")


def test_check_update_propaga_error_del_repositorio(repo_mock):
    repo_mock.get_last_update_date.side_effect = IndexError("sin filas")
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_cobot_repository] = lambda: repo_mock
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/catalog/check-update/cobot-inexistente")

    assert response.status_code == 500