import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import Usuario, Emprestimo
from app.schemas.schemas import (
    UsuarioOut, UsuarioUpdate,
    EmprestimoCreate, EmprestimoUpdate, EmprestimoOut,
    PaginatedResponse,
)
from app.services.usuario_service import UsuarioService
from app.services.especime_service import EspecimeService
from app.core.security import get_current_user, require_roles

# ─── Usuários ─────────────────────────────────────────────────────────────────

usuario_router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@usuario_router.get("", response_model=PaginatedResponse,
                    summary="Listar usuários (admin)")
async def listar_usuarios(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador")),
):
    total, items = await UsuarioService.listar(db, (page - 1) * per_page, per_page)
    return PaginatedResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[UsuarioOut.model_validate(i) for i in items],
    )


@usuario_router.get("/{uid}", response_model=UsuarioOut)
async def detalhe_usuario(
    uid: int, db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Usuário pode ver a si mesmo; admin pode ver qualquer um
    if current_user.id != uid and current_user.perfil != "administrador":
        raise HTTPException(403, "Acesso negado")
    u = await UsuarioService.get_by_id(db, uid)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    return u


@usuario_router.put("/{uid}", response_model=UsuarioOut)
async def atualizar_usuario(
    uid: int, data: UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.id != uid and current_user.perfil != "administrador":
        raise HTTPException(403, "Acesso negado")
    # Apenas admin pode mudar perfil
    if data.perfil is not None and current_user.perfil != "administrador":
        raise HTTPException(403, "Apenas administradores podem alterar perfis")
    u = await UsuarioService.get_by_id(db, uid)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    return await UsuarioService.update(db, u, data)


@usuario_router.delete("/{uid}", status_code=204)
async def remover_usuario(
    uid: int, db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador")),
):
    u = await UsuarioService.get_by_id(db, uid)
    if not u:
        raise HTTPException(404, "Usuário não encontrado")
    await UsuarioService.delete(db, u)


# ─── Empréstimos ──────────────────────────────────────────────────────────────

emprestimo_router = APIRouter(prefix="/emprestimos", tags=["Empréstimos"])


@emprestimo_router.get("", response_model=PaginatedResponse)
async def listar_emprestimos(
    apenas_ativos: bool = True,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    query = (
        select(Emprestimo)
        .options(selectinload(Emprestimo.especime).selectinload(
            __import__("app.models.models", fromlist=["Especime"]).Especime.taxonomia
        ))
    )
    if apenas_ativos:
        query = query.where(Emprestimo.ativo == True)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    items = (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    return PaginatedResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[EmprestimoOut.model_validate(i) for i in items],
    )


@emprestimo_router.post("", response_model=EmprestimoOut, status_code=201)
async def criar_emprestimo(
    data: EmprestimoCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles("administrador", "curador")),
):
    especime = await EspecimeService.get_by_id(db, data.especime_id)
    if not especime:
        raise HTTPException(404, "Espécime não encontrado")
    if especime.status != "ativo":
        raise HTTPException(400, f"Espécime não disponível para empréstimo (status: {especime.status})")

    emprestimo = Emprestimo(**data.model_dump(), responsavel_id=current_user.id)
    db.add(emprestimo)

    # Atualizar status do espécime
    especime.status = "emprestado"
    await db.flush()
    await db.refresh(emprestimo)
    return emprestimo


@emprestimo_router.put("/{eid}", response_model=EmprestimoOut)
async def atualizar_emprestimo(
    eid: int, data: EmprestimoUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_roles("administrador", "curador")),
):
    emp = (await db.execute(
        select(Emprestimo).where(Emprestimo.id == eid)
    )).scalar_one_or_none()
    if not emp:
        raise HTTPException(404, "Empréstimo não encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # Se retornou, atualizar status do espécime
    if "data_retorno" in update_data and update_data["data_retorno"]:
        especime = await EspecimeService.get_by_id(db, emp.especime_id)
        if especime:
            especime.status = "ativo"
        update_data["ativo"] = False

    for k, v in update_data.items():
        setattr(emp, k, v)
    await db.flush()
    await db.refresh(emp)
    return emp
