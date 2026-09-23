from decimal import Decimal

from app.models.cobot_menu_item import CobotMenuItem
from app.schemas.get_catalog_response import CobotCatalogResponse


def test_response_con_items_y_total_correctos():
    items = [
        CobotMenuItem(
            nombre_item="Pizza",
            precio_item=Decimal("10.0"),
            estado=True,
            ingredientes="queso",
            codigo_modbus="M001",
        )
    ]
    response = CobotCatalogResponse(items=items, total=len(items))

    assert response.total == 1
    assert response.items[0].nombre_item == "Pizza"


def test_response_con_lista_vacia():
    response = CobotCatalogResponse(items=[], total=0)
    assert response.items == []
    assert response.total == 0