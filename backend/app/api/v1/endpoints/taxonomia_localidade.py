import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.models import Taxonomia, LocalidadeGeografica
from app.schemas.schemas import (
    TaxonomiaCreate, TaxonomiaUpdate, TaxonomiaOut,
    LocalidadeCreate, LocalidadeUpdate, LocalidadeOut,
    PaginatedResponse,
)
from app.core.security import get_current_user, require_roles

# ─── Taxonomia ────────────────────────────────────────────────────────────────

taxonomia_router = APIRouter(prefix="/taxonomias", tags=["Taxonomia"])


@taxonomia_router.get("", response_model=PaginatedResponse)
async def listar_taxonomias(
    q: Optional[str] = Query(None, description="Busca por nome científico ou comum"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = select(Taxonomia)
    if q:
        query = query.where(
            Taxonomia.nome_cientifico.ilike(f"%{q}%") |
            Taxonomia.nome_comum.ilike(f"%{q}%") |
            Taxonomia.familia.ilike(f"%{q}%")
        )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return PaginatedResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[TaxonomiaOut.model_validate(i) for i in items],
    )


@taxonomia_router.get("/{tid}", response_model=TaxonomiaOut)
async def detalhe_taxonomia(tid: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    t = (await db.execute(select(Taxonomia).where(Taxonomia.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Taxonomia não encontrada")
    return t


@taxonomia_router.post("", response_model=TaxonomiaOut, status_code=201)
async def criar_taxonomia(
    data: TaxonomiaCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    t = Taxonomia(**data.model_dump())
    db.add(t)
    await db.flush()
    await db.refresh(t)
    return t


@taxonomia_router.put("/{tid}", response_model=TaxonomiaOut)
async def atualizar_taxonomia(
    tid: int, data: TaxonomiaUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    t = (await db.execute(select(Taxonomia).where(Taxonomia.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Taxonomia não encontrada")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    await db.flush()
    await db.refresh(t)
    return t


@taxonomia_router.delete("/{tid}", status_code=204)
async def remover_taxonomia(
    tid: int, db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador")),
):
    t = (await db.execute(select(Taxonomia).where(Taxonomia.id == tid))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Taxonomia não encontrada")
    await db.delete(t)


# ─── Localidade Geográfica ────────────────────────────────────────────────────

localidade_router = APIRouter(prefix="/localidades", tags=["Localidades Geográficas"])


@localidade_router.get("", response_model=PaginatedResponse)
async def listar_localidades(
    estado: Optional[str] = None,
    municipio: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    query = select(LocalidadeGeografica)
    if estado:
        query = query.where(LocalidadeGeografica.estado.ilike(f"%{estado}%"))
    if municipio:
        query = query.where(LocalidadeGeografica.municipio.ilike(f"%{municipio}%"))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return PaginatedResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[LocalidadeOut.model_validate(i) for i in items],
    )


@localidade_router.get("/{lid}", response_model=LocalidadeOut)
async def detalhe_localidade(lid: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    l = (await db.execute(select(LocalidadeGeografica).where(LocalidadeGeografica.id == lid))).scalar_one_or_none()
    if not l:
        raise HTTPException(404, "Localidade não encontrada")
    return l


@localidade_router.post("", response_model=LocalidadeOut, status_code=201)
async def criar_localidade(
    data: LocalidadeCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    l = LocalidadeGeografica(**data.model_dump())
    db.add(l)
    await db.flush()
    await db.refresh(l)
    return l


@localidade_router.put("/{lid}", response_model=LocalidadeOut)
async def atualizar_localidade(
    lid: int, data: LocalidadeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    l = (await db.execute(select(LocalidadeGeografica).where(LocalidadeGeografica.id == lid))).scalar_one_or_none()
    if not l:
        raise HTTPException(404, "Localidade não encontrada")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(l, k, v)
    await db.flush()
    await db.refresh(l)
    return l


@localidade_router.delete("/{lid}", status_code=204)
async def remover_localidade(
    lid: int, db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador")),
):
    l = (await db.execute(select(LocalidadeGeografica).where(LocalidadeGeografica.id == lid))).scalar_one_or_none()
    if not l:
        raise HTTPException(404, "Localidade não encontrada")
    await db.delete(l)
