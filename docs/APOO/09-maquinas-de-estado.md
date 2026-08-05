# Máquinas de Estado

## 1. Objetivo

Documentar os estados relevantes das entidades que possuem ciclo de vida controlado por regras de negócio.

## 2. Usuário (`PerfilUsuario` + `ativo`)

| Estado | Transição | Gatilho | Regra |
|---|---|---|---|
| criado | `leitor` (padrão) | admin cria | RN-01 |
| ativo | `ativo = True` | admin aprova | `require_roles("administrador")` |
| inativo | `ativo = False` | admin desativa | RN-04 |

## 3. Espécime (`StatusEspecime`)

| Estado | Significado | Transição | Regra |
|---|---|---|---|
| `ativo` | disponível no acervo | criação ou retorno | RN-16 |
| `emprestado` | fora para instituição | criação de empréstimo | RN-15 (exige status==ativo, RN-14) |
| retorno | `ativo` novamente | `data_retorno` informada | RN-16 |

## 4. Empréstimo (`ativo`)

| Estado | Significado | Transição | Regra |
|---|---|---|---|
| ativo | em andamento | POST /emprestimos | RN-15 |
| encerrado | devolvido | PUT com `data_retorno` | RN-16 (`ativo=False`) |

## 5. Observações

- O status do espécime é a fonte de verdade para disponibilidade de empréstimo (RN-14)
- Mudanças de status devem ser validadas no backend, não na UI
