import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from app.db.session import get_db
from app.schemas.schemas import (
    EspecimeCreate, EspecimeUpdate, EspecimeOut,
    BuscaEspecime, PaginatedResponse, ImagemOut,
)
from app.services.especime_service import EspecimeService
from app.services.imagem_service import ImagemService
from app.services.export_service import ExportService, EtiquetaService
from app.core.security import get_current_user, require_roles

router = APIRouter(prefix="/especimes", tags=["Espécimes"])


# ─── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedResponse, summary="Listar espécimes")
async def listar(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    skip = (page - 1) * per_page
    total, items = await EspecimeService.listar_todos(db, skip=skip, limit=per_page)
    return PaginatedResponse(
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[EspecimeOut.model_validate(i) for i in items],
    )


@router.post("/buscar", response_model=PaginatedResponse, summary="Buscar por múltiplos critérios")
async def buscar(
    filtros: BuscaEspecime,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    total, items = await EspecimeService.buscar(db, filtros)
    return PaginatedResponse(
        total=total,
        page=filtros.page,
        per_page=filtros.per_page,
        pages=math.ceil(total / filtros.per_page) if total else 0,
        items=[EspecimeOut.model_validate(i) for i in items],
    )


@router.get("/{especime_id}", response_model=EspecimeOut, summary="Detalhe de um espécime")
async def detalhe(
    especime_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    especime = await EspecimeService.get_by_id(db, especime_id)
    if not especime:
        raise HTTPException(status_code=404, detail="Espécime não encontrado")
    return especime


@router.post("", response_model=EspecimeOut, status_code=201, summary="Cadastrar espécime")
async def criar(
    data: EspecimeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles("administrador", "curador")),
):
    # Verificar se código de catálogo já existe
    existente = await EspecimeService.get_by_codigo(db, data.codigo_catalogo)
    if existente:
        raise HTTPException(status_code=400, detail="Código de catálogo já cadastrado")
    return await EspecimeService.create(db, data, current_user.id)


@router.put("/{especime_id}", response_model=EspecimeOut, summary="Atualizar espécime")
async def atualizar(
    especime_id: int,
    data: EspecimeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    especime = await EspecimeService.get_by_id(db, especime_id)
    if not especime:
        raise HTTPException(status_code=404, detail="Espécime não encontrado")
    return await EspecimeService.update(db, especime, data)


@router.delete("/{especime_id}", status_code=204, summary="Remover espécime")
async def remover(
    especime_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador")),
):
    especime = await EspecimeService.get_by_id(db, especime_id)
    if not especime:
        raise HTTPException(status_code=404, detail="Espécime não encontrado")
    await EspecimeService.delete(db, especime)


# ─── Imagens ──────────────────────────────────────────────────────────────────

@router.post("/{especime_id}/imagens", response_model=ImagemOut, status_code=201,
             summary="Upload de imagem para espécime")
async def upload_imagem(
    especime_id: int,
    arquivo: UploadFile = File(...),
    descricao: Optional[str] = Form(None),
    is_principal: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    especime = await EspecimeService.get_by_id(db, especime_id)
    if not especime:
        raise HTTPException(status_code=404, detail="Espécime não encontrado")
    return await ImagemService.upload(db, especime_id, arquivo, descricao, is_principal)


@router.get("/{especime_id}/imagens", response_model=List[ImagemOut],
            summary="Listar imagens de um espécime")
async def listar_imagens(
    especime_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await ImagemService.listar_por_especime(db, especime_id)


@router.delete("/{especime_id}/imagens/{imagem_id}", status_code=204,
               summary="Remover imagem")
async def remover_imagem(
    especime_id: int,
    imagem_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    removido = await ImagemService.deletar(db, imagem_id, especime_id)
    if not removido:
        raise HTTPException(status_code=404, detail="Imagem não encontrada")


# ─── Exportação DwC-A ─────────────────────────────────────────────────────────

@router.post("/exportar/dwca", summary="Exportar seleção em Darwin Core Archive")
async def exportar_dwca(
    ids: Optional[List[int]] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    conteudo = await ExportService.exportar_dwca(db, ids)
    return Response(
        content=conteudo,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=dwca_export.zip",
            "Content-Length": str(len(conteudo)),
        },
    )


@router.get("/exportar/dwca/todos", summary="Exportar todos os espécimes em Darwin Core Archive")
async def exportar_dwca_todos(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    conteudo = await ExportService.exportar_dwca(db)
    return Response(
        content=conteudo,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=dwca_completo.zip"},
    )


# ─── Etiqueta PDF ─────────────────────────────────────────────────────────────

@router.get("/{especime_id}/etiqueta", summary="Gerar etiqueta PDF com código de barras")
async def etiqueta(
    especime_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    especime = await EspecimeService.get_by_id(db, especime_id)
    if not especime:
        raise HTTPException(status_code=404, detail="Espécime não encontrado")
    pdf_bytes = EtiquetaService.gerar_etiqueta_pdf(especime)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=etiqueta_{especime.codigo_catalogo}.pdf"
        },
    )
