# Arquitetura

Este projeto publica um site estatico. Nao ha backend em producao: toda pagina
publica e arquivo em `site/`, e as funcionalidades de leitura usam JavaScript no
navegador com `localStorage`.

## Componentes

| Componente | Responsabilidade |
|---|---|
| `scripts/expand_verses.py` | Monta `site/data/verses.json` a partir de fontes locais em `raw_materials/`. |
| `scripts/fill_pt.py` | Preenche `texto_pt` com Almeida de dominio publico, preservando divergencias de numeracao. |
| `scripts/gen_translit.py` | Gera transliteracao aproximada para hebraico/aramaico. |
| `scripts/validate_data.py` | Valida slugs, campos obrigatorios, idioma/direcao e referencias entre JSON curados. |
| `scripts/build.py` | Gera home, paginas por versiculo, artigos, leitura por livro/capitulo, JS gerado, sitemap, robots e manifest. |
| `scripts/build_config.py` | Configuracao estavel do build: URL publica, nome do site, ordem canonica, linha do tempo e links externos. |
| `scripts/app.asset.js` e `scripts/study.asset.js` | JavaScript fonte que o build publica em `site/assets/`. |
| `site/data/*.json` | Entrada do build e alguns artefatos derivados. |
| `site/assets/styles.css` | Estilo mantido manualmente. |
| `tests/` | Testes de funcoes puras e build completo com fixture pequena. |

## Fonte versus artefato

Considere como fonte revisavel:

- `scripts/*.py`
- `scripts/*.asset.js`
- `site/assets/styles.css`
- `site/data/verses.json`
- `site/data/articles.json`
- `site/data/topics.json`
- `site/data/sources.json`
- `site/data/book-intros.json`, `glossary.json`, `places.json`, `topic-refs.json`, `hebrew-lexicon.json`
- `tests/*.py`
- documentacao em `README.md`, `docs/`, `scripts/README.md` e `site/data/README.md`

Considere como artefato gerado:

- `site/**/*.html`
- `site/assets/app.js`
- `site/assets/study.js`
- `site/sitemap.xml`
- `site/robots.txt`
- `site/manifest.webmanifest`
- `site/data/search-index.json`, `random.json`, `daily.json`, `plan-index.json`,
  `chapter-verses.json` e `site/data/tokens/`

Os artefatos gerados **nao sao versionados** (estao no `.gitignore`). O
workflow de deploy roda `python scripts/build.py` e publica o resultado; para
ver o site localmente, rode o build antes de servir `site/`.

## Biblioteca de referencia

`scripts/build_reference.py` monta o conteudo de `/temas/`, `/dicionario/`,
`/mapas/`, `/lexico/hebraico/` e do "Panorama do livro" (`/ler/<livro>/`). O
modulo devolve objetos `Page` (url, titulo, descricao, corpo, JSON-LD) e o
`build.py` escreve cada um com head/nav/footer; assim o modulo nao depende de
`SITE`/`DATA` e e facil de testar. A frequencia do lexico hebraico e contada a
partir de `site/data/hebrew-tokens.json` (numeracao de Strong do WLC).

## Build

`scripts/build.py` le os JSON em `site/data/`, ordena os versiculos pela ordem
canonica, agrupa por livro/capitulo e reescreve as saidas geradas em `site/`.

O build remove antes as pastas geradas:

- `site/versiculos/`
- `site/artigos/`
- `site/ler/`
- `site/anotacoes/`

Em seguida recria paginas, assets JS gerados, indice de busca, pool aleatorio,
sitemap, robots, manifest e 404.

## Decisoes de projeto

- Site estatico: reduz custo operacional e simplifica publicacao no GitHub Pages.
- Dados em JSON: facilita auditoria manual e testes com fixtures pequenas.
- Testes em cima de funcoes puras: mantem confianca sem depender dos JSON grandes.
- Artefatos gerados versionados: simplifica deploy, mas exige disciplina de review.

## Dividas tecnicas conhecidas

- `scripts/build.py` ainda concentra templates HTML. A configuracao, utilitarios,
  assets JS e orquestracao principal ja foram separados; novas refatoracoes devem
  manter os smoke tests verdes antes de mover blocos maiores.
- `site/data/verses.json` e grande; mudancas manuais devem ser pequenas,
  justificadas e revisadas por referencia biblica.
- Validacoes sobre o dataset real cobrem slugs, campos obrigatorios,
  idioma/direcao e referencias de artigos. Ainda podem crescer para regras
  biblicas mais especificas, como cobertura esperada por livro.
