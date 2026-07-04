-- Aplicado ao projeto pxqhpntifbtjaoqtirao (migration: weekly_missions).
-- Proposito: missoes semanais, extensao aditiva de docs/supabase-gamification.sql.
--
-- Aditivo e reversivel: espelha o padrao de daily_missions / user_mission_progress
-- (catalogo com leitura publica e escrita por staff; progresso por dono via RLS).

-- 1) Catalogo de missoes semanais
create table if not exists public.weekly_missions (
  key text primary key,
  title text not null,
  description text not null,
  icon text not null default '🗓️',
  goal int not null default 1,
  metric text not null,
  points int not null default 40,
  active boolean not null default true,
  sort int not null default 0
);

-- 2) Progresso de missao semanal por usuario e semana (ISO: 'YYYY-Www')
create table if not exists public.user_weekly_mission_progress (
  user_id uuid not null references auth.users(id) on delete cascade,
  mission_key text not null references public.weekly_missions(key) on delete cascade,
  week text not null,
  progress int not null default 0,
  completed boolean not null default false,
  updated_at timestamptz not null default now(),
  primary key (user_id, mission_key, week)
);
create index if not exists uwmp_user_week_idx
  on public.user_weekly_mission_progress(user_id, week);

-- 3) RLS
alter table public.weekly_missions enable row level security;
alter table public.user_weekly_mission_progress enable row level security;

drop policy if exists weekly_missions_select on public.weekly_missions;
create policy weekly_missions_select on public.weekly_missions for select using (true);
drop policy if exists weekly_missions_write on public.weekly_missions;
create policy weekly_missions_write on public.weekly_missions for all
  using (public.is_platform_mod()) with check (public.is_platform_mod());

drop policy if exists uwmp_select_own on public.user_weekly_mission_progress;
create policy uwmp_select_own on public.user_weekly_mission_progress
  for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists uwmp_insert_own on public.user_weekly_mission_progress;
create policy uwmp_insert_own on public.user_weekly_mission_progress
  for insert to authenticated with check ((select auth.uid()) = user_id);
drop policy if exists uwmp_update_own on public.user_weekly_mission_progress;
create policy uwmp_update_own on public.user_weekly_mission_progress
  for update to authenticated using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);
drop policy if exists uwmp_delete_own on public.user_weekly_mission_progress;
create policy uwmp_delete_own on public.user_weekly_mission_progress
  for delete to authenticated using ((select auth.uid()) = user_id);

-- 4) Grants
revoke all on public.weekly_missions from public, anon, authenticated;
grant select on public.weekly_missions to anon, authenticated;
grant insert, update, delete on public.weekly_missions to authenticated; -- gated por RLS (staff)

revoke all on public.user_weekly_mission_progress from public, anon, authenticated;
grant select, insert, update, delete on public.user_weekly_mission_progress to authenticated;

-- 5) Seed do catalogo (idempotente)
insert into public.weekly_missions (key, title, description, icon, goal, metric, points, sort) values
  ('semana_leitura',   'Ritmo de leitura',      'Marque trechos de leitura em 4 dias desta semana.', '📖', 4, 'read_chapters', 40, 1),
  ('semana_anotacoes', 'Semana de anotacoes',   'Faca 3 anotacoes nesta semana.',                    '✍️', 3, 'notes',         40, 2),
  ('semana_favoritos', 'Colecionador da semana','Guarde 5 versiculos favoritos nesta semana.',       '⭐', 5, 'favorites',     40, 3)
on conflict (key) do update set
  title = excluded.title, description = excluded.description, icon = excluded.icon,
  goal = excluded.goal, metric = excluded.metric, points = excluded.points, sort = excluded.sort;

comment on table public.weekly_missions is 'Catalogo de missoes semanais (leitura publica).';
comment on table public.user_weekly_mission_progress is 'Progresso semanal de missoes por usuario (privado, dono).';
