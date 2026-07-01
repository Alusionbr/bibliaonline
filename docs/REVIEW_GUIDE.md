# Guia de Revisao Humana

Use este guia para revisar mudancas sem se perder no volume de arquivos gerados.

## Ordem de revisao

1. Leia a descricao da mudanca e identifique se ela e codigo, dado, layout ou build.
2. Revise primeiro arquivos-fonte: `scripts/`, `tests/`, `site/data/` curado e CSS.
3. Rode `python scripts/validate_data.py` quando a mudanca afetar `site/data/`.
4. Rode `ruff check .`.
5. Rode `pytest`.
6. Se a mudanca afeta o site, rode `python scripts/build.py`.
7. Revise artefatos gerados apenas para confirmar o efeito esperado.

## O que merece mais atencao

| Area | Risco |
|---|---|
| `scripts/expand_verses.py` | Parser pode perder versiculos ou montar referencias erradas. |
| `scripts/fill_pt.py` | Numeracao divergente pode associar traducao ao versiculo errado. |
| `scripts/build.py` | Pode quebrar navegacao, SEO, busca, anotacoes ou HTML. |
| `site/data/verses.json` | Mudancas grandes podem esconder erro de texto, slug ou referencia. |
| `site/assets/styles.css` | Regressao visual em mobile, leitura RTL ou ferramentas flutuantes. |

## Como revisar diffs grandes

- Trate `site/**/*.html`, `site/assets/app.js`, `site/assets/study.js`,
  `site/sitemap.xml`, `site/robots.txt`, `site/manifest.webmanifest`,
  `site/data/search-index.json` e `site/data/random.json` como saidas geradas.
- Se o diff gerado for enorme, revise a causa em `scripts/build.py` ou nos JSON
  de entrada.
- Para `verses.json`, filtre por `slug`, `referencia` ou livro. Nao revise o
  arquivo inteiro visualmente.

## Checklist antes de aceitar

- `pytest` passou.
- `ruff check .` passou.
- `python scripts/validate_data.py` passou quando houve mudanca em dados curados.
- O build local executou sem erro quando aplicavel.
- Nao ha fonte com copyright indevido.
- Slugs publicos nao mudaram sem justificativa.
- Mudancas editoriais citam ou preservam a fonte.
- Artefatos gerados batem com a mudanca de fonte.

## Comandos uteis

```bash
pytest
ruff check .
python scripts/validate_data.py
python scripts/build.py
git diff --stat
git diff -- scripts site/data/verses.json site/assets/styles.css
```
