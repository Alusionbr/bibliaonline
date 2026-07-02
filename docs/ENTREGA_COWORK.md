# Entrega para o Claude Cowork — executar o que falta

> Como usar: envie este arquivo ao Cowork (ou cole o conteudo da secao
> **"PROMPT"** abaixo) numa sessao com os conectores **Supabase** e **GitHub**
> ativos no projeto `Alusionbr/bibliaonline`. Toda a parte de codigo/SQL ja
> esta embutida aqui — o Cowork so precisa executar.

---

## PROMPT (cole isto no Cowork)

Você é o **Claude Cowork** no projeto **Bíblia em Contexto**
(repo `Alusionbr/bibliaonline`, site `https://alusionbr.github.io/bibliaonline`,
projeto Supabase `pxqhpntifbtjaoqtirao`, região `sa-east-1`). Use os conectores
**Supabase** e **GitHub** para tudo que der; o que exigir o painel de Auth ou
segredo do GitHub, pare e entregue instruções claras ao dono.

**Contexto (já feito — não refazer):** gamificação + papéis + RLS aplicados;
segurança endurecida; bug do `join_group` corrigido; front com login/sync, selo
Beta, painel de Progresso e Salas de Estudo reais. O deploy
(`.github/workflows/deploy.yml`) gera o `supabase-config.js` a partir do secret
`SUPABASE_PUBLISHABLE_KEY` e roda no push para `main`. Trabalho no branch
`claude/bible-platform-db-structure-osup2x`.

**Regras:** nunca commitar chaves nem usar `service_role` no frontend. **Não**
ativar leaked password protection (decisão do dono). Mudanças pequenas e
verificáveis; registre o resultado de cada passo.

### Parte A — você executa via MCP

1. **Conferir o banco** (Supabase): rode a consulta do Anexo 1 (verificação).
   Confirme as tabelas de gamificação/comunidade, que `join_group` já tem a
   correção, e rode `get_advisors` (security e performance). Aviso esperado: 4
   helpers de RLS executáveis por `anon` (`is_staff`, `is_active_member`,
   `is_group_admin`, `is_group_mod`) — intencionais.
2. **Promover o dono a admin**: rode o Anexo 2, trocando `EMAIL_DO_DONO`. Se o
   email ainda não tiver conta, avise para criar a conta primeiro e rode depois.
3. **Abrir o Pull Request** do branch `claude/bible-platform-db-structure-osup2x`
   para `main` (título: "Plataforma de estudo: gamificação, Beta e Salas
   reais"), com um resumo. **Não** mergear sozinho — peça aprovação do dono (o
   deploy só roda após o merge em `main`).

### Parte B — entregar ao dono (painel/segredo)

Monte uma checklist curta para o dono:

1. **GitHub > Settings > Secrets and variables > Actions:** criar/confirmar o
   secret `SUPABASE_PUBLISHABLE_KEY` com a chave **publishable/anon** do Supabase
   (Settings > API). Nunca a `service_role`.
2. **Supabase > Authentication > URL Configuration:**
   - Site URL: `https://alusionbr.github.io/bibliaonline`
   - Redirect URLs: `https://alusionbr.github.io/bibliaonline/**`,
     `http://localhost:8000/**`, `http://127.0.0.1:8000/**`
3. **Authentication > Providers > Email:** Email/Password habilitado; anotar a
   política de confirmação de email.
4. **Senha mínima = 8.** Não ligar leaked password protection nem CAPTCHA agora.
5. Aprovar/mergear o PR em `main` para disparar o deploy.

### Parte C — validação após o deploy

Em `https://alusionbr.github.io/bibliaonline`:

- Criar conta/entrar → selo **Beta** aparece na conta.
- Favoritar/anotar/grifar numa página de leitura → no **Workspace**, missões do
  dia e medalhas refletem a atividade.
- **Comunidade > Salas:** criar sala, copiar o código; em outra conta entrar por
  código; como admin, aprovar o membro e ver que ele passa a ver as discussões.
- Sair e entrar de novo: estudo e progresso continuam sincronizados.
- Rodar `get_advisors` de novo e comparar.

### Responda com

(1) estado do banco + advisors antes/depois; (2) para qual email aplicou o
admin; (3) link do PR; (4) a checklist da Parte B pronta para copiar; (5)
resultado da validação; (6) onde parou pedindo decisão do dono.

---

