-- Extensao aditiva de docs/supabase-gamification.sql / -weekly.sql /
-- -authoritative.sql: missoes, medalha e eventos de memorizacao (repeticao
-- espacada) e de quiz por capitulo.
--
-- Nada existente e alterado de forma destrutiva. Como a gamificacao ja e
-- autoritativa no servidor (ver -authoritative.sql, secao "Fase FINAL"), a
-- funcao recompute_gamification precisa ser recriada (create or replace)
-- para reconhecer as medalhas novas: as missoes diarias/semanais em si sao
-- genericas (o motor ja lê qualquer linha ativa de daily_missions/
-- weekly_missions), so as medalhas ficam com a logica hardcoded que segue.

-- 1) Seed dos catalogos (idempotente) -----------------------------------------
insert into public.daily_missions (key, title, description, icon, goal, metric, points, sort) values
  ('revisar', 'Revise seus versiculos',  'Revise 3 versiculos na fila de memorizacao.', '🧠', 3, 'memorize', 15, 6),
  ('quiz',    'Teste seu conhecimento',  'Complete o quiz de um capitulo.',             '🧩', 1, 'quiz',     15, 7)
on conflict (key) do update set
  title = excluded.title, description = excluded.description, icon = excluded.icon,
  goal = excluded.goal, metric = excluded.metric, points = excluded.points, sort = excluded.sort;

insert into public.weekly_missions (key, title, description, icon, goal, metric, points, sort) values
  ('semana_memoria', 'Semana de memorizacao', 'Faca 10 revisoes espacadas nesta semana.', '🧠', 10, 'memorize', 40, 4)
on conflict (key) do update set
  title = excluded.title, description = excluded.description, icon = excluded.icon,
  goal = excluded.goal, metric = excluded.metric, points = excluded.points, sort = excluded.sort;

insert into public.badges (key, title, description, icon, tier, points, sort) values
  ('memorizador',    'Memorizador',           'Fez a primeira revisao espacada.',   '🧠', 'bronze', 15, 11),
  ('memorizador_10', 'Guardiao da Palavra',   'Fez 10 revisoes espacadas.',         '🧠', 'prata',  40, 12),
  ('quiz_10',        'Estudante Atento',      'Completou 10 quizzes de capitulo.',  '🧩', 'prata',  40, 13)
on conflict (key) do update set
  title = excluded.title, description = excluded.description, icon = excluded.icon,
  tier = excluded.tier, points = excluded.points, sort = excluded.sort;

-- 2) recompute_gamification: mesma funcao de -authoritative.sql, com as
-- medalhas de memorizacao/quiz adicionadas ao bloco de avaliacao. As
-- missoes diaria/semanal de metric='memorize' ja sao creditadas pelo bloco
-- generico (nao precisa mudar); so as medalhas sao hardcoded aqui.
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
    union all select 'memorizador'    where exists (select 1 from public.user_events e where e.user_id=p_uid and e.metric='memorize')
    union all select 'memorizador_10' where (select count(*) from public.user_events e where e.user_id=p_uid and e.metric='memorize') >= 10
    union all select 'quiz_10'        where (select count(*) from public.user_events e where e.user_id=p_uid and e.metric='quiz') >= 10
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

comment on function public.recompute_gamification(uuid) is
  'Recomputa XP/missoes/medalhas a partir de user_events; inclui memorizacao (SM-2) e quiz por capitulo.';
