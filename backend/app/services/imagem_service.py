import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException, status
from PIL import Image as PILImage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ImagemEspecime
from app.core.config import settings


class ImagemService:

    @staticmethod
    async def upload(
        db: AsyncSession,
        especime_id: int,
        arquivo: UploadFile,
        descricao: Optional[str] = None,
        is_principal: bool = False,
    ) -> ImagemEspecime:
        # Validar tipo MIME
        if arquivo.content_type not in settings.allowed_image_types_list:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Tipo de arquivo não suportado: {arquivo.content_type}. "
                       f"Permitidos: {', '.join(settings.allowed_image_types_list)}",
            )

        # Ler conteúdo e validar tamanho
        conteudo = await arquivo.read()
        if len(conteudo) > settings.max_image_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Arquivo muito grande. Máximo: {settings.MAX_IMAGE_SIZE_MB}MB",
            )

        # Gerar nome único
        ext = Path(arquivo.filename).suffix or ".jpg"
        nome_arquivo = f"{uuid.uuid4().hex}{ext}"
        pasta_especime = Path(settings.UPLOAD_DIR) / str(especime_id)
        pasta_especime.mkdir(parents=True, exist_ok=True)
        caminho_completo = pasta_especime / nome_arquivo

        # Salvar arquivo
        async with aiofiles.open(caminho_completo, "wb") as f:
            await f.write(conteudo)

        # Obter dimensões
        largura, altura = None, None
        try:
            img = PILImage.open(caminho_completo)
            largura, altura = img.size
        except Exception:
            pass

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
            nome_arquivo=arquivo.filename,
            caminho=str(caminho_completo),
            url_relativa=url_relativa,
            tipo_mime=arquivo.content_type,
            tamanho_bytes=len(conteudo),
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
