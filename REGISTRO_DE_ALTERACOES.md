# Registro de Alteracoes

Este arquivo e o caderno de bordo do projeto. Toda alteracao relevante deve
ser registrada aqui antes do commit, junto com o que foi analisado, o que foi
mudado, como foi testado e qual commit publicou a mudanca.

## Protocolo de trabalho

1. Verificar `git status` antes de editar.
2. Ler o historico recente com `git log` e respeitar o que ja existe.
3. Entender os arquivos geradores antes de alterar HTML gerado.
4. Registrar a intencao da mudanca neste arquivo.
5. Alterar somente os arquivos necessarios.
6. Rodar o build/testes aplicaveis.
7. Registrar o resultado da validacao.
8. Fazer commit com mensagem clara e enviar ao GitHub quando aprovado.

## 2026-06-26 - Hebraico palavra-a-palavra (significado + gramatica ao tocar/hover)

Pedido do usuario: passar o mouse/tocar em cada palavra hebraica e ver o
significado com explicacao gramatical resumida (cobertura total, palavra por
palavra).

Mudancas:

- **Dados (OSHB)**: `scripts/build_hebrew_tokens.py` baixa o OpenScriptures
  Hebrew Bible (WLC + lema Strong + morfologia OSHM, CC BY 4.0) e gera
  `site/data/hebrew-tokens.json` (mapa "Livro c:v" -> [[lemma, morph], ...]).
  Alinhamento POSICIONAL com o nosso `original`: 23.213 versiculos do AT,
  **100% alinhados, 0 divergentes** (o nosso texto ja vinha do WLC). ~6,2 MB.
- **Render** (`scripts/build.py`): `original_html`/`hebrew_inner` quebram o
  hebraico/aramaico em `<span class="w hw" data-f data-i data-l data-m>` e marcam
  o `<p class="orig">` com `data-wrapped="1"` para o `study.js` nao re-embrulhar
  (preserva os spans). `w` mantem o marca-texto; `hw` liga o popover. Vale para
  pagina de versiculo e de capitulo.
- **Gramatica** (`app.js`): `decodeMorph()` decodifica o codigo OSHM para
  portugues (substantivo/verbo/adjetivo/pronome/particula/sufixo + genero,
  numero, estado, binyan, tempo, pessoa...). Deterministico, cobre 100% das
  palavras.
- **Significado** (`site/data/hebrew-lexicon.json`): 167 lemas mais frequentes
  com glosa PT ORIGINAL (~58,7% das ocorrencias do AT). Carregado uma vez,
  pre-cacheado no `sw.js` (offline). Palavra sem glosa mostra translit +
  gramatica + "significado em curadoria".
- **Popover** (`app.js`): toque (mobile) alterna; hover (desktop) comanda; clique
  no desktop so fecha ao clicar fora. Com a canetinha ligada (`body.hl-mode`) o
  toque MARCA e o popover nao abre. Sem inline (CSP ok). CSS `.hw`/`.hw-pop` em
  `styles.css`.
- Atribuicao: `sources.json` ganha Strong 1894 (dominio publico, so referencia;
  glosas PT sao nossas) e detalha o uso do OSHB.

Validacao:

- `python scripts/build_hebrew_tokens.py --write` (23.213 alinhados),
  `python scripts/build.py`, `python -m pytest` (84 passando, novo
  `test_hebraico_palavra_interativa`). `node --check app.js`/`sw.js`.
- Teste de navegador real (Playwright/Chromium): hover em אֱלֹהִים mostra
  "Deus..." + "substantivo · masculino · plural · absoluto"; toque (Pixel 5) em
  בְּרֵאשִׁית mostra "preposicao + substantivo · feminino · singular · absoluto";
  com a caneta ligada o toque marca e nao abre popover.

## 2026-06-26 - Titulos dos Salmos em PT e comentario judaico recolhivel

Pedidos do usuario: (1) corrigir Salmos cujo 1o versiculo nao aparecia em
portugues; (2) fazer o comentario judaico/rabinico "surgir durante os estudos
sem atrapalhar quem nao tem interesse".

Mudancas:

- **Bug dos Salmos (inscricoes)**: o texto massoretico conta o titulo do Salmo
  como versiculo 1 (ex.: `Salmos 3:1` = "מִזְמוֹר לְדָוִד..."), mas a Almeida
  PD imprime o titulo como cabecalho sem numero — 66 versiculos em 62 Salmos
  ficavam sem `texto_pt`. Novo `site/data/psalm-titles.json` (inscricoes em PT,
  renderizadas fielmente do hebraico massoretico que ja temos) e
  `scripts/fill_psalm_titles.py` (patch CIRURGICO que so preenche essas linhas
  quando vazias). NAO usei `fill_pt.py --write` completo porque ele regrediria
  177 versiculos do NT ja curados. `resolve_pt` agora aceita as inscricoes
  (cobertura de teste em `test_fill_pt.py`).
- **Comentario judaico recolhivel**: novo helper `study_disclosure()` envolve os
  blocos "Leitura judaica (contexto)" e "Comentario rabinico" num `<details
  class="study-toggle">` recolhido por padrao (disclosure nativo, sem JS inline
  — CSP ok), igual ao padrao da transliteracao. Quem tem interesse abre a seta;
  quem nao tem ignora. A nota de respeito continua visivel ao abrir. CSS
  `.study-toggle` em `styles.css`; o handler de toque (`app.js`) passa a ignorar
  `.study-toggle summary` para nao abrir a barra de estudo. Teste
  `test_leitura_judaica_contexto` atualizado para exigir o `<details>` recolhido.

Validacao:

- `python scripts/fill_psalm_titles.py --write` (66 preenchidos, 0 sobrescritos),
  `python scripts/build.py` e `python -m pytest` (verde). `node --check app.js`.
- Conferido `site/versiculos/salmos-3-1/` e `salmos-19-1/` com titulo em PT (e em
  `site/ler/salmos/3/`); `site/versiculos/deuteronomio-6-4/` com os dois blocos
  judaicos recolhidos por padrao; NT intacto (Mateus 1:1).

## 2026-06-26 - Leitura judaica de contexto (sem divergir do leitor cristao)

Pedido do usuario: incluir comentarios judaicos/rabinicos que ajudem no estudo
e entendimento SEM criar atrito com o leitor cristao. Decisoes confirmadas:
postura "so contexto, sem divergencia" (contexto linguistico/historico; evitar
passagens messianicas divergentes) e lote inicial medio (~30-40 versiculos).

Mudancas:

- Novo dado curado e VALIDADO: `site/data/jewish-readings.json` (41 versiculos
  -> `{angulo, texto}`), com resumos ORIGINAIS de contexto da tradicao judaica
  (Tora, Salmos, Proverbios, Eclesiastes e profetas mais lidos). Toda referencia
  existe no dataset e tem texto PT (validado com a regra de slug do build).
  Passagens messianicas divergentes (Isaias 53, Salmos 22, Genesis 3:15) ficaram
  de fora de proposito.
