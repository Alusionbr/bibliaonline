-- ============================================================================
-- Bíblia em Contexto — FASE 2: comunidade de estudos (papéis, discussões, beta)
-- ----------------------------------------------------------------------------
-- Rodar UMA vez no SQL Editor do Supabase (idempotente: pode rodar de novo sem
-- quebrar). NÃO recria os dados da Fase 1 — só adiciona colunas/tabelas/funções
-- e ENDURECE as policies de segurança.
--
-- Depois de rodar, adicione-se à Equipe (staff) com o seu user id:
--   insert into staff(user_id) values ('<SEU-AUTH-UID>') on conflict do nothing;
-- (pegue o uid em Authentication -> Users, ou rode:  select auth.uid();  logado)
--
-- Eixo de segurança: toda mutação sensível passa por função `security definer`
-- com checagem de quem chama; o cliente nunca insere papéis/aprovações direto.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 0) PROFILES — novas colunas do cadastro (idade, gênero, tipo, beta)
-- ----------------------------------------------------------------------------
alter table public.profiles add column if not exists age          int;
alter table public.profiles add column if not exists gender       text;
alter table public.profiles add column if not exists account_type text;
alter table public.profiles add column if not exists is_beta      boolean default true;

alter table public.profiles drop constraint if exists profiles_age_check;
alter table public.profiles add  constraint profiles_age_check
  check (age is null or (age >= 13 and age <= 120));
alter table public.profiles drop constraint if exists profiles_gender_check;
alter table public.profiles add  constraint profiles_gender_check
  check (gender is null or gender in ('m','f','prefiro_nao_dizer'));
alter table public.profiles drop constraint if exists profiles_type_check;
alter table public.profiles add  constraint profiles_type_check
  check (account_type is null or account_type in ('pastor','aluno'));

-- ----------------------------------------------------------------------------
-- 1) GROUP_MEMBERS — papel agora inclui 'moderator'
-- ----------------------------------------------------------------------------
alter table public.group_members drop constraint if exists group_members_role_check;
alter table public.group_members add  constraint group_members_role_check
  check (role in ('admin','moderator','member'));

-- ----------------------------------------------------------------------------
-- 2) STAFF — equipe do site (superadmin). NÃO editável pelo cliente.
-- ----------------------------------------------------------------------------
create table if not exists public.staff (
  user_id  uuid primary key references public.profiles(id) on delete cascade,
  added_at timestamptz default now()
);
alter table public.staff enable row level security;

-- ----------------------------------------------------------------------------
-- 3) TABELAS NOVAS — fórum, sugestões (colab beta) e auditoria
-- ----------------------------------------------------------------------------
create table if not exists public.group_topics (
  id         uuid primary key default gen_random_uuid(),
  group_id   uuid not null references public.groups(id) on delete cascade,
  user_id    uuid references public.profiles(id),
  title      text not null,
  body       text default '',
  pinned     boolean default false,
  locked     boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
alter table public.group_topics enable row level security;

create table if not exists public.topic_posts (
  id         uuid primary key default gen_random_uuid(),
  topic_id   uuid not null references public.group_topics(id) on delete cascade,
  user_id    uuid references public.profiles(id),
  body       text not null,
  created_at timestamptz default now()
);
alter table public.topic_posts enable row level security;

create table if not exists public.suggestions (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references public.profiles(id),
  kind        text default 'sugestao',
  verse_ref   text,
  page_url    text,
  body        text not null,
  status      text default 'pendente',
  reviewed_by uuid references public.profiles(id),
  reviewed_at timestamptz,
  created_at  timestamptz default now()
);
alter table public.suggestions enable row level security;

create table if not exists public.audit_log (
  id         uuid primary key default gen_random_uuid(),
  actor      uuid,
  action     text not null,
  entity     text,
  entity_id  uuid,
  meta       jsonb default '{}',
  created_at timestamptz default now()
);
alter table public.audit_log enable row level security;

-- ----------------------------------------------------------------------------
-- 4) HELPERS (security definer) — reusados nas policies e RPCs
-- ----------------------------------------------------------------------------
create or replace function public.is_active_member(gid uuid)
returns boolean language sql security definer set search_path = public stable as $$
  select exists (select 1 from group_members gm
    where gm.group_id = gid and gm.user_id = auth.uid() and gm.status = 'active');
$$;

