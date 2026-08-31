from fastapi import APIRouter, Depends

from app.dependencies import get_cobot_repository
from app.repositories.catalog_respository import CatalogRepository
from app.schemas.get_catalog_response import CobotCatalogResponse

catalog_router = APIRouter(prefix="/catalog", tags=["catalog"])


@catalog_router.get("/{id_cobot}/get", response_model=CobotCatalogResponse)
async def obtener_menu(
    id_cobot: str,
    repo: CatalogRepository = Depends(get_cobot_repository),
):
    items = await repo.get_menu(id_cobot)
    return CobotCatalogResponse(items=items, total=len(items))
