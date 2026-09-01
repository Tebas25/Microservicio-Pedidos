from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_cobot_repository
from app.repositories.catalog_respository import CatalogRepository
from app.schemas.create_item_request import CreateItemRequest
from app.models.db_exceptions import CobotNotFoundError, ItemAlreadyExistsError

router = APIRouter(prefix="/catalog", tags=["catalog"])


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
