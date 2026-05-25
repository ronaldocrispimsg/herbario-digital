import os
import uuid
import aiofiles
from io import BytesIO
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from PIL import Image as PILImage, UnidentifiedImageError
from PIL.Image import DecompressionBombError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ImagemEspecime
from app.core.config import settings


class ImagemService:
    FORMAT_MIME = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "TIFF": "image/tiff",
        "WEBP": "image/webp",
    }
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
        pasta_especime = Path(settings.UPLOAD_DIR) / str(especime_id)
        pasta_especime.mkdir(parents=True, exist_ok=True)
        caminho_completo = pasta_especime / nome_arquivo

        # Salvar arquivo
        async with aiofiles.open(caminho_completo, "wb") as f:
            await f.write(conteudo_sanitizado)

        url_relativa = f"/uploads/{especime_id}/{nome_arquivo}"

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
            nome_arquivo=Path(arquivo.filename or nome_arquivo).name,
            caminho=str(caminho_completo),
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
        # Remover arquivo físico
        try:
            if os.path.exists(imagem.caminho):
                os.remove(imagem.caminho)
        except Exception:
            pass
        await db.delete(imagem)
        await db.flush()
        return True
