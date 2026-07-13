# Registro de Alteracoes

Este arquivo e o caderno de bordo do projeto. Toda alteracao relevante deve
ser registrada aqui antes do commit, junto com o que foi analisado, o que foi
mudado, como foi testado e qual commit publicou a mudanca.

## Pausa Comunidade/Salas de Estudo (decisao de produto) - 2026-07-12

Intencao: decisao explicita do usuario — Comunidade sera reformulada antes de
voltar ao projeto; por enquanto, tirar do site publicado.

Mudancas:

- `scripts/build.py`: remove a secao `#comunidade` do Workspace, o CTA
  "Salas de Estudo" no hero do Workspace, o bloco `room-suggest` (+ link "Ver
  Salas de Estudo") de `study_continue_module()`, o card "Salas" da home, o
  link "Comunidade" do rodape, e a entrada de `community.js` em
  `SOURCE_ASSETS`/no `<script>`/em `build_site()`. Os redirects
  `/comunidade/` e `/comunidade/salas/` continuam existindo (noindex), mas
  agora apontam para `workspace/` em vez de uma secao que nao existe mais.
  `scripts/community.asset.js` (integracao Supabase completa: salas, papeis,
  convites, topicos) continua no repositorio para a proxima versao — so nao
  e mais gerado nem carregado.
- `scripts/sw.asset.js`: remove `community.js` da lista de precache do
  service worker (apontava pra um arquivo que deixou de existir).
- `scripts/gamification.asset.js`: remove a medalha "Companheiro" (so podia
  ser concedida ao entrar numa sala — ficaria eternamente trancada e
  confusa na grade de medalhas).
- `site/assets/styles.css`: remove o bloco inteiro de estilos exclusivos de
  Comunidade (`.community-*`, `.room-*`, `.role-pill`, `.topic-*`,
  `.post-*`, `.member-*`, `.invite`, `.pending-count`), preservando
  `.btn.tiny` (usado em outros lugares).
- `CLAUDE.md`: atualizado para nao listar mais `#comunidade` como secao
  fundida no Workspace e documentar a pausa (com nota para nao reativar sem
  confirmar com o usuario).
- `tests/test_build_smoke.py`: `test_salas_de_estudo_reais` virou
  `test_comunidade_pausada` (confirma ausencia, nao presenca); ajustes em
  `test_nova_navegacao_principal` (sem `id="comunidade"`, redirects apontam
  pra `workspace/` sem ancora).

Validacao realizada:

- `python scripts/build.py`: passou.
- `python -m pytest`: 96 testes, todos passaram.
- `git diff --check`: sem espacos em branco problematicos.
- Playwright (servidor local): `/comunidade/`, `/comunidade/salas/`,
  `/workspace/` e a home carregam sem erro; workspace nao tem mais
  `id="comunidade"` nem o CTA "Salas de Estudo"; nenhuma referencia a
  `community.js` sobrou em HTML gerado nem no `sw.js`.
- Removido manualmente o `site/assets/community.js` (artefato de builds
  anteriores que o build.py parou de regenerar).

## Leitor: audio de verdade pausa, marcador automatico opcional, leitura continua, contraste e identidade por era - 2026-07-12

Intencao: corrigir um bug real de audio, adicionar controle sobre efeitos de
leitura (com opcao de desligar), e dar mais cara de ferramenta de estudo aos
livros e a linha do tempo.

Descobertas antes de mudar:

- Bug real: o botao "Pausar" do audio (folha de ferramentas do versiculo)
  chamava `speak()` de novo ao ser clicado, que fazia `cancel()` e recomecava
  a fala do zero — nunca pausava de verdade. Havia tambem um listener morto
  em `app.asset.js` para `[data-speak]`, atributo que `build.py` nunca gera
  (sobrou de uma versao anterior da folha de ferramentas).
- Bug real (nao relacionado ao pedido original, mas no mesmo bloco): o
  checkbox "Mostrar hebraico/grego e transliteracao" em Configuracoes nunca
  teve um listener de fato — `syncUI()` refletia o estado salvo, mas marcar/
  desmarcar a caixa nao chamava `applyOrig()`.
- Contraste medido: no tema sepia, `--muted` (usado em bastante texto
  secundario) tinha 3.28:1 de contraste contra o fundo — abaixo do minimo de
  acessibilidade (4.5:1 para texto normal). Os outros dois temas estavam OK.
- "Modo cronologico" ja existia como uma ordem alternativa de listar os
  livros (`data-set-order=chron`), mas sem nenhuma identidade visual por
  epoca; a listagem de livros (`/ler/`) era so nome + idioma + contagem de
  capitulos, sem contexto de Antigo/Novo Testamento ou periodo historico.

Mudancas:

- `scripts/app.asset.js`: `BEC.speak()` reescrito para usar
  `speechSynthesis.pause()/resume()` de verdade (Pausar ⇄ Continuar) em vez
  de cancelar e reiniciar; remove o listener morto de `[data-speak]` e o
  `showTranscript()` que dependia dele. Corrige o checkbox de idioma
  original (`window.BEC.applyOrig` exposto + listener). Novo par de opcoes em
  Configuracoes: "Marcar versiculos como lidos automaticamente ao rolar"
  (estende `bec.readingRanges` via IntersectionObserver, reaproveitando
  getRanges/setRanges/normalize/paint/creditRead do modulo de progresso por
  trecho) e "Efeito de entrada suave no texto ao rolar" (liga/desliga
  `html.no-reveal`, sempre respeitando `prefers-reduced-motion`). Nova
  ferramenta "Ouvir capitulo" no leitor: le os versiculos em portugues em
  sequencia, destacando o atual, parando quando qualquer outra fala comeca.
- `scripts/build.py`: `.ch-verse` ganha `verse-reveal` (efeito de entrada
  cresce+aparece ao rolar); nova opcao no `<head>` grava `no-reveal` cedo
  (evita flash); novo botao "Ouvir capitulo" no leque de ferramentas do
  leitor; `/ler/` (listagem de livros) ganha faixa lateral por Testamento
  (AT/NT) e legenda com a era da linha do tempo por livro (reaproveita
  `BOOK_ERA`, novo em `build_config.py`, sem duplicar `TIMELINE`); a linha do
  tempo (`/linha-do-tempo/`) ganha um matiz proprio por era (varredura
  dourado→violeta calculada no build, so decorativo) nas bordas e no selo do
  periodo.
- `site/assets/styles.css`: `--muted` do tema sepia escurecido (3.28:1 →
  4.72:1); novas regras `.verse-reveal`, `.listen-current`, `.book-card.bt-*`,
  `.book-era`, `--era-accent` na linha do tempo.

Validacao realizada:

- `python scripts/build.py`: passou (mesmos totais de sempre).
- `python -m pytest`: 96 testes, todos passaram.
- `node --check` em `app.js`/`study.js`: sem erro de sintaxe.
- `git diff --check`: sem espacos em branco problematicos.
- Playwright (servidor local, `speechSynthesis` mockado para determinismo):
  pausar/retomar audio alterna Pausar⇄Continuar de verdade; trocar de
  verso cancela e reseta o anterior; "Ouvir capitulo" toca os versiculos em
  sequencia com destaque, termina sozinho no ultimo, e para no clique manual;
  abrir a folha de um verso interrompe a leitura continua sem erro. Rolar um
  capitulo com o marcador automatico ligado grava `bec.readingRanges`
  corretamente e credita a missao de leitura. Checkbox de idioma original
  agora aplica `orig-on` de verdade. Ordenacao biblica/alfabetica/cronologica
  em `/ler/` continua funcionando com os cartoes novos. Capturas de tela nos
  3 temas confirmam a varredura de cor por era na linha do tempo e o
  contraste do sepia.

## Criar Plano embutido nas abas do Workspace - 2026-07-12

Intencao: "Criar Plano" ja funcionava (gera cronograma, liga com leitor e
home), mas ficava enterrado numa secao propria abaixo de "Explorar", so
alcancavel por um linkzinho no cabecalho de "Estudar" — pouco descoberto.

Mudancas:

- `scripts/build.py`: a secao `#criar-plano` deixa de ser uma `<section>`
  separada e vira mais uma aba dentro de `#estudar` (`data-ws-tab`/
  `data-ws-panel="criar-plano"`, ao lado de Atalhos/Anotacoes/Favoritos/
  Colecoes/Cadernos). O painel mantem `id="criar-plano"` para os links
  existentes (`workspace/#criar-plano` na home e no leitor) continuarem
  funcionando. O link solto "Criar plano" no cabecalho de "Estudar" foi
  removido (redundante com a aba).
- `scripts/app.asset.js`: o modulo de abas do Workspace passa a ler
  `location.hash` no carregamento da pagina — se o hash bater com o nome
  de uma aba, ela e selecionada (sobrepondo a ultima aba lembrada) e o
  painel recebe `scrollIntoView()`. Sem isso, a aba nova ficaria com
  `hidden` e o link `#criar-plano` nao rolaria ate ela.

Validacao realizada:

- `python scripts/build.py`: passou (mesmos totais de sempre).
- `python -m pytest`: 96 testes, todos passaram.
- `git diff --check`: sem espacos em branco problematicos.
- Verificacao com Playwright (servidor local): `workspace/#criar-plano`
  carrega com a aba certa ativa e o formulario visivel no viewport sem
  precisar clicar em nada; criar um plano pelo formulario funciona;
  trocar de aba manualmente e recarregar `workspace/` sem hash preserva a
  ultima aba escolhida (nao forca `criar-plano`); sem erros de console.

## PWA de bolso: icones/service worker reais, barra de app, leitor ligado ao plano, Workspace com abas - 2026-07-12

Intencao: virar uma ferramenta de estudo "de bolso" (instalavel, funciona
offline) e com as ferramentas funcionando em conjunto (leitor, planos,
home e Workspace conversando entre si), em vez de partes isoladas.

Descobertas antes de mudar:

- O PWA era fachada: `manifest.webmanifest` nao declarava `icons` (nao
  havia nenhum arquivo de icone no repositorio) e `site/sw.js` estava
  orfao — o build nao o gerava e nenhum script chamava
  `serviceWorker.register()`, entao o offline nunca funcionou de verdade.
- A barra inferior mobile tinha `grid-template-columns:repeat(5,1fr)`
  para so 3 links (bug visual), sem icones e sem
  `env(safe-area-inset-bottom)`.
- Leitor e plano de leitura eram silos: nada dizia "Dia N do plano X" no
  capitulo, e os cards "Plano de hoje"/"Ultimas anotacoes" da home eram
  texto fixo fingindo ser dado real (bec.studyPlans/bec.notes existiam e
  nunca eram lidos ali). O Workspace so linkava para anotacoes/coleções/
  cadernos/favoritos em vez de embuti-los, apesar de todos os modulos JS
  ja se inicializarem sozinhos a partir do container.
- ~40 seletores `html.dark` usavam cor literal (`#211c13` ~9x, `#2a2418`
  ~5x etc.) em vez de token; `.btn.ghost` (texto claro, pensado pro hero
  escuro) estava sendo usado sem escopo em `/anotacoes/` e no overlay de
  busca — botoes praticamente ilegiveis em fundo claro (bug real,
  confirmado e corrigido).

Mudancas:

- `scripts/build_icons.py` (novo): gera `site/assets/icons/` (SVG + 4 PNG
  via encoder proprio, so stdlib `zlib`+`struct`, sem Pillow nem outra
  dependencia) — livro aberto dourado sobre navy. Rodado uma vez, commitado
  como asset estatico (nao regenerado a cada build, evita custo em teste).
- `scripts/build.py`: `head()` ganha `viewport-fit=cover`, `theme-color`
  unico atualizado por JS, `link rel=icon`/`apple-touch-icon`; `build_meta()`
  completa o manifest (`id`, `scope`, `icons`, `shortcuts`,
  `display_override`, `categories`); novo `build_sw_js()` gera `sw.js` a
  partir de `scripts/sw.asset.js` com `ASSET_VER` e shell completo (todos
  os 10 scripts); `nav()` ganha barra inferior de 4 itens com icone SVG
  (Inicio/Biblia/Buscar/Workspace, `grid-template-columns:repeat(4,1fr)`
  corrigido); novo `build_plan_index()`/`build_chapter_verse_counts()`
  geram `site/data/plan-index.json` e `chapter-verses.json` (dados de
  ponte pro leitor saber em que dia de plano um capitulo esta); capitulo
  ganha `data-plan-context`; Workspace `#estudar` vira abas (Atalhos/
  Anotacoes/Favoritos/Colecoes/Cadernos) com os apps existentes embutidos
  sem nenhuma mudanca neles; nova secao `#explorar` (dicionario/mapas/
  temas/artigos) desorfaniza esse conteudo; hero da home reescrito pro
  publico de estudo biblico profundo.
- `scripts/core.asset.js`: registra o service worker.
- `scripts/app.asset.js`: modulo `bec:chapter-read` (disparado no credito
  real de leitura) liga o leitor ao plano — banner "Dia N de T" + auto-
  marca o dia quando todos os capitulos do dia estao 100% cobertos (dias
  com versiculo avulso de plano por tema ficam manuais); `window.BEC.planData`
  compartilhado entre leitor/home; home "Plano de hoje"/"Ultimas anotacoes"
  viram dinamicos; Workspace "Continuar leitura" usa `bec.lastRead`; modulo
  de abas do Workspace.
- `scripts/study.asset.js`: grava `bec.notesMeta` (data da nota, so local)
  pra home ordenar por mais recente.
- `site/assets/styles.css`: novos tokens semanticos (`--surface-raised`,
  `--surface-hover`, `--accent-soft`, `--ink-strong`, `--nav-bg`) — ~15
  overrides `html.dark` com cor literal viram `var(...)`; corrige
  `.btn.ghost` ilegivel em `/anotacoes/` e no overlay de busca; remove
  regra `.hub-hero` morta/duplicada (mesclada, sem mudanca visual).

Corte deliberado (nao bloqueia): screenshots no manifest (exigiriam captura
real), tokenizacao total das cores hardcoded restantes (so as recorrentes
foram tokenizadas), icone set completo pra emojis estruturais (ficou pra
proxima leva).

Teste: `pytest` (mais testes novos: PWA/manifest implicito via checagem de
icones e sw.js, plan-index, chapter-verses, integracao leitor-plano, abas
do Workspace), `validate_data.py`, `git diff --check`, `ruff` (sem erro
novo). Verificacao ponta a ponta com Playwright (servidor estatico local):
service worker registra e fica `activated`; manifest valido; barra
inferior com 4 itens e estado ativo correto por pagina; criar plano no
Workspace, abrir o dia 1, marcar o capitulo inteiro como lido credita o
dia automaticamente com toast, banner mostra "concluido" apos reload;
abas do Workspace mostram nota/favorito/coleçao/caderno reais criados em
outras paginas; dark mode sem regressao visual apos a tokenizacao
(inspecionado); botoes de `/anotacoes/` legiveis (antes brancos sobre
fundo claro). 15 paginas carregadas sem erro de console.

## Redesign profissional: folha de ferramentas unica, lexico, referencias cruzadas, plano gerado e busca global - 2026-07-12

Intencao: a pagina de leitura acumulava controles em 4 lugares ao mesmo
tempo (barra do header, 3 botoes repetidos sob cada versiculo, modulos
empilhados e 3 botoes flutuantes concorrentes). Redesign para ficar
profissional e funcional, agrupando as ferramentas de estudo e adicionando
paridade de recursos, sem custo (sem IA, sem dependencia nova, sem servidor
adicional).

Fase A - leitor limpo:

- `scripts/build.py`: remove `verse_tools()`/`audio_button()`/`fav_button()`
  (botoes por versiculo saem do HTML gerado); `verse_map_module`+
  `study_desk_module` viram um unico `study_continue_module` compacto;
  `study_fraction_module` passa a `<details class="collap">` recolhido por
  padrao; `reader_fab()` absorve os antigos `tools-fab`/`report-fab`.
- `scripts/study.asset.js` (reescrito): folha de ferramentas unica por
  versiculo (favoritar, grifar em 4 cores, nota, copiar, compartilhar,
  salvar em colecao, referencias cruzadas), acionada ao tocar no texto
  (`.verse-tap`). Remove a caneta de marca-texto morta (`makePenTools`
  comecava com `return;`, nunca funcionou em producao) e o cartao de doacao
  com link quebrado (`DONATE_URL` sem conta).

Fase B - bugs e utilitarios:

- Cartoes duplicados "Anotacoes"/"Marcacoes" no Workspace (ambos apontavam
  para o mesmo lugar) viram um so.
- `scripts/core.asset.js` (novo -> `assets/core.js`): esc/download/
  confirmModal/copyText compartilhados, antes duplicados em ate 6 arquivos.
- `scripts/gamification.asset.js`: para de descartar silenciosamente
  missoes com metric "highlights" (grifar agora e uma ferramenta real).
- Workspace `#configuracoes`: controles reais (tema, fonte, idioma
  original, ordem dos livros, backup/apagar dados locais).

Fase C - paridade de recursos:

- `scripts/lexicon.asset.js` (novo -> `assets/lexicon.js`) + shards
  `site/data/tokens/<livro>.json` (gerados por `build_lexicon_shards()` a
  partir de `hebrew-tokens.json`, ja existente e sem uso ate agora): toca
  numa palavra do hebraico/aramaico original e ve numero de Strong, glosa
  e morfologia. Alinhamento palavra<->token validado em 100% das 23213
  verses hebraicas/aramaicas antes de implementar.
- Referencias cruzadas (`site/data/cross-references.json`, ja existente):
  renderizadas na pagina do versiculo e na folha de ferramentas.
- Gerador de plano de leitura real (por livro ou tema, com cronograma dia
  a dia), substituindo o antigo formulario que so salvava metadados sem
  gerar nada.
- Dashboard de estatisticas no Workspace (`#progresso`).
- Busca disponivel em qualquer pagina (overlay global, botao no nav e no
  painel de leitura), nao so na home. Indice de busca (`search-index.json`)
  ~37% menor: campo `k` deixou de duplicar referencia/traducao ja presentes
  em `titulo`/`desc`.

Fase D - polimento:

- Suporte a `prefers-color-scheme` quando o usuario nao escolheu tema.
- Folha de estilo de impressao; metadados `og:url`/`twitter:card`.
- Estilo novo para os componentes acima (folha de ferramentas, painel
  unico, popover do lexico, overlay de busca, dashboard, configuracoes).

Cortado deliberadamente (nao bloqueia a publicacao, fica para depois):
lexico interativo em grego (sem dado de tokenizacao disponivel), repintura
completa das cores hardcoded do modo escuro, expansao do dataset de
referencias cruzadas, e 2a traducao em portugues para comparacao lado a
lado.

Teste: suite completa (`pytest`, 108 testes, incluindo 5 reescritos e 1
novo para refletir o novo comportamento) verde. Verificacao ponta a ponta
num navegador real (Playwright, servidor estatico local): grifo colorido,
nota, favorito, popover do lexico, referencias cruzadas, busca global,
gerador de plano e alternancia de tema escuro, todos funcionando sem erros
de console (fora recursos externos indisponiveis no sandbox, como CDN do
Supabase e Google Fonts). `git diff --check` e `python
scripts/validate_data.py` OK. HTML de capitulo de exemplo (Genesis 1)
caiu de 67531 para 42047 bytes com a remocao dos botoes duplicados.
Publicado no commit `b5890f1`.

## Salas de Estudo reais (ligacao Comunidade) - 2026-07-01

Intencao: ligar a pagina /comunidade/salas/ ao banco real (tabela `groups` e
RPCs), saindo dos dados demonstrativos.

Bug encontrado e corrigido (`docs/supabase-fix-join-group.sql`):

- `join_group()` falhava sempre com "column reference group_id is ambiguous"
  (coluna OUT colidia com a coluna no ON CONFLICT). Ninguem conseguia entrar
  numa sala. Corrigido com `#variable_conflict use_column`, API preservada.

Mudancas:

- `scripts/community.asset.js` (novo → `assets/community.js`): app das Salas —
  listar minhas salas, criar sala, entrar por codigo, ver participantes,
  aprovar/recusar (admin), definir moderador, remover, criar discussoes e
  responder. Tudo via cliente Supabase (`window.BEC_ACCOUNT`) com RLS.
- `scripts/build.py`: `/comunidade/salas/` agora renderiza `[data-community-app]`
  em vez de salas fixas; registra `community.js`.
- `scripts/gamification.asset.js`: novo `BEC_GAME.grant()` para conceder a
  medalha `comunidade` ao criar/entrar numa sala.
- `site/assets/styles.css`: estilos das salas, membros, discussoes e posts.

Teste ponta a ponta no banco (transacao revertida, nada persistido):
criar sala → topico → post → entrar por codigo (pendente, RLS bloqueia
topicos) → admin aprova → membro ativo ve topicos e responde. Passou.
`pytest` 84 testes (novo `test_salas_de_estudo_reais`). `git diff --check` OK.

## Gamificacao, selo Beta e revisao do banco - 2026-07-01

Analise do banco (projeto Supabase `pxqhpntifbtjaoqtirao`):

- O backend colaborativo (grupos, membros com papeis, topicos, posts, notas,
  comentarios, planos, feed, sugestoes, staff, audit_log, profiles,
  user_study_state) ja existia e estava mais completo que o front. RLS ligada,
  funcoes `SECURITY DEFINER` validando `auth.uid()` e rate-limit (`rl_guard`).
- Causa dos "bugs quando logado": o front so fazia login + sincronizava
  `user_study_state`. Nao lia/completava `profiles`, nao mostrava Beta e a
  Comunidade era estatica (dados demonstrativos), sem ligacao com `groups`.
- Faltava toda a gamificacao (missoes, medalhas, XP/streak) e um papel de
  moderador de plataforma.

Mudancas aplicadas:

- Banco (aditivo, reversivel — `docs/supabase-gamification.sql`):
  `badges`, `user_badges`, `daily_missions`, `user_mission_progress`,
  `user_gamification`, `profiles.platform_role` e `is_platform_mod()`, com RLS,
  grants e seed (11 medalhas, 5 missoes).
- Seguranca (`docs/supabase-security-hardening.sql`): revogado `EXECUTE` de
  `anon` nas RPCs de escrita e nas funcoes de trigger/auditoria, sem quebrar
  RLS (helpers usados por politicas mantem `EXECUTE`). Avisos de funcao
  executavel por `anon` cairam de ~22 para 4 (helpers de RLS, intencionais).
- Front:
  - `scripts/auth.asset.js`: carrega `profiles` apos login e expoe
    `window.BEC_ACCOUNT` + evento `bec:account`; chip Beta/Moderador/Admin.
  - `scripts/gamification.asset.js` (novo → `assets/game.js`): missoes,
    medalhas, streak e XP; sync best-effort ao Supabase; funciona offline.
  - `scripts/app.asset.js`: envia atividade (`read_chapters`, `meditate`).
  - `scripts/build.py`: registra `game.js`, banner Beta global, selo da conta
    e painel de Progresso no Workspace.
  - `site/assets/styles.css`: estilos do banner, chips, missoes e medalhas.
  - `docs/gamification.md`: documentacao da fundacao.

Como testado:

- `python scripts/build.py` (OK), `python -m pytest` (83 passam, novo teste
  `test_gamificacao_e_beta`), `git diff --check`.
- Supabase: migracao aplicada, seed confirmado (11 badges / 5 missions),
  security advisor reexecutado.

Pendente (proxima fase): ligar Comunidade/Salas reais a UI; ativar no painel
Auth leaked password protection e senha minima >= 8.

## Plataforma de estudo biblico - 2026-07-01

Intencao:

- Reorganizar a interface para parecer uma plataforma de estudo biblico, com a
  Biblia no centro e areas claras: Inicio, Biblia, Estudar, Comunidade e
  Workspace.
- Tirar ferramentas de estudo do contexto da conta e mover a descoberta visual
  para Estudar, Workspace, Biblioteca, Colecoes, Cadernos e Salas de Estudo.
- Manter a conta simples: Meu perfil, Configuracoes, Sincronizacao,
  Privacidade e Sair.
- Nao criar recursos de IA para usuario final.

Arquivos alterados:

- `scripts/build.py`: nova navegacao, barra inferior mobile, home em formato de
  painel, paginas `/estudar/`, `/workspace/`, `/comunidade/`,
  `/comunidade/salas/`, `/biblioteca/`, `/colecoes/`, `/cadernos/` e
  `/privacidade/`, alem de Mapa de Estudos e Mesa de Estudo em paginas de
  livro/capitulo/versiculo.
- `scripts/app.asset.js`: primeira versao local de Criar Plano usando
  `localStorage`.
- `scripts/auth.asset.js`: menu da conta simplificado.
- `site/assets/styles.css`: estilos mobile-first para hubs, cards, mapa,
  mesa de estudo e navegacao inferior.
- `tests/test_build_smoke.py`: cobertura para navegacao, paginas novas,
  sitemap, conta simples e ausencia dos nomes proibidos de IA no HTML gerado.
- `CLAUDE.md`: direcao de produto e comandos de validacao.
- `docs/supabase-community-schema.md`: proposta nao destrutiva para tabelas de
  comunidade/workspace em fase futura.

Decisoes de produto:

- Comunidade deve ser organizada por conteudo estudado, usando Salas de Estudo
  em vez de grupos.
- Perfil passa a ser perfil de estudo, sem seguidores, seguindo ou ranking por
  curtidas.
- Mapa de Estudos e Mesa de Estudo comecam como blocos estruturados com dados
  demonstrativos, prontos para substituir por dados reais via Supabase depois.
- Criar Plano comeca funcional no navegador, sem alterar banco.

Como testar:

```bash
python scripts/build.py
python -m pytest
git diff --check
```

Verificacao manual sugerida:

- `site/index.html`
- `site/estudar/index.html`
- `site/workspace/index.html`
- `site/comunidade/index.html`
- `site/ler/joao/3/index.html`
- `site/versiculos/joao-3-16/index.html`

Proxima fase:

- Conectar Mapa de Estudos, Salas, Colecoes, Cadernos e Planos a tabelas reais
  do Supabase com RLS revisada.
- Implementar moderacao, privacidade por sala e progressos reais.
- Refinar visualmente as paginas de leitura com ferramentas contextuais por
  selecao de versiculo.

## Protocolo de trabalho

1. Verificar `git status` antes de editar.
2. Ler o historico recente com `git log` e respeitar o que ja existe.
3. Entender os arquivos geradores antes de alterar HTML gerado.
4. Registrar a intencao da mudanca neste arquivo.
5. Alterar somente os arquivos necessarios.
6. Rodar o build/testes aplicaveis.
7. Registrar o resultado da validacao.
8. Fazer commit com mensagem clara e enviar ao GitHub quando aprovado.

## Estado atual - 2026-06-17

- Repositorio: `Alusionbr/bibliaonline`
- Branch principal: `main`
- Site publicado: `https://alusionbr.github.io/bibliaonline/`
- Checkout local: `C:\Users\Beto\Downloads\biblia`
- Estado antes deste registro: `git status --short` limpo.
- Commit sincronizado: `4d79fa398e` (`origin/main`)

### Historico recente observado

- `4d79fa398e` - merge do PR #11.
- `dc7bacf906` - ordenacao de livros e pagina Linha do tempo.
- `bde9f1cc01` - ajustes iOS, painel de ferramentas e exportacao de notas.
- `37e751d309` - cartao de compartilhamento, ferramentas ocultas, navegacao entre livros, confirmacao de exclusao, bloqueio de IAs e ajuste do modo noturno.
- `4827047beb` - caneta marca-texto, leitura, doacao e versiculo aleatorio.
- `bdf86f266e` - cache-busting de assets.
- `7b9db48982` - marca-texto por selecao e copia com nota.

### Estrutura respeitada

- `scripts/build.py` e o gerador central do site estatico.
- `site/assets/app.js` e gerado pelo `build.py`.
- `site/assets/study.js` tambem e gerado pelo `build.py`.
- Paginas em `site/versiculos/` e `site/ler/` sao HTML gerado; evitar edicao manual direta nelas.
- O deploy roda pelo GitHub Actions publicando a pasta `site/` no GitHub Pages.

### Proxima solicitacao em analise

Pedido do usuario: adicionar falas/audio para textos em hebraico/original e
portugues, sem interferir em direitos autorais, e permitir salvar favoritos
para aparecerem na pagina inicial.

Direcao tecnica preliminar:

- Usar `speechSynthesis` do navegador para leitura em voz alta, evitando
distribuir arquivos de audio gravados de terceiros.
- Salvar favoritos em `localStorage`, seguindo o padrao ja usado por
anotacoes, marca-texto, ultimo texto lido e preferencias.
- Integrar os botoes pelo `scripts/build.py`, nao editando paginas geradas
uma a uma.
- Antes de implementar, mapear o comportamento atual de `app.js`, `study.js`
e das paginas de versiculo/capitulo.

## Analise tecnica - audio e favoritos - 2026-06-17

Estado antes de editar:

- `git status --short` limpo.
- Branch `main` sincronizada com `origin/main`.
- Commit base: `0a84978398` (`Adiciona registro permanente de alteracoes`).

Arquivos analisados:

- `scripts/build.py`: gera as paginas estaticas, `site/assets/app.js` e
  `site/assets/study.js`.
- `site/assets/app.js`: contem busca, rolagem infinita, ferramentas de leitura,
  continuar lendo, versiculo aleatorio e ordenacao de livros.
- `site/assets/study.js`: contem anotacoes, marca-texto e exportacao, usando
  `localStorage` com prefixo `bec.*`.
- `tests/test_build_smoke.py`: cobre o build integrado e verifica recursos
  gerados em HTML/JS.

Decisoes:

- Audio: usar Web Speech API (`speechSynthesis`) no navegador. Nao hospedar nem
  redistribuir arquivos de audio de terceiros.
- Idiomas de leitura: `he-IL` para hebraico/aramaico, `el-GR` para grego,
  `pt-BR` para portugues.
- Favoritos: salvar em `localStorage` como `bec.favs`, separado de `notes`,
  `vhl` e `whl`.
- UI: adicionar botoes pequenos nos versiculos:
  - `Ouvir original`
  - `Ouvir PT` quando houver texto em portugues
  - `Favoritar`
- Home: mostrar uma secao compacta de favoritos quando houver itens salvos.
- Integracao com rolagem infinita: o handler de clique deve ser delegado no
  documento, funcionando tambem para versiculos inseridos dinamicamente.
- Implementacao deve acontecer no `scripts/build.py`, com regeneracao dos
  assets e paginas pelo build. Nao editar manualmente HTML gerado.

### Implementacao realizada

- `scripts/build.py`
  - adicionados helpers para idioma de fala, botoes de audio e botao de
    favorito;
  - paginas individuais de versiculo passaram a receber `Ouvir original`,
    `Ouvir PT` quando houver traducao, e `Favoritar`;
  - paginas de leitura por capitulo passaram a receber os mesmos controles em
    cada versiculo;
  - home passou a ter area `Favoritos`, exibida apenas quando houver favoritos
    salvos no navegador;
  - `build_app_js()` passou a gerar o JS de `speechSynthesis` e favoritos.
- `site/assets/styles.css`
  - estilos para botoes de audio/favorito e lista compacta de favoritos.
- `tests/test_build_smoke.py`
  - teste de fumaça para garantir os ganchos de audio/favoritos no HTML e JS.

### Validacao realizada

- `python scripts/build.py`: passou.
  - Resultado: `home + 31173 versiculos + 66 livros + 1189 capitulos + 10 artigos`.
- `python -m py_compile scripts\build.py`: passou.
- `python -m py_compile` nos scripts auxiliares principais: passou.
- Verificacao estatica:
  - `site/versiculos/genesis-1-1/index.html` contem `Ouvir original`, `Ouvir PT`
    e `Favoritar`;
  - `site/ler/genesis/1/index.html` contem botoes por versiculo;
  - `site/index.html` contem `favorite-home` e `favorite-list`;
  - `site/assets/app.js` contem `speechSynthesis`, `SpeechSynthesisUtterance` e
    `bec.favs`.

Validacao pendente/inconclusiva:

- `pytest` nao rodou porque o Python local nao tem `pytest` instalado.
- Tentativa de instalar `requirements-dev.txt` falhou por certificado SSL ao
  acessar o PyPI.
- Teste visual pelo navegador interno contra `localhost:8765` ficou inconclusivo:
  o servidor respondeu `200` via PowerShell, mas o navegador interno recebeu
  `ERR_CONNECTION_REFUSED`, aparentemente por isolamento de rede do ambiente.
