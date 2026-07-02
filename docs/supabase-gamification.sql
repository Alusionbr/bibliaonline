-- Aplicado ao projeto pxqhpntifbtjaoqtirao.
-- Proposito: fundacao aditiva de gamificacao (missoes diarias, medalhas, XP/streak)
-- e papel de plataforma (usuario/moderador/admin) para a comunidade de estudo.
--
-- Aditivo e reversivel: nenhuma tabela ou funcao existente e alterada de forma
-- destrutiva. Padrao de RLS segue o de public.user_study_state (dono le/escreve
-- a propria linha; catalogos sao leitura publica).

-- 1) Papel de plataforma em profiles -----------------------------------------
-- staff (admin de plataforma) ja existe; aqui adicionamos um papel legivel em
-- profiles para diferenciar usuario / moderador / admin sem quebrar nada.
alter table public.profiles
  add column if not exists platform_role text not null default 'user'
  check (platform_role in ('user','moderator','admin'));

create or replace function public.is_platform_mod()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.profiles p
    where p.id = (select auth.uid())
      and p.platform_role in ('moderator','admin')
  ) or exists (
    select 1 from public.staff s where s.user_id = (select auth.uid())
  );
$$;

revoke execute on function public.is_platform_mod() from public, anon, authenticated;

-- 2) Catalogo de medalhas -----------------------------------------------------
create table if not exists public.badges (
  key text primary key,
  title text not null,
  description text not null,
  icon text not null default '🏅',
  tier text not null default 'bronze' check (tier in ('bronze','prata','ouro')),
  points int not null default 10,
  sort int not null default 0
);

-- 3) Medalhas conquistadas por usuario ---------------------------------------
create table if not exists public.user_badges (
  user_id uuid not null references auth.users(id) on delete cascade,
  badge_key text not null references public.badges(key) on delete cascade,
  earned_at timestamptz not null default now(),
  primary key (user_id, badge_key)
);
create index if not exists user_badges_user_id_idx on public.user_badges(user_id);

-- 4) Catalogo de missoes diarias ---------------------------------------------
create table if not exists public.daily_missions (
  key text primary key,
  title text not null,
  description text not null,
  icon text not null default '📖',
  goal int not null default 1,
  metric text not null,
  points int not null default 10,
  active boolean not null default true,
  sort int not null default 0
);

-- 5) Progresso de missao por usuario e dia -----------------------------------
create table if not exists public.user_mission_progress (
  user_id uuid not null references auth.users(id) on delete cascade,
  mission_key text not null references public.daily_missions(key) on delete cascade,
  day date not null default current_date,
  progress int not null default 0,
  completed boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (user_id, mission_key, day)
);
create index if not exists user_mission_progress_user_day_idx
  on public.user_mission_progress(user_id, day);

-- 6) Estado de gamificacao do usuario (XP, nivel, streak) --------------------
create table if not exists public.user_gamification (
  user_id uuid primary key references auth.users(id) on delete cascade,
  xp int not null default 0,
  level int not null default 1,
  streak int not null default 0,
  longest_streak int not null default 0,
  last_active date,
  updated_at timestamptz not null default now()
);

-- 7) RLS ---------------------------------------------------------------------
alter table public.badges enable row level security;
alter table public.daily_missions enable row level security;
alter table public.user_badges enable row level security;
alter table public.user_mission_progress enable row level security;
alter table public.user_gamification enable row level security;

-- Catalogos: leitura publica (anon + authenticated), escrita so por staff/moderador.
drop policy if exists badges_select on public.badges;
create policy badges_select on public.badges for select using (true);
drop policy if exists badges_write on public.badges;
create policy badges_write on public.badges for all
  using (public.is_platform_mod()) with check (public.is_platform_mod());

drop policy if exists missions_select on public.daily_missions;
create policy missions_select on public.daily_missions for select using (true);
drop policy if exists missions_write on public.daily_missions;
create policy missions_write on public.daily_missions for all
  using (public.is_platform_mod()) with check (public.is_platform_mod());

-- Dados por usuario: dono le/escreve apenas a propria linha.
drop policy if exists user_badges_select_own on public.user_badges;
create policy user_badges_select_own on public.user_badges
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists user_badges_insert_own on public.user_badges;
create policy user_badges_insert_own on public.user_badges
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists user_badges_delete_own on public.user_badges;
create policy user_badges_delete_own on public.user_badges
  for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists ump_select_own on public.user_mission_progress;
create policy ump_select_own on public.user_mission_progress
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists ump_insert_own on public.user_mission_progress;
create policy ump_insert_own on public.user_mission_progress
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists ump_update_own on public.user_mission_progress;
create policy ump_update_own on public.user_mission_progress
  for update to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
drop policy if exists ump_delete_own on public.user_mission_progress;
create policy ump_delete_own on public.user_mission_progress
  for delete to authenticated using ((select auth.uid()) = user_id);

drop policy if exists ug_select_own on public.user_gamification;
create policy ug_select_own on public.user_gamification
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists ug_insert_own on public.user_gamification;
create policy ug_insert_own on public.user_gamification
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists ug_update_own on public.user_gamification;
create policy ug_update_own on public.user_gamification
  for update to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

-- 8) Grants ------------------------------------------------------------------
revoke all on public.badges from public, anon, authenticated;
revoke all on public.daily_missions from public, anon, authenticated;
grant select on public.badges to anon, authenticated;
grant select on public.daily_missions to anon, authenticated;
grant insert, update, delete on public.badges to authenticated;         -- gated por RLS (staff)
grant insert, update, delete on public.daily_missions to authenticated; -- gated por RLS (staff)

revoke all on public.user_badges from public, anon, authenticated;
revoke all on public.user_mission_progress from public, anon, authenticated;
revoke all on public.user_gamification from public, anon, authenticated;
grant select, insert, delete on public.user_badges to authenticated;
grant select, insert, update, delete on public.user_mission_progress to authenticated;
grant select, insert, update, delete on public.user_gamification to authenticated;

-- 9) Seed dos catalogos (idempotente) ----------------------------------------
insert into public.badges (key, title, description, icon, tier, points, sort) values
  ('primeiro_passo', 'Primeiro Passo', 'Criou a conta e comecou a jornada de estudo.', '🌱', 'bronze', 10, 1),
  ('primeira_nota',  'Escriba',        'Escreveu a primeira anotacao.',                 '✍️', 'bronze', 15, 2),
  ('primeiro_favorito','Tesouro',      'Guardou o primeiro versiculo favorito.',        '⭐', 'bronze', 15, 3),
  ('primeiro_grifo', 'Iluminador',     'Grifou a primeira passagem.',                   '🖍️', 'bronze', 15, 4),
  ('leitor_10',      'Leitor',         'Leu 10 capitulos.',                             '📖', 'bronze', 20, 5),
  ('leitor_50',      'Estudioso',      'Leu 50 capitulos.',                             '📚', 'prata',  40, 6),
  ('streak_3',       'Constante',      'Estudou 3 dias seguidos.',                      '🔥', 'bronze', 20, 7),
  ('streak_7',       'Semana Fiel',    'Estudou 7 dias seguidos.',                      '🔥', 'prata',  40, 8),
  ('streak_30',      'Devoto',         'Estudou 30 dias seguidos.',                     '🔥', 'ouro',  100, 9),
  ('missoes_7',      'Peregrino',      'Completou 7 missoes diarias.',                  '🎯', 'prata',  40, 10),
  ('comunidade',     'Companheiro',    'Entrou em uma sala de estudo da comunidade.',   '🤝', 'bronze', 20, 11)
on conflict (key) do update set
  title = excluded.title, description = excluded.description, icon = excluded.icon,
  tier = excluded.tier, points = excluded.points, sort = excluded.sort;

insert into public.daily_missions (key, title, description, icon, goal, metric, points, sort) values
  ('ler_capitulo', 'Leia um capitulo',        'Abra e leia ao menos um capitulo hoje.',        '📖', 1, 'read_chapters', 10, 1),
  ('meditar',      'Medite no versiculo',     'Abra o versiculo para meditar hoje.',           '🕊️', 1, 'meditate',      10, 2),
  ('anotar',       'Faca uma anotacao',       'Registre um aprendizado em uma anotacao.',      '✍️', 1, 'notes',         10, 3),
  ('favoritar',    'Guarde um versiculo',     'Marque um versiculo como favorito.',            '⭐', 1, 'favorites',     10, 4),
  ('grifar',       'Grife uma passagem',      'Destaque uma passagem com o marca-texto.',      '🖍️', 1, 'highlights',    10, 5)
on conflict (key) do update set
  title = excluded.title, description = excluded.description, icon = excluded.icon,
  goal = excluded.goal, metric = excluded.metric, points = excluded.points, sort = excluded.sort;

comment on table public.badges is 'Catalogo de medalhas da plataforma de estudo (leitura publica).';
comment on table public.daily_missions is 'Catalogo de missoes diarias (leitura publica).';
comment on table public.user_badges is 'Medalhas conquistadas por usuario (privado, dono).';
comment on table public.user_mission_progress is 'Progresso diario de missoes por usuario (privado, dono).';
comment on table public.user_gamification is 'XP, nivel e streak por usuario (privado, dono).';
