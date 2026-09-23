from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_cobot_repository
from app.repositories.catalog_respository import CatalogRepository
from app.schemas.get_catalog_response import CobotCatalogResponse
from app.schemas.create_item_request import CreateItemRequest
from app.models.db_exceptions import CobotNotFoundError, ItemAlreadyExistsError
from app.schemas.catalog_dto import UpdateItemStatus
from app.services.catalog_service import CatalogService
from app.api.dependencies import get_catalog_service

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/{id_cobot}/get", response_model=CobotCatalogResponse)
async def obtener_menu(
    id_cobot: str,
    repo: CatalogRepository = Depends(get_cobot_repository),
):
    items = await repo.get_menu(id_cobot)
    return CobotCatalogResponse(items=items, total=len(items))


@router.post("/add-item", status_code=status.HTTP_201_CREATED)
async def crear_item(
    payload: CreateItemRequest,
    repo: CatalogRepository = Depends(get_cobot_repository),
):
    try:
        await repo.add_item(
            nombre_item=payload.nombre_item,
            precio_item=payload.precio_item,
            estado=payload.estado,
            ingredientes=payload.ingredientes,
            codigo_modbus=payload.codigo_modbus,
            id_cobot=payload.id_cobot,
        )
    except CobotNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ItemAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"mensaje": "Item creado correctamente"}


@router.patch("/update-state", status_code=status.HTTP_200_OK)
async def update_item_estado(
    payload: UpdateItemStatus, service: CatalogService = Depends(get_catalog_service)
):
    try:
        await service.update_item_state(payload)
        return {
            "status": "success",
            "message": f"Estado del ítem '{payload.item_name}' actualizado correctamente.",
        }
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
