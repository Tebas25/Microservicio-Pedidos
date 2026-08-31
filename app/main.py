from fastapi import FastAPI
from app.api.get_catalog import catalog_router

app = FastAPI(
    title="APP Bartender Robótico - Microservicio de catálogo",
    description="Microservicio encargado de la gestión de catálogo",
    version="1.0.0",
)
app.include_router(catalog_router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Estructura base configurada y en línea."}
