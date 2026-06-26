#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_psalm_titles.py — patch CIRÚRGICO: preenche o texto_pt das inscrições
(títulos) dos Salmos a partir de site/data/psalm-titles.json.

Por que existe: o texto massorético conta a inscrição do Salmo como versículo 1
(ex.: Salmos 3:1 = "מִזְמוֹר לְדָוִד..."), mas a Almeida de domínio público
imprime o título como cabeçalho SEM número — então esses versículos ficavam sem
texto_pt e apareciam vazios no site.

Diferente de fill_pt.py (que reprocessa todo o texto a partir da fonte e
sobrescreveria o NT já curado), este script SÓ toca os versículos de título
listados em psalm-titles.json e SÓ quando estão vazios. Nada mais é alterado.

Uso:
    python scripts/fill_psalm_titles.py            # relatório (dry-run)
    python scripts/fill_psalm_titles.py --write    # grava o verses.json
"""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "data" / "verses.json"
TITLES = ROOT / "site" / "data" / "psalm-titles.json"
FONTE = "Inscrição do Salmo (do hebraico massorético) — domínio público."

def main():
    write = "--write" in sys.argv
    titles = json.loads(TITLES.read_text(encoding="utf-8"))
    verses = json.loads(OUT.read_text(encoding="utf-8"))
    byref = {v["referencia"]: v for v in verses}

    filled, skipped, missing = 0, 0, []
    for ref, title in titles.items():
        v = byref.get(ref)
        if v is None:
            missing.append(ref)
            continue
        if (v.get("texto_pt") or "").strip():
            skipped += 1  # já tem PT: não sobrescreve
            continue
        v["texto_pt"] = title
        v["texto_pt_fonte"] = FONTE
        filled += 1

    print(f"Inscrições no arquivo: {len(titles)}")
    print(f"Preenchidas (estavam vazias): {filled}")
    print(f"Puladas (já tinham PT): {skipped}")
    if missing:
        print(f"AVISO — refs inexistentes no dataset: {missing}")

    if write:
        OUT.write_text(json.dumps(verses, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nGRAVADO em {OUT}")
    else:
        print("\n(dry-run — nada gravado; use --write para gravar)")

if __name__ == "__main__":
    main()
