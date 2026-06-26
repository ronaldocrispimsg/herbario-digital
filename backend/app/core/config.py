from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Banco de dados
    DATABASE_URL: str = "postgresql+asyncpg://bioacervo:bioacervo_dev_password@database:5432/bioacervo"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://bioacervo:bioacervo_dev_password@database:5432/bioacervo"

    # Segurança
    SECRET_KEY: str = "sua-chave-secreta-muito-segura-troque-em-producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ENVIRONMENT: str = "development"

    # Upload
    UPLOAD_DIR: str = "uploads/images"
    MAX_IMAGE_SIZE_MB: int = 20
    MAX_IMAGE_PIXELS: int = 50_000_000
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/tiff,image/webp"

    # Exportação
    EXPORT_DIR: str = "uploads/exports"

    # Servidor
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost,http://localhost:8080,http://127.0.0.1:8080"

    # Seed/desenvolvimento
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None
    CREATE_TABLES_ON_SEED: bool = False

    @property
    def allowed_image_types_list(self) -> List[str]:
        return [item.strip() for item in self.ALLOWED_IMAGE_TYPES.split(",") if item.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    @property
    def max_image_size_bytes(self) -> int:
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Garantir que os diretórios existam
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