## Anexo 1 — Verificação do banco (somente leitura)

```sql
-- Tabelas de gamificação e comunidade existem?
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in (
    'badges','daily_missions','user_badges','user_mission_progress',
    'user_gamification','groups','group_members','group_topics',
    'topic_posts','group_notes','group_plans','profiles','user_study_state')
order by table_name;

-- Catálogos populados?
select (select count(*) from public.badges) as badges,
       (select count(*) from public.daily_missions) as missions;

-- Correção do join_group aplicada? (deve conter "variable_conflict use_column")
select position('variable_conflict use_column' in pg_get_functiondef(p.oid)) > 0
       as join_group_corrigido
from pg_proc p join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public' and p.proname = 'join_group';

-- Papel de plataforma existe em profiles?
select column_name from information_schema.columns
where table_schema='public' and table_name='profiles' and column_name='platform_role';
```

## Anexo 2 — Promover o dono a administrador

```sql
-- Troque EMAIL_DO_DONO pelo email real da conta do dono.
insert into public.staff (user_id)
select id from auth.users where email = 'EMAIL_DO_DONO'
on conflict (user_id) do nothing;

update public.profiles
set platform_role = 'admin'
where id = (select id from auth.users where email = 'EMAIL_DO_DONO');

-- Conferir:
select p.id, u.email, p.platform_role,
       exists(select 1 from public.staff s where s.user_id = p.id) as is_staff
from public.profiles p join auth.users u on u.id = p.id
where u.email = 'EMAIL_DO_DONO';
```

## Anexo 3 — Teste ponta a ponta das Salas (opcional, reverte sozinho)

Valida criar sala → tópico → post → entrar por código → admin aprova → membro
ativo vê e responde. Troque os dois UUIDs por dois `profiles.id` reais. Não
persiste nada (a exceção final faz rollback do bloco).

```sql
do $$
declare
  ua uuid := 'UUID_USUARIO_A';
  ub uuid := 'UUID_USUARIO_B';
  gid uuid; code text; mid uuid; tid uuid; cnt int; joinstat text;
begin
  perform set_config('request.jwt.claims', json_build_object('sub', ua::text, 'role','authenticated')::text, true);
  perform set_config('role','authenticated', true);
  select g.id, g.invite_code into gid, code from public.create_group('Sala Teste E2E','Validacao') g;
  select public.create_topic(gid, 'Topico de teste', 'Corpo') into tid;
  perform public.add_post(tid, 'Resposta de A');

  perform set_config('request.jwt.claims', json_build_object('sub', ub::text, 'role','authenticated')::text, true);
  select status into joinstat from public.join_group(code);
  raise notice 'B entrou com status % (esperado pending)', joinstat;
  select count(*) into cnt from public.group_topics where group_id = gid;
  raise notice 'B pendente ve % topicos (esperado 0)', cnt;

  perform set_config('request.jwt.claims', json_build_object('sub', ua::text, 'role','authenticated')::text, true);
  select id into mid from public.group_members where group_id=gid and user_id=ub;
  perform public.decide_member(mid, true);

  perform set_config('request.jwt.claims', json_build_object('sub', ub::text, 'role','authenticated')::text, true);
  select count(*) into cnt from public.group_topics where group_id = gid;
  raise notice 'B ativo ve % topicos (esperado 1)', cnt;
  perform public.add_post(tid, 'Resposta de B');

  raise exception 'ROLLBACK_OK';
exception when others then
  if sqlerrm = 'ROLLBACK_OK' then raise notice 'E2E OK — nada persistido';
  else raise; end if;
end $$;
```

---

## Anexo 4 — SQL já aplicado (referência / reaplicar só se precisar)

> Estes blocos JÁ FORAM aplicados na base. Use apenas se precisar recriar em
> outro ambiente. São idempotentes/aditivos.

### 4.1 Gamificação, papéis e RLS

