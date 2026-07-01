# Prompt para Claude cowork: configuracao e auditoria Supabase

Voce e o Claude cowork trabalhando no projeto Biblia Online. Sua tarefa e terminar a configuracao Supabase e corrigir os pontos pendentes de seguranca/performance sem causar conflito com o site ou com funcionalidades colaborativas existentes.

## Contexto do projeto

- Supabase project: `bibliaonline`
- Project ref: `pxqhpntifbtjaoqtirao`
- Regiao: `sa-east-1`
- Site em producao: `https://alusionbr.github.io/bibliaonline`
- Teste local: `http://localhost:8000`
- Repositorio local usado pelo Codex: `C:\Users\Beto\Downloads\biblia`
- O frontend ja foi integrado com Supabase Auth e sincronizacao de estudo.
- O deploy GitHub Pages espera gerar `site/assets/supabase-config.js` a partir do secret GitHub `SUPABASE_PUBLISHABLE_KEY`.
- Nunca commitar `site/assets/supabase-config.js` real nem qualquer secret.

## Regra principal

Faca mudancas pequenas, verificaveis e reversiveis. Antes de alterar funcoes, politicas, grants ou Auth settings, capture o estado atual. Depois de cada bloco, rode verificacao e registre o resultado.

Pare e pergunte ao Beto antes de:

- Fazer upgrade pago ou ativar recurso pago.
- Desativar confirmacao de email em ambiente de producao.
- Dropar, recriar ou substituir tabelas/funcoes existentes.
- Alterar semantica de grupos, comunidade, moderacao, sugestoes ou feed.
- Tornar anonimo qualquer acesso a tabela, RPC ou funcao que hoje nao seja claramente publica.
- Usar, expor ou salvar `service_role` key em repo, site, logs publicos ou GitHub Pages.

## Fontes oficiais obrigatorias antes de executar

Antes de aplicar mudancas, confira a documentacao/changelog atual da Supabase, especialmente:

- Auth com email/senha e redirect URLs: https://supabase.com/docs/guides/auth/passwords
- Password security/leaked password protection: https://supabase.com/docs/guides/auth/password-security
- RLS e politicas: https://supabase.com/docs/guides/database/postgres/row-level-security
- Database linter/advisors: https://supabase.com/docs/guides/database/database-linter

Rode tambem os advisors do projeto:

- Security advisor
- Performance advisor

Salve no relatorio os achados antes e depois.

## Objetivo 1: Auth e chaves

No painel Supabase/Auth:

1. Confirmar que o provider Email/Password esta habilitado.
2. Configurar Site URL:
   - `https://alusionbr.github.io/bibliaonline`
3. Configurar Redirect URLs permitidas:
   - `https://alusionbr.github.io/bibliaonline/**`
   - `http://localhost:8000/**`
   - `http://127.0.0.1:8000/**`
4. Confirmar a politica de confirmacao de email:
   - Se estiver habilitada, documente o fluxo esperado para os testes.
   - Nao desative em producao sem confirmar com Beto.
5. Ativar leaked password protection se disponivel no plano atual.
6. Definir senha minima de pelo menos 8 caracteres.
7. Nao habilitar CAPTCHA se as chaves ainda nao existirem, para nao bloquear os testes. Documente como melhoria posterior.

No GitHub:

1. Obter somente a publishable/anon key do projeto Supabase.
2. Criar ou confirmar o secret `SUPABASE_PUBLISHABLE_KEY`.
3. Nunca usar `service_role` key no frontend.
4. Confirmar que o workflow de deploy escreve `site/assets/supabase-config.js` no build, sem commitar esse arquivo.

## Objetivo 2: validar `public.user_study_state`

Confirmar que existe a tabela:

- `public.user_study_state`
- `user_id uuid primary key references auth.users(id) on delete cascade`
- colunas JSONB para notas, favoritos, destaques e preferencias
- timestamps
- RLS habilitado

Confirmar grants:

- `authenticated`: `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- `anon`: sem acesso
- `public`: sem acesso direto

Confirmar politicas:

- usuario autenticado le apenas a propria linha
- usuario autenticado insere apenas propria linha
- usuario autenticado atualiza apenas propria linha
- usuario autenticado remove apenas propria linha
- usar `(select auth.uid()) = user_id` nas expressoes

SQL de verificacao:

```sql
select grantee, privilege_type
from information_schema.role_table_grants
where table_schema = 'public'
  and table_name = 'user_study_state'
order by grantee, privilege_type;

select policyname, roles, cmd, qual, with_check
from pg_policies
where schemaname = 'public'
  and tablename = 'user_study_state'
order by policyname;
```

Teste obrigatorio:

- usuario A cria/atualiza estado proprio
- usuario B nao consegue ler nem alterar o estado do usuario A
- anon nao consegue ler, inserir, atualizar nem deletar

## Objetivo 3: corrigir achados de seguranca sem quebrar RPCs

Os advisors anteriores apontaram problemas pre-existentes em funcoes `SECURITY DEFINER`, grants para `anon`/`authenticated` e `search_path` mutavel. Nao faca revogacao em massa sem entender cada funcao.

Primeiro inventarie:

```sql
select
  n.nspname as schema_name,
  p.proname as function_name,
  pg_get_function_identity_arguments(p.oid) as args,
  p.prosecdef as security_definer,
  p.proconfig as config
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.prosecdef
order by p.proname, args;