create or replace function public.is_group_admin(gid uuid)
returns boolean language sql security definer set search_path = public stable as $$
  select exists (select 1 from group_members gm
    where gm.group_id = gid and gm.user_id = auth.uid()
      and gm.status = 'active' and gm.role = 'admin');
$$;

create or replace function public.is_group_mod(gid uuid)
returns boolean language sql security definer set search_path = public stable as $$
  select exists (select 1 from group_members gm
    where gm.group_id = gid and gm.user_id = auth.uid()
      and gm.status = 'active' and gm.role in ('admin','moderator'));
$$;

create or replace function public.is_staff()
returns boolean language sql security definer set search_path = public stable as $$
  select exists (select 1 from staff s where s.user_id = auth.uid());
$$;

create or replace function public.log_audit(p_action text, p_entity text, p_entity_id uuid, p_meta jsonb default '{}')
returns void language sql security definer set search_path = public as $$
  insert into audit_log(actor, action, entity, entity_id, meta)
  values (auth.uid(), p_action, p_entity, p_entity_id, coalesce(p_meta,'{}'));
$$;

-- ----------------------------------------------------------------------------
-- 5) RLS — recria TODAS as policies das tabelas tocadas (fonte única, idempotente)
--    Equipe (is_staff) vê/modera tudo. Auto-entrada em grupo só vira pendente.
-- ----------------------------------------------------------------------------
do $$
declare r record;
begin
  for r in
    select policyname, tablename from pg_policies
    where schemaname = 'public'
      and tablename in ('profiles','staff','groups','group_members','group_notes',
                        'note_comments','group_plans','group_plan_progress',
                        'activity_feed','group_topics','topic_posts','suggestions','audit_log')
  loop
    execute format('drop policy if exists %I on public.%I', r.policyname, r.tablename);
  end loop;
end $$;

-- profiles: leitura pública (para badges/nomes); escrita só via RPC save_profile.
create policy profiles_select on public.profiles for select using (true);
create policy profiles_insert on public.profiles for insert with check (auth.uid() = id);
-- (sem policy de UPDATE: bloqueia adulteração de flags; save_profile é definer)

-- staff: leitura pública (mostrar badge "Equipe"); sem escrita pelo cliente.
create policy staff_select on public.staff for select using (true);

-- groups
create policy groups_select on public.groups for select
  using (is_active_member(id) or is_staff());
create policy groups_update on public.groups for update
  using (is_group_admin(id) or is_staff());
create policy groups_delete on public.groups for delete
  using (is_group_admin(id) or is_staff());
-- (sem INSERT direto: grupos nascem pela RPC create_group)

-- group_members
create policy gm_select on public.group_members for select
  using (user_id = auth.uid() or is_active_member(group_id) or is_staff());
create policy gm_insert_self_pending on public.group_members for insert
  with check (user_id = auth.uid() and role = 'member' and status = 'pending');
create policy gm_update_admin on public.group_members for update
  using (is_group_admin(group_id) or is_staff());
create policy gm_delete on public.group_members for delete
  using (is_group_admin(group_id) or is_staff() or user_id = auth.uid());

-- group_notes
create policy notes_select on public.group_notes for select
  using (is_active_member(group_id) or is_staff());
create policy notes_insert on public.group_notes for insert
  with check (user_id = auth.uid() and is_active_member(group_id));
create policy notes_update_own on public.group_notes for update
  using (user_id = auth.uid());
create policy notes_delete on public.group_notes for delete
  using (user_id = auth.uid() or is_group_mod(group_id) or is_staff());

-- note_comments
create policy comments_select on public.note_comments for select
  using (exists (select 1 from group_notes n where n.id = note_id
                 and (is_active_member(n.group_id) or is_staff())));
create policy comments_insert on public.note_comments for insert
  with check (user_id = auth.uid()
              and exists (select 1 from group_notes n where n.id = note_id and is_active_member(n.group_id)));
create policy comments_delete on public.note_comments for delete
  using (user_id = auth.uid()
         or is_staff()
         or exists (select 1 from group_notes n where n.id = note_id and is_group_mod(n.group_id)));

-- group_plans
create policy plans_select on public.group_plans for select
  using (is_active_member(group_id) or is_staff());
create policy plans_write on public.group_plans for all
  using (is_group_admin(group_id) or is_staff())
  with check (is_group_admin(group_id) or is_staff());

-- group_plan_progress
create policy progress_select on public.group_plan_progress for select
  using (exists (select 1 from group_plans p where p.id = plan_id
                 and (is_active_member(p.group_id) or is_staff())));
