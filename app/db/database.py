from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.db_config import db_settings


def get_connect_args(ssl_mode: str) -> dict:
    return {"ssl": "require"} if ssl_mode == "require" else {}


connect_args = get_connect_args(db_settings.db_ssl_mode)

engine = create_async_engine(
    db_settings.database_url,
    echo=True,  # pon False en producción
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
