# CLAUDE.md

Guia operacional para Claude, Codex e outros desenvolvedores assistidos por IA
trabalhando neste repositorio.

## Objetivo do projeto

Este repositorio gera e publica o site estatico **Biblia em Contexto**:

- Site publicado: `https://alusionbr.github.io/bibliaonline/`
- Repositorio: `Alusionbr/bibliaonline`
- Branch principal: `main`
- Publicacao: GitHub Pages a partir da pasta `site/`

O projeto nao e uma aplicacao com backend. O conteudo final publicado fica em
HTML/CSS/JS estatico dentro de `site/`.

## Estrutura principal

- `scripts/build.py`
  - Gerador central do site.
  - Le `site/data/*.json`.
  - Gera home, paginas de livros, capitulos, versiculos, artigos, anotacoes,
    busca, sitemap, robots e assets JavaScript gerados.
  - Tambem gera `site/assets/app.js` e `site/assets/study.js`.

- `site/`
  - Saida estatica publicada pelo GitHub Pages.
  - Deve ser commitada depois de rodar `python scripts/build.py`, porque o
    workflow de deploy publica `./site` diretamente.

- `site/data/`
  - Dados de entrada do gerador, incluindo versiculos, artigos, fontes,
    topicos e indices auxiliares.
  - `topic-refs.json`: mapa tema -> lista de referencias curadas (gera as
    paginas `/temas/<slug>/`). Toda referencia deve existir no dataset e ter
    texto PT.
  - `cross-references.json`: mapa "Livro c:v" -> passagens relacionadas
    (bloco "Referencias cruzadas" na pagina do versiculo).
  - `glossary.json`: lista de termos do original (slug, termo, original,
    translit, idioma, dir, definicao, refs) que gera o dicionario em
    `/dicionario/` e o bloco "Palavras do original" no versiculo.
  - `commentary.json`: mapa "Livro c:v" -> lista de
    `{perspectiva, texto}` (bloco "Comentario" no versiculo). Os textos sao
    resumos ORIGINAIS; nao copie comentarios protegidos.
  - `jewish-readings.json`: mapa "Livro c:v" -> lista de `{angulo, texto}`
    (bloco "Leitura judaica (contexto)" no versiculo). Resumos ORIGINAIS de
    contexto da tradicao judaica. Veja a rubrica editorial em "Funcionalidades
    sensiveis".
  - `places.json`: lugares biblicos (slug, nome, tipo, regiao, descricao, lat,
    lon, refs) que geram o atlas `/mapas/` e o bloco "Lugares" no versiculo. O
    mapa e um LINK para o OpenStreetMap (sem embed/tiles), preservando CSP e
    offline.
  - `reading-plans.json`: planos de leitura (slug, titulo, descricao, dias),
    onde cada dia e uma lista de capitulos "Livro C". Gera `/planos/`; o
    progresso fica no localStorage (`bec.plan.<slug>`).
  - Ao adicionar referencias, valide que elas existem (mesma regra de slug do
    build) antes de commitar. Veja o padrao de validacao usado nas Fases 2/3.

- `site/assets/styles.css`
  - CSS mantido diretamente.
  - Alteracoes nele exigem novo build para atualizar o cache-busting dos HTMLs.

- `site/assets/app.js`
  - Gerado por `scripts/build.py`.
  - Nao editar manualmente.

- `site/assets/study.js`
  - Gerado por `scripts/build.py`.
  - Nao editar manualmente.
  - Comporta ferramentas de estudo: anotacoes, grifos, marca-texto,
    exportacao, compartilhamento e controles relacionados.

- `site/sw.js`
  - Service worker (modo offline). Gerado por `scripts/build.py`.
  - Nao editar manualmente.
  - Pre-cacheia o app-shell e guarda paginas visitadas. O nome do cache leva
    `ASSET_VER`, entao cada deploy invalida o cache antigo.

- `tests/`
  - Suite `pytest` para partes criticas do pipeline de geracao.

- `.github/workflows/tests.yml`
  - Roda `pytest` em push e pull request.

- `.github/workflows/deploy.yml`
  - Roda testes e publica `site/` no GitHub Pages.

- `REGISTRO_DE_ALTERACOES.md`
  - Caderno de bordo do projeto.
  - Use para registrar mudancas relevantes quando a alteracao tiver impacto
    funcional, de publicacao ou de arquitetura.

## Comandos essenciais

Instalar dependencias de teste:

```bash
pip install -r requirements-dev.txt
```

Rodar build completo:

```bash
python scripts/build.py
```

Rodar testes:

```bash
python -m pytest
```

Checar problemas de whitespace no diff:

```bash
git diff --check
```

Verificar status do repositorio:

```bash
git status --short --branch
```