create policy progress_write on public.group_plan_progress for all
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- activity_feed (insert só por trigger/definer)
create policy feed_select on public.activity_feed for select
  using (is_active_member(group_id) or is_staff());

-- group_topics (writes via RPC create_topic/moderate_topic)
create policy topics_select on public.group_topics for select
  using (is_active_member(group_id) or is_staff());

-- topic_posts (writes via RPC add_post/delete_post)
create policy posts_select on public.topic_posts for select
  using (exists (select 1 from group_topics t where t.id = topic_id
                 and (is_active_member(t.group_id) or is_staff())));

-- suggestions (insert via RPC; review via RPC)
create policy sugg_select on public.suggestions for select
  using (user_id = auth.uid() or is_staff());

-- audit_log (insert só por definer)
create policy audit_select on public.audit_log for select using (is_staff());

-- ----------------------------------------------------------------------------
-- 6) RATE-LIMIT (anti-flood) — ≤ 20 inserts/min por usuário, por tabela
-- ----------------------------------------------------------------------------
create or replace function public.rl_guard()
returns trigger language plpgsql security definer set search_path = public as $$
declare cnt int;
begin
  if auth.uid() is null then return new; end if;
  execute format(
    'select count(*) from public.%I where user_id = $1 and created_at > now() - interval ''1 minute''',
    tg_table_name) into cnt using auth.uid();
  if cnt >= 20 then
    raise exception 'Muitas ações em pouco tempo. Aguarde um instante.';
  end if;
  return new;
end $$;

drop trigger if exists rl_notes    on public.group_notes;
drop trigger if exists rl_comments on public.note_comments;
drop trigger if exists rl_posts    on public.topic_posts;
drop trigger if exists rl_sugg     on public.suggestions;
create trigger rl_notes    before insert on public.group_notes  for each row execute function public.rl_guard();
create trigger rl_comments before insert on public.note_comments for each row execute function public.rl_guard();
create trigger rl_posts    before insert on public.topic_posts   for each row execute function public.rl_guard();
create trigger rl_sugg     before insert on public.suggestions   for each row execute function public.rl_guard();

-- ----------------------------------------------------------------------------
-- 7) RPCs (security definer) — única via de mutação sensível
-- ----------------------------------------------------------------------------

-- Perfil: whitelist de campos do próprio usuário (cadastro obrigatório).
create or replace function public.save_profile(p_name text, p_age int, p_gender text, p_type text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'Não autenticado'; end if;
  p_name := trim(coalesce(p_name,''));
  if length(p_name) < 2 or length(p_name) > 60 then raise exception 'Nome inválido'; end if;
  if p_age is null or p_age < 13 or p_age > 120 then raise exception 'Idade inválida (mínimo 13 anos)'; end if;
  if p_gender not in ('m','f','prefiro_nao_dizer') then raise exception 'Gênero inválido'; end if;
  if p_type not in ('pastor','aluno') then raise exception 'Tipo inválido'; end if;
  update profiles set name = p_name, age = p_age, gender = p_gender, account_type = p_type
  where id = auth.uid();
end $$;
grant execute on function public.save_profile(text,int,text,text) to authenticated;

-- Criar grupo: limite de 3 (exceto staff), cria grupo + admin atômico.
create or replace function public.create_group(p_name text, p_description text default '')
returns table(id uuid, name text, invite_code text)
language plpgsql security definer set search_path = public as $$
declare g_id uuid; g_code text; n int;
begin
  if auth.uid() is null then raise exception 'Não autenticado'; end if;
  p_name := trim(coalesce(p_name,''));
  if length(p_name) < 2 then raise exception 'Nome do grupo muito curto'; end if;
  if length(p_name) > 80 then raise exception 'Nome do grupo muito longo'; end if;
  if not is_staff() then
    select count(*) into n from groups where created_by = auth.uid();
    if n >= 3 then raise exception 'Você já criou o máximo de 3 grupos'; end if;
  end if;
  g_id := gen_random_uuid();
  g_code := substring(replace(gen_random_uuid()::text,'-','') from 1 for 8);
  insert into groups(id, name, invite_code, description, created_by)
    values (g_id, p_name, g_code, left(coalesce(p_description,''),500), auth.uid());
  insert into group_members(group_id, user_id, role, status)
    values (g_id, auth.uid(), 'admin', 'active');
  perform log_audit('create_group','group',g_id, jsonb_build_object('name',p_name));
  return query select g_id, p_name, g_code;
end $$;
grant execute on function public.create_group(text,text) to authenticated;

-- Aprovar/recusar pedido de entrada (admin do grupo ou staff).
create or replace function public.decide_member(p_member_id uuid, p_approve boolean)
returns void language plpgsql security definer set search_path = public as $$
declare m record;
begin
  select * into m from group_members where id = p_member_id;
  if m.id is null then raise exception 'Membro não encontrado'; end if;
  if not (is_group_admin(m.group_id) or is_staff()) then raise exception 'Sem permissão'; end if;
  if p_approve then
    update group_members set status = 'active' where id = p_member_id;
    perform log_audit('approve_member','group_member',p_member_id, jsonb_build_object('group_id',m.group_id));
  else
    delete from group_members where id = p_member_id;
    perform log_audit('reject_member','group_member',p_member_id, jsonb_build_object('group_id',m.group_id));
  end if;
end $$;
grant execute on function public.decide_member(uuid,boolean) to authenticated;

-- Promover a moderador / rebaixar a membro (admin ou staff). Não mexe em admins.
create or replace function public.set_member_role(p_member_id uuid, p_role text)
returns void language plpgsql security definer set search_path = public as $$
declare m record;
begin
  if p_role not in ('moderator','member') then raise exception 'Papel inválido'; end if;
  select * into m from group_members where id = p_member_id;
  if m.id is null then raise exception 'Membro não encontrado'; end if;
  if not (is_group_admin(m.group_id) or is_staff()) then raise exception 'Sem permissão'; end if;
  if m.role = 'admin' then raise exception 'Não é possível alterar o papel de um administrador'; end if;
  update group_members set role = p_role where id = p_member_id;
  perform log_audit('set_role','group_member',p_member_id, jsonb_build_object('role',p_role,'group_id',m.group_id));
end $$;
grant execute on function public.set_member_role(uuid,text) to authenticated;

-- Remover membro (admin/staff; ou o próprio saindo). Admin não pode ser removido por outro.
create or replace function public.remove_member(p_member_id uuid)
returns void language plpgsql security definer set search_path = public as $$
declare m record;
begin
  select * into m from group_members where id = p_member_id;
  if m.id is null then return; end if;
  if not (is_group_admin(m.group_id) or is_staff() or m.user_id = auth.uid()) then
    raise exception 'Sem permissão';
  end if;
  if m.role = 'admin' and m.user_id <> auth.uid() then
    raise exception 'Não é possível remover um administrador';
  end if;
  delete from group_members where id = p_member_id;
  perform log_audit('remove_member','group_member',p_member_id, jsonb_build_object('group_id',m.group_id));
end $$;
grant execute on function public.remove_member(uuid) to authenticated;

-- Discussões: criar tópico (membro ativo), responder (tópico aberto), moderar.
create or replace function public.create_topic(p_group_id uuid, p_title text, p_body text default '')
returns uuid language plpgsql security definer set search_path = public as $$
declare t_id uuid;
begin
  if not is_active_member(p_group_id) then raise exception 'Sem permissão'; end if;
  p_title := trim(coalesce(p_title,''));
  if length(p_title) < 2 then raise exception 'Título muito curto'; end if;
  if length(p_title) > 140 then raise exception 'Título muito longo'; end if;
  if length(coalesce(p_body,'')) > 5000 then raise exception 'Texto muito longo'; end if;
  insert into group_topics(group_id, user_id, title, body)
    values (p_group_id, auth.uid(), p_title, coalesce(p_body,'')) returning id into t_id;
  perform log_audit('create_topic','topic',t_id, jsonb_build_object('group_id',p_group_id));
  return t_id;
end $$;
grant execute on function public.create_topic(uuid,text,text) to authenticated;

create or replace function public.add_post(p_topic_id uuid, p_body text)
returns uuid language plpgsql security definer set search_path = public as $$
declare t record; pid uuid;
begin
  select * into t from group_topics where id = p_topic_id;
  if t.id is null then raise exception 'Tópico não encontrado'; end if;
  if not is_active_member(t.group_id) then raise exception 'Sem permissão'; end if;
  if t.locked and not (is_group_mod(t.group_id) or is_staff()) then raise exception 'Tópico trancado'; end if;
  p_body := trim(coalesce(p_body,''));
  if length(p_body) < 1 then raise exception 'Escreva algo'; end if;
  if length(p_body) > 5000 then raise exception 'Texto muito longo'; end if;
  insert into topic_posts(topic_id, user_id, body) values (p_topic_id, auth.uid(), p_body) returning id into pid;
  update group_topics set updated_at = now() where id = p_topic_id;
  return pid;
end $$;
grant execute on function public.add_post(uuid,text) to authenticated;

create or replace function public.moderate_topic(p_topic_id uuid, p_pin boolean, p_lock boolean, p_delete boolean)
returns void language plpgsql security definer set search_path = public as $$
declare t record;
begin
  select * into t from group_topics where id = p_topic_id;
  if t.id is null then return; end if;
  if not (is_group_mod(t.group_id) or is_staff()) then raise exception 'Sem permissão'; end if;
  if p_delete then
    delete from group_topics where id = p_topic_id;
    perform log_audit('delete_topic','topic',p_topic_id, jsonb_build_object('group_id',t.group_id));
    return;
  end if;
  update group_topics set pinned = coalesce(p_pin, pinned), locked = coalesce(p_lock, locked), updated_at = now()
  where id = p_topic_id;
  perform log_audit('moderate_topic','topic',p_topic_id, jsonb_build_object('pin',p_pin,'lock',p_lock));
end $$;
grant execute on function public.moderate_topic(uuid,boolean,boolean,boolean) to authenticated;

create or replace function public.delete_post(p_post_id uuid)
returns void language plpgsql security definer set search_path = public as $$
declare p record;
begin
  select tp.id, tp.user_id, gt.group_id as gid into p
  from topic_posts tp join group_topics gt on gt.id = tp.topic_id
  where tp.id = p_post_id;
  if p.id is null then return; end if;
  if not (p.user_id = auth.uid() or is_group_mod(p.gid) or is_staff()) then raise exception 'Sem permissão'; end if;
  delete from topic_posts where id = p_post_id;
  perform log_audit('delete_post','post',p_post_id, jsonb_build_object('group_id',p.gid));
end $$;
grant execute on function public.delete_post(uuid) to authenticated;

-- Colaboração beta: enviar sugestão/correção; staff revisa.
create or replace function public.submit_suggestion(p_kind text, p_verse_ref text, p_page_url text, p_body text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'Não autenticado'; end if;
  if p_kind is null or p_kind not in ('correcao','sugestao') then p_kind := 'sugestao'; end if;
  p_body := trim(coalesce(p_body,''));
  if length(p_body) < 3 then raise exception 'Escreva sua sugestão'; end if;
  if length(p_body) > 4000 then raise exception 'Texto muito longo'; end if;
  insert into suggestions(user_id, kind, verse_ref, page_url, body)
    values (auth.uid(), p_kind, left(coalesce(p_verse_ref,''),120), left(coalesce(p_page_url,''),300), p_body);
end $$;
grant execute on function public.submit_suggestion(text,text,text,text) to authenticated;

create or replace function public.review_suggestion(p_id uuid, p_status text)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not is_staff() then raise exception 'Sem permissão'; end if;
  if p_status not in ('aprovada','descartada','pendente') then raise exception 'Status inválido'; end if;
  update suggestions set status = p_status, reviewed_by = auth.uid(), reviewed_at = now() where id = p_id;
  perform log_audit('review_suggestion','suggestion',p_id, jsonb_build_object('status',p_status));
end $$;
grant execute on function public.review_suggestion(uuid,text) to authenticated;

-- ----------------------------------------------------------------------------
-- 8) REALTIME — adiciona as tabelas novas à publicação (ignora se já estão)
-- ----------------------------------------------------------------------------
do $$
begin
  begin alter publication supabase_realtime add table public.group_topics; exception when others then null; end;
  begin alter publication supabase_realtime add table public.topic_posts;  exception when others then null; end;
end $$;

-- ----------------------------------------------------------------------------
-- 9) FEED — registra criação de tópico no activity_feed (igual ao feed_on_note)
-- ----------------------------------------------------------------------------
create or replace function public.feed_on_topic()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into activity_feed(group_id, user_id, event_type, payload)
  values (new.group_id, new.user_id, 'topic_added', jsonb_build_object('topic_id', new.id, 'title', new.title));
  return new;
end $$;
drop trigger if exists trg_feed_topic on public.group_topics;
create trigger trg_feed_topic after insert on public.group_topics
  for each row execute function public.feed_on_topic();

-- ============================================================================
-- FIM. Lembrete: adicione-se à equipe:
--   insert into staff(user_id) values ('<SEU-AUTH-UID>') on conflict do nothing;
-- ============================================================================
