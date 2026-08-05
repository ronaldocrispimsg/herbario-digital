# Sumário Executivo

## 1. Apresentação

O **BioAcervo** é uma API RESTful de Gestão de Acervo Biológico (herbário digital), construída com **FastAPI** e **PostgreSQL** (acesso via SQLAlchemy ORM assíncrono). Sua proposta é registrar, catalogar, identificar taxonômicamente, georreferenciar e disponibilizar espécimes biológicos, além de controlar seu empréstimo entre instituições e exportar os dados no padrão **Darwin Core Archive (DwC-A)** para portais de biodiversidade (GBIF, iDigBio, SpeciesLink).

O sistema combina cadastro de espécimes, classificação taxonômica, geolocalização, imagens, controle de acesso por perfil e exportação padronizada. Seu objetivo principal é dar rastreabilidade, padronização (DwC) e continuidade ao acervo do herbário.

## 2. Problema que o sistema busca resolver

O contexto identificado no repositório indica a necessidade de resolver, ao mesmo tempo, problemas de organização e de padronização:
- dispersão do acervo em planilhas e registros manuais de coleta
- falta de padronização taxonômica e geográfica entre coletores
- dificuldade de rastrear procedência, status e localização física de cada espécime
- ausência de controle de empréstimo entre instituições
- impedimento de integração com portais de biodiversidade por falta de exportação DwC-A

## 3. Objetivos do sistema

Os objetivos centrais do BioAcervo são:
- centralizar o acervo biológico em uma única plataforma
- catalogar espécimes com código de catálogo e código de barras únicos
- identificar taxonomicamente cada espécime (taxonomia + sinônimos)
- georreferenciar a coleta (latitude, longitude, altitude, datum, precisão)
- registrar imagens do espécime (JPEG/PNG/TIFF/WebP até 20 MB)
- controlar empréstimo de espécimes com marcão de status
- exportar os dados em DwC-A (occurrence.csv + meta.xml + eml.xml)

De forma mais específica, o sistema busca:
- apoiar a curadoria do acervo (cadastro, edição, baixa)
- oferecer busca avançada por critérios taxonômicos, geográficos, temporais e bounding box
- gerar etiqueta PDF com Code128
- garantir conformidade com Darwin Core para portais externos

## 4. Público-alvo

Os perfis de usuário identificados no sistema (enum `PerfilUsuario`) são:
- **Curador**: cadastra e edita espécimes, taxonomias, localidades e empréstimos
- **Administrador**: acesso total, inclusive gestão de usuários e remoção definitiva de registros
- **Leitor**: acesso somente leitura (consulta do acervo)

Instituições de pesquisa são destinatárias de empréstimos de espécimes.

## 5. Capacidades de negócio suportadas

O sistema suporta, em nível executivo, os seguintes grupos de capacidade:
- cadastro, autenticação e gestão de usuários por perfil
- CRUD completo de Espécimes, Taxonomias, Localidades Geográficas e Imagens
- controle de Empréstimos (saída, retorno, status)
- georreferenciamento e busca por caixa geográfica (bounding box)
- upload e associação de imagens ao espécime
- geração de etiqueta PDF com código de barras
- exportação DwC-A (ZIP com occurrence.csv, meta.xml, eml.xml)

Essas capacidades atendem a uma proposta de centralização e padronização do acervo, com foco em conformidade Darwin Core.

## 6. Benefícios esperados

Os principais benefícios esperados com a utilização do sistema são:
- maior rastreabilidade sobre procedência e status de cada espécime
- padronização taxonômica e geográfica (DwC)
- histórico consistente de empréstimos
- integração com portais de biodiversidade (GBIF, iDigBio, SpeciesLink)
- melhor onboarding de novos curadores

## 7. Visão geral da solução

Do ponto de vista tecnológico, o sistema foi implementado como uma API web (FastAPI) com persistência relacional (PostgreSQL via SQLAlchemy assíncrono). A solução adota:
- interface web/API para uso cotidiano (endpoints REST)
- backend modular por domínio (services) + camada de API (endpoints)
- banco relacional PostgreSQL com esquema em `models.py`
- controle de autenticação e autorização via JWT Bearer Token

## 8. Premissas e restrições iniciais

No contexto atual do projeto, foram informadas as seguintes premissas:
- o sistema opera com perfis de acesso (leitor, curador, administrador) definidos em `PerfilUsuario`
- a exportação DwC-A é a via de integração com portais externos
- imagens são armazenadas em bucket local (volume Docker)

Essas premissas devem ser levadas em conta ao interpretar os requisitos não funcionais e as decisões arquiteturais registradas nos demais documentos.

## 9. Limites desta versão do sumário

Este sumário executivo foi produzido a partir da base de código e da documentação técnica existente. Portanto, ele descreve com segurança:
- o que o sistema faz
- quem aparenta usar o sistema
- quais processos são suportados
- quais preocupações arquiteturais e operacionais estão presentes

Permanecem como pontos que podem ser refinados em versões futuras:
- detalhamento de requisitos de privacidade e conformidade ligados à LGPD
- endurecimento de segurança para ambiente além da rede local
- definição de indicadores formais de sucesso e adoção
- eventual mapeamento de processos externos ou integrações futuras
