-- Applied to project pxqhpntifbtjaoqtirao on 2026-06-29.
-- Purpose: private per-user sync for local study tools.

create table if not exists public.user_study_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  notes jsonb not null default '{}'::jsonb,
  verse_highlights jsonb not null default '{}'::jsonb,
  word_highlights jsonb not null default '{}'::jsonb,
  favorites jsonb not null default '{}'::jsonb,
  preferences jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.user_study_state enable row level security;

revoke all on table public.user_study_state from public;
revoke all on table public.user_study_state from anon;
revoke all on table public.user_study_state from authenticated;
grant select, insert, update, delete on table public.user_study_state to authenticated;

drop policy if exists user_study_state_select_own on public.user_study_state;
drop policy if exists user_study_state_insert_own on public.user_study_state;
drop policy if exists user_study_state_update_own on public.user_study_state;
drop policy if exists user_study_state_delete_own on public.user_study_state;

create policy user_study_state_select_own
on public.user_study_state
for select
to authenticated
using ((select auth.uid()) = user_id);

create policy user_study_state_insert_own
on public.user_study_state
for insert
to authenticated
with check ((select auth.uid()) = user_id);

create policy user_study_state_update_own
on public.user_study_state
for update
to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy user_study_state_delete_own
on public.user_study_state
for delete
to authenticated
using ((select auth.uid()) = user_id);

comment on table public.user_study_state is
  'Private per-user sync state for Biblia em Contexto local study tools.';
