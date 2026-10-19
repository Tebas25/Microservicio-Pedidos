from collections.abc import Iterator

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_cobot_repository
from app.api.endpoints import router


class FakeRepo:
    """Repositorio falso: el endpoint se prueba sin tocar PostgreSQL."""

    def __init__(self, cobots: list[dict]):
        self._cobots = cobots

    async def get_cobot(self) -> list[dict]:
        return self._cobots


@pytest.fixture
def app() -> Iterator[FastAPI]:
    app = FastAPI()
    app.include_router(router)
    yield app
    app.dependency_overrides.clear()


async def call_endpoint(app: FastAPI, cobots: list[dict]) -> httpx.Response:
    app.dependency_overrides[get_cobot_repository] = lambda: FakeRepo(cobots)
    # url_path_for evita depender del prefijo con el que se monte el router
    url = app.url_path_for("obtener_cobots")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        return await client.get(url)


@pytest.mark.asyncio
async def test_get_cobots_returns_items_with_id_and_name(app: FastAPI):
    response = await call_endpoint(
        app, [{"id_cobot": "CBT000T", "nombre_cobot": "Cobot JAKA"}]
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [{"id_cobot": "CBT000T", "nombre_cobot": "Cobot JAKA"}]
    }


@pytest.mark.asyncio
async def test_get_cobots_returns_empty_items_when_there_are_none(app: FastAPI):
    response = await call_endpoint(app, [])

    assert response.status_code == 200
    assert response.json() == {"items": []}
