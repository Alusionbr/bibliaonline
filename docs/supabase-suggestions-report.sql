-- Applied to project pxqhpntifbtjaoqtirao on 2026-07-02.
-- Formulario de "Reportar" do site (apenas usuarios logados).
--
-- Nao cria nada novo: reusa os RPCs SECURITY DEFINER que ja existem.
--   - Envio:   submit_suggestion(p_kind, p_verse_ref, p_page_url, p_body)
--              exige login (auth.uid() nao nulo); kind em ('correcao','sugestao');
--              ja concedido a `authenticated`.
--   - Revisao: review_suggestion(p_id, p_status)  -- staff-only
--              status em ('aprovada','descartada','pendente'); concedido a `authenticated`.
--   - Leitura: policy sugg_select (user_id = auth.uid() OR is_staff()) ja permite
--              ao staff ler todos os reportes via select.
--
-- Este arquivo apenas REVERTE as policies de INSERT/UPDATE direto que foram
-- testadas e descartadas em favor dos RPCs acima (mantendo a superficie minima).
drop policy if exists sugg_insert_public on public.suggestions;
drop policy if exists sugg_update_staff on public.suggestions;
