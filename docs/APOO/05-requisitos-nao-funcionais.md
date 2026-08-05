# Requisitos Não-Funcionais

## 1. Convenções

- Identificador de requisito não-funcional: `RNF-XX`
- Requisitos derivados da estrutura do projeto (Docker, SQLAlchemy assíncrono, Pydantic v2)

## 2. Tecnologia e Plataforma

- `RNF-01` O backend deve usar FastAPI + SQLAlchemy ORM assíncrono (asyncpg) (`core/session.py`)
- `RNF-02` O banco de dados deve ser PostgreSQL 16 (container `bioacervo-database`) (`docker-compose.yml`)
- `RNF-03` A validação de entrada deve usar Pydantic v2 (DTOs em `schemas.py`)

## 3. Persistência e Integridade

- `RNF-04` O sistema deve garantir unicidade de `email` (Usuário), `nome_cientifico` (Taxonomia, com índice trigram), `codigo_catalogo` e `codigo_barras` (Espécime), `dwc_record_id` (`models.py`)
- `RNF-05` Relações de exclusão em cascata devem ser aplicadas (ImagemEspecime → Espécime `ON DELETE CASCADE`) (`models.py:ImagemEspecime`)

## 4. Segurança

- `RNF-06` Senhas devem ser armazenadas com hash (bcrypt) e autenticação via JWT (`core/security.py`)
- `RNF-07` Controle de acesso por perfil (`PerfilUsuario`: leitor/curador/administrador) via `require_roles`

## 5. Interoperabilidade

- `RNF-08` A exportação deve seguir o padrão Darwin Core Archive (occurrence.csv + meta.xml + eml.xml) para GBIF/iDigBio/SpeciesLink (`export_service.py`)

## 6. Operação

- `RNF-09` Imagens devem ser armazenadas em bucket local (volume Docker) com limite de 20 MB por arquivo (`imagem_service.py`)
- `RNF-10` O sistema deve expor saúde da API em `/health` (`main.py`)

## 7. Observações

Estes requisitos refletem o estado atual do `docker-compose.yml` e de `models.py`. Ajustes futuros (LGPD, hardening de rede) devem ser registrados como trabalho futuro.
