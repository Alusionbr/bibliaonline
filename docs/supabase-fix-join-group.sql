-- Aplicado ao projeto pxqhpntifbtjaoqtirao em 2026-07-01.
-- Bug encontrado no teste ponta a ponta das Salas de Estudo:
--   join_group() falhava SEMPRE com
--   "column reference \"group_id\" is ambiguous"
--   porque a coluna OUT `group_id` colidia com a coluna da tabela
--   group_members no ON CONFLICT. Ou seja, ninguem conseguia entrar numa sala.
-- Correcao minima e nao-destrutiva: a diretiva #variable_conflict use_column
-- faz nomes ambiguos resolverem para a coluna. API preservada (retorna
-- group_id, name, status).
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
