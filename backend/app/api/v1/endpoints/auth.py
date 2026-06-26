from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import Token, UsuarioCreate, UsuarioOut
from app.services.usuario_service import UsuarioService
from app.core.security import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=Token, summary="Login e obtenção de token JWT")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    usuario = await UsuarioService.authenticate(db, form_data.username, form_data.password)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(usuario.id), "perfil": usuario.perfil})
    return Token(access_token=token, usuario=usuario)


@router.post("/registrar", response_model=UsuarioOut, status_code=201,
             summary="Registrar novo usuário (apenas administradores)")
async def registrar(
    data: UsuarioCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.models import PerfilUsuario
    if current_user.perfil != PerfilUsuario.administrador:
        raise HTTPException(status_code=403, detail="Apenas administradores podem cadastrar usuários")
    existente = await UsuarioService.get_by_email(db, data.email)
    if existente:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    return await UsuarioService.create(db, data)


@router.get("/me", response_model=UsuarioOut, summary="Dados do usuário autenticado")
async def me(current_user=Depends(get_current_user)):
    return current_user
