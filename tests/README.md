# Testes

Suíte em `pytest` cobrindo a lógica de maior risco do pipeline de geração do site.

## Como rodar

```bash
pip install -r requirements-dev.txt
pytest
```

Os testes não acessam a rede nem dependem do `verses.json` real (29 MB): as
funções puras são exercitadas com dados sintéticos e o build é rodado contra um
dataset minúsculo em diretório temporário.

## O que está coberto

| Arquivo de teste | Alvo | Foco |
|---|---|---|
| `test_gen_translit.py` | `gen_translit.py` | Transliteração hebraico→latino: vav (u/o/v), shin vs. sin, begadkefat com/sem dagesh, vogais, cantilação ignorada, entradas degeneradas. |
| `test_fill_pt.py` | `fill_pt.py` | Reconciliação de numeração hebraico↔Almeida: casamento direto, Salmos (offset de título), Joel (remapeamento 4→3 caps), garantia "diverge → não inventa". |
| `test_expand_verses.py` | `expand_verses.py` | Faixas de aramaico (`is_aramaic`), `slugify` (acentos/colisões), `strip_cantillation`, integridade dos mapas OSIS/NT (66 livros). |
| `test_build.py` | `build.py` | Ordem canônica (`verse_sort_key`), `ref_chvs`, `sefaria_url`, escape de HTML (`esc`), `script_class`/`lang_label`. |
| `test_build_smoke.py` | `build.py` (integração) | Roda o build inteiro num dataset de fixture e verifica páginas geradas, links anterior/próximo, índice de busca e `sitemap.xml`. |

## Refactor associado

`fill_pt.py` ganhou a função pura `resolve_pt()`, extraída de `main()`, para que a
lógica de numeração seja testável sem download da Almeida.

## CI

`.github/workflows/tests.yml` roda a suíte em todo push e pull request. O deploy
(`deploy.yml`) depende desse job — site quebrado não é publicado.

## Última execução registrada

```
56 passed in 0.14s
```

(coletados: build_smoke=4, build=12, expand_verses=24, fill_pt=8, gen_translit=8)

## Próximos passos sugeridos (ainda não cobertos)

- Validação de integridade sobre o `verses.json` real (slugs únicos, idioma válido,
  RTL com `dir:"rtl"`, referências de `artigos` resolvíveis).
- Parsers de fontes (`parse_oshb`/`parse_nestle`/`parse_almeida`) com fixtures
  pequenas de XML/TSV.