```sql
-- Papel de plataforma em profiles
alter table public.profiles
  add column if not exists platform_role text not null default 'user'
  check (platform_role in ('user','moderator','admin'));

create or replace function public.is_platform_mod()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.profiles p
    where p.id = (select auth.uid()) and p.platform_role in ('moderator','admin'))
  or exists (select 1 from public.staff s where s.user_id = (select auth.uid()));
$$;
revoke execute on function public.is_platform_mod() from public, anon;
grant execute on function public.is_platform_mod() to authenticated;

create table if not exists public.badges (
  key text primary key, title text not null, description text not null,
  icon text not null default '🏅',
  tier text not null default 'bronze' check (tier in ('bronze','prata','ouro')),
  points int not null default 10, sort int not null default 0);
create table if not exists public.user_badges (
  user_id uuid not null references auth.users(id) on delete cascade,
  badge_key text not null references public.badges(key) on delete cascade,
  earned_at timestamptz not null default now(), primary key (user_id, badge_key));
create index if not exists user_badges_user_id_idx on public.user_badges(user_id);
create table if not exists public.daily_missions (
  key text primary key, title text not null, description text not null,
  icon text not null default '📖', goal int not null default 1, metric text not null,
  points int not null default 10, active boolean not null default true, sort int not null default 0);
create table if not exists public.user_mission_progress (
  user_id uuid not null references auth.users(id) on delete cascade,
  mission_key text not null references public.daily_missions(key) on delete cascade,
  day date not null default current_date, progress int not null default 0,
  completed boolean not null default false, updated_at timestamptz not null default now(),
  primary key (user_id, mission_key, day));
create index if not exists user_mission_progress_user_day_idx on public.user_mission_progress(user_id, day);
create table if not exists public.user_gamification (
  user_id uuid primary key references auth.users(id) on delete cascade,
  xp int not null default 0, level int not null default 1, streak int not null default 0,
  longest_streak int not null default 0, last_active date, updated_at timestamptz not null default now());

alter table public.badges enable row level security;
alter table public.daily_missions enable row level security;
alter table public.user_badges enable row level security;
alter table public.user_mission_progress enable row level security;
alter table public.user_gamification enable row level security;

drop policy if exists badges_select on public.badges;
create policy badges_select on public.badges for select using (true);
drop policy if exists badges_write on public.badges;
create policy badges_write on public.badges for all using (public.is_platform_mod()) with check (public.is_platform_mod());
drop policy if exists missions_select on public.daily_missions;
create policy missions_select on public.daily_missions for select using (true);
drop policy if exists missions_write on public.daily_missions;
create policy missions_write on public.daily_missions for all using (public.is_platform_mod()) with check (public.is_platform_mod());

drop policy if exists user_badges_select_own on public.user_badges;
create policy user_badges_select_own on public.user_badges for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists user_badges_insert_own on public.user_badges;
create policy user_badges_insert_own on public.user_badges for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists user_badges_delete_own on public.user_badges;
create policy user_badges_delete_own on public.user_badges for delete to authenticated using ((select auth.uid()) = user_id);
drop policy if exists ump_select_own on public.user_mission_progress;
create policy ump_select_own on public.user_mission_progress for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists ump_insert_own on public.user_mission_progress;
create policy ump_insert_own on public.user_mission_progress for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists ump_update_own on public.user_mission_progress;
create policy ump_update_own on public.user_mission_progress for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists ump_delete_own on public.user_mission_progress;
create policy ump_delete_own on public.user_mission_progress for delete to authenticated using ((select auth.uid()) = user_id);
drop policy if exists ug_select_own on public.user_gamification;
create policy ug_select_own on public.user_gamification for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists ug_insert_own on public.user_gamification;
create policy ug_insert_own on public.user_gamification for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists ug_update_own on public.user_gamification;
create policy ug_update_own on public.user_gamification for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

revoke all on public.badges from public, anon, authenticated;
revoke all on public.daily_missions from public, anon, authenticated;
grant select on public.badges to anon, authenticated;
grant select on public.daily_missions to anon, authenticated;
grant insert, update, delete on public.badges to authenticated;
grant insert, update, delete on public.daily_missions to authenticated;
revoke all on public.user_badges from public, anon, authenticated;
revoke all on public.user_mission_progress from public, anon, authenticated;
revoke all on public.user_gamification from public, anon, authenticated;
grant select, insert, delete on public.user_badges to authenticated;
grant select, insert, update, delete on public.user_mission_progress to authenticated;
grant select, insert, update, delete on public.user_gamification to authenticated;

insert into public.badges (key, title, description, icon, tier, points, sort) values
  ('primeiro_passo','Primeiro Passo','Criou a conta e comecou a jornada de estudo.','🌱','bronze',10,1),
  ('primeira_nota','Escriba','Escreveu a primeira anotacao.','✍️','bronze',15,2),
  ('primeiro_favorito','Tesouro','Guardou o primeiro versiculo favorito.','⭐','bronze',15,3),
  ('primeiro_grifo','Iluminador','Grifou a primeira passagem.','🖍️','bronze',15,4),
  ('leitor_10','Leitor','Leu 10 capitulos.','📖','bronze',20,5),
  ('leitor_50','Estudioso','Leu 50 capitulos.','📚','prata',40,6),
  ('streak_3','Constante','Estudou 3 dias seguidos.','🔥','bronze',20,7),
  ('streak_7','Semana Fiel','Estudou 7 dias seguidos.','🔥','prata',40,8),
  ('streak_30','Devoto','Estudou 30 dias seguidos.','🔥','ouro',100,9),
  ('missoes_7','Peregrino','Completou 7 missoes diarias.','🎯','prata',40,10),
  ('comunidade','Companheiro','Entrou em uma sala de estudo da comunidade.','🤝','bronze',20,11)
on conflict (key) do update set title=excluded.title, description=excluded.description,
  icon=excluded.icon, tier=excluded.tier, points=excluded.points, sort=excluded.sort;

insert into public.daily_missions (key, title, description, icon, goal, metric, points, sort) values
  ('ler_capitulo','Leia um capitulo','Abra e leia ao menos um capitulo hoje.','📖',1,'read_chapters',10,1),
  ('meditar','Medite no versiculo','Abra o versiculo para meditar hoje.','🕊️',1,'meditate',10,2),
  ('anotar','Faca uma anotacao','Registre um aprendizado em uma anotacao.','✍️',1,'notes',10,3),
  ('favoritar','Guarde um versiculo','Marque um versiculo como favorito.','⭐',1,'favorites',10,4),
  ('grifar','Grife uma passagem','Destaque uma passagem com o marca-texto.','🖍️',1,'highlights',10,5)
on conflict (key) do update set title=excluded.title, description=excluded.description,
  icon=excluded.icon, goal=excluded.goal, metric=excluded.metric, points=excluded.points, sort=excluded.sort;
```

