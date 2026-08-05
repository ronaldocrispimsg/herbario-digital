# Padrões de Projeto e Diretizes de Extensão

## 1. Objetivo

Consolidar padrões de implementação observados no backend do BioAcervo, para guiar evolução futura sem regressão.

## 2. Padrões de backend

- **DTOs Pydantic v2** em `schemas/` separam validação de persistência (models.py)
- **Services estáticos** (`@staticmethod`) em `services/` concentram regras de negócio
- **Endpoints magros**: autenticam, validam e delegam a Service; não contêm regra de negócio
- **Async ao longo de toda a pilha**: `async def` + `AsyncSession` + `asyncpg`
- **get_db** como dependency do FastAPI injeta a sessão (commit/rollback/close)

## 3. Modelo de dados

- Herança de `Base` (SQLAlchemy Declarative)
- `Cascade` em relações críticas (ImagemEspecime → Espécime ON DELETE CASCADE)
- Campos JSONB para dados flexíveis (sinonimos, coletores_adicionais, referencias)
- UniqueConstraints em identificadores (email, nome_cientifico, codigo_catalogo, codigo_barras, dwc_record_id)

## 4. Autenticação e autorização

- JWT emitido em login; `get_current_user` decodifica o token
- `require_roles(*perfis)` protege endpoints por `PerfilUsuario`
- A decisão de acesso é sempre no backend

## 5. Exportação

- `ExportService` isola a lógica DwC-A (occurrence.csv + meta.xml + eml.xml)
- Etiquetas via `EtiquetaService` (PDF Code128 a partir de codigo_barras)

## 6. Diretizes de extensão

- Novos domínios devem seguir a triade: `endpoint` (HTTP) → `service` (regra) → `model` (ORM)
- Validção de entrada sempre em `schemas/` (Pydantic)
- Dados geográficos seguem WGS84 por padrão; bounding box via filtros lat/lon
- Imagens limitadas a 20 MB e armazenadas em bucket local
- Qualquer evolução de modelo deve atualizar `10-analise-e-modelo-conceitual.md` e `08-regras-de-negocio.md`
