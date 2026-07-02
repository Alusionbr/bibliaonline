-- Aplicado ao projeto pxqhpntifbtjaoqtirao.
-- Proposito: reduzir superficie de ataque sem quebrar RLS nem os fluxos logados.
--
-- Regra que evita quebrar o banco:
--   Funcoes usadas DENTRO de politicas RLS (is_staff, is_active_member,
--   is_group_admin, is_group_mod, is_platform_mod) PRECISAM de EXECUTE para o
--   papel que consulta a tabela. NAO revogar EXECUTE dessas para authenticated.
--   Por isso aqui so revogamos de funcoes de trigger e de RPCs de escrita.

-- Funcoes de trigger: nunca sao chamadas via RPC nem por politicas -> revogar tudo.
revoke execute on function public.handle_new_user() from public, anon, authenticated;
revoke execute on function public.feed_on_note() from public, anon, authenticated;
revoke execute on function public.feed_on_topic() from public, anon, authenticated;
revoke execute on function public.rl_guard() from public, anon, authenticated;

-- Helper de auditoria: so chamado dentro de funcoes SECURITY DEFINER (roda como owner).
revoke execute on function public.log_audit(text, text, uuid, jsonb) from public, anon, authenticated;

-- RPCs de escrita: exigem login (validam auth.uid() internamente) -> tirar anon.
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

-- is_platform_mod e usada pelas politicas de escrita de badges/daily_missions.
grant execute on function public.is_platform_mod() to authenticated;

-- Pendente (so pelo painel/Auth Admin, nao via SQL):
--   Ativar "Leaked password protection" e senha minima >= 8 em Auth > Policies.