select routine_schema, routine_name, grantee, privilege_type
from information_schema.routine_privileges
where routine_schema = 'public'
order by routine_name, grantee;
```

Classifique antes de alterar:

1. Trigger-only functions, como possiveis `handle_new_user`, `feed_on_note`, `feed_on_topic`.
   - Nao devem ser chamadas via REST/RPC.
   - Revogar `EXECUTE` de `PUBLIC`, `anon` e `authenticated`, se isso nao quebrar triggers.
   - Definir `search_path` fixo.
2. Helpers usados por RLS, como possiveis `is_staff`, `is_active_member`, `is_group_admin`, `is_group_mod`.
   - Verificar dependencias em politicas antes de revogar.
   - Se revogar quebrar RLS, documentar e propor mover para schema privado em uma migracao separada.
3. RPCs de usuario, como possiveis `create_group`, `join_group`, `create_topic`, `add_post`, `save_profile`, `submit_suggestion`.
   - Devem ser chamaveis somente por `authenticated`, exceto se houver requisito publico documentado.
   - Revogar `anon` salvo quando a funcao for intencionalmente publica.
   - Validar `auth.uid()` dentro da funcao quando houver escrita ou leitura sensivel.
   - Considerar `SECURITY INVOKER` quando RLS puder proteger corretamente.

Para funcoes `SECURITY DEFINER` que permanecerem, usar `search_path` fixo e minimo. Preferir schema-qualificar objetos dentro da funcao. Exemplo de ajuste, adaptando por funcao:

```sql
alter function public.nome_da_funcao(argumentos)
set search_path = public, auth, extensions;
```

Nao use `auth.role()` em politicas novas. Prefira `TO authenticated`/`TO anon` e predicados de propriedade.

## Objetivo 4: corrigir achados de performance

Os advisors anteriores apontaram FKs sem indice e politicas RLS com helper reavaliado por linha.

Antes:

- Rode performance advisor.
- Liste indices existentes.
- Confira se cada indice ja nao existe com nome diferente.

Indices candidatos, se ainda faltarem:

```sql
create index if not exists activity_feed_group_id_idx on public.activity_feed(group_id);
create index if not exists activity_feed_user_id_idx on public.activity_feed(user_id);
create index if not exists group_members_user_id_idx on public.group_members(user_id);
create index if not exists group_notes_group_id_idx on public.group_notes(group_id);
create index if not exists group_notes_user_id_idx on public.group_notes(user_id);
create index if not exists group_plan_progress_user_id_idx on public.group_plan_progress(user_id);
create index if not exists group_plans_created_by_idx on public.group_plans(created_by);
create index if not exists group_plans_group_id_idx on public.group_plans(group_id);
create index if not exists group_topics_group_id_idx on public.group_topics(group_id);
create index if not exists group_topics_user_id_idx on public.group_topics(user_id);
create index if not exists groups_created_by_idx on public.groups(created_by);
create index if not exists note_comments_note_id_idx on public.note_comments(note_id);
create index if not exists note_comments_user_id_idx on public.note_comments(user_id);
create index if not exists suggestions_reviewed_by_idx on public.suggestions(reviewed_by);
create index if not exists suggestions_user_id_idx on public.suggestions(user_id);
create index if not exists topic_posts_topic_id_idx on public.topic_posts(topic_id);
create index if not exists topic_posts_user_id_idx on public.topic_posts(user_id);
```

Se usar `CREATE INDEX CONCURRENTLY`, lembre que nao pode rodar dentro de transacao. Se a ferramenta executar SQL em transacao e o projeto ainda estiver em beta/baixo trafego, use `create index if not exists` normal e documente.

Para RLS:

- Trocar chamadas diretas como `auth.uid() = user_id` por `(select auth.uid()) = user_id`.
- Trocar helpers diretos como `is_staff()` por `(select is_staff())` somente depois de confirmar a assinatura e efeito.
- Nao consolidar politicas permissivas multiplas no mesmo passo em que endurece funcoes, a menos que haja teste cobrindo o comportamento.

## Objetivo 5: smoke test ponta a ponta

Depois das configuracoes:

1. Rodar localmente:

```powershell
python -m http.server 8000 --directory site
```

2. Abrir `http://localhost:8000`.
3. Criar conta ou fazer login.
4. Criar favorito, nota e destaque.
5. Recarregar a pagina.
6. Sair e entrar novamente.
7. Confirmar que o estado sincroniza.
8. Testar que sem login o site continua funcionando localmente.
9. Conferir no deploy GitHub Pages que `site/assets/supabase-config.js` foi gerado pelo workflow.

## Entregaveis esperados

Ao terminar, responda com:

1. Configuracoes Auth aplicadas.
2. Confirmacao do GitHub secret `SUPABASE_PUBLISHABLE_KEY` sem revelar valor.
3. SQL aplicado, em blocos pequenos.
4. Advisors antes/depois.
5. Resultado dos testes de isolamento RLS.
6. Resultado do smoke test frontend.
7. Riscos que ficaram intencionalmente pendentes e motivo.
8. Qualquer ponto em que voce parou para pedir decisao do Beto.
