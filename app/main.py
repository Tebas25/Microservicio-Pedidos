from fastapi import FastAPI
from app.api.get_catalog import router as get_catalog_router
from app.api.add_catalog_item import router as add_catalog_item_router

app = FastAPI(
    title="APP Bartender Robótico - Microservicio de catálogo",
    description="Microservicio encargado de la gestión de catálogo",
    version="1.0.0",
)
app.include_router(get_catalog_router)
app.include_router(add_catalog_item_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Estructura base configurada y en línea."}
