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
TITLES = ROOT / "site" / "data" / "psalm-titles.json"
ALM_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_aa.json"
NAME_FIX = {"Lamentações": "Lamentações de Jeremias", "Oseias": "Oséias"}

def load_psalm_titles():
    # inscrições (títulos) dos Salmos em PT — a Almeida de domínio público as
    # imprime como cabeçalho sem número, então o hebraico (que conta o título
    # como v1) ficava sem texto_pt. Aqui preenchemos essas linhas de título.
    if TITLES.exists():
        return json.loads(TITLES.read_text(encoding="utf-8"))
    return {}

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

def resolve_pt(livro, ch, vs, amap, A, H, titles=None):
    """Resolve o texto Almeida (PT) para um versículo, tratando as diferenças
    de numeração hebraico↔português. Função pura (sem I/O) para ser testável.

    livro: nome do livro em PT (como no verses.json)
    ch, vs: capítulo e versículo (numeração hebraica)
    amap: dict {(nome_almeida, cap, vers): texto}
    A: nº de versículos do capítulo na Almeida (alen)
    H: nº de versículos do capítulo no hebraico (hlen)
    titles: dict {"Salmos c:v": título PT} para as inscrições dos Salmos
    Retorna o texto PT ou "" quando a numeração diverge (não inventa)."""
    titles = titles or {}
    nm = NAME_FIX.get(livro, livro)
    if livro == "Joel":
        # Hebraico: 4 caps | Almeida: 3 caps. Hb2=27v, Alm2=32v (=Hb2+Hb3), Hb4->Alm3
        if ch == 1:
            return amap.get((nm, 1, vs), "")
        elif ch == 2:
            return amap.get((nm, 2, vs), "")
        elif ch == 3:
            return amap.get((nm, 2, 27 + vs), "")
        elif ch == 4:
            return amap.get((nm, 3, vs), "")
        return ""
    elif livro == "Êxodo":
        # Numeração massorética (hebraica) ≠ Almeida em dois trechos:
        # "Praga das rãs": Heb 7 tem 29v, Alm 7 tem 25v.
        #   Heb 7:1-25  = Alm 7:1-25 ; Heb 7:26-29 = Alm 8:1-4
        #   Heb 8 (28v) = Alm 8:5-32 (deslocamento +4)
        if ch == 7:
            if vs <= 25:
                return amap.get((nm, 7, vs), "")
            return amap.get((nm, 8, vs - 25), "")  # 26->8:1 ... 29->8:4
        elif ch == 8:
            return amap.get((nm, 8, vs + 4), "")    # 1->8:5 ... 28->8:32
        # "Leis civis": Heb 21 tem 37v, Alm 21 tem 36v.
        #   Heb 21:1-36 = Alm 21:1-36 ; Heb 21:37 = Alm 22:1
        #   Heb 22 (30v) = Alm 22:2-31 (deslocamento +1)
        elif ch == 21:
            if vs <= 36:
                return amap.get((nm, 21, vs), "")
            return amap.get((nm, 22, 1), "")        # 21:37 -> 22:1
        elif ch == 22:
            return amap.get((nm, 22, vs + 1), "")   # 1->22:2 ... 30->22:31
        # demais capítulos do Êxodo: casamento direto quando bate
        if A == H:
            return amap.get((nm, ch, vs), "")
        return ""
    elif livro == "Salmos":
        k = H - A  # nº de linhas de título (0, 1 ou 2)
        if k > 0:
            if vs <= k:
                # linha de inscrição (título): a Almeida não a numera; usa a
                # inscrição curada (psalm-titles.json) quando disponível
                return titles.get(f"Salmos {ch}:{vs}", "")
            return amap.get((nm, ch, vs - k), "")
        return amap.get((nm, ch, vs), "")
    else:
        if A == H:
            return amap.get((nm, ch, vs), "")
        return ""  # numeração divergente: não inventa

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
        txt = resolve_pt(livro, ch, vs, amap, A, H)

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
