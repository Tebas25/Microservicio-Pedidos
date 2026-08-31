from unittest.mock import AsyncMock

from app.dependencies import get_cobot_repository
from app.repositories.catalog_respository import CatalogRepository


def test_get_cobot_repository_retorna_catalog_repository():
    mock_db = AsyncMock()
    repo = get_cobot_repository(mock_db)

    assert isinstance(repo, CatalogRepository)
    assert repo.db is mock_db