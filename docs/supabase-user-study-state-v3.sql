-- Migracao v3 do user_study_state: coluna para a memorizacao com repeticao
-- espacada (fila de revisao por versiculo, algoritmo SM-2 simplificado).
--
-- Enquanto esta migracao nao for aplicada, o site continua funcionando:
-- o auth.js detecta a ausencia da coluna (erro 42703/PGRST204) e desce para
-- o conjunto v2 de colunas; a memorizacao fica local no navegador (nao
-- sincroniza entre aparelhos ate a migracao ser aplicada).
--
-- Idempotente: pode rodar mais de uma vez sem efeito colateral.
-- As politicas RLS existentes (por linha, definidas na v1) ja cobrem a
-- coluna nova; nenhuma mudanca de grant/policy e necessaria.

alter table public.user_study_state
  add column if not exists memory jsonb not null default '{"items":{},"log":{}}'::jsonb;

comment on column public.user_study_state.memory is
  'Fila de memorizacao com repeticao espacada (aba Decorar do Workspace): '
  '{"items":{"Livro c:v":{t,url,ef,ivl,due,reps,lapses,addedAt,last}}, "log":{"YYYY-MM-DD":n}}.';
