from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: garantir diretórios
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    print("✅ BioAcervo API iniciada")
    yield
    print("🛑 BioAcervo API encerrada")


app = FastAPI(
    title="BioAcervo API",
    description="""
## Sistema de Gestão de Acervo Biológico

API RESTful para gerenciamento completo de coleções científicas, com suporte a:

- **CRUD** de espécimes com identificação taxonômica completa
- **Upload de imagens** de alta resolução (JPEG, PNG, TIFF, WebP)
- **Coordenadas GPS** e localização geográfica detalhada
- **Exportação Darwin Core Archive (DwC-A)** para integração global (GBIF, iDigBio)
- **Busca avançada** por múltiplos critérios (taxonômicos, geográficos, temporais)
- **Etiquetas PDF** com código de barras para rastreabilidade física
- **Controle de acesso** por perfis: Administrador, Curador e Leitor Público
- **Gestão de empréstimos** entre instituições

### Autenticação
Utilize `/api/v1/auth/login` para obter um token JWT Bearer.
    """,
    version="1.0.0",
    contact={"name": "BioAcervo", "email": "admin@bioacervo.org"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# CORS: em produção, configure CORS_ORIGINS com domínios explícitos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos persistidos no bucket via /uploads.
# TODO: avaliar regra de negócio para tornar imagens privadas/autorizadas sem quebrar a galeria atual.
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Registrar rotas
app.include_router(api_router)


@app.get("/", tags=["Status"])
async def root():
    return {
        "sistema": "BioAcervo API",
        "versao": "1.0.0",
        "status": "operacional",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Status"])
async def health():
    return {"status": "ok"}
