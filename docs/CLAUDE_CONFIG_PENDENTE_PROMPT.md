# Prompt para o Claude Code: configuracoes finais (Supabase + deploy)

Cole este prompt numa sessao do Claude Code que tenha acesso ao painel do
Supabase e ao GitHub deste repositorio. Todo o codigo e o banco ja estao
prontos; faltam apenas ajustes de credenciais/painel que nao dA para fazer por
codigo.

---

Voce e o Claude Code trabalhando no projeto **Biblia em Contexto**
(repo `Alusionbr/bibliaonline`, site `https://alusionbr.github.io/bibliaonline`,
projeto Supabase `pxqhpntifbtjaoqtirao`, regiao `sa-east-1`).

## Contexto (o que ja esta feito, nao refazer)

- Banco: schema colaborativo + gamificacao (tabelas `badges`, `daily_missions`,
  `user_badges`, `user_mission_progress`, `user_gamification`,
  `profiles.platform_role`, `is_platform_mod()`), com RLS. SQL versionado em
  `docs/supabase-gamification.sql`.
- Seguranca endurecida (`docs/supabase-security-hardening.sql`) e bug do
  `join_group` corrigido (`docs/supabase-fix-join-group.sql`).
- Front: login + sincronizacao, selo Beta, painel de Progresso e Salas de
  Estudo reais (`assets/community.js`). Deploy (`.github/workflows/deploy.yml`)
  ja gera `site/assets/supabase-config.js` a partir do secret
  `SUPABASE_PUBLISHABLE_KEY` (roda no push para `main`).

## Regras

- **Nunca** comitar `site/assets/supabase-config.js` real nem qualquer chave.
- **Nunca** usar a `service_role` key no frontend/site/logs.
- **Nao** ativar "leaked password protection" (decisao do dono: nao usar agora).
- Fazer mudancas pequenas e verificaveis; registrar o resultado.

## Tarefa 1 — Secret do GitHub (bloqueia o login em producao)

1. Pegue **apenas** a chave publishable/anon do projeto Supabase
   (Settings > API > Project API keys > `anon`/`publishable`). Nunca a
   `service_role`.
2. Em GitHub > repo `Alusionbr/bibliaonline` > Settings > Secrets and variables
   > Actions, crie/atualize o secret **`SUPABASE_PUBLISHABLE_KEY`** com esse
   valor. Confirme que existe sem revelar o valor.

## Tarefa 2 — Auth no painel Supabase

Em Authentication > URL Configuration:

1. **Site URL:** `https://alusionbr.github.io/bibliaonline`
2. **Redirect URLs** (adicionar todas):
   - `https://alusionbr.github.io/bibliaonline/**`
   - `http://localhost:8000/**`
   - `http://127.0.0.1:8000/**`

Em Authentication > Providers > Email:

3. Confirme que **Email/Password** esta habilitado.
4. Anote a politica de **confirmacao de email**: se estiver ligada, o fluxo
   esperado e "criar conta -> confirmar email -> entrar". Nao desligar em
   producao sem confirmar com o dono.

Em Authentication > Policies (ou Sign In / Providers > Password):

5. Defina **senha minima = 8**.
6. **NAO** habilitar leaked password protection (decisao do dono).
7. Nao habilitar CAPTCHA agora (evita travar os testes); anote como melhoria.

## Tarefa 3 — Definir o dono como administrador

Para o dono poder moderar salas e (futuramente) o painel de plataforma, promova
a conta dele. No SQL Editor do Supabase (ou via MCP), troque o email:

```sql
-- staff = admin de plataforma; platform_role deixa o papel legivel.
insert into public.staff (user_id)
select id from auth.users where email = 'EMAIL_DO_DONO' 
on conflict (user_id) do nothing;

update public.profiles
set platform_role = 'admin'
where id = (select id from auth.users where email = 'EMAIL_DO_DONO');
```

## Tarefa 4 — Publicar e validar

1. Garanta que o branch de trabalho
   (`claude/bible-platform-db-structure-osup2x`) foi revisado e **mergeado em
   `main`** (o deploy so roda no `main`). Se preferir, abra o Pull Request e
   peca revisao do dono antes do merge.
2. Apos o deploy do GitHub Pages concluir, abra
   `https://alusionbr.github.io/bibliaonline` e teste:
   - Criar conta / entrar. Confirmar que aparece o selo **Beta** na conta.
   - Em uma pagina de leitura, favoritar/anotar/grifar e abrir o Workspace:
     as **missoes de hoje** e as **medalhas** devem refletir a atividade.
   - Em Comunidade > Salas de Estudo: **criar uma sala**, copiar o codigo, e
     em outra conta **entrar por codigo**; como admin, **aprovar** o membro e
     confirmar que ele passa a ver as discussoes.
   - Sair e entrar de novo: o estudo e o progresso continuam (sincronizados).
3. Rode os advisors (Security e Performance) e registre o resultado. Os avisos
   restantes esperados sao os 4 helpers de RLS executaveis por `anon`
   (`is_staff`, `is_active_member`, `is_group_admin`, `is_group_mod`) — sao
   intencionais.

## Entregaveis

Responda com: (1) secret confirmado (sem valor), (2) settings de Auth aplicados,
(3) SQL de admin aplicado para qual email, (4) status do deploy, (5) resultado
do teste manual (conta/beta, missoes/medalhas, salas), (6) advisors depois,
(7) qualquer ponto em que parou para pedir decisao do dono.
