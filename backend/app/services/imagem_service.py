import uuid
import asyncio
import json
from io import BytesIO
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from minio import Minio
from PIL import Image as PILImage, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ImagemEspecime
from app.config.config import settings


class ImagemService:
    _bucket_ready = False

    FORMAT_MIME = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "TIFF": "image/tiff",
        "WEBP": "image/webp",
    }

    @staticmethod
    def _client() -> Minio:
        return Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=settings.MINIO_SECURE,
        )

    @staticmethod
    def _public_url(object_name: str) -> str:
        return f"{settings.MINIO_PUBLIC_ENDPOINT.rstrip('/')}/{object_name}"

    @staticmethod
    def _ensure_bucket_sync(client: Minio) -> None:
        bucket = settings.MINIO_BUCKET
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
        client.set_bucket_policy(bucket, json.dumps(policy))

    @classmethod
    async def _ensure_bucket(cls, client: Minio) -> None:
        if cls._bucket_ready:
            return
        await asyncio.to_thread(cls._ensure_bucket_sync, client)
        cls._bucket_ready = True

    @classmethod
    async def _put_object(
        cls,
        object_name: str,
        data: bytes,
        content_type: str,
    ) -> None:
        client = cls._client()
        await cls._ensure_bucket(client)
        await asyncio.to_thread(
            client.put_object,
            settings.MINIO_BUCKET,
            object_name,
            BytesIO(data),
            len(data),
            content_type=content_type,
        )

    @classmethod
    async def _remove_object(cls, object_name: str) -> None:
        client = cls._client()
        await cls._ensure_bucket(client)
        await asyncio.to_thread(client.remove_object, settings.MINIO_BUCKET, object_name)

    FORMAT_EXT = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "TIFF": ".tiff",
        "WEBP": ".webp",
    }

    @staticmethod
    async def upload(
        db: AsyncSession,
        especime_id: int,
        arquivo: UploadFile,
        descricao: Optional[str] = None,
        is_principal: bool = False,
    ) -> ImagemEspecime:
        # Ler conteúdo e validar tamanho
        conteudo = await arquivo.read()
        if len(conteudo) > settings.max_image_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Máximo: {settings.MAX_IMAGE_SIZE_MB}MB",
            )
        if not conteudo:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Arquivo vazio")

        PILImage.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
        try:
            with PILImage.open(BytesIO(conteudo)) as img:
                img.verify()
            with PILImage.open(BytesIO(conteudo)) as img:
                formato = img.format
                largura, altura = img.size
                if formato not in ImagemService.FORMAT_MIME:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail="Formato de imagem não suportado",
                    )
                tipo_mime = ImagemService.FORMAT_MIME[formato]
                if tipo_mime not in settings.allowed_image_types_list:
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Tipo de imagem não permitido: {tipo_mime}",
                    )
                sanitized = BytesIO()
                clean_img = img.copy()
                if formato == "JPEG" and clean_img.mode not in ("RGB", "L"):
                    clean_img = clean_img.convert("RGB")
                clean_img.save(sanitized, format=formato)
                conteudo_sanitizado = sanitized.getvalue()
        except HTTPException:
            raise
        except (UnidentifiedImageError, OSError, ValueError, DecompressionBombError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo enviado não é uma imagem válida",
            ) from exc

        if len(conteudo_sanitizado) > settings.max_image_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande após processamento. Máximo: {settings.MAX_IMAGE_SIZE_MB}MB",
            )

        # Gerar nome único
        ext = ImagemService.FORMAT_EXT[formato]
        nome_arquivo = f"{uuid.uuid4().hex}{ext}"
        object_name = f"images/{especime_id}/{nome_arquivo}"

        try:
            await ImagemService._put_object(object_name, conteudo_sanitizado, tipo_mime)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Não foi possível salvar a imagem no bucket",
            ) from exc

        url_relativa = ImagemService._public_url(object_name)

        # Se for principal, desmarcar as anteriores
        if is_principal:
            result = await db.execute(
                select(ImagemEspecime).where(
                    ImagemEspecime.especime_id == especime_id,
                    ImagemEspecime.is_principal == True,
                )
            )
            for img in result.scalars().all():
                img.is_principal = False

        imagem = ImagemEspecime(
            especime_id=especime_id,
            nome_arquivo=(arquivo.filename or nome_arquivo).split("/")[-1].split("\\")[-1],
            caminho=object_name,
            url_relativa=url_relativa,
            tipo_mime=tipo_mime,
            tamanho_bytes=len(conteudo_sanitizado),
            largura_px=largura,
            altura_px=altura,
            descricao=descricao,
            is_principal=is_principal,
        )
        db.add(imagem)
        await db.flush()
        await db.refresh(imagem)
        return imagem

    @staticmethod
    async def listar_por_especime(db: AsyncSession, especime_id: int) -> List[ImagemEspecime]:
        result = await db.execute(
            select(ImagemEspecime)
            .where(ImagemEspecime.especime_id == especime_id)
            .order_by(ImagemEspecime.is_principal.desc(), ImagemEspecime.criado_em)
        )
        return list(result.scalars().all())

    @staticmethod
    async def deletar(db: AsyncSession, imagem_id: int, especime_id: int) -> bool:
        result = await db.execute(
            select(ImagemEspecime).where(
                ImagemEspecime.id == imagem_id,
                ImagemEspecime.especime_id == especime_id,
            )
        )
        imagem = result.scalar_one_or_none()
        if not imagem:
            return False
        try:
            await ImagemService._remove_object(imagem.caminho)
        except Exception:
            pass
        await db.delete(imagem)
        await db.flush()
        return True
