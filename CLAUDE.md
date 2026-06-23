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
  - Ao adicionar referencias, valide que elas existem (mesma regra de slug do
    build) antes de commitar.

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

### Modo offline

`site/sw.js` (service worker) guarda o app-shell e as paginas visitadas para
leitura sem conexao. Paginas ainda nao abertas caem em `site/offline/`.

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
