# Guia de Leitura da Documentação APOO

## Objetivo

Esta pasta concentra a documentação formal do sistema **BioAcervo** (Herbário Digital) no formato de Análise e Projeto Orientados a Objetos (Wazlawick), usado no IFNMG Campus Januária.

Ela foi estruturada para atender dois objetivos simultâneos:
- apoiar leitura acadêmica e de projeto
- facilitar onboarding e manutenção por novos desenvolvedores

## Ordem recomendada de leitura

1. `01-sumario-executivo.md`
2. `02-visao-geral-e-escopo.md`
3. `03-atores-e-glossario.md`
4. `04-requisitos-funcionais.md`
5. `05-requisitos-nao-funcionais.md`
6. `06-casos-de-uso-catalogo.md`
7. `07-casos-de-uso-expandidos.md`
8. `08-regras-de-negocio.md`
9. `09-maquinas-de-estado.md`
10. `10-analise-e-modelo-conceitual.md`
11. `11-projeto-arquitetural.md`
12. `12-padroes-de-projeto-e-diretrizes-de-extensao.md`
13. `13-rastreabilidade-e-priorizacao.md`

Depois da leitura funcional, seguir para os artefatos técnicos:

- `Architecture/00_Arquitetura.md` (visão em camadas C4)


- `Finals/APOO_Herbario_Digital.pdf` (documento consolidado)

## Escopo da documentação

Esta documentação não descreve cada função do código-fonte nem cada detalhe de interface.

Ela prioriza:
- processos suportados pelo sistema
- atores e responsabilidades
- requisitos
- casos de uso
- estados e regras relevantes
- arquitetura e manutenção futura

## Fontes de verdade usadas nesta etapa

- `backend/app/models/models.py`
- `backend/app/schemas/schemas.py`
- `backend/app/services/*.py`
- `backend/app/api/v1/endpoints/*.py`
- `backend/app/core/security.py`, `backend/app/core/config.py`
- `README.md`, `docker-compose.yml`

## Observação importante

O backend usa SQLAlchemy ORM assíncrono (asyncpg) e FastAPI. O modelo de dados em `models.py` é a fonte de verdade para atributos e restrições; os endpoints em `api/v1/endpoints/` são a fonte para casos de uso e regras de acesso.
