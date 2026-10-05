# ---- Etapa de build ----
FROM python:3.12-slim AS builder

# Instala uv copiando el binario oficial (rápido, sin pip)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Variables recomendadas para uv en contenedores
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

# Cachea dependencias antes de copiar el código (mejor uso de cache de capas)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copia el resto del código y sincroniza (instala el propio paquete si aplica)
COPY . .
RUN uv sync --frozen --no-dev

# ---- Etapa final (imagen ligera) ----
FROM python:3.12-slim

WORKDIR /app

# Crea usuario no root
RUN useradd -m appuser
COPY --from=builder --chown=appuser:appuser /app /app

USER appuser

# Añade el venv de uv al PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8102

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8102"]