## Fluxo correto de alteracao

1. Verifique `git status --short --branch`.
2. Entenda se a mudanca pertence ao gerador, ao CSS ou aos dados.
3. Evite editar HTML gerado manualmente.
4. Para comportamento em `app.js` ou `study.js`, edite `scripts/build.py`.
5. Para layout/visual, edite `site/assets/styles.css`.
6. Rode `python scripts/build.py`.
7. Rode `python -m pytest`.
8. Confirme exemplos gerados quando a mudanca afetar leitura:
   - `site/ler/genesis/1/index.html`
   - `site/ler/exodo/1/index.html`
   - `site/versiculos/genesis-1-1/index.html`
   - `site/versiculos/exodo-1-1/index.html`
9. Commitar tambem a pasta `site/` regenerada.
10. Abrir PR, aguardar GitHub Actions e confirmar deploy do Pages.

## Regras importantes para agentes

- Nao editar `site/assets/app.js` diretamente.
- Nao editar `site/assets/study.js` diretamente.
- Nao editar `site/sw.js` diretamente.
- Nao editar paginas em `site/ler/` ou `site/versiculos/` diretamente.
- Se um HTML gerado precisa mudar, altere `scripts/build.py` e rode o build.
- Preserve alteracoes existentes no worktree. Nao use `git reset --hard` sem
  autorizacao explicita.
- Use branches pequenas a partir de `main`.
- Prefira PRs pequenos e descritivos.
- Depois de merge em `main`, confirme:
  - workflow `Tests` com sucesso;
  - workflow `Deploy site to GitHub Pages` com sucesso;
  - site ao vivo carregando o novo asset com `?v=<hash>`.

## Arquitetura de geracao

O build segue este fluxo geral:

1. Carrega dados de `site/data`.
2. Ordena versiculos pela ordem canonica.
3. Agrupa por livro e capitulo.
4. Gera:
   - home;
   - indice de livros;
   - linha do tempo;
   - pagina de cada livro;
   - pagina de cada capitulo;
   - pagina individual de cada versiculo;
   - artigos;
   - pagina de anotacoes;
   - indice de busca;
   - pool de versiculos aleatorios;
   - sitemap, robots, manifest e 404.
5. Escreve `site/assets/app.js`.
6. Escreve `site/assets/study.js`.
7. Calcula cache-busting dos assets com base em `scripts/build.py` e
   `site/assets/styles.css`.

## Padrao para adicionar conteudo curado (Fases 2/3)

Varias IAs trabalham neste repo. Recursos novos seguem SEMPRE o mesmo padrao
data-driven, para serem faceis de entender e continuar:

1. Crie/edite um arquivo de dados em `site/data/*.json` (curado).
2. VALIDE que toda referencia citada existe no dataset e tem texto PT antes de
   commitar (a regra de slug e `book_slug(livro) + "-c-v"`; veja
   `ref_to_slug()` em `scripts/build.py`). Trocar uma referencia sem PT por uma
   equivalente que tenha PT e aceitavel (diferencas de numeracao
   hebraico<->Almeida deixam alguns versiculos sem PT).
3. Carregue o arquivo no `main()` com `load_opt(nome, default)` (carga
   opcional: nao quebra os testes/fixtures que nao tem o arquivo).
4. Gere as paginas com uma funcao `build_*` dedicada e/ou um bloco
   `*_block(...)` na pagina do versiculo.
5. Ligue na navegacao, no indice de busca (`build_search_index`) e no sitemap
   (`build_meta`) quando fizer sentido.
6. Acrescente um teste no smoke test (`tests/test_build_smoke.py`): a fixture
   grava um exemplo do novo JSON e um teste verifica a saida.
7. Rode `python scripts/build.py` e `python -m pytest`. Regenere `site/`.
8. Registre no `REGISTRO_DE_ALTERACOES.md`.

Exemplos ja implementados: `topic-refs.json` (temas), `cross-references.json`
(referencias cruzadas), `glossary.json` (dicionario), `commentary.json`
(comentario teologico), `places.json` (mapas/atlas), `reading-plans.json`
(planos de leitura), `jewish-readings.json` (leitura judaica de contexto).

## Funcionalidades sensiveis

### Transliteracao

Nas paginas de capitulo e versiculo, a transliteracao fica recolhida por
padrao em um disclosure nativo (`details.translit-toggle`). O texto original
permanece visivel; a transliteracao aparece apenas ao abrir a seta.

### Ferramentas de estudo

A barra contextual aparece quando o usuario seleciona/toca um versiculo. Ela
oferece:

- grifar versiculo;
- anotar;
- copiar;
- compartilhar.

A caixa de nota deve abrir dentro do fluxo do versiculo selecionado, sem cobrir
o texto.

