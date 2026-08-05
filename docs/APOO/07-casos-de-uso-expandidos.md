# Casos de Uso Expandidos

## 1. Convenções

- Cada caso abaixo detalha fluxo, entradas e exceções conforme `endpoints/` e `services/`
- Identificador mantém o padrão `UC-XX` do catálogo

## 2. UC-06 — Cadastrar Espécime (expandido)

**Atores:** curador, administrador
**Pré-condição:** sessão autenticada com perfil autorizado; `taxonomia_id` válido
**Fluxo principal:**
1. O ator aciona criação de espécime (`especimes.py` POST `/especimes`)
2. O endpoint valida JWT e `require_roles("administrador","curador")`
3. `EspecimeService.create` gera `codigo_barras = SPEC-<uuid>[:12]` e `dwc_record_id = urn:uuid:<uuid>` (especime_service.py:46-54)
4. O serviço persiste `data_entrada_colecao = utcnow()` e `cadastrado_por_id = usuario_id`
5. Retorna espécime com relacionamentos carregados

**Exceções:** `taxonomia_id` inválido → 404; `localidade_id` opcional

## 3. UC-07 — Buscar por Bounding Box (expandido)

**Atores:** usuário autenticado
**Fluxo:**
1. `GET /especimes/buscar` com filtros (especime_service.buscar)
2. Condições acumulativas: nome_cientifico/familia/genero (ILIKE em Taxonomia), estado/municipio/bioma (ILIKE em LocalidadeGeografica), lat/lon min/max (bounding box), coletor, status, data_coleta_inicio/fim
3. Contagem total + paginação (page/per_page, order_by id desc)
4. Retorna `PaginatedResponse`

## 4. UC-09 — Emprestar Espécime (expandido)

**Atores:** curador, administrador
**Pré:** espécime existe e `status == "ativo"`
**Fluxo:**
1. `POST /emprestimos` (usuarios_emprestimos.py:125)
2. Valida perfil e existência do espécime (404 se ausente)
3. Se `status != "ativo"` → 400 "Espécime não disponível"
4. Cria Empréstimo com `responsavel_id = current_user.id`
5. Define `especime.status = "emprestado"` e flush (linha 141)

## 5. UC-10 — Retornar Espécime (expandido)

**Atores:** curador, administrador
**Fluxo:**
1. `PUT /emprestimos/{eid}` com `data_retorno` (usuarios_emprestimos.py:147)
2. Se `data_retorno` presente: `especime.status = "ativo"` e `ativo = False` (linhas 162-166)
3. Persiste alterações

## 6. UC-11 — Exportar DwC-A (expandido)

**Atores:** curador, administrador
**Fluxo:**
1. `ExportService` coleta espécimes + taxonomias + localidades
2. Gera `occurrence.csv` (padão DwC), `meta.xml`, `eml.xml`
3. Empacota em ZIP retornado ao cliente (export_service.py)

![Fluxo de Empréstimo](docs/APOO/Diagrams/fluxo_emprestimo.png)

