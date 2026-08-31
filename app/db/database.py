from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.db_config import db_settings

connect_args = {}
if db_settings.db_ssl_mode == "require":
    connect_args = {"ssl": "require"}

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
