from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str
    db_port: int = 5432
    db_name: str
    db_ssl_mode: str = "disable"  # "require" para Neon

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


db_settings = DbSettings()
