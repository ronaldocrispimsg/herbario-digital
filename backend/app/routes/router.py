from fastapi import APIRouter
from app.routes.endpoints.auth import router as auth_router
from app.routes.endpoints.especimes import router as especime_router
from app.routes.endpoints.taxonomia_localidade import (
    taxonomia_router,
    localidade_router,
)
from app.routes.endpoints.usuarios_emprestimos import (
    usuario_router,
    emprestimo_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(especime_router)
api_router.include_router(taxonomia_router)
api_router.include_router(localidade_router)
api_router.include_router(usuario_router)
api_router.include_router(emprestimo_router)
