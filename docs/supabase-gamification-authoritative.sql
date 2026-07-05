-- Aplicado ao projeto pxqhpntifbtjaoqtirao (migration: gamification_authoritative).
-- Proposito: tornar XP/missoes/medalhas DERIVADOS no servidor a partir de
-- eventos validados, para que o front nao possa forjar progresso pelo devtools.
--
-- Estrategia faseada e reversivel:
--   Fase 0 (este arquivo, secoes 1-3): aditivo. Nada e revogado; o caminho de
--     escrita atual continua funcionando (dual-write no cliente).
--   Fase 1 (secao 4): backfill do piso de XP + recompute (ninguem regride).
--   Fase 2: cliente passa a emitir eventos (record_event) alem do upsert atual.
--   Fase FINAL (secao 5, COMENTADA): revoga a escrita direta -> injecao fica
--     impossivel. Aplicar SO depois de confirmar em producao que a RPC funciona.

-- ============================================================================
-- Fase 0 -- log, recompute e RPC (aditivo)
-- ============================================================================

-- 1) Log append-only de eventos (escrito SO pela RPC definer)
create table if not exists public.user_events (
  id            bigint generated always as identity primary key,
  user_id       uuid not null references auth.users(id) on delete cascade,
  metric        text not null,
  occurred_on   date not null default current_date,
  occurred_week text,
  dedup_key     text,
  payload       jsonb not null default '{}'::jsonb,
  created_at    timestamptz not null default now()
);
create index if not exists user_events_user_metric_day_idx
  on public.user_events(user_id, metric, occurred_on);
create index if not exists user_events_user_metric_week_idx
  on public.user_events(user_id, metric, occurred_week);
create unique index if not exists user_events_dedup_idx
  on public.user_events(user_id, metric, dedup_key) where dedup_key is not null;

alter table public.user_events enable row level security;
drop policy if exists user_events_select_own on public.user_events;
create policy user_events_select_own on public.user_events
  for select to authenticated using ((select auth.uid()) = user_id);

revoke all on public.user_events from public, anon, authenticated;
grant select on public.user_events to authenticated;   -- insert so via definer

-- Piso de XP para nao penalizar contas existentes.
alter table public.user_gamification
  add column if not exists legacy_xp int not null default 0;

-- Alinha o catalogo diario ao cliente (que nao exibe a missao de grifos).
update public.daily_missions set active = false where key = 'grifar';

-- 2) Recompute autoritativo (derivacao completa a partir dos eventos)
create or replace function public.recompute_gamification(p_uid uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_today  date := current_date;
  v_week   text := to_char(current_date, 'IYYY-"W"IW');
  v_xp     int  := 0;
  v_streak int; v_longest int; v_last date; v_legacy int;
begin
  insert into public.user_mission_progress (user_id, mission_key, day, progress, completed, updated_at)
  select p_uid, dm.key, v_today, least(c.cnt, dm.goal), c.cnt >= dm.goal, now()
  from public.daily_missions dm
  join lateral (select count(*)::int cnt from public.user_events e
                where e.user_id=p_uid and e.metric=dm.metric and e.occurred_on=v_today) c on true
  where dm.active
  on conflict (user_id, mission_key, day) do update
    set progress   = greatest(user_mission_progress.progress, excluded.progress),
        completed  = user_mission_progress.completed or excluded.completed,
        updated_at = now();

  insert into public.user_weekly_mission_progress (user_id, mission_key, week, progress, completed, updated_at)
  select p_uid, wm.key, v_week, least(c.cnt, wm.goal), c.cnt >= wm.goal, now()
  from public.weekly_missions wm
  join lateral (select count(*)::int cnt from public.user_events e
                where e.user_id=p_uid and e.metric=wm.metric and e.occurred_week=v_week) c on true
  where wm.active
  on conflict (user_id, mission_key, week) do update
    set progress   = greatest(user_weekly_mission_progress.progress, excluded.progress),
        completed  = user_weekly_mission_progress.completed or excluded.completed,
        updated_at = now();

  select streak, longest_streak, last_active, legacy_xp
    into v_streak, v_longest, v_last, v_legacy
    from public.user_gamification where user_id=p_uid;
  v_streak := coalesce(v_streak,0); v_longest := coalesce(v_longest,0); v_legacy := coalesce(v_legacy,0);
  if    v_last is null        then v_streak := greatest(v_streak,1);
  elsif v_last =  v_today     then null;
  elsif v_last =  v_today - 1 then v_streak := v_streak + 1;
  else  v_streak := 1;
  end if;
  v_longest := greatest(v_longest, v_streak);

  insert into public.user_badges (user_id, badge_key)
  select p_uid, k from (
              select 'primeiro_passo'::text k
    union all select 'primeira_nota'     where exists (select 1 from public.user_events e where e.user_id=p_uid and e.metric='notes')
    union all select 'primeiro_favorito' where exists (select 1 from public.user_events e where e.user_id=p_uid and e.metric='favorites')
    union all select 'primeiro_grifo'    where exists (select 1 from public.user_events e where e.user_id=p_uid and e.metric='highlights')
    union all select 'leitor_10' where (select count(*) from public.user_events e where e.user_id=p_uid and e.metric='read_chapters') >= 10
    union all select 'leitor_50' where (select count(*) from public.user_events e where e.user_id=p_uid and e.metric='read_chapters') >= 50
    union all select 'streak_3'  where v_streak >= 3
    union all select 'streak_7'  where v_streak >= 7
    union all select 'streak_30' where v_streak >= 30
    union all select 'missoes_7' where (select count(*) from public.user_mission_progress p where p.user_id=p_uid and p.completed) >= 7
    union all select 'comunidade' where exists (select 1 from public.user_events e where e.user_id=p_uid and e.metric='room_joined')
  ) q
  where exists (select 1 from public.badges b where b.key=q.k)
  on conflict (user_id, badge_key) do nothing;

  select coalesce((select sum(dm.points) from public.user_mission_progress p
                     join public.daily_missions dm on dm.key=p.mission_key
                    where p.user_id=p_uid and p.completed),0)
       + coalesce((select sum(wm.points) from public.user_weekly_mission_progress p
                     join public.weekly_missions wm on wm.key=p.mission_key
                    where p.user_id=p_uid and p.completed),0)
       + coalesce((select sum(b.points) from public.user_badges ub
                     join public.badges b on b.key=ub.badge_key
                    where ub.user_id=p_uid),0)
    into v_xp;
  v_xp := greatest(v_xp, v_legacy);

  insert into public.user_gamification (user_id, xp, level, streak, longest_streak, last_active, updated_at)
  values (p_uid, v_xp, 1 + (v_xp/100), v_streak, v_longest, v_today, now())
  on conflict (user_id) do update
    set xp=excluded.xp, level=1+(excluded.xp/100),
        streak=excluded.streak, longest_streak=excluded.longest_streak,
        last_active=excluded.last_active, updated_at=now();
end;
$$;
revoke execute on function public.recompute_gamification(uuid) from public, anon, authenticated;

-- 3) RPC publica: valida entrada, registra evento (idempotente), recomputa
create or replace function public.record_event(
  p_metric text, p_dedup_key text default null, p_payload jsonb default '{}'::jsonb)
