# Prompt para o Claude Cowork: configuracoes finais

Cole este prompt numa sessao do **Claude Cowork** com os conectores **Supabase**
e **GitHub** ativos no projeto `Alusionbr/bibliaonline`. Todo o codigo e o banco
ja estao prontos; aqui o Cowork executa o que da via MCP e te entrega, no fim,
so a lista curta do que voce precisa clicar no painel (segredo do GitHub e Auth).

---

Voce e o **Claude Cowork** no projeto **Biblia em Contexto**
(repo `Alusionbr/bibliaonline`, site `https://alusionbr.github.io/bibliaonline`,
projeto Supabase `pxqhpntifbtjaoqtirao`, regiao `sa-east-1`). Use os conectores
Supabase e GitHub para tudo que for possivel; para o que exigir o painel do
Supabase Auth ou segredo do GitHub, pare e entregue instrucoes claras ao dono.

## Contexto (ja feito — nao refazer)

- Gamificacao + papeis + RLS aplicados (`docs/supabase-gamification.sql`).
- Seguranca endurecida (`docs/supabase-security-hardening.sql`) e bug do
  `join_group` corrigido (`docs/supabase-fix-join-group.sql`).
- Front: login/sync, selo Beta, painel de Progresso e Salas de Estudo reais
  (`assets/community.js`). O deploy (`.github/workflows/deploy.yml`) gera
  `site/assets/supabase-config.js` a partir do secret `SUPABASE_PUBLISHABLE_KEY`
  e roda no push para `main`.
- Trabalho no branch `claude/bible-platform-db-structure-osup2x`.

## Regras

- Nunca comitar `supabase-config.js` real nem chaves; nunca usar `service_role`
  no frontend. **Nao** ativar leaked password protection (decisao do dono).
- Mudancas pequenas e verificaveis; registre o resultado de cada passo.

## Parte A — O Cowork executa via MCP

1. **Verificar o banco** (Supabase MCP):
   - `list_tables` confirmando as tabelas de gamificacao e comunidade.
   - Confirmar que `public.join_group` tem `#variable_conflict use_column`
     (a correcao do bug) com uma consulta a `pg_get_functiondef`.
   - Rodar `get_advisors` (security e performance) e salvar o resultado. Aviso
     esperado: 4 helpers de RLS executaveis por `anon` (`is_staff`,
     `is_active_member`, `is_group_admin`, `is_group_mod`) — intencionais.

2. **Promover o dono a administrador** (Supabase MCP `execute_sql`), trocando o
   email:
   ```sql
   insert into public.staff (user_id)
   select id from auth.users where email = 'EMAIL_DO_DONO'
   on conflict (user_id) do nothing;

   update public.profiles set platform_role = 'admin'
   where id = (select id from auth.users where email = 'EMAIL_DO_DONO');
   ```
   Se o email ainda nao tiver conta, avise o dono para criar a conta primeiro e
   rode depois.

3. **Abrir o Pull Request** do branch para `main` (GitHub MCP
   `create_pull_request`), titulo tipo "Plataforma de estudo: gamificacao,
   Beta e Salas reais", com um resumo do que muda. **Nao** mergear sozinho:
   peca revisao/aprovacao do dono (o deploy so roda apos o merge em `main`).

## Parte B — Entregar ao dono (painel/segredo, o Cowork nao faz)

Monte uma checklist curta e objetiva para o dono executar:

1. **GitHub > Settings > Secrets and variables > Actions:** criar/confirmar o
   secret `SUPABASE_PUBLISHABLE_KEY` com a chave **publishable/anon** do Supabase
   (Settings > API). Nunca a `service_role`.
2. **Supabase > Authentication > URL Configuration:**
   - Site URL: `https://alusionbr.github.io/bibliaonline`
   - Redirect URLs: `https://alusionbr.github.io/bibliaonline/**`,
     `http://localhost:8000/**`, `http://127.0.0.1:8000/**`
3. **Supabase > Authentication > Providers > Email:** Email/Password habilitado;
   anotar a politica de confirmacao de email.
4. **Senha minima = 8.** Nao ligar leaked password protection nem CAPTCHA agora.
5. Aprovar/mergear o PR em `main` para disparar o deploy.

## Parte C — Validacao apos o deploy

Quando o dono confirmar o merge e o deploy, oriente (ou valide o que der) o
teste em `https://alusionbr.github.io/bibliaonline`:

- Criar conta/entrar -> selo **Beta** aparece na conta.
- Favoritar/anotar/grifar numa pagina de leitura -> no **Workspace**, missoes do
  dia e medalhas refletem a atividade.
- **Comunidade > Salas:** criar sala, copiar codigo; em outra conta entrar por
  codigo; como admin, aprovar o membro e ver que ele passa a ver as discussoes.
- Sair e entrar de novo: estudo e progresso continuam sincronizados.
- Rodar `get_advisors` de novo e comparar.

## Entregaveis (responda assim)

1. Estado do banco e advisors (antes/depois).
2. SQL de admin aplicado para qual email.
3. Link do PR aberto.
4. Checklist do que ficou para o dono (Parte B), pronta para copiar.
5. Resultado da validacao (Parte C), quando possivel.
6. Pontos em que parou para decisao do dono.
