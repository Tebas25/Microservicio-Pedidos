from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_cobot_repository
from app.repositories.catalog_respository import CatalogRepository
from app.schemas.add_item_to_catalog_request import AddItemToCtlgRequest
from app.schemas.get_catalog_response import CobotCatalogResponse
from app.schemas.create_item_request import CreateItemRequest
from app.models.db_exceptions import (
    CobotNotFoundError,
    ItemAlreadyExistsError,
    ItemNotFoundError,
)
from app.schemas.catalog_dto import UpdateItemStatus
from app.schemas.get_cobot_dto import CobotListDto
from app.schemas.get_items_response import GetItemsResponse
from app.services.catalog_service import CatalogService
from app.schemas.update_item_price_dto import UpdateItemPriceDTO
from app.api.dependencies import get_catalog_service

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/cobots", response_model=CobotListDto)
async def obtener_cobots(repo: CatalogRepository = Depends(get_cobot_repository)):
    items = await repo.get_cobot()
    return CobotListDto(items=items)


@router.get("/get/{id_cobot}", response_model=CobotCatalogResponse)
async def obtener_menu(
    id_cobot: str,
    repo: CatalogRepository = Depends(get_cobot_repository),
):
    items = await repo.get_menu(id_cobot)
    return CobotCatalogResponse(items=items, total=len(items))


@router.get("/all-items", response_model=GetItemsResponse)
async def obtener_items(repo: CatalogRepository = Depends(get_cobot_repository)):
    items = await repo.get_all_items()
    return GetItemsResponse(items=items, total=len(items))


@router.get("/check-update/{id_cobot}", response_model=str)
async def obtener_ultima_actualizacion(
    id_cobot: str,
    repo: CatalogRepository = Depends(get_cobot_repository),
):
    date = await repo.get_last_update_date(id_cobot)
    return date


@router.post("/add-item", status_code=status.HTTP_201_CREATED)
async def crear_item(
    payload: CreateItemRequest,
    repo: CatalogRepository = Depends(get_cobot_repository),
):
    try:
        await repo.add_item(
            nombre_item=payload.nombre_item,
            imagen=payload.imagen,
            ingredientes=payload.ingredientes,
            codigo_modbus=payload.codigo_modbus,
        )
    except CobotNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ItemAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"mensaje": "Item creado correctamente"}


@router.post("/update-item/new", status_code=status.HTTP_201_CREATED)
async def add_item_to_catalog(
    payload: AddItemToCtlgRequest,
    repo: CatalogRepository = Depends(get_cobot_repository),
):
    try:
        await repo.add_item_to_catalog(
            nombre_item=payload.nombre_item,
            id_cobot=payload.id_cobot,
            precio_item=payload.precio_item,
        )
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"mensaje": "Item agregado a menu correctamente"}


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


@router.patch("/update-price", status_code=status.HTTP_200_OK)
async def update_item_price(
    payload: UpdateItemPriceDTO, service: CatalogService = Depends(get_catalog_service)
):
    try:
        await service.update_item_price(payload)
        return {
            "success": "success",
            "message": f"Precio del ítem '{payload.item_name}' actualizado correctamente.",
        }
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
