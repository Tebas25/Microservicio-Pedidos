# tests/test_database.py
import pytest
from unittest.mock import AsyncMock, patch

from app.db.database import get_db, get_connect_args


@pytest.mark.asyncio
async def test_get_db_entrega_y_cierra_sesion():
    mock_session = AsyncMock()

    with patch("app.db.database.AsyncSessionLocal") as mock_sessionmaker:
        mock_sessionmaker.return_value.__aenter__.return_value = mock_session
        mock_sessionmaker.return_value.__aexit__.return_value = None

        gen = get_db()
        session = await gen.__anext__()

        assert session is mock_session

        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()


def test_connect_args_con_ssl_require():
    assert get_connect_args("require") == {"ssl": "require"}


def test_connect_args_sin_ssl():
    assert get_connect_args("disable") == {}