returns public.user_gamification
language plpgsql
security definer
set search_path = public
as $$
declare
  v_uid uuid := (select auth.uid());
  v_ok  boolean;
  v_row public.user_gamification;
begin
  if v_uid is null then raise exception 'auth required'; end if;
  select exists(select 1 from public.daily_missions  where active and metric=p_metric)
      or exists(select 1 from public.weekly_missions where active and metric=p_metric)
      or p_metric in ('highlights','room_joined','room_comment_created','room_material_opened','account_created')
    into v_ok;
  if not v_ok then raise exception 'unknown metric %', p_metric; end if;
  if length(coalesce(p_dedup_key,'')) > 200 then raise exception 'dedup_key too long'; end if;
  if pg_column_size(coalesce(p_payload,'{}'::jsonb)) > 2048 then raise exception 'payload too large'; end if;

  insert into public.user_events(user_id, metric, occurred_on, occurred_week, dedup_key, payload)
  values (v_uid, p_metric, current_date, to_char(current_date,'IYYY-"W"IW'),
          nullif(p_dedup_key,''), coalesce(p_payload,'{}'::jsonb))
  on conflict do nothing;

  perform public.recompute_gamification(v_uid);
  select * into v_row from public.user_gamification where user_id=v_uid;
  return v_row;
end;
$$;
revoke execute on function public.record_event(text, text, jsonb) from public, anon;
grant   execute on function public.record_event(text, text, jsonb) to authenticated;

comment on table public.user_events is 'Log append-only de eventos de estudo; escrito so via record_event (definer).';
comment on function public.record_event(text,text,jsonb) is 'Registra um evento validado e recomputa a gamificacao do usuario autenticado.';

-- ============================================================================
-- Fase 1 -- backfill (aplicado): piso de XP legado + recompute
-- ============================================================================
-- update public.user_gamification set legacy_xp = greatest(legacy_xp, xp) where xp > 0;
-- insert into public.user_events(user_id, metric, dedup_key, payload)
--   select user_id, 'account_created', 'legacy', '{"legacy":true}'::jsonb
--     from public.user_gamification on conflict do nothing;
-- do $$ declare r record; begin
--   for r in select user_id from public.user_gamification loop
--     perform public.recompute_gamification(r.user_id); end loop; end $$;

-- ============================================================================
-- Fase FINAL -- lockdown (APLICADO em 2026-07-04, migration: gamification_lockdown)
-- ============================================================================
-- Pre-condicao verificada em producao: user_events ja recebia eventos reais do
-- cliente (read_chapters, notes, highlights, favorites). A partir daqui a
-- escrita e exclusiva da RPC record_event; o select segue liberado para o pull
-- e os upserts legados do cliente falham em silencio (best-effort).
-- Reversivel devolvendo os grants, se um dia for necessario.

revoke insert, update, delete on public.user_gamification            from authenticated;
revoke insert, update, delete on public.user_mission_progress        from authenticated;
revoke insert, update, delete on public.user_weekly_mission_progress from authenticated;
revoke insert, update, delete on public.user_badges                  from authenticated;
