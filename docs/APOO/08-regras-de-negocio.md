# Regras de Negócio Consolidadas

## 1. Objetivo

Este documento consolida as regras de negócio mais relevantes do BioAcervo, evitando que elas fiquem dispersas entre casos de uso, rotas e implementações backend.

As regras abaixo foram extraídas da codebase atual e devem ser tratadas como referência operacional do sistema.

## 2. Convenções

- Identificador de regra de negócio: `RN-XX`
- Quando uma regra depender fortemente de estado, a máquina correspondente deve ser consultada em `09-maquinas-de-estado.md`
- Quando uma regra estiver associada a um caso de uso expandido, o identificador do caso deve ser referenciado na manutenção futura

## 3. Usuários e acesso

- `RN-01` Novos usuários são criados com perfil padrão `leitor` (models.py:PerfilUsuario; usuario_service.create)
- `RN-02` Apenas `administrador` pode criar usuários (usuarios_emprestimos.py:43)
- `RN-03` Usuário só atualiza próprio perfil; admin pode editar qualquer um (usuarios_emprestimos.py:65-81)
- `RN-04` Não-admin não pode alterar `perfil` ou `ativo` de usuário (usuarios_emprestimos.py:74-75)
- `RN-05` Leitor possui acesso somente leitura a todos os endpoints

## 4. Taxonomia e Localidades

- `RN-06` Taxonomia exige `nome_cientifico` único e não nulo (models.py:Taxonomia, UNIQUE)
- `RN-07` CRUD de Taxonomia/Localidade exige perfil `administrador` ou `curador` (taxonomia_localidade.py:57,133)
- `RN-08` Localidade usa `datum_geodesico` padrão WGS84 (models.py:LocalidadeGeografica)

## 5. Espécimes

- `RN-09` Espécime exige `taxonomia_id` (FK NOT NULL) (models.py:Especime)
- `RN-10` `codigo_catalogo` e `codigo_barras` são únicos (models.py:Especime, UNIQUE)
- `RN-11` Na criação, geram-se automaticamente `codigo_barras = SPEC-<uuid>[:12]` e `dwc_record_id = urn:uuid:<uuid>` (especime_service.py:46-54)
- `RN-12` `coletores_adicionais` e `referencias_bibliograficas` são JSONB (models.py:Especime)
- `RN-13` Exclusão de espécime remove em cascata suas imagens (ImagemEspecime ON DELETE CASCADE)

## 6. Empréstimos

- `RN-14` Espécime só pode ser emprestado se `status == "ativo"` (usuarios_emprestimos.py:134)
- `RN-15` Ao criar empréstimo, espécime vai para `status = "emprestado"` (usuarios_emprestimos.py:141)
- `RN-16` Ao retornar (data_retorno informada), espécime volta a `status = "ativo"` e empréstimo `ativo = False` (usuarios_emprestimos.py:162-166)
- `RN-17` Empréstimo exige `especime_id` e `responsavel_id` (FK NOT NULL)

## 7. Exportação

- `RN-18` A exportação DwC-A gera `occurrence.csv` + `meta.xml` + `eml.xml` conforme Darwin Core (export_service.py)

## 8. Observações para manutenção

- Regras de acesso devem ser validadas no backend (require_roles), não apenas na UI
- Campos JSONB (coletores_adicionais, referencias_bibliograficas, sinonimos) exigem parse defensivo no import
- O status do espécime é a fonte de verdade para disponibilidade de empréstimo
