# Rastreabilidade e Priorização

## 1. Objetivo

Consolidar a matriz de rastreabilidade entre Requisitos Funcionais (RF), Casos de Uso (UC) e Regras de Negócio (RN), extraída do código-fonte.

## 2. Matriz RF → UC → RN

| Requisito | Caso de Uso | Regra de Negócio | Evidência (arquivo:linha) |
|---|---|---|---|
| RF-01 Cadastro de usuário | UC-01 | RN-02 | usuarios_emprestimos.py:39 |
| RF-03 Autenticação JWT | UC-02 | RN-01 | core/security.py:get_current_user |
| RF-05 Criação só por admin | UC-01 | RN-02 | usuarios_emprestimos.py:43 |
| RF-08 CRUD Taxonomia | UC-04 | RN-06, RN-07 | taxonomia_localidade.py:53,57 |
| RF-10 CRUD Localidade | UC-05 | RN-07, RN-08 | taxonomia_localidade.py:129,133 |
| RF-12 Cadastro Espécime (códigos auto) | UC-06 | RN-09, RN-11 | especime_service.py:46-54 |
| RF-13 Taxonomia FK NOT NULL | UC-06 | RN-09 | models.py:Especime |
| RF-15 Bounding box | UC-07 | RN-10 | especime_service.py:125-133 |
| RF-19 Upload imagem | UC-08 | RN-13 | imagem_service.py |
| RF-21 Criar Empréstimo | UC-09 | RN-14, RN-15 | usuarios_emprestimos.py:125,134,141 |
| RF-24 Retornar Empréstimo | UC-10 | RN-16 | usuarios_emprestimos.py:162-166 |
| RF-25 Export DwC-A | UC-11 | RN-18 | export_service.py |

## 3. Priorização inicial

| Prioridade | Itens | Motivo |
|---|---|---|
| Alta | RF-12, RF-21, RF-24, RN-09/14/15/16 | Núcleo de curadoria e disponibilidade |
| Média | RF-08/10, RF-15, RN-06/07 | Padronização taxonômica/geográfica |
| Média | RF-25, RN-18 | Interoperabilidade com portais |
| Baixa | RF-19/20 | Apoio visual (imagens/etiquetas) |

## 4. Observações

- `models.py` é a fonte de verdade para atributos e restrições (UNIQUE, FK, JSONB)
- `endpoints/` é a fonte para casos de uso e regras de acesso (require_roles)
- `services/` concentra as regras de negócio (RN-11 geração de códigos, RN-14/15/16 ciclo de empréstimo)
