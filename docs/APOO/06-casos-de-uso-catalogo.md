# Catálogo de Casos de Uso

## 1. Convenções

- Identificador de caso de uso: `UC-XX`
- Este catálogo resume os casos de uso do sistema sem expandir todos os fluxos
- Apenas os casos mais relevantes serão detalhados em versão expandida

## 2. Acesso e usuários

### `UC-01` Cadastrar usuário no sistema
- Objetivo: permitir que um admin registre um novo usuário
- Atores primários: administrador
- Gatilho: o admin acessa a tela de criação de usuário
- Pré-condições: permissão `administrador`
- Pós-condições: usuário criado (models.py:UsuarioService.create)

### `UC-02` Autenticar usuário
- Objetivo: permitir acesso autenticado via JWT
- Atores primários: usuário cadastrado
- Gatilho: o usuário informa credenciais na tela de login
- Pré-condições: conta existente
- Pós-condições: token JWT emitido (core/security.py)

### `UC-03` Atualizar próprio perfil
- Objetivo: manter dados de perfil atualizados
- Atores primários: usuário autenticado
- Gatilho: o usuário acessa a área de perfil
- Pré-condições: sessão autenticada
- Pós-condições: perfil persistido (UsuarioSelfUpdate)

## 3. Taxonomia e Localidades

### `UC-04` Cadastrar Taxonomia
- Objetivo: registrar classificação científica
- Atores: curador, administrador
- Pré: `require_roles("administrador","curador")`
- Pós: Taxonomia criada (taxonomia_localidade.py:53)

### `UC-05` Cadastrar Localidade Geográfica
- Objetivo: registrar ponto de coleta
- Atores: curador, administrador
- Pós: LocalidadeGeografica criada (taxonomia_localidade.py:129)

## 4. Espécimes

### `UC-06` Cadastrar Espécime
- Objetivo: registrar espécime com código de barras e DwC ID automáticos
- Atores: curador, administrador
- Gatilho: formulário de criação de espécime
- Pós: Espécime criado com `codigo_barras=SPEC-<uuid>`, `dwc_record_id=urn:uuid:<uuid>` (especime_service.py:46-54)

### `UC-07` Buscar Espécimes por Bounding Box
- Objetivo: filtrar espécimes por caixa geográfica
- Atores: usuário autenticado
- Gatilho: informa lat/lon min/max
- Pós: lista paginada de espécimes (especime_service.buscar:125-133)

### `UC-08` Associa Imagem a Espécime
- Objetivo: vincular imagem (até 20 MB) ao espécime
- Atores: curador, administrador
- Pós: ImagemEspecime criada (imagem_service.py)

## 5. Empréstimos

### `UC-09` Emprestar Espécime
- Objetivo: registrar saída de espécime para instituição
- Atores: curador, administrador
- Pré: espécime com `status == "ativo"`
- Pós: Espécime `status="emprestado"` (usuarios_emprestimos.py:134-141)

### `UC-10` Retornar Espécime Emprestado
- Objetivo: registrar retorno e reativar espécime
- Atores: curador, administrador
- Gatilho: informa `data_retorno`
- Pós: Espécime `status="ativo"`, Empréstimo `ativo=False` (usuarios_emprestimos.py:162-166)

## 6. Exportação

### `UC-11` Exportar Darwin Core Archive
- Objetivo: gerar ZIP DwC-A (occurrence.csv + meta.xml + eml.xml)
- Atores: curador, administrador
- Pós: arquivo DwC-A disponibilizado (export_service.py)

## 7. Casos prioritários para expansão

- `UC-01`, `UC-02`, `UC-04`, `UC-05`, `UC-06`, `UC-07`, `UC-09`, `UC-10`, `UC-11`

![Fluxo de Exportação DwC-A](docs/APOO/Diagrams/fluxo_exportacao.png)

