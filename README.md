# BioAcervo API

Sistema de Gestão de Acervo Biológico — API RESTful construída com FastAPI, SQLAlchemy, PostgreSQL e MinIO para armazenamento de imagens e exportações.

## Execução com Docker

O projeto está preparado para subir frontend, backend, banco PostgreSQL e bucket local com um único comando:

```bash
docker compose up --build -d
```

Acesse:

- **Frontend:** http://localhost:8080
- **API:** http://localhost:8000
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

No primeiro start, o backend cria as tabelas e inicializa o usuário administrativo por meio do seed, quando as variáveis de ambiente estão definidas.

> Antes de usar em produção, defina valores próprios para `SECRET_KEY`, `ADMIN_PASSWORD` e demais credenciais sensíveis.

### Estrutura Docker

```text
bioacervo/
├── frontend/            # Nginx + página inicial
├── backend/             # FastAPI, SQLAlchemy, seed e serviços da API
├── database/            # PostgreSQL com dados persistidos em database/data
├── bucket/              # MinIO local com dados persistidos em bucket/data
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

---

## Instalação local sem Docker

### 1. Pré-requisitos

- Python 3.11+
- PostgreSQL 14+

### 2. Criar banco de dados PostgreSQL

```sql
CREATE DATABASE bioacervo;
CREATE USER bioacervo WITH PASSWORD 'bioacervo_dev_password';
GRANT ALL PRIVILEGES ON DATABASE bioacervo TO bioacervo;
```

### 3. Instalar dependências

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

```bash
cp ../.env.example .env
```

Os campos principais estão definidos em [.env.example](.env.example) e incluem:

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

### 5. Inicializar banco e usuário admin

```bash
python seed.py
```

O script cria/verifica as tabelas automaticamente e, no ambiente de desenvolvimento, cria um usuário administrador padrão se as variáveis `ADMIN_EMAIL` e `ADMIN_PASSWORD` não forem informadas.

### 6. Executar o servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Acesse:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Autenticação

Todas as rotas, exceto `/health` e `/`, exigem autenticação via JWT Bearer.

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=AdminDev123"
```

### Perfis de Acesso

| Perfil | Permissões |
|---|---|
| `administrador` | Acesso total ao sistema |
| `curador` | Criar e editar espécimes, taxonomias, localidades e empréstimos |
| `leitor` | Somente leitura e exportação |

---

## Endpoints Principais

### Autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/v1/auth/login` | Login e obtenção de token JWT |
| POST | `/api/v1/auth/registrar` | Cadastrar usuário (apenas admin) |
| GET | `/api/v1/auth/me` | Dados do usuário autenticado |

### Espécimes

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/v1/especimes` | Listar espécimes |
| POST | `/api/v1/especimes` | Cadastrar espécime |
| GET | `/api/v1/especimes/{id}` | Detalhes |
| PUT | `/api/v1/especimes/{id}` | Atualizar |
| DELETE | `/api/v1/especimes/{id}` | Remover |
| POST | `/api/v1/especimes/buscar` | Busca avançada |
| POST | `/api/v1/especimes/{id}/imagens` | Upload de imagem |
| GET | `/api/v1/especimes/{id}/imagens` | Listar imagens |
| DELETE | `/api/v1/especimes/{id}/imagens/{img_id}` | Remover imagem |
| GET | `/api/v1/especimes/{id}/etiqueta` | Etiqueta PDF |
| GET | `/api/v1/especimes/exportar/dwca/todos` | Exportar todos em DwC-A |
| POST | `/api/v1/especimes/exportar/dwca` | Exportar seleção em DwC-A |

### Taxonomia e Localidades

| Método | Rota |
|---|---|
| GET/POST | `/api/v1/taxonomias` |
| GET/PUT/DELETE | `/api/v1/taxonomias/{id}` |
| GET/POST | `/api/v1/localidades` |
| GET/PUT/DELETE | `/api/v1/localidades/{id}` |

### Usuários e Empréstimos

| Método | Rota |
|---|---|
| GET | `/api/v1/usuarios` (admin) |
| GET/PUT/DELETE | `/api/v1/usuarios/{id}` |
| GET/POST | `/api/v1/emprestimos` |
| PUT | `/api/v1/emprestimos/{id}` |

---

## Estrutura do Projeto

```text
backend/
├── app/
│   ├── config/          # Configurações e segurança
│   ├── db/              # Sessão assíncrona com SQLAlchemy
│   ├── models/          # Modelos ORM
│   ├── routes/          # Endpoints da API
│   ├── schemas/         # Schemas Pydantic
│   └── services/        # Regras de negócio e integrações
├── main.py              # Aplicação FastAPI
├── seed.py              # Criação de tabelas e usuário inicial
└── requirements.txt
```

---

## Observações de Desenvolvimento

- A API usa autenticação JWT via OAuth2 Bearer.
- O armazenamento de arquivos é feito em MinIO por meio do bucket local.
- O seed é o ponto de inicialização do banco de dados.
- O frontend é estático e é servido pelo Nginx.

---

## Darwin Core Archive (DwC-A)

Os arquivos exportados em ZIP incluem:

- `occurrence.csv` — dados dos espécimes mapeados para Darwin Core
- `meta.xml` — descritor de campos conforme o padrão TDWG
- `eml.xml` — metadados do dataset

Essa exportação é compatível com GBIF, iDigBio, SpeciesLink e outros portais de biodiversidade.