import pytest
from pydantic import ValidationError
from app.core.db_config import DbSettings


def test_settings_carga_valores_correctamente(monkeypatch):
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_pass")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_NAME", "test_db")

    settings = DbSettings(_env_file=None)  # ignora el .env real, usa solo env vars

    assert settings.db_user == "test_user"
    assert settings.db_password == "test_pass"
    assert settings.db_host == "localhost"
    assert settings.db_name == "test_db"


def test_settings_usa_valores_por_defecto(monkeypatch):
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.setenv("DB_HOST", "h")
    monkeypatch.setenv("DB_NAME", "n")

    settings = DbSettings(_env_file=None)

    assert settings.db_port == 5432
    assert settings.db_ssl_mode == "disable"


def test_settings_falla_si_falta_variable_obligatoria(monkeypatch):
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.setenv("DB_HOST", "h")
    monkeypatch.setenv("DB_NAME", "n")

    with pytest.raises(ValidationError):
        DbSettings(_env_file=None)


def test_database_url_se_construye_correctamente(monkeypatch):
    monkeypatch.setenv("DB_USER", "user1")
    monkeypatch.setenv("DB_PASSWORD", "pass1")
    monkeypatch.setenv("DB_HOST", "myhost")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "mydb")

    settings = DbSettings(_env_file=None)

    assert settings.database_url == (
        "postgresql+asyncpg://user1:pass1@myhost:5433/mydb"
    )


def test_db_port_invalido_lanza_error(monkeypatch):
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.setenv("DB_HOST", "h")
    monkeypatch.setenv("DB_NAME", "n")
    monkeypatch.setenv("DB_PORT", "no-es-numero")

    with pytest.raises(ValidationError):
        DbSettings(_env_file=None)