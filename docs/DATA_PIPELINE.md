# Pipeline de Dados

O pipeline transforma fontes publicas em JSON consumido pelo site estatico.

## Entradas esperadas

Arquivos locais em `raw_materials/`:

| Arquivo | Uso |
|---|---|
| `morphhb-master.zip` | Texto hebraico/aramaico OSHB/WLC. |
| `nestle1904-master.zip` | Texto grego do Novo Testamento. |
| `almeida_gutenberg_62383.txt` ou `almeida.json` | Traducao Almeida em dominio publico. |

`raw_materials/` nao precisa ser versionado. Ele e insumo local para regenerar
`site/data/verses.json`.

## Ordem recomendada

```bash
python scripts/download_sources.py
python scripts/expand_verses.py
python scripts/fill_pt.py --write
python scripts/gen_translit.py --write
python scripts/build.py
pytest
```

Se as fontes ja existirem em `raw_materials/`, o primeiro comando nao e
necessario.

## Arquivos em `site/data/`

| Arquivo | Tipo | Observacao de revisao |
|---|---|---|
| `verses.json` | Fonte curada | Grande e sensivel. Revise por referencia, nao por volume. |
| `articles.json` | Fonte curada | Conteudo editorial; revisar texto, slugs e referencias. |
| `topics.json` | Fonte curada | Temas exibidos na home. |
| `sources.json` | Fonte curada | Licencas, URLs e status das fontes. |
| `search-index.json` | Gerado | Saida de `scripts/build.py`. |
| `random.json` | Gerado | Saida de `scripts/build.py`. |

## Regras importantes

- Nao inventar texto quando ha divergencia de numeracao entre fontes.
- Nao substituir Almeida de dominio publico por revisao protegida.
- Manter `slug` estavel sempre que possivel; slugs quebram URLs publicas.
- Alterar dados grandes em lotes pequenos quando a mudanca precisar de revisao
  humana.
