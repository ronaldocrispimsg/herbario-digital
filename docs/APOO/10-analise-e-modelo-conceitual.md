# Análise e Modelo Conceitual

## 1. Objetivo

Registrar as entidades de domínio do BioAcervo, seus atributos mais relevantes e os relacionamentos principais, tomando como fonte de verdade `backend/app/models/models.py`.

Este documento não substitui o schema. Ele serve como apoio de leitura para manutenção e análise de impacto.

## 2. Fonte de verdade

- `backend/app/models/models.py`

## 3. Entidades centrais

### `Usuario`

Acesso ao sistema. Perfil define permissões (leitor/curador/administrador).
- Campos: `id`, `nome`, `email` (único), `senha_hash`, `perfil` (ENUM), `ativo` (bool), `criado_em`, `atualizado_em`
- Relacionamentos: 1-* Espécime (cadastrado_por_id); 1-* Empréstimo (responsavel_id)

### `Taxonomia`

Classificação científica do espécime.
- Campos: `id`, `reino/filo/classe/ordem`, `familia/genero`, `epiteto_especifico`, `nome_cientifico` (único, NOT NULL), `autor_descricao`, `ano_descricao`, `nome_comum`, `sinonimos` (JSONB), `notas_taxonomicas` (TEXT)
- Relacionamentos: 1-* Espécime (taxonomia_id, NOT NULL)

### `LocalidadeGeografica`

Ponto de coleta georreferenciado.
- Campos: `id`, `pais` (default Brasil), `estado/municipio/localidade`, `latitude/longitude` (FLOAT), `altitude_m/precisao_coord`, `datum_geodesico` (WGS84), `metodo_geolocalizacao`, `bioma`
- Relacionamentos: 1-* Espécime (localidade_id, opcional)

### `Especime`

Entidade central. Indivíduo biológico catalogado.
- Campos: `id`, `codigo_catalogo` (único), `codigo_barras` (único SPEC-), `taxonomia_id` (FK NOT NULL), `localidade_id` (FK), `data_coleta/data_coleta_fim`, `tipo_coleta` (ENUM), `coletor_principal`, `coletores_adicionais` (JSONB), `numero_campo`, `sexo/estagio_vida/condicao`, `numero_individuos`, `descricao_morfologica/habitat/obs`, `identificado_por`, `data_identificacao`, `status` (ENUM ativo/emprestado), `localizacao_fisica`, `meio_preservacao`, `dwc_record_id` (único urn:uuid), `cadastrado_por_id` (FK), `criado_em/atualizado_em`
- Relacionamentos: *-1 Taxonomia; *-1 Localidade; 1-* ImagemEspecime (CASCADE); 1-* Empréstimo

### `ImagemEspecime`

Mídia do espécime.
- Campos: `id`, `especime_id` (FK NOT NULL ON DELETE CASCADE), `nome_arquivo`, `caminho`, `url_relativa`, `tamanho_bytes/largura_px/altura_px`, `descricao`, `is_principal` (bool)
- Relacionamentos: *-1 Espécime

### `Emprestimo`

Saída temporária de espécime.
- Campos: `id`, `especime_id` (FK NOT NULL), `responsavel_id` (FK NOT NULL), `instituicao_destino`, `pesquisador_responsavel`, `finalidade`, `data_saida` (NOT NULL), `data_prevista_retorno`, `data_retorno`, `observacoes`, `ativo` (bool)
- Relacionamentos: *-1 Espécime; *-1 Usuário (responsavel)

## 4. Enumerações

- `PerfilUsuario`: `leitor`, `curador`, `administrador`
- `StatusEspecime`: `ativo`, `emprestado`
- `TipoColeta`: `campo`, `cultivo`, `aves`, `mamuideo`

## 5. Observações

- `sinonimos`, `coletores_adicionais`, `referencias_bibliograficas` são JSONB
- `codigo_barras` segue padrão `SPEC-<hex>`; `dwc_record_id` é URN Darwin Core
- Imagens seguem `ON DELETE CASCADE` a partir do espécime

![Diagrama ER do PostgreSQL](docs/APOO/Diagrams/er.png)

