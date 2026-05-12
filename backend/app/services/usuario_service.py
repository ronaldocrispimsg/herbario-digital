from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from app.models.models import Usuario
from app.schemas.schemas import UsuarioCreate, UsuarioUpdate
from app.core.security import get_password_hash, verify_password


class UsuarioService:

    @staticmethod
    async def get_by_id(db: AsyncSession, usuario_id: int) -> Optional[Usuario]:
        result = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[Usuario]:
        result = await db.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, data: UsuarioCreate) -> Usuario:
        usuario = Usuario(
            nome=data.nome,
            email=data.email,
            senha_hash=get_password_hash(data.senha),
            perfil=data.perfil,
        )
        db.add(usuario)
        await db.flush()
        await db.refresh(usuario)
        return usuario

    @staticmethod
    async def update(db: AsyncSession, usuario: Usuario, data: UsuarioUpdate) -> Usuario:
        update_data = data.model_dump(exclude_unset=True)
        if "senha" in update_data:
            update_data["senha_hash"] = get_password_hash(update_data.pop("senha"))
        for field, value in update_data.items():
            setattr(usuario, field, value)
        usuario.atualizado_em = datetime.utcnow()
        await db.flush()
        await db.refresh(usuario)
        return usuario

    @staticmethod
    async def delete(db: AsyncSession, usuario: Usuario) -> None:
        await db.delete(usuario)
        await db.flush()

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, senha: str) -> Optional[Usuario]:
        usuario = await UsuarioService.get_by_email(db, email)
        if not usuario or not verify_password(senha, usuario.senha_hash):
            return None
        if not usuario.ativo:
            return None
        return usuario

    @staticmethod
    async def listar(db: AsyncSession, skip: int = 0, limit: int = 50) -> Tuple[int, List[Usuario]]:
        total = (await db.execute(select(func.count(Usuario.id)))).scalar()
        result = await db.execute(select(Usuario).offset(skip).limit(limit).order_by(Usuario.id))
        return total, list(result.scalars().all())
