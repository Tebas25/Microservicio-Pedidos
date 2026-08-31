from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.repositories.catalog_respository import CatalogRepository


def get_cobot_repository(db: AsyncSession = Depends(get_db)) -> CatalogRepository:
    return CatalogRepository(db)
