#!/bin/bash
set -euo pipefail

echo "🛡️ Backup antes das correções..."
git status
git branch "backup-antes-correcoes-$(date +%Y%m%d-%H%M%S)"

echo "🤖 Rodando Codex com instruções detalhadas..."

codex exec --cd . '
Você está trabalhando no projeto herbario-digital.

OBJETIVO:
Corrigir os problemas encontrados na auditoria, alterando arquivos com cuidado, sem apagar dados e sem quebrar funcionalidades existentes.

REGRAS OBRIGATÓRIAS:
1. NÃO faça git commit.
2. NÃO faça git push.
3. NÃO apague banco, volumes, imagens ou dados do usuário.
4. NÃO rode comandos destrutivos como rm -rf em diretórios de dados.
5. NÃO altere credenciais reais.
6. Preserve compatibilidade com Docker Compose.
7. Faça mudanças pequenas e coerentes.
8. Após cada área corrigida, verifique sintaxe quando possível.
9. Se algo for incerto, deixe comentário TODO seguro em vez de inventar solução perigosa.
10. No final, gere resumo com arquivos alterados e motivo.

CONTEXTO DA AUDITORIA:
Foram encontrados problemas em:
- Alembic/migrations quase inexistentes.
- Uso perigoso de Base.metadata.create_all em produção.
- Alembic com URL fixa.
- Risco de XSS no frontend por uso de innerHTML.
- Upload aceitando MIME informado pelo cliente.
- Upload não rejeitando imagem inválida obrigatoriamente.
- CORS aberto demais.
- UID/permissões de volumes Docker.
- Admin padrão com senha conhecida.
- Leitor podendo acessar exportações amplas.
- Imagens públicas em /uploads.
- Usuário comum podendo alterar campos indevidos no próprio cadastro.
- Endpoint de exportação possivelmente sem Body correto.
- Imports e código morto.
- Erros engolidos silenciosamente no frontend.
- Latitude/longitude 0 tratados como falsy.
- Falta de testes de autorização e upload.

TAREFAS DETALHADAS:

1. ALEMBIC E BANCO
- Verifique backend/alembic.ini, backend/alembic/env.py e models.
- Configure Alembic para usar DATABASE_URL do ambiente/.env.
- Evite URL fixa usuario:senha@localhost.
- Se não existir diretório backend/alembic/versions, crie.
- Crie migration inicial coerente com os models atuais, sem apagar dados existentes.
- Não execute downgrade.
- Não drope tabelas.
- Se o projeto ainda precisar de create_all em desenvolvimento, limite isso de forma segura e documentada.
- Em produção, não depender de Base.metadata.create_all.

2. SEED E ADMIN PADRÃO
- Remova ou reduza risco de senha padrão conhecida.
- Preferir ADMIN_EMAIL e ADMIN_PASSWORD vindos de variável de ambiente.
- Se ADMIN_PASSWORD não existir, não criar admin com senha fraca em produção.
- Mantenha desenvolvimento funcional, mas com aviso claro.

3. XSS NO FRONTEND
- Procure usos de innerHTML em frontend/app.js.
- Onde houver dados vindos da API/banco/usuário, não inserir direto com innerHTML.
- Substitua por textContent, createElement ou função escapeHTML segura.
- Se precisar manter template string, escape todos os campos dinâmicos.
- Atenção especial a espécimes, detalhes, taxonomias, localidades, usuários e mensagens.
- Não quebrar layout nem botões.

4. UPLOAD DE IMAGENS
- Em backend/app/services/imagem_service.py:
  - Não confiar somente em file.content_type.
  - Validar conteúdo real com PIL.
  - Se PIL falhar, rejeitar upload com erro HTTP adequado.
  - Normalizar formato/extensão quando possível.
  - Limitar tamanho e dimensões se já houver configuração.
  - Evitar salvar arquivo inválido em /uploads.
  - Remover metadados perigosos se possível.
- Garantir que somente imagens reais sejam aceitas.

5. CORS
- Em backend/app/main.py/config:
  - Não usar allow_origins=["*"] com credenciais em produção.
  - Ler origens permitidas de variável de ambiente, exemplo CORS_ORIGINS.
  - Manter localhost funcional para desenvolvimento.
  - Documentar exemplo no .env.example se existir.

6. PERMISSÕES
- Revisar backend das rotas de:
  - espécimes
  - taxonomia
  - localidades
  - usuários
  - empréstimos
  - exportações
- Garantir que leitor não consegue criar, editar ou deletar.
- Garantir que permissões não dependem só do frontend.
- Se leitor puder exportar, avaliar e restringir campos sensíveis, especialmente coordenadas/localização.
- Usuário comum não pode alterar perfil, ativo ou permissões.
- Usuário comum só pode alterar dados próprios permitidos.

7. EXPORTAÇÃO DWC-A
- Corrigir endpoint se precisar usar Body para ids.
- Evitar comportamento ambíguo com Optional[List[int]].
- Garantir que permissões sejam checadas antes da exportação.
- Não expor dados sensíveis para leitor se isso contrariar o modelo de permissão.

8. /UPLOADS PÚBLICO
- Verificar se imagens precisam ser públicas.
- Se não houver regra clara, pelo menos documentar risco.
- Não bloquear funcionalidade sem entender fluxo.
- Se simples, adicionar validação/autorização para acesso privado.
- Se complexo, deixar TODO e proteger upload na origem.

9. FRONTEND PERMISSÕES E ERROS
- Frontend pode esconder botões, mas backend deve proteger.
- Melhorar mensagens de erro onde hoje erro é engolido silenciosamente.
- loadSelectsForEmprestimo não deve falhar sem log/mensagem.
- Corrigir latitude/longitude 0 usando checagem != null em vez de truthy.

10. LIMPEZA
- Remover imports não usados.
- Remover variáveis mortas.
- Não fazer refatoração gigante desnecessária.

11. TESTES
- Se existir pytest, adicionar testes mínimos para:
  - leitor não cria/edita/deleta espécime
  - leitor não edita taxonomia/localidade
  - usuário comum não altera ativo/perfil
  - upload rejeita arquivo não imagem
  - exportação respeita permissão
- Se não existir estrutura de testes, crie testes simples sem quebrar o projeto.

VALIDAÇÕES A RODAR:
- python3 -m compileall -q backend
- node --check frontend/app.js
- docker compose config --quiet
- Se possível: pytest
- Se possível: alembic check
- Se possível: alembic revision --autogenerate -m "check_schema" apenas para verificar, sem manter migration temporária se for lixo.

SAÍDA FINAL:
No final, responda com:
1. Arquivos alterados.
2. O que foi corrigido em cada arquivo.
3. O que não foi possível corrigir automaticamente.
4. Comandos que o usuário deve rodar.
5. Riscos restantes.
'

echo "🧪 Validações básicas..."

python3 -m compileall -q backend
node --check frontend/app.js
docker compose config --quiet

echo "✅ Validações básicas passaram."

echo "📌 Status:"
git status --short

echo ""
echo "Agora revise:"
echo "git diff"
echo ""
echo "Depois teste com:"
echo "docker compose up -d --build"
echo "docker compose logs backend --tail=100"
echo ""
echo "Se estiver tudo certo:"
echo "git add ."
echo "git commit -m \"Corrige segurança, permissões, uploads, migrations e frontend\""
echo "git push origin dev"
