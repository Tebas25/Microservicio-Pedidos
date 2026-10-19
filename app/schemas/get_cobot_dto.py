from pydantic import BaseModel


class CobotDto(BaseModel):
    id_cobot: str
    nombre_cobot: str


class CobotListDto(BaseModel):
    items: list[CobotDto]
