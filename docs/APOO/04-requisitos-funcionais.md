# Requisitos Funcionais

## 1. Convenções

- Identificador de requisito funcional: `RF-XX`
- Sempre que possível, cada requisito deve se ligar a um ou mais casos de uso
- Requisitos derivados diretamente do comportamento observado no código podem ser refinados na fase de casos de uso expandidos

## 2. Acesso e usuários

- `RF-01` O sistema deve permitir o cadastro de novos usuários com nome, email e senha (`usuarios_emprestimos.py:39`)
- `RF-02` O sistema deve registrar novos usuários com perfil padrão `leitor` (`models.py:PerfilUsuario`, `usuario_service.create`)
- `RF-03` O sistema deve permitir autenticação por JWT Bearer Token (`core/security.py:get_current_user`)
- `RF-04` O sistema deve impedir acesso autenticado a usuários sem perfil autorizado (`require_roles`)
- `RF-05` O sistema deve permitir a criação de usuários apenas por `administrador` (`usuarios_emprestimos.py:43`)
- `RF-06` O sistema deve permitir atualização de próprio perfil pelo usuário (`usuarios_emprestimos.py:65`, `UsuarioSelfUpdate`)
- `RF-07` O sistema deve impedir que não-admin altere perfil ou status de usuário (`usuarios_emprestimos.py:74`)

## 3. Taxonomia e Localidades

- `RF-08` O sistema deve permitir CRUD de Taxonomias por `administrador`/`curador` (`taxonomia_localidade.py:53`, `require_roles("administrador","curador")`)
- `RF-09` O sistema deve garantir `nome_cientifico` único e não nulo (`models.py:Taxonomia`, `UNIQUE`)
- `RF-10` O sistema deve permitir CRUD de Localidades Geográficas por `administrador`/`curador` (`taxonomia_localidade.py:129`)
- `RF-11` O sistema deve validar `latitude`/`longitude` como FLOAT e `datum_geodesico` padrão WGS84 (`models.py:LocalidadeGeografica`)

## 4. Espécimes

- `RF-12` O sistema deve permitir cadastro de Espécime com geração automática de `codigo_barras` (`SPEC-<uuid>`) e `dwc_record_id` (`urn:uuid:<uuid>`) (`especime_service.py:46-54`)
- `RF-13` O sistema deve exigir `taxonomia_id` (FK NOT NULL) em todo Espécime (`models.py:Especime`)
- `RF-14` O sistema deve permitir busca avançada por nome científico, família, gênero, estado, município, bioma (`especime_service.buscar`, `ilike`)
- `RF-15` O sistema deve permitir busca por caixa geográfica (bounding box: lat/lon min/max) (`especime_service.buscar:125-133`)
- `RF-16` O sistema deve permitir busca por coletor, status e intervalo de data de coleta (`especime_service.buscar:135-149`)
- `RF-17` O sistema deve permitir edição de Espécime apenas por `administrador`/`curador` (`especimes.py` + `require_roles`)
- `RF-18` O sistema deve impedir exclusão de Espécime com imagens associadas (ON DELETE CASCADE em `ImagemEspecime`)

## 5. Imagens e Etiquetas

- `RF-19` O sistema deve permitir upload de imagens (JPEG/PNG/TIFF/WebP até 20 MB) vinculadas ao Espécime (`imagem_service.py`)
- `RF-20` O sistema deve gerar etiqueta PDF com Code128 a partir do `codigo_barras` (`export_service.EtiquetaService`)

## 6. Empréstimos

- `RF-21` O sistema deve permitir criar Empréstimo de Espécime por `administrador`/`curador` (`usuarios_emprestimos.py:125`)
- `RF-22` O sistema deve impedir empréstimo de Espécime com `status != "ativo"` (`usuarios_emprestimos.py:134`)
- `RF-23` O sistema deve marcar `status = "emprestado"` no Espécime ao criar empréstimo (`usuarios_emprestimos.py:141`)
- `RF-24` O sistema deve marcar `status = "ativo"` no Espécime e `ativo = False` no Empréstimo ao retornar (`usuarios_emprestimos.py:162-166`)

## 7. Exportação

- `RF-25` O sistema deve exportar os dados em Darwin Core Archive (ZIP: `occurrence.csv` + `meta.xml` + `eml.xml`) (`export_service.ExportService`)

## 8. Rastreabilidade inicial com os casos de uso

O mapeamento detalhado entre requisitos funcionais e casos de uso será consolidado na fase seguinte, no catálogo e na matriz de rastreabilidade.

![Fluxo de Busca Avançada](docs/APOO/Diagrams/fluxo_busca.png)

