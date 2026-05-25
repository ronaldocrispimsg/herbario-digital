# 🧬 BioAcervo API

Sistema de Gestão de Acervo Biológico — API RESTful construída com **FastAPI** e **PostgreSQL**.

---

## 📋 Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| **CRUD completo** | Espécimes, Taxonomia, Localidades, Usuários, Empréstimos |
| **Upload de imagens** | JPEG, PNG, TIFF, WebP — até 20 MB por arquivo |
| **GPS / Coordenadas** | Latitude, longitude, altitude, datum geodésico e precisão |
| **Exportação DwC-A** | Darwin Core Archive (ZIP com CSV + meta.xml + eml.xml) |
| **Busca avançada** | Critérios taxonômicos, geográficos, temporais e bounding box |
| **Etiquetas PDF** | Geração de etiqueta A6 com código de barras Code128 |
| **Controle de acesso** | Perfis: `administrador`, `curador`, `leitor` |
| **Empréstimos** | Gestão de saída/retorno de espécimes entre instituições |

---

## 🚀 Execução com Docker

O projeto está preparado para subir frontend, backend, banco PostgreSQL e bucket local com um único comando:

```bash
docker compose up --build -d
```

Acesse:

- **Frontend:** http://localhost:8080
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

O backend aplica migrations na primeira inicialização. O usuário admin inicial é criado pelo seed somente quando `ADMIN_EMAIL` e `ADMIN_PASSWORD` estiverem configurados.

> Defina `ADMIN_PASSWORD` e `SECRET_KEY` próprios antes de usar em produção.

### Estrutura Docker

```text
bioacervo/
├── frontend/            # Nginx + página inicial
├── backend/             # FastAPI, SQLAlchemy, Alembic e seed
├── database/            # Imagem PostgreSQL e dados persistentes em database/data
├── bucket/              # Imagem bucket local e arquivos persistentes em bucket/data
├── docker-compose.yml
└── .env
```

Para acompanhar logs:

```bash
docker compose logs -f
```

Para parar:

```bash
docker compose down
```

## 🛠️ Instalação local sem Docker

### 1. Pré-requisitos

- Python 3.11+
- PostgreSQL 14+

### 2. Criar banco de dados PostgreSQL

```sql
CREATE DATABASE bioacervo;
CREATE USER usuario WITH PASSWORD 'senha';
GRANT ALL PRIVILEGES ON DATABASE bioacervo TO usuario;
```

### 3. Instalar dependências

```bash
cd bioacervo/backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env com suas credenciais do banco de dados
```

Campos essenciais no `.env`:
```env
DATABASE_URL=postgresql+asyncpg://bioacervo:bioacervo_dev_password@database:5432/bioacervo
DATABASE_URL_SYNC=postgresql+psycopg2://bioacervo:bioacervo_dev_password@database:5432/bioacervo
SECRET_KEY=gere-uma-chave-segura-aqui
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=defina-uma-senha-forte
CORS_ORIGINS=http://localhost:8080
```

Para gerar uma chave segura:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Migrar tabelas e usuário inicial

```bash
alembic upgrade head
python seed.py
```

O seed cria o usuário admin somente a partir de `ADMIN_EMAIL` e `ADMIN_PASSWORD`.
Em desenvolvimento, sem essas variáveis, ele usa credenciais locais com aviso; em produção, não cria admin padrão.

### 6. Executar o servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🔐 Autenticação

Todas as rotas (exceto `/health` e `/`) exigem autenticação via **JWT Bearer Token**.

```bash
# Obter token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ADMIN_EMAIL&password=$ADMIN_PASSWORD"

# Usar token
curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/v1/especimes
```

### Perfis de Acesso

| Perfil | Permissões |
|---|---|
| `administrador` | Acesso total (CRUD, gerenciar usuários, deletar) |
| `curador` | Criar e editar espécimes, taxonomias, localidades, empréstimos |
| `leitor` | Somente leitura e exportação |

---

## 📡 Endpoints Principais

