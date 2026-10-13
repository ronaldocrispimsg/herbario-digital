# Visão Geral e Escopo

## 1. Propósito deste documento

Este documento descreve a visão geral do **BioAcervo** e o escopo da documentação APOO. Ele serve como ponte entre o Sumário Executivo e os requisitos detalhados.

## 2. Visão geral do sistema

O BioAcervo é uma API de acervo biológico que centraliza:
- **Catalogação** de espécimes (código de catálogo + código de barras únicos)
- **Identificação taxonômica** (reino → espécie, com sinônimos)
- **Georreferenciamento** da coleta (lat/long, altitude, datum, precisão)
- **Imagens** do espécime (JPEG/PNG/TIFF/WebP até 20 MB)
- **Empréstimo** de espécimes entre instituições
- **Exportação Darwin Core Archive (DwC-A)** para GBIF/iDigBio/SpeciesLink

## 3. Fronteiras do sistema

| Dentro do escopo | Fora do escopo (versão atual) |
|---|---|
| CRUD de Espécimes, Taxonomias, Localidades | Interface web (frontend não documentado nesta APOO) |
| Autenticação JWT + RBAC por perfil | Federção de identidade externa |
| Busca avançada (taxonômica, geográfica, bounding box) | Análisefilogenética |
| Upload de imagens + etiqueta PDF Code128 | Curadoria de dados de terceiros |
| Empréstimo com mudança de status | Workflow de publicação científica |
| Export DwC-A (ZIP) | Integração direta com portais (push) |

## 4. Escopo da documentação

Esta APOO cobre:
- Requisitos funcionais (RF-01 a RF-20)
- Requisitos não-funcionais (RNF-01 a RNF-06)
- Casos de uso (UC-01 a UC-14)
- Regras de negócio (RN-01 a RN-12)
- Máquinas de estado ( Usuário, Espécime, Empréstimo)
- Modelo conceitual (entidades e associações)
- Projeto arquitetural (camadas C4)
- Rastreabilidade RF → UC → RN

## 5. Fontes de verdade

- `backend/app/models/models.py` — entidades e enums
- `backend/app/schemas/schemas.py` — DTOs Pydantic v2
- `backend/app/services/*.py` — lógica de negócio
- `backend/app/api/v1/endpoints/*.py` — exposição REST
- `backend/app/core/security.py` — JWT/RBAC
- `README.md`, `docker-compose.yml`
