# Supabase: comunidade e workspace

Este documento descreve uma proposta de schema para fases futuras. Nenhuma alteracao destrutiva no banco foi aplicada nesta fase.

## Objetivo

Persistir dados reais para Workspace, Biblioteca, Colecoes, Cadernos e Comunidade sem transformar a experiencia em rede social generica. Os registros devem ser ligados a conteudo biblico sempre que possivel: livro, capitulo, versiculo, tema, plano ou sala.

## Tabelas sugeridas

- `profiles`: perfil de estudo, bio curta, temas favoritos e contadores publicos de contribuicao.
- `study_rooms`: Salas de Estudo com nome, descricao, livro/tema relacionado e plano vinculado.
- `study_room_members`: participacao em salas e progresso por pessoa.
- `community_posts`: perguntas, discussoes, pedidos de oracao, testemunhos e estudos publicos.
- `community_comments`: respostas e comentarios em discussoes.
- `prayer_requests`: pedidos de oracao com privacidade e moderacao.
- `testimonies`: testemunhos ligados a estudo, sala ou tema.
- `public_collections`: colecoes publicas ligadas a versiculos, capitulos, artigos, mapas, manuscritos ou planos.
- `collection_items`: itens de colecoes.
- `notebooks`: cadernos pessoais ou compartilhados.
- `notebook_items`: notas, perguntas, grifos, colecoes, planos e referencias dentro de cadernos.
- `study_plans_user`: planos criados ou salvos por usuario.
- `study_plan_progress`: progresso por dia, trecho e plano.
- `reports`: moderacao de conteudo.
- `notifications`: notificacoes de sala, resposta e progresso.

## Decisoes de produto

- Evitar seguidores, ranking de popularidade e destaque por curtidas.
- Priorizar contribuicoes, estudos, colecoes, cadernos e salas.
- Encontrar usuarios por conteudo estudado: livro, capitulo, versiculo, tema ou plano.
- Comecar com placeholders estruturados no site estatico e substituir por dados reais depois.

## Proxima fase

Antes de aplicar SQL, revisar RLS para dados privados, dados publicos e moderacao. O estado privado atual de estudo continua em `user_study_state`.