### Autenticação
| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/login` | Login (retorna JWT) |
| POST | `/api/v1/auth/registrar` | Cadastrar usuário (admin) |
| GET | `/api/v1/auth/me` | Dados do usuário atual |

### Espécimes
| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/especimes` | Listar (paginado) |
| POST | `/api/v1/especimes` | Cadastrar |
| GET | `/api/v1/especimes/{id}` | Detalhe |
| PUT | `/api/v1/especimes/{id}` | Atualizar |
| DELETE | `/api/v1/especimes/{id}` | Remover |
| POST | `/api/v1/especimes/buscar` | Busca avançada |
| POST | `/api/v1/especimes/{id}/imagens` | Upload de imagem |
| GET | `/api/v1/especimes/{id}/imagens` | Listar imagens |
| DELETE | `/api/v1/especimes/{id}/imagens/{img_id}` | Remover imagem |
| GET | `/api/v1/especimes/{id}/etiqueta` | Etiqueta PDF com código de barras |
| GET | `/api/v1/especimes/exportar/dwca/todos` | Exportar todos em DwC-A |
| POST | `/api/v1/especimes/exportar/dwca` | Exportar seleção em DwC-A |

### Taxonomia
| Método | Rota |
|---|---|
| GET/POST | `/api/v1/taxonomias` |
| GET/PUT/DELETE | `/api/v1/taxonomias/{id}` |

### Localidades
| Método | Rota |
|---|---|
| GET/POST | `/api/v1/localidades` |
| GET/PUT/DELETE | `/api/v1/localidades/{id}` |

### Usuários
| Método | Rota |
|---|---|
| GET | `/api/v1/usuarios` (admin) |
| GET/PUT/DELETE | `/api/v1/usuarios/{id}` |

### Empréstimos
| Método | Rota |
|---|---|
| GET/POST | `/api/v1/emprestimos` |
| PUT | `/api/v1/emprestimos/{id}` |

---

## 🔍 Exemplo de Busca Avançada

```bash
curl -X POST http://localhost:8000/api/v1/especimes/buscar \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "nome_cientifico": "Passiflora",
    "estado": "Minas Gerais",
    "data_coleta_inicio": "2020-01-01T00:00:00",
    "status": "ativo",
    "page": 1,
    "per_page": 20
  }'
```

---

## 🗂️ Estrutura do Projeto

```
bioacervo/
├── backend/
│   ├── app/
│   ├── api/v1/
│   │   └── endpoints/
│   │       ├── auth.py
│   │       ├── especimes.py
│   │       ├── taxonomia_localidade.py
│   │       └── usuarios_emprestimos.py
│   ├── core/
│   │   ├── config.py         # Configurações e variáveis de ambiente
│   │   └── security.py       # JWT, hashing, permissões
│   ├── db/
│   │   └── session.py        # Engine e sessão assíncrona
│   ├── models/
│   │   └── models.py         # Modelos SQLAlchemy (ORM)
│   ├── schemas/
│   │   └── schemas.py        # Schemas Pydantic (validação/serialização)
│   ├── services/
│   │   ├── especime_service.py
│   │   ├── usuario_service.py
│   │   ├── imagem_service.py
│   │   └── export_service.py # DwC-A e etiquetas PDF
│   │   └── main.py           # Aplicação FastAPI
│   ├── alembic/              # Migrações de banco de dados
│   ├── seed.py               # Script de inicialização
│   └── requirements.txt
├── frontend/                 # Frontend estático servido por Nginx
├── database/                 # Dockerfile + dados persistentes em database/data
├── bucket/                   # Dockerfile + imagens/exportações em bucket/data
├── docker-compose.yml
├── .env
└── .env.example
```

---

## 🧪 Migrações com Alembic

```bash
# Gerar nova migração após alterar models.py
alembic revision --autogenerate -m "descricao da mudanca"

# Aplicar migrações
alembic upgrade head

# Reverter última migração
alembic downgrade -1
```

---

## 🌍 Darwin Core Archive (DwC-A)

O arquivo ZIP exportado contém:
- `occurrence.csv` — dados dos espécimes mapeados para Darwin Core
- `meta.xml` — descritor de campos conforme padrão TDWG
- `eml.xml` — metadados do dataset (EML 2.1.1)

Compatível com **GBIF**, **iDigBio**, **SpeciesLink** e outros portais de biodiversidade.
