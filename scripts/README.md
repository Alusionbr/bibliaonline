# Scripts

Os scripts formam o pipeline do projeto. Eles sao arquivos Python independentes,
nao um pacote instalavel.

## Mapa rapido

| Script | Quando usar |
|---|---|
| `download_sources.py` | Baixar fontes externas para `raw_materials/`. Requer rede. |
| `validate_data.py` | Validar JSON curados antes de build/publicacao. |
| `expand_verses.py` | Recriar `site/data/verses.json` a partir das fontes locais. |
| `fill_pt.py` | Preencher `texto_pt`; por padrao faz dry-run, `--write` grava. |
| `gen_translit.py` | Gerar transliteracao; por padrao faz dry-run, `--write` grava. |
| `build.py` | Gerar o site estatico em `site/`. |
| `build_config.py` | Configuracao compartilhada pelo build. Nao execute diretamente. |
| `app.asset.js` | JavaScript fonte para `site/assets/app.js`. |
| `study.asset.js` | JavaScript fonte para `site/assets/study.js`. |
| `add_nt.py` | Script auxiliar historico para Novo Testamento. Revise antes de usar. |
| `make_prototype.py` | Script auxiliar historico/prototipagem. Nao faz parte do fluxo normal. |

## Fluxo normal

```bash
python scripts/expand_verses.py
python scripts/fill_pt.py --write
python scripts/gen_translit.py --write
python scripts/validate_data.py
python scripts/build.py
pytest
```

## Convencoes

- Scripts que alteram `verses.json` devem ter modo dry-run quando possivel.
- Funcoes puras devem ficar separadas de I/O para facilitar testes.
- Mudancas grandes em parser devem vir acompanhadas de fixture pequena em
  `tests/`.
- Scripts que acessam rede devem ficar fora do build normal.
