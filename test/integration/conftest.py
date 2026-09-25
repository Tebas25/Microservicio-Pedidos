import os
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
    f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS "cobots" (
    "id_cobot" varchar(32) NOT NULL,
    "nombre_cobot" varchar(64) NOT NULL,
    PRIMARY KEY ("id_cobot")
);

CREATE SEQUENCE IF NOT EXISTS item_menu_id_item_seq;

CREATE TABLE IF NOT EXISTS "item_menu" (
    "id_item" int4 NOT NULL DEFAULT nextval('item_menu_id_item_seq'::regclass),
    "nombre_item" varchar(64) NOT NULL,
    "precio_item" numeric(10,2) NOT NULL,
    "estado" bool NOT NULL DEFAULT false,
    "ingredientes" varchar NOT NULL,
    "codigo_modbus" varchar NOT NULL,
    "id_cobot" varchar(32) NOT NULL DEFAULT 'CBT000T',
    PRIMARY KEY ("id_item")
);
"""

# SP real, confirmado en producción (corrige ambigüedad, sin validación de existencia)
UPDATE_SP_SQL = """
CREATE OR REPLACE PROCEDURE update_menu_item_state(
	p_item_state BOOLEAN,
	p_item_name character varying,
	p_id_cobot character varying
)
LANGUAGE plpgsql
AS $$
BEGIN
	UPDATE item_menu
	SET estado = p_item_state
	FROM cobots
	WHERE p_id_cobot = item_menu.id_cobot AND item_menu.nombre_item = p_item_name;
END;
$$;
"""

# SP real, confirmado en producción (corrige ambigüedad, sin validación de existencia)
UPDATE_PRICE_SP_SQL = """
CREATE OR REPLACE PROCEDURE update_menu_item_price(
	p_precio_item numeric,
	p_item_name character varying,
	p_id_cobot character varying
)
LANGUAGE plpgsql
AS $$
BEGIN
	UPDATE item_menu
	SET precio_item = p_precio_item
	WHERE item_menu.id_cobot = p_id_cobot AND item_menu.nombre_item = p_item_name;
END;
$$;
"""


@pytest_asyncio.fixture
async def engine():
    """Un motor nuevo por test, evita conflictos de event loop entre tests."""
    eng = create_async_engine(DATABASE_URL, echo=False)

    async with eng.begin() as conn:
        for statement in SCHEMA_SQL.strip().split(";"):
            if statement.strip():
                await conn.exec_driver_sql(statement)
        await conn.exec_driver_sql(UPDATE_SP_SQL)
        await conn.exec_driver_sql(UPDATE_PRICE_SP_SQL)

    yield eng

    async with eng.begin() as conn:
        await conn.exec_driver_sql("DROP TABLE IF EXISTS item_menu")
        await conn.exec_driver_sql("DROP TABLE IF EXISTS cobots")

    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def seed_data(engine):
    async with engine.begin() as conn:
        await conn.exec_driver_sql("""
            INSERT INTO cobots (id_cobot, nombre_cobot)
            VALUES ('CBT001', 'Cobot Pruebas'), ('CBT002', 'Cobot Pruebas 2')
            ON CONFLICT DO NOTHING
            """)
        await conn.exec_driver_sql("""
            INSERT INTO item_menu (nombre_item, precio_item, estado, ingredientes, codigo_modbus, id_cobot)
            VALUES ('Mojito', 5.50, false, 'ron, menta', 'M010', 'CBT001')
            ON CONFLICT DO NOTHING
            """)
    yield
