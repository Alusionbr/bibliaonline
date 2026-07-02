-- PENDENTE DE APLICACAO no projeto Supabase.
-- Migracao v2 do user_study_state: colunas para planos de estudo,
-- colecoes e cadernos criados pelas ferramentas pessoais do site.
--
-- Enquanto esta migracao nao for aplicada, o site continua funcionando:
-- o auth.js detecta a ausencia das colunas (erro 42703/PGRST204) e cai
-- para o conjunto v1 de colunas; os dados novos ficam locais no navegador
-- (e lastRead/history/planProgress ja viajam dentro de preferences).
--
-- Idempotente: pode rodar mais de uma vez sem efeito colateral.
-- As politicas RLS existentes (por linha, definidas na v1) ja cobrem
-- as colunas novas; nenhuma mudanca de grant/policy e necessaria.

alter table public.user_study_state
  add column if not exists study_plans jsonb not null default '[]'::jsonb;

alter table public.user_study_state
  add column if not exists collections jsonb not null default '{}'::jsonb;

alter table public.user_study_state
  add column if not exists notebooks jsonb not null default '{}'::jsonb;

comment on column public.user_study_state.study_plans is
  'Planos criados em Estudar > Criar Plano (lista, max. 12).';
comment on column public.user_study_state.collections is
  'Colecoes de versiculos da pagina /colecoes/.';
comment on column public.user_study_state.notebooks is
  'Cadernos de estudo em texto livre da pagina /cadernos/.';
