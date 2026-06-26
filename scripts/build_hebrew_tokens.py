#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_hebrew_tokens.py — gera site/data/hebrew-tokens.json a partir do
OpenScriptures Hebrew Bible (OSHB / morphhb), para a interação palavra-a-palavra
do hebraico (significado + gramática ao tocar/passar o mouse).

Fonte: https://github.com/openscriptures/morphhb (texto WLC com etiqueta por
palavra: lemma Strong + código de morfologia OSHM). Licença CC-BY 4.0.

Estratégia de alinhamento: o nosso `original` (em verses.json) já vem do WLC e
tem a MESMA contagem de palavras do OSHB. Alinhamos POSICIONALMENTE (índice da
palavra). Quando a contagem diverge (segmentação diferente), o versículo é
PULADO (o site cai no texto simples, sem tooltip) — nunca desalinha.

Saída (compacta): { "Livro c:v": [[lemma, morph], ...] }  (na ordem das palavras)

Uso:
    python scripts/build_hebrew_tokens.py            # baixa (cache), alinha, relatório
    python scripts/build_hebrew_tokens.py --write    # grava hebrew-tokens.json
"""
import sys, re, json, urllib.request
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "data" / "hebrew-tokens.json"
VERSES = ROOT / "site" / "data" / "verses.json"
CACHE = Path("/tmp/oshb")
BASE = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/"

# nome PT (verses.json) -> arquivo OSHB
OSHB = {
 "Gênesis":"Gen","Êxodo":"Exod","Levítico":"Lev","Números":"Num","Deuteronômio":"Deut",
 "Josué":"Josh","Juízes":"Judg","Rute":"Ruth","1 Samuel":"1Sam","2 Samuel":"2Sam",
 "1 Reis":"1Kgs","2 Reis":"2Kgs","1 Crônicas":"1Chr","2 Crônicas":"2Chr","Esdras":"Ezra",
 "Neemias":"Neh","Ester":"Esth","Jó":"Job","Salmos":"Ps","Provérbios":"Prov",
 "Eclesiastes":"Eccl","Cânticos":"Song","Isaías":"Isa","Jeremias":"Jer","Lamentações":"Lam",
 "Ezequiel":"Ezek","Daniel":"Dan","Oseias":"Hos","Joel":"Joel","Amós":"Amos","Obadias":"Obad",
 "Jonas":"Jonah","Miquéias":"Mic","Naum":"Nah","Habacuque":"Hab","Sofonias":"Zeph",
 "Ageu":"Hag","Zacarias":"Zech","Malaquias":"Mal",
}

def fetch(book_file):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / f"{book_file}.xml"
    if not p.exists():
        url = BASE + f"{book_file}.xml"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=120).read()
        p.write_bytes(data)
    return p.read_text(encoding="utf-8")

def parse_book(xml):
    """Retorna {(ch, vs): [(lemma, morph), ...]} para um livro OSHB."""
    out = {}
    for ch, vs, body in re.findall(r'<verse osisID="[^"]+\.(\d+)\.(\d+)">(.*?)</verse>', xml, re.S):
        toks = []
        for w in re.findall(r'<w\b([^>]*)>.*?</w>', body):
            lemma = re.search(r'lemma="([^"]*)"', w)
            morph = re.search(r'morph="([^"]*)"', w)
            toks.append((lemma.group(1) if lemma else "", morph.group(1) if morph else ""))
        out[(int(ch), int(vs))] = toks
    return out

def main():
    write = "--write" in sys.argv
    verses = json.loads(VERSES.read_text(encoding="utf-8"))
    by_book = defaultdict(dict)
    for v in verses:
        m = re.search(r"(\d+):(\d+)", v["referencia"])
        if m:
            by_book[v["livro"]][(int(m.group(1)), int(m.group(2)))] = v

    result = {}
    aligned = mismatched = 0
    sample_mism = []
    for livro, bookfile in OSHB.items():
        if livro not in by_book:
            continue
        try:
            parsed = parse_book(fetch(bookfile))
        except Exception as e:
            print(f"  ! falha em {livro} ({bookfile}): {e}")
            continue
        for (ch, vs), v in by_book[livro].items():
            toks = parsed.get((ch, vs))
            if not toks:
                continue
            ours = v["original"].split()
            if len(ours) == len(toks):
                result[v["referencia"]] = [[l, m] for (l, m) in toks]
                aligned += 1
            else:
                mismatched += 1
                if len(sample_mism) < 10:
                    sample_mism.append((v["referencia"], len(ours), len(toks)))

    print(f"Alinhados: {aligned} | divergentes (fallback texto simples): {mismatched}")
    if sample_mism:
        print("Exemplos divergentes:", sample_mism)
    if write:
        OUT.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        size = OUT.stat().st_size
        print(f"\nGRAVADO em {OUT} ({size/1024/1024:.2f} MB)")
    else:
        import io
        size = len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        print(f"\n(dry-run) tamanho estimado do JSON: {size/1024/1024:.2f} MB; use --write para gravar")

if __name__ == "__main__":
    main()
