#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fill_pt.py — preenche texto_pt (Almeida, domínio público) no verses.json.

Trata as diferenças de numeração hebraico↔português com SEGURANÇA:
- capítulos com mesmo número de versículos: casamento direto (correto);
- Salmos: deslocamento do título (o hebraico conta a inscrição como v1);
- Joel: remapeamento explícito (4 capítulos no hebraico, 3 na Almeida);
- demais capítulos com numeração divergente: deixa em branco (não inventa).

Uso:
    python scripts/fill_pt.py            # relatório (dry-run)
    python scripts/fill_pt.py --write    # grava o verses.json
"""
import sys, json, re, urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "data" / "verses.json"
ALM_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_aa.json"
NAME_FIX = {"Lamentações": "Lamentações de Jeremias", "Oseias": "Oséias"}

def load_almeida():
    req = urllib.request.Request(ALM_URL, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8-sig")
    alm = json.loads(raw)
    amap, alen, achaps = {}, {}, {}
    for b in alm:
        nm = b["name"]
        achaps[nm] = len(b["chapters"])
        for ci, chap in enumerate(b["chapters"], 1):
            alen[(nm, ci)] = len(chap)
            for vi, txt in enumerate(chap, 1):
                amap[(nm, ci, vi)] = txt
    return amap, alen, achaps

def ref_chvs(referencia):
    m = re.search(r"(\d+):(\d+)", referencia)
    return int(m.group(1)), int(m.group(2))

def main():
    write = "--write" in sys.argv
    amap, alen, achaps = load_almeida()
    verses = json.loads(OUT.read_text(encoding="utf-8"))

    # comprimento hebraico por (livro, cap)
    hlen = defaultdict(int)
    for v in verses:
        ch, vs = ref_chvs(v["referencia"])
        hlen[(v["livro"], ch)] = max(hlen[(v["livro"], ch)], vs)

    filled = 0
    empty_chaps = defaultdict(int)
    for v in verses:
        livro = v["livro"]
        nm = NAME_FIX.get(livro, livro)
        ch, vs = ref_chvs(v["referencia"])
        A = alen.get((nm, ch), 0)
        H = hlen[(livro, ch)]
        txt = ""

        if livro == "Joel":
            # Hebraico: 4 caps | Almeida: 3 caps. Hb2=27v, Alm2=32v (=Hb2+Hb3), Hb4->Alm3
            if ch == 1:
                txt = amap.get((nm, 1, vs), "")
            elif ch == 2:
                txt = amap.get((nm, 2, vs), "")
            elif ch == 3:
                txt = amap.get((nm, 2, 27 + vs), "")
            elif ch == 4:
                txt = amap.get((nm, 3, vs), "")
        elif livro == "Salmos":
            k = H - A  # nº de linhas de título (0, 1 ou 2)
            if k > 0:
                txt = amap.get((nm, ch, vs - k), "") if vs > k else ""
            else:
                txt = amap.get((nm, ch, vs), "")
        else:
            if A == H:
                txt = amap.get((nm, ch, vs), "")
            else:
                txt = ""  # numeração divergente: não inventa

        v["texto_pt"] = txt
        if txt:
            filled += 1
        else:
            empty_chaps[f"{livro} {ch}"] += 1

    total = len(verses)
    print(f"Total: {total} | com português: {filled} ({100*filled/total:.1f}%) | "
          f"em branco: {total-filled}")
    print("\nCapítulos com versículos em branco (numeração divergente / título):")
    for k, n in sorted(empty_chaps.items(), key=lambda x: -x[1])[:40]:
        print(f"  {k:30s} {n}")

    if write:
        OUT.write_text(json.dumps(verses, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nGRAVADO em {OUT}")
    else:
        print("\n(dry-run — nada gravado; use --write para gravar)")

if __name__ == "__main__":
    main()
