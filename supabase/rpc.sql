-- ============================================================================
-- Bíblia em Contexto — funções RPC complementares (rodar UMA vez no Supabase)
-- ----------------------------------------------------------------------------
-- Por quê: a policy de leitura da tabela `groups` só libera para MEMBROS ATIVOS.
-- Logo, alguém que tem apenas o CÓDIGO de convite (e ainda não é membro) não
-- consegue resolver código -> grupo via SELECT direto. Estas duas funções
-- `security definer` cobrem exatamente esse caso, sem afrouxar o RLS:
--   * join_group(p_code)  -> cria um pedido de entrada (status 'pending').
--   * group_brief(p_code) -> devolve nome/descrição mínimos p/ exibir ao convidado.
--
-- NÃO recria o schema; só adiciona estas funções. O front-end (cloud.js) já as
-- chama via supabase.rpc(...). Cole tudo no SQL Editor do Supabase e rode.
-- ============================================================================

-- Entrar em um grupo pelo código do convite (cria membership pendente).
create or replace function public.join_group(p_code text)
returns table(group_id uuid, name text, status text)
language plpgsql
security definer
set search_path = public
as $$
declare
  g_id  uuid;
  g_nm  text;
begin
  if auth.uid() is null then
    raise exception 'Não autenticado';
  end if;

  select id, groups.name into g_id, g_nm
  from groups
  where invite_code = lower(trim(p_code));

  if g_id is null then
    raise exception 'Grupo não encontrado para o código informado';
  end if;

  insert into group_members(group_id, user_id, role, status)
  values (g_id, auth.uid(), 'member', 'pending')
  on conflict (group_id, user_id) do nothing;

  return query
    select gm.group_id, g_nm, gm.status
    from group_members gm
    where gm.group_id = g_id and gm.user_id = auth.uid();
end;
$$;

grant execute on function public.join_group(text) to authenticated;

-- Dados mínimos do grupo pelo código (para mostrar nome/descrição a quem ainda
-- não é membro ativo, ex.: pedido pendente ou link de convite recém-aberto).
create or replace function public.group_brief(p_code text)
returns table(id uuid, name text, description text)
language sql
security definer
set search_path = public
as $$
  select id, name, description
  from groups
  where invite_code = lower(trim(p_code));
$$;

grant execute on function public.group_brief(text) to authenticated;