### Marca-texto

A canetinha ativa o modo de marcar palavras. Com ela ligada:

- tocar/arrastar marca palavras;
- duplo toque/click rapido na mesma palavra marcada remove a marcacao;
- a opcao `x` da paleta remove marcacoes ao arrastar.

### Armazenamento local

Anotacoes, grifos, preferencias e historico ficam em `localStorage` do
navegador. Nao ha backend para esses dados.

### Audio (leitura em voz alta)

Paginas de capitulo e versiculo tem uma barra `data-audio` que usa a Web
Speech API (`speechSynthesis`, `pt-BR`) para ler o texto em portugues. O
controle so aparece se o navegador suportar a API. Nao distribuimos arquivos
de audio de terceiros.

### Leitura judaica (contexto)

`jewish-readings.json` alimenta o bloco "Leitura judaica (contexto)" na pagina
do versiculo (`jewish_reading_block` em `scripts/build.py`). O objetivo e
ajudar no estudo SEM criar atrito com o leitor cristao. Rubrica editorial para
quem adicionar conteudo:

- Texto sempre RESUMO ORIGINAL; nunca copiar Rashi/Talmud/Midrash/Sefaria
  verbatim (mesma regra de `commentary.json`).
- So CONTEXTO linguistico/historico: sentido do hebraico, costumes, mundo
  antigo, uso na tradicao e na liturgia judaica.
- EVITAR passagens messianicas divergentes (ex.: Isaias 53, Salmos 22,
  Genesis 3:15). A postura escolhida e "so contexto, sem divergencia": nesses
  versiculos fica apenas o link automatico do Sefaria, sem leitura curada.
- O bloco traz uma nota de respeito fixa: contexto da tradicao judaica,
  apresentado ao lado da leitura crista, sem substitui-la nem contradize-la.
- O bloco "Comentario rabinico" (link para o Sefaria) continua automatico em
  versiculos do AT, como porta para aprofundar.
- Validar referencias (existir no dataset + ter PT) antes de commitar.

### Modo offline

`site/sw.js` (service worker) guarda o app-shell e as paginas visitadas para
leitura sem conexao. Paginas ainda nao abertas caem em `site/offline/`.

### Mapas (atlas)

`/mapas/` lista lugares por regiao; cada lugar tem pagina propria com os
versiculos onde aparece e um LINK para o OpenStreetMap (sem embed nem tiles,
para nao quebrar a CSP nem o modo offline). O bloco "Lugares" no versiculo liga
de volta ao atlas.

### Planos de leitura

`/planos/` traz planos com checkbox por dia. O progresso fica no localStorage
(`bec.plan.<slug>`), sem servidor. O wiring esta em `app.js` (procura
`[data-plan]`).

### Seguranca (CSP)

Todas as paginas tem `Content-Security-Policy` estrita via `<meta>`. Nao ha
`unsafe-inline` em scripts: o unico script inline (bootstrap de tema, em
`THEME_BOOTSTRAP`) e liberado por um hash sha256 calculado no build. Se mudar
esse script, o hash se atualiza sozinho — mas nao adicione novos scripts
inline nem atributos de evento inline (`onclick`, `onerror`), pois a CSP os
bloqueia. Use `addEventListener` em `app.js`/`study.js`.

## Validacao manual recomendada

Depois de publicar, testar no site ao vivo:

- `https://alusionbr.github.io/bibliaonline/ler/exodo/1/`
- `https://alusionbr.github.io/bibliaonline/versiculos/exodo-1-1/`

Checklist:

- transliteracao nao aparece aberta no carregamento;
- seta abre e fecha a transliteracao;
- toque no versiculo mostra a barra contextual;
- botao de anotacao abre textarea perto do versiculo;
- texto de portugues nao fica coberto pela interface;
- canetinha liga/desliga;
- palavra marcada pode ser desmarcada por duplo toque/click;
- pagina funciona em largura mobile.

## Observacoes sobre cache

O site usa query string `?v=<hash>` em assets para reduzir cache antigo. Mesmo
assim, Safari/Chrome em celular podem manter arquivos por alguns minutos. Ao
validar bug corrigido, recarregue a pagina ou use query string temporaria, por
exemplo:

```text
https://alusionbr.github.io/bibliaonline/ler/exodo/1/?check=YYYYMMDD
```

## Quando envolver o usuario

Pergunte antes de:

- alterar dados biblicos fonte;
- mudar estrategia de traducao/transliteracao;
- remover funcionalidade existente;
- mexer em workflows de deploy;
- apagar historico, branches ou arquivos em massa.

Para ajustes pequenos de UI, bugs de comportamento, testes e documentacao,
implemente em branch, valide e abra PR.