- `scripts/build.py`: nova funcao `jewish_reading_block()` (molde de
  `commentary_block`) que gera a secao "Leitura judaica (contexto)" com nota de
  respeito ("apresentado ao lado da leitura crista, nao a substitui nem
  contradiz"). Carga via `load_opt("jewish-readings.json", {})`, novo parametro
  em `build_verse_page` e chamada na montagem do corpo. Removido o bloco legado
  baseado no campo `leitura_judaica` (sempre vazio em verses.json) para nao
  duplicar o id `leitura-judaica`. O link automatico do Sefaria ("Comentario
  rabinico") permanece como porta para aprofundar.
- `tests/test_build_smoke.py`: fixture grava `jewish-readings.json` e novo teste
  `test_leitura_judaica_contexto` confirma a secao, o conteudo e a nota de
  respeito num versiculo curado, e a ausencia da secao onde nao ha curadoria.
- `CLAUDE.md`: documentada a rubrica editorial e o novo arquivo de dados.

Validacao:

- `python scripts/build.py` (31173 versiculos) e `python -m pytest` (82 passando,
  incluindo o teste novo).
- Conferido HTML gerado: `site/versiculos/deuteronomio-6-4/` (Shema) com a secao
  + nota de respeito + link Sefaria; `site/versiculos/genesis-1-1/` com o angulo
  "Sentido do hebraico" (bara); `site/versiculos/isaias-53-5/` SEM leitura
  curada (so o link automatico do Sefaria), confirmando a postura escolhida.

## 2026-06-25 - Letras vermelhas, TTS mais natural e cobertura PT do Êxodo

Pedidos do usuario: (1) vozes do audio mais naturais e com entonacao;
(2) investigar versiculos que nao apareciam no site; (3) implementar letras
vermelhas (palavras de Jesus) comecando por Jesus. Atualizar o site ao final.

Mudancas:

- Letras vermelhas: `site/data/red-letters.json` (2033 versiculos curados onde
  Jesus fala — Evangelhos + Atos + Apocalipse). `scripts/build.py` aplica a
  classe `pt pt-jesus` na pagina de versiculo e de capitulo;
  `site/assets/styles.css` colore #c62828 (claro) / #ef9a9a (escuro).
- TTS: em `scripts/build.py` (fonte do `app.js`), `speakFrom()` agora usa
  `pitch=1.1`, `volume=0.9` e `addPausesForProsody()` para pausas em pontuacao.
- Cobertura PT do Êxodo: `scripts/fill_pt.py` ganhou mapeamento explicito para
  os capitulos 7, 8, 21 e 22, onde a numeracao massoretica diverge da Almeida
  1911. Preenche 124 versiculos antes vazios (praga das ras e leis civis) com
  patch cirurgico — sem reprocessar/sobrescrever texto existente de outros
  livros (o `--write` completo regrediria NT que ja tinha PT curado).

Validacao:

- `python scripts/build.py` (31173 versiculos) e `python -m pytest` (verde),
  incluindo novos testes `test_letras_vermelhas_jesus` e
  `test_exodo_pragas_e_leis_civis`.
- Conferido HTML gerado: `site/ler/exodo/7/` com 29 paragrafos `.pt`,
  `site/versiculos/exodo-7-26/` com o texto da praga das ras; Mateus 5 em
  vermelho; Genesis 1 sem vermelho.

## 2026-06-23 - Fase 4: mapas (atlas) e planos de leitura

Pedido do usuario: concluir o que falta seguindo a mesma logica, mantendo a
arquitetura facil de revisar, e atualizar o site no GitHub ao final.

Mudancas:

- Novos dados curados e VALIDADOS contra o dataset:
  - `site/data/places.json`: 22 lugares biblicos (slug, nome, tipo, regiao,
    descricao, lat/lon, refs) agrupados em 4 regioes.
  - `site/data/reading-plans.json`: 3 planos (Joao 21 dias, Proverbios 31 dias,
    Historia da salvacao 10 dias). Cada dia e uma lista de capitulos "Livro C".
- `scripts/build.py`:
  - Mapas: atlas `/mapas/` (por regiao) e pagina por lugar `/mapas/<slug>/` com
    versiculos e LINK para o OpenStreetMap (sem embed/tiles -> CSP e offline
    preservados). Bloco "Lugares" na pagina do versiculo (chips -> atlas).
  - Planos: indice `/planos/` e pagina por plano `/planos/<slug>/` com checkbox
    por dia, barra de progresso e links para os capitulos em `/ler/`.
  - Nav reorganizada: Biblia, Planos, Temas, Dicionario, Mapas, Linha do tempo,
    Anotacoes (Artigos seguem na home e no rodape).
  - Busca e sitemap incluem lugares (tipo Lugar) e planos (tipo Plano).
- `site/assets/app.js`: modulo de progresso dos planos (localStorage
  `bec.plan.<slug>`), via `[data-plan]`/`[data-day]` (sem script inline; CSP ok).
- `site/assets/styles.css`: estilos de `.place-*` e `.plan-*`.
- `tests/test_build_smoke.py`: fixture grava `places.json` e
  `reading-plans.json`; 2 testes novos cobrem atlas/lugar/bloco no versiculo e
  indice/pagina de plano com progresso.

Validacao:

- `python scripts/build.py` (... + 22 lugares + 3 planos + ...).
- `python -m pytest` (todos passando, incluindo os testes novos).
- `node --check` em `app.js` e `sw.js`. CSP confirmada em sincronia.
- Conferido em versiculo real (Mateus 2:1 -> Belem) o bloco "Lugares" e no
  plano de Joao os 21 dias com links de capitulo. Regenerado `site/`.

Conclui a serie de 4 fases pedida (seguranca/offline/audio/busca; temas e
referencias cruzadas; dicionario e comentario; mapas e planos).

## 2026-06-23 - Fase 3: dicionario integrado e comentario teologico

Pedido do usuario: criar dicionario integrado e comentarios teologicos, com
conteudo curado. Reforco: o sistema e construido por varias IAs, entao deve
ser facil de outras (e de mim) entenderem o que foi feito.

Mudancas:

- Novos dados curados e VALIDADOS contra o dataset:
  - `site/data/glossary.json`: 14 termos do original (hebraico/grego/aramaico)
    com original, transliteracao, definicao e versiculos de exemplo.
  - `site/data/commentary.json`: 15 versiculos -> resumos ORIGINAIS, concisos,
    em uma ou mais perspectivas (Contexto/Aplicacao/Conexao).
- `scripts/build.py`:
  - Dicionario: indice `/dicionario/` (agrupado por idioma) e pagina por termo
    `/dicionario/<slug>/` com original em destaque, definicao e "Onde aparece".
  - Bloco "Palavras do original" na pagina do versiculo: chips que ligam ao
    termo do dicionario quando o versiculo e exemplo daquele termo.
  - Bloco "Comentario" na pagina do versiculo (marcado como resumo original,
    sem reproduzir comentarios protegidos).
  - Nav ganha "Dicionario"; busca e sitemap incluem os termos.
  - `load_opt()` reutilizado; indice referencia->termos montado no `main()`.
- `site/assets/styles.css`: estilos de `.comm-*`, `.gloss-chip`, `.gloss-card`,
  `.gloss-hero` e do destaque do original.
- `tests/test_build_smoke.py`: fixture grava `glossary.json` e
  `commentary.json`; 2 testes novos cobrem dicionario (indice/termo/bloco no
  versiculo/busca) e comentario teologico.
- `CLAUDE.md`: documentado o padrao data-driven das Fases 2/3 para qualquer IA
  dar continuidade (criar JSON -> validar -> load_opt -> build_* -> nav/busca/
  sitemap -> teste -> registro).

Validacao:

- `python scripts/build.py` (... + 14 termos + ...).
- `python -m pytest` (todos passando, incluindo os testes novos).
- `node --check` em `app.js` (sintaxe valida).
- Conferido no versiculo real (Joao 1:1) o bloco de comentario e o "Palavras do
  original" ligando ao termo `logos`. Regenerado `site/`.

## 2026-06-23 - Fase 2: indice de topicos e referencias cruzadas

Pedido do usuario: criar indice de topicos e referencias cruzadas, com
conteudo inicial curado (decisao registrada na Fase 1).

Contexto descoberto: `palavras`, `tema` e `artigos` estao vazios em todos os
31k versiculos, entao nao havia associacao versiculo<->tema. Para um site de
estudo, casar por palavra-chave no texto seria ruidoso; optou-se por
referencias CURADAS e VALIDADAS contra o dataset.

Mudancas:

- Novos dados curados (validados: toda referencia existe e tem texto PT):
  - `site/data/topic-refs.json`: 12 temas -> listas de versiculos.
  - `site/data/cross-references.json`: 39 versiculos -> passagens relacionadas.
- `scripts/build.py`:
  - `ref_to_slug()` e `fold()`; carga opcional `load_opt()`; slug do tema
    derivado do titulo quando ausente.
  - Indice de temas `/temas/` e pagina por tema `/temas/<slug>/` com cartoes
    de versiculo (referencia + texto) e "Para aprofundar" (artigos por
    correspondencia simples de termo).
  - Bloco "Referencias cruzadas" nas paginas de versiculo (links irmaos).
  - Home: chips de tema agora apontam para as paginas reais + link
    "Ver todos os temas"; nav e rodape apontam para `/temas/`.
  - Indice de busca: temas apontam para `/temas/<slug>/`; sitemap inclui temas.
- `site/assets/styles.css`: estilos de `.topic-card`, `.topic-count`,
  `.block-note` e ajuste de `.gl` no titulo.
- `tests/test_build_smoke.py`: fixture passa a gravar `topic-refs.json` e
  `cross-references.json` (com slug no tema) e dois testes novos cobrindo o
  indice/pagina de temas e o bloco de referencias cruzadas.

Validacao:

- `python scripts/build.py` (... + 12 temas + ...).
- `python -m pytest` (todos passando, incluindo os 2 testes novos).
- Conferido que cada tema lista a quantidade certa de versiculos e que os
  links de cross-reference apontam para paginas existentes.
- Regenerado `site/`.

## 2026-06-23 - Fase 1: seguranca, offline, audio e busca avancada

Pedido do usuario: melhorar o site para estudo biblico (varios recursos) e
reforcar a seguranca antes de testes de vulnerabilidade. Entrega acordada em
fases pequenas; esta e a Fase 1 (apenas codigo, sem novos dados de conteudo).

Mudancas:

- Seguranca (GitHub e site):
  - `SECURITY.md` com politica de divulgacao (Private Vulnerability Reporting).
  - `.github/dependabot.yml` (atualiza GitHub Actions e pip semanalmente).
  - `.github/workflows/codeql.yml` (analise estatica Python + JavaScript).
  - `tests.yml` e `deploy.yml` endurecidos: `permissions: contents: read` e
    `persist-credentials: false` no checkout.
  - `Content-Security-Policy` estrita via `<meta>` em todas as paginas: sem
    `unsafe-inline` em scripts; o unico script inline (bootstrap de tema) e
    liberado por hash sha256 calculado no build, mantido em sincronia.
  - `Referrer-Policy` via `<meta>`.
  - Removido o `onerror` inline das imagens de manuscrito (incompativel com a
    CSP); a falha passou a ser tratada por `app.js` via `data-fallback`.
- Modo offline: novo `site/sw.js` (service worker) gerado pelo build,
  registrado por `app.js`. Pre-cacheia o app-shell e guarda as paginas
  visitadas; navegacao cai para cache e, por fim, para `site/offline/`.
  O nome do cache leva `ASSET_VER`, invalidando a cada deploy.
- Audio: leitura em voz alta (Web Speech API, `pt-BR`) nas paginas de
  capitulo e versiculo, com botao Ouvir/Pausar/Parar e destaque do trecho
  lido. Sem distribuir audio de terceiros (segue a direcao ja registrada).
- Busca avancada na home: filtros por tipo (Tudo/Versiculos/Artigos/Temas),
  suporte a frase exata entre aspas, contador de resultados e escape do HTML
  dos resultados.

Validacao:

- `python scripts/build.py` (OK: 31173 versiculos + ...).
- `python -m pytest` (todos passando).
- `node --check` em `app.js`, `study.js` e `sw.js` (sintaxe valida).
- Conferido que o hash sha256 da CSP casa com o script inline emitido.
- Regenerado `site/` (inclui novo `?v=` em todos os HTML por cache-busting).

## 2026-06-21 - Guia operacional para Claude/Codex

Pedido do usuario: entender se o projeto esta organizado para outros
desenvolvedores e criar um arquivo `CLAUDE.md` para uso com Claude e Codex.

Mudanca:

- Criado `CLAUDE.md` na raiz do repositorio.
- Documentada a estrutura do projeto, fluxo de build, testes, deploy,
  regras para nao editar arquivos gerados diretamente e checklist de validacao
  manual do site publicado.

Validacao:

- Documento criado sem alterar o pipeline de build.
- Nao exige rebuild do `site/`, pois e apenas documentacao.

## 2026-06-21 - Texto grego recolhido por seta

Pedido do usuario: escritas em grego devem seguir a mesma regra visual do
hebraico com a seta `>`.

Mudanca:

- Criado `original_html()` no gerador para recolher o texto original grego em
  `details.original-toggle`.
- Hebraico e aramaico continuam com o original visivel; suas transliteracoes
  seguem em `details.translit-toggle`.
- Atualizado `study.js` gerado para ignorar cliques dentro de
  `.original-toggle`, evitando conflito com a barra de estudo.
- Atualizado CSS para `original-toggle` compartilhar o estilo de seta.
- Regenerado `site/`.

Validacao:

- `python scripts/build.py`
- `python -m pytest` (`73 passed`)
- `git diff --check` nos arquivos alterados e paginas de exemplo.

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
