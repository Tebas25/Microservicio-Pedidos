import os
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.getenv('DB_USER', 'test_user')}:{os.getenv('DB_PASSWORD', 'test_password')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'test_db')}"
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS public.cobots (
    id_cobot VARCHAR(32) PRIMARY KEY,
    nombre_cobot VARCHAR(64) NOT NULL,
    ultima_actualizacion_catalogo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.catalog_item (
    id_item INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_item VARCHAR(50) NOT NULL UNIQUE,
    ingredientes VARCHAR(200) NOT NULL,
    imagen VARCHAR NOT NULL,
    codigo_modbus INT NOT NULL UNIQUE CHECK (codigo_modbus > 0)
);

CREATE TABLE IF NOT EXISTS public.cobot_catalog (
    id_cobot_catalog INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_item INT NOT NULL REFERENCES public.catalog_item(id_item),
    id_cobot VARCHAR(32) NOT NULL REFERENCES public.cobots(id_cobot),
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    precio_item NUMERIC NOT NULL CHECK (precio_item > 0),
    UNIQUE (id_cobot, id_item)
);
"""

UPDATE_SP_SQL = """
CREATE OR REPLACE PROCEDURE public.update_menu_item_state(
    p_item_state BOOLEAN,
    p_item_name VARCHAR,
    p_id_cobot VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_item INT;
BEGIN
    SELECT ci.id_item
    INTO v_id_item
    FROM public.catalog_item ci
    WHERE ci.nombre_item = p_item_name;

    IF v_id_item IS NULL THEN
        RAISE EXCEPTION
            'El ítem "%" no existe en el catálogo maestro',
            p_item_name;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM public.cobot_catalog cc
        WHERE cc.id_item = v_id_item
          AND cc.id_cobot = p_id_cobot
    ) THEN
        RAISE EXCEPTION
            'El ítem "%" no está asignado al cobot %',
            p_item_name, p_id_cobot;
    END IF;

    UPDATE public.cobot_catalog
    SET estado = p_item_state
    WHERE id_item = v_id_item
      AND id_cobot = p_id_cobot;

    UPDATE public.cobots
    SET ultima_actualizacion_catalogo = CURRENT_TIMESTAMP
    WHERE id_cobot = p_id_cobot;
END;
$$;
"""

UPDATE_PRICE_SP_SQL = """
CREATE OR REPLACE PROCEDURE public.update_menu_item_price(
    p_precio_item NUMERIC(10,2),
    p_item_name VARCHAR,
    p_id_cobot VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_item INT;
BEGIN
    SELECT ci.id_item
    INTO v_id_item
    FROM public.catalog_item ci
    WHERE ci.nombre_item = p_item_name;

    IF v_id_item IS NULL THEN
        RAISE EXCEPTION
            'El ítem "%" no existe en el catálogo maestro',
            p_item_name;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM public.cobot_catalog cc
        WHERE cc.id_item = v_id_item
          AND cc.id_cobot = p_id_cobot
    ) THEN
        RAISE EXCEPTION
            'El ítem "%" no está asignado al cobot %',
            p_item_name, p_id_cobot;
    END IF;

    UPDATE public.cobot_catalog
    SET precio_item = p_precio_item
    WHERE id_item = v_id_item
      AND id_cobot = p_id_cobot;

    UPDATE public.cobots
    SET ultima_actualizacion_catalogo = CURRENT_TIMESTAMP
    WHERE id_cobot = p_id_cobot;
END;
$$;
"""


@pytest_asyncio.fixture
async def engine():
    """Crea una base de pruebas con el esquema real."""
    eng = create_async_engine(DATABASE_URL, echo=False)

    async with eng.begin() as conn:
        for statement in SCHEMA_SQL.strip().split(";"):
            if statement.strip():
                await conn.exec_driver_sql(statement)

        await conn.exec_driver_sql(UPDATE_SP_SQL)
        await conn.exec_driver_sql(UPDATE_PRICE_SP_SQL)

    yield eng

    async with eng.begin() as conn:
        await conn.exec_driver_sql(
            "DROP PROCEDURE IF EXISTS public.update_menu_item_state"
            "(boolean, character varying, character varying)"
        )
        await conn.exec_driver_sql(
            "DROP PROCEDURE IF EXISTS public.update_menu_item_price"
            "(numeric, character varying, character varying)"
        )
        await conn.exec_driver_sql("DROP TABLE IF EXISTS public.cobot_catalog")
        await conn.exec_driver_sql("DROP TABLE IF EXISTS public.catalog_item")
        await conn.exec_driver_sql("DROP TABLE IF EXISTS public.cobots")

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
            INSERT INTO public.cobots (
                id_cobot,
                nombre_cobot
            )
            VALUES
                ('CBT001', 'Cobot Pruebas'),
                ('CBT002', 'Cobot Pruebas 2')
            ON CONFLICT (id_cobot) DO NOTHING
        """)

        await conn.exec_driver_sql("""
            INSERT INTO public.catalog_item (
                nombre_item,
                ingredientes,
                imagen,
                codigo_modbus
            )
            VALUES (
                'Mojito',
                'ron, menta',
                'mojito.png',
                1001
            )
            ON CONFLICT (nombre_item) DO NOTHING
        """)

        await conn.exec_driver_sql("""
            INSERT INTO public.cobot_catalog (
                id_item,
                id_cobot,
                estado,
                precio_item
            )
            SELECT
                ci.id_item,
                'CBT001',
                FALSE,
                5.50
            FROM public.catalog_item ci
            WHERE ci.nombre_item = 'Mojito'
            ON CONFLICT (id_cobot, id_item) DO NOTHING
        """)

    yield
