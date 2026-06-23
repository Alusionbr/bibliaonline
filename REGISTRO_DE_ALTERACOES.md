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
