from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Banco de dados
    DATABASE_URL: str = "postgresql+asyncpg://usuario:senha@localhost:5432/bioacervo"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://usuario:senha@localhost:5432/bioacervo"

    # Segurança
    SECRET_KEY: str = "sua-chave-secreta-muito-segura-troque-em-producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Upload
    UPLOAD_DIR: str = "uploads/images"
    MAX_IMAGE_SIZE_MB: int = 20
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/tiff,image/webp"

    # Exportação
    EXPORT_DIR: str = "uploads/exports"

    # Servidor
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    @property
    def allowed_image_types_list(self) -> List[str]:
        return self.ALLOWED_IMAGE_TYPES.split(",")

    @property
    def max_image_size_bytes(self) -> int:
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Garantir que os diretórios existam
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.EXPORT_DIR, exist_ok=True)
