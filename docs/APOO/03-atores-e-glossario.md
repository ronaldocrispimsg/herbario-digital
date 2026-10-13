# Atores e Glossário

## 1. Atores do sistema

| Ator | Perfil (`PerfilUsuario`) | Responsabilidade |
|---|---|---|
| Curador | `curador` | Cadastra e edita espécimes, taxonomias, localidades e empréstimos |
| Administrador | `administrador` | Acesso total, gestão de usuários e remoção definitiva de registros |
| Leitor | `leitor` | Apenas consulta o acervo (somente leitura) |
| Instituição de pesquisa | externa | Destinatária de empréstimos de espécimes |

## 2. Glossário

| Termo | Definição |
|---|---|
| Espécime | Indivíduo biológico coletado, catalogado e georreferenciado |
| Taxonomia | Classificação científica (reino → espécie) de um espécime |
| Localidade Geográfica | Ponto de coleta (país, estado, município, lat/long, altitude, datum) |
| Código de Catálogo | Identificador único do espécime no acervo (ex.: `A11.1`) |
| Código de Barras | Identificador `SPEC-<uuid>` para etiquetas físicas |
| DwC Record ID | URN `urn:uuid:<uuid>` no padrão Darwin Core |
| Darwin Core Archive (DwC-A) | Pacote ZIP com `occurrence.csv`, `meta.xml`, `eml.xml` para GBIF/iDigBio/SpeciesLink |
| Empréstimo | Saída temporária de espécime para instituição externa |
| Status do Espécime | `ativo` \| `emprestado` (enum `StatusEspecime`) |
| Tipo de Coleta | `campo` \| `cultivo` \| `aves` \| `mamuídeo` (enum `TipoColeta`) |
| Bucket Local | Volume Docker para armazenamento de imagens |
| JWT Bearer Token | Mecanismo de autenticação via `Authorization: Bearer <token>` |
