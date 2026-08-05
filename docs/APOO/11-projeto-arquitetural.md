# Projeto Arquitetural

## 1. Visão geral

O BioAcervo é uma API RESTful em FastAPI com persistência PostgreSQL (SQLAlchemy ORM assíncrono). Ver `Architecture/00_Arquitetura.md` para detalhe em camadas C4.

## 2. Stack

- **API**: FastAPI + Pydantic v2 (DTOs)
- **ORM**: SQLAlchemy assíncrono (asyncpg)
- **Banco**: PostgreSQL 16 (container `bioacervo-database`)
- **Auth**: JWT Bearer Token (bcrypt + `get_current_user`, `require_roles`)
- **Armazenamento**: bucket local (volume Docker) para imagens
- **Orquestração**: Docker Compose (database + backend + bucket + frontend)

## 3. Camadas (C4 — Nível de Contêiner)

| Contêiner | Tecnologia | Responsabilidade |
|---|---|---|
| Frontend | Nginx + React | UI de consulta/curadoria |
| Backend (API) | FastAPI + Uvicorn | Rotas, auth, orquestração de domínio |
| Banco | PostgreSQL 16 | Persistência relacional |
| Bucket | Volume local | Armazenamento de imagens |

## 4. Camadas internas (Backend)

- `api/v1/endpoints/` — adaptadores HTTP (auth, especimes, taxonomia_localidade, usuarios_emprestimos)
- `services/` — regras de negócio (EspecimeService, UsuarioService, ImagemService, ExportService + EtiquetaService)
- `models/` — ORM (6 entidades + 3 enums)
- `schemas/` — DTOs Pydantic v2
- `core/` — security (JWT), config (settings)
- `db/session.py` — engine assíncrono + `get_db`

## 5. Fluxo de requisição

1. Endpoint recebe requisição, autentica (JWT) e valida entrada (Pydantic)
2. Chama Service correspondente
3. Service orquestra regras de negócio e acesso a dados (ORM)
4. Retorna DTO serializado



## 7. Decisões arquiteturais

- ORM assíncrono para concorrência em I/O de banco
- Controle de acesso no backend (`require_roles`), não na UI
- Exportação DwC-A desacoplada em `ExportService` (interoperabilidade com GBIF/iDigBio/SpeciesLink)
- Bucket local como volume, facilitando migração futura para objeto store

## 5. Diagramas

![Diagrama de Classes](docs/APOO/Diagrams/classes.png)

![Diagrama de Pacotes/Componentes](docs/APOO/Diagrams/pacotes.png)


