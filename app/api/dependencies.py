from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.catalog_respository import CatalogRepository
from app.services.catalog_service import CatalogService


def get_cobot_repository(db: AsyncSession = Depends(get_db)) -> CatalogRepository:
    return CatalogRepository(db)


def get_catalog_service(db: AsyncSession = Depends(get_db)) -> CatalogService:
    repo = CatalogRepository(db)
    return CatalogService(repo)
