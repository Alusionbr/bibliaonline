#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_crossrefs.py — gera as referências cruzadas ("Veja também") por versículo.

Fonte: OpenBible.info cross references (derivado do Treasury of Scripture
Knowledge, domínio público) — https://www.openbible.info/labs/cross-references/
Licença do conjunto curado: Creative Commons Attribution. O crédito aparece na
seção "Metodologia" da home.

O arquivo de origem é um TSV com cabeçalho `From Verse\tTo Verse\tVotes`, com
referências no estilo OSIS (`Gen.1.1`) e intervalos (`Gen.1.1-Gen.1.5`). Aqui
mapeamos cada referência para o nosso `slug` (`livro-capítulo-versículo`),
ficamos com as ~6 mais votadas por versículo e filtramos para os slugs que
existem de fato no verses.json (evita link morto por diferença de numeração
entre o original e a edição Almeida 1911).

Uso:
    python scripts/gen_crossrefs.py            # relatório (dry-run, baixa o dataset)
    python scripts/gen_crossrefs.py --write    # grava site/data/crossrefs.json
"""
import io
import json
import re
import sys
import unicodedata
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSES = ROOT / "site" / "data" / "verses.json"
OUT = ROOT / "site" / "data" / "crossrefs.json"
SOURCE_URL = "https://a.openbible.info/data/cross-references.zip"
TOP_N = 6

# abreviação OSIS → nome do livro em português (mesma ordem/cânon do build)
OSIS_PT = {
    "Gen": "Gênesis", "Exod": "Êxodo", "Lev": "Levítico", "Num": "Números",
    "Deut": "Deuteronômio", "Josh": "Josué", "Judg": "Juízes", "Ruth": "Rute",
    "1Sam": "1 Samuel", "2Sam": "2 Samuel", "1Kgs": "1 Reis", "2Kgs": "2 Reis",
    "1Chr": "1 Crônicas", "2Chr": "2 Crônicas", "Ezra": "Esdras", "Neh": "Neemias",
    "Esth": "Ester", "Job": "Jó", "Ps": "Salmos", "Prov": "Provérbios",
    "Eccl": "Eclesiastes", "Song": "Cânticos", "Isa": "Isaías", "Jer": "Jeremias",
    "Lam": "Lamentações", "Ezek": "Ezequiel", "Dan": "Daniel", "Hos": "Oseias",
    "Joel": "Joel", "Amos": "Amós", "Obad": "Obadias", "Jonah": "Jonas",
    "Mic": "Miquéias", "Nah": "Naum", "Hab": "Habacuque", "Zeph": "Sofonias",
    "Hag": "Ageu", "Zech": "Zacarias", "Mal": "Malaquias", "Matt": "Mateus",
    "Mark": "Marcos", "Luke": "Lucas", "John": "João", "Acts": "Atos",
    "Rom": "Romanos", "1Cor": "1 Coríntios", "2Cor": "2 Coríntios", "Gal": "Gálatas",
    "Eph": "Efésios", "Phil": "Filipenses", "Col": "Colossenses",
    "1Thess": "1 Tessalonicenses", "2Thess": "2 Tessalonicenses", "1Tim": "1 Timóteo",
    "2Tim": "2 Timóteo", "Titus": "Tito", "Phlm": "Filemom", "Heb": "Hebreus",
    "Jas": "Tiago", "1Pet": "1 Pedro", "2Pet": "2 Pedro", "1John": "1 João",
    "2John": "2 João", "3John": "3 João", "Jude": "Judas", "Rev": "Apocalipse",
    # alguns apelidos OSIS alternativos, por segurança
    "Psa": "Salmos", "Php": "Filipenses", "Sng": "Cânticos", "Jhn": "João",
}


def slugify_book(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def osis_to_slug(osis):
    """`Gen.1.1` (ou um intervalo `Gen.1.1-Gen.2.3`) → `genesis-1-1`. '' se desconhecido."""
    if not osis:
        return ""
    osis = osis.split("-", 1)[0]  # intervalos: usa o versículo inicial
    parts = osis.split(".")
    if len(parts) != 3:
        return ""
    book, ch, vs = parts
    nome = OSIS_PT.get(book)
    if not nome or not ch.isdigit() or not vs.isdigit():
        return ""
    return f"{slugify_book(nome)}-{int(ch)}-{int(vs)}"


def parse_refs(text, valid_slugs, top_n=TOP_N):
    """TSV `From\tTo\tVotes` → {fromSlug: [toSlug,…]} (top N por votos, sem link morto)."""
    agg = defaultdict(list)  # fromSlug -> [(votes, toSlug)]
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("From Verse"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        frm, to, votes = parts[0], parts[1], parts[2]
        try:
            votes = int(votes)
        except ValueError:
            continue
        if votes <= 0:
            continue
        fs, ts = osis_to_slug(frm), osis_to_slug(to)
        if not fs or not ts or fs == ts:
            continue
        agg[fs].append((votes, ts))

    out = {}
    for fs, lst in agg.items():
        if fs not in valid_slugs:
            continue
        lst.sort(key=lambda x: -x[0])
        seen, picked = set(), []
        for _votes, ts in lst:
            if ts in seen or ts not in valid_slugs:
                continue
            seen.add(ts)
            picked.append(ts)
            if len(picked) >= top_n:
                break
        if picked:
            out[fs] = picked
    return out


def download_text():
    data = urllib.request.urlopen(SOURCE_URL, timeout=60).read()
    zf = zipfile.ZipFile(io.BytesIO(data))
    name = next(n for n in zf.namelist() if n.endswith(".txt"))
    return zf.read(name).decode("utf-8")


def load_valid_slugs():
    verses = json.loads(VERSES.read_text(encoding="utf-8"))
    return {v["slug"] for v in verses}


def main():
    write = "--write" in sys.argv
    valid = load_valid_slugs()
    print(f"versículos no verses.json: {len(valid)}")
    text = download_text()
    refs = parse_refs(text, valid)
    links = sum(len(v) for v in refs.values())
    print(f"versículos com referências: {len(refs)} · links totais: {links}")
    if write:
        OUT.write_text(json.dumps(refs, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"gravado: {OUT} ({OUT.stat().st_size/1024:.0f} KB)")
    else:
        print("(dry-run; use --write para gravar site/data/crossrefs.json)")


if __name__ == "__main__":
    main()
