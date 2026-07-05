-- Aplicado ao projeto pxqhpntifbtjaoqtirao (migration: rooms_reference_and_discovery).
-- Salas de Estudo com referencia biblica + descoberta opcional.
--
-- reference: livro/capitulo/tema que a sala estuda (texto livre, ex.: "Joao 3").
-- is_listed: a sala aparece em "Salas abertas" (Workspace) e nas sugestoes da
--   pagina do capitulo. Entrar continua passando pela aprovacao do admin
--   (status pending) — listar nao abre a sala, so permite o pedido.
-- A view listed_rooms roda com privilegios do dono DE PROPOSITO: e o unico
--   caminho de leitura publica e expoe apenas colunas seguras (sem invite_code).

alter table public.groups add column if not exists reference text;
alter table public.groups add column if not exists is_listed boolean not null default false;

-- create_group ganha referencia e listagem. Drop evita sobrecarga ambigua no
-- PostgREST; chamadas antigas com 2 argumentos seguem validas via defaults.
-- Mantem as travas: nivel 3 de gamificacao e maximo de 3 salas (staff isento).
drop function if exists public.create_group(text, text);
create function public.create_group(
  p_name text,
  p_description text default ''::text,
  p_reference text default null,
  p_listed boolean default false)
 returns table(id uuid, name text, invite_code text)
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
declare g_id uuid; g_code text; n int; v_level int;
begin
  if auth.uid() is null then raise exception 'Não autenticado'; end if;
  p_name := trim(coalesce(p_name,''));
  if length(p_name) < 2 then raise exception 'Nome do grupo muito curto'; end if;
  if length(p_name) > 80 then raise exception 'Nome do grupo muito longo'; end if;
  p_reference := nullif(left(trim(coalesce(p_reference,'')), 80), '');
  if not is_staff() then
    select coalesce(g.level,1) into v_level from user_gamification g where g.user_id = auth.uid();
    if coalesce(v_level,1) < 3 then
      raise exception 'Criar salas é liberado no nível 3. Complete missões de estudo para subir de nível.';
    end if;
    select count(*) into n from groups where created_by = auth.uid();
    if n >= 3 then raise exception 'Você já criou o máximo de 3 grupos'; end if;
  end if;
  g_id := gen_random_uuid();
  g_code := substring(replace(gen_random_uuid()::text,'-','') from 1 for 8);
  insert into groups(id, name, invite_code, description, created_by, reference, is_listed)
    values (g_id, p_name, g_code, left(coalesce(p_description,''),500), auth.uid(), p_reference, coalesce(p_listed,false));
  insert into group_members(group_id, user_id, role, status)
    values (g_id, auth.uid(), 'admin', 'active');
  perform log_audit('create_group','group',g_id, jsonb_build_object('name',p_name,'reference',p_reference,'listed',coalesce(p_listed,false)));
  return query select g_id, p_name, g_code;
end $function$;
revoke execute on function public.create_group(text, text, text, boolean) from public, anon;
grant execute on function public.create_group(text, text, text, boolean) to authenticated;

-- Vitrine somente-leitura das salas listadas (sem invite_code).
create or replace view public.listed_rooms as
  select g.id, g.name, g.description, g.reference, g.created_at
    from public.groups g
   where g.is_listed;
revoke all on public.listed_rooms from public, anon, authenticated;
grant select on public.listed_rooms to anon, authenticated;

-- Pedir para entrar numa sala listada (sem codigo; entra como pendente).
create or replace function public.join_listed_group(p_group_id uuid)
 returns table(group_id uuid, name text, status text)
 language plpgsql
 security definer
 set search_path to 'public'
as $function$
#variable_conflict use_column
declare g_nm text; g_listed boolean;
begin
  if auth.uid() is null then raise exception 'Não autenticado'; end if;
  select groups.name, groups.is_listed into g_nm, g_listed from groups where id = p_group_id;
  if g_nm is null or not coalesce(g_listed,false) then
    raise exception 'Sala não está aberta a pedidos';
  end if;
  insert into group_members(group_id, user_id, role, status)
  values (p_group_id, auth.uid(), 'member', 'pending')
  on conflict (group_id, user_id) do nothing;
  perform log_audit('join_listed_group','group',p_group_id, '{}'::jsonb);
  return query select gm.group_id, g_nm, gm.status from group_members gm
    where gm.group_id = p_group_id and gm.user_id = auth.uid();
end $function$;
revoke execute on function public.join_listed_group(uuid) from public, anon;
grant execute on function public.join_listed_group(uuid) to authenticated;