### 4.2 Endurecimento de segurança (não-destrutivo)

```sql
revoke execute on function public.handle_new_user() from public, anon, authenticated;
revoke execute on function public.feed_on_note() from public, anon, authenticated;
revoke execute on function public.feed_on_topic() from public, anon, authenticated;
revoke execute on function public.rl_guard() from public, anon, authenticated;
revoke execute on function public.log_audit(text, text, uuid, jsonb) from public, anon, authenticated;
revoke execute on function public.save_profile(text, integer, text, text) from anon, public;
revoke execute on function public.create_group(text, text) from anon, public;
revoke execute on function public.join_group(text) from anon, public;
revoke execute on function public.create_topic(uuid, text, text) from anon, public;
revoke execute on function public.add_post(uuid, text) from anon, public;
revoke execute on function public.decide_member(uuid, boolean) from anon, public;
revoke execute on function public.delete_post(uuid) from anon, public;
revoke execute on function public.moderate_topic(uuid, boolean, boolean, boolean) from anon, public;
revoke execute on function public.remove_member(uuid) from anon, public;
revoke execute on function public.review_suggestion(uuid, text) from anon, public;
revoke execute on function public.set_member_role(uuid, text) from anon, public;
revoke execute on function public.submit_suggestion(text, text, text, text) from anon, public;
revoke execute on function public.group_brief(text) from anon, public;
```

### 4.3 Correção do bug do `join_group`

```sql
CREATE OR REPLACE FUNCTION public.join_group(p_code text)
 RETURNS TABLE(group_id uuid, name text, status text)
 LANGUAGE plpgsql SECURITY DEFINER SET search_path TO 'public'
AS $function$
#variable_conflict use_column
declare g_id uuid; g_nm text;
begin
  if auth.uid() is null then raise exception 'Não autenticado'; end if;
  select id, groups.name into g_id, g_nm from groups where invite_code = lower(trim(p_code));
  if g_id is null then raise exception 'Grupo não encontrado'; end if;
  insert into group_members(group_id, user_id, role, status)
  values (g_id, auth.uid(), 'member', 'pending')
  on conflict (group_id, user_id) do nothing;
  return query select gm.group_id, g_nm, gm.status from group_members gm
    where gm.group_id = g_id and gm.user_id = auth.uid();
end; $function$;
revoke execute on function public.join_group(text) from anon, public;
```
