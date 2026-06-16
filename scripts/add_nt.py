#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_nt.py — adiciona o Novo Testamento ao verses.json, SEM tocar no AT existente.

Fontes (baixadas na hora, ambas de domínio público):
  - Grego: Nestle 1904 (biblicalhumanities/Nestle1904), morph/Nestle1904.csv
  - Português: Almeida Revista e Corrigida (thiagobodruk/bible, pt_aa.json)

Estratégia:
  - universo = união das referências do grego (Nestle) e do PT (Almeida NT);
  - cada versículo recebe o original grego (quando há) e o texto_pt da Almeida
    (quando há) — nenhum dos dois é inventado;
  - preserva tudo que já está no verses.json (o AT e qualquer curado vencem
    por referência), e só acrescenta o que falta;
  - reordena em ordem canônica (Gênesis → Apocalipse).

Uso:
    python3 scripts/add_nt.py            # relatório (dry-run)
    python3 scripts/add_nt.py --write    # grava o verses.json
"""
import sys, json, io, re, zipfile, unicodedata, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "data" / "verses.json"

NESTLE_ZIP = "https://github.com/biblicalhumanities/Nestle1904/archive/refs/heads/master.zip"
NESTLE_CSV = "Nestle1904-master/morph/Nestle1904.csv"
ALM_URL = "https://raw.githubusercontent.com/thiagobodruk/bible/master/json/pt_aa.json"

FONTE_GR = "Novum Testamentum Graece, ed. Eberhard Nestle (1904) — domínio público."
FONTE_PT = "João Ferreira de Almeida, Revista e Corrigida (1911) — domínio público no Brasil."

# código do livro no Nestle CSV (= OSIS) -> nome em português, em ordem canônica do NT.
# A mesma ordem vale para os livros 40..66 do pt_aa.json (mapeamento por posição).
NT_ORDER = [
    ("Matt","Mateus"),("Mark","Marcos"),("Luke","Lucas"),("John","João"),("Acts","Atos"),
    ("Rom","Romanos"),("1Cor","1 Coríntios"),("2Cor","2 Coríntios"),("Gal","Gálatas"),
    ("Eph","Efésios"),("Phil","Filipenses"),("Col","Colossenses"),("1Thess","1 Tessalonicenses"),
    ("2Thess","2 Tessalonicenses"),("1Tim","1 Timóteo"),("2Tim","2 Timóteo"),("Titus","Tito"),
    ("Phlm","Filemom"),("Heb","Hebreus"),("Jas","Tiago"),("1Pet","1 Pedro"),("2Pet","2 Pedro"),
    ("1John","1 João"),("2John","2 João"),("3John","3 João"),("Jude","Judas"),("Rev","Apocalipse"),
]
OSIS_PT = {osis: pt for osis, pt in NT_ORDER}

def slugify(livro, ch, vs):
    base = unicodedata.normalize("NFKD", livro).encode("ascii","ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return f"{base}-{ch}-{vs}"

def fetch(url, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=timeout).read()

def load_greek():
    print("Baixando grego (Nestle 1904)...")
    raw = fetch(NESTLE_ZIP)
    z = zipfile.ZipFile(io.BytesIO(raw))
    lines = z.read(NESTLE_CSV).decode("utf-8", "ignore").splitlines()
    hdr = lines[0].lstrip("﻿").split("\t")
    i_bcv, i_text = hdr.index("BCV"), hdr.index("text")
    out = {}
    for l in lines[1:]:
        c = l.split("\t")
        if len(c) <= max(i_bcv, i_text):
            continue
        book, chvs = c[i_bcv].strip().rsplit(" ", 1)
        if book not in OSIS_PT or ":" not in chvs:
            continue
        ch, vs = chvs.split(":")
        out.setdefault((OSIS_PT[book], int(ch), int(vs)), []).append(c[i_text].strip())
    return {k: " ".join(w for w in v if w) for k, v in out.items()}

def load_pt():
    print("Baixando português (Almeida)...")
    alm = json.loads(fetch(ALM_URL).decode("utf-8-sig"))
    out = {}
    # NT = livros 40..66 (índices 39..65), na mesma ordem de NT_ORDER
    for i, (_, livro) in enumerate(NT_ORDER):
        book = alm[39 + i]
        for ci, chap in enumerate(book["chapters"], 1):
            for vi, txt in enumerate(chap, 1):
                out[(livro, ci, vi)] = txt
    return out

def make_verse(livro, ch, vs, original, texto_pt):
    return {
        "slug": slugify(livro, ch, vs), "referencia": f"{livro} {ch}:{vs}", "livro": livro,
        "tema": "", "idioma": "grego", "dir": "ltr",
        "original": original, "original_fonte": FONTE_GR if original else "",
        "transliteracao": "", "texto_pt": texto_pt, "texto_pt_fonte": FONTE_PT if texto_pt else "",
        "palavras": [], "contexto": "", "origem": "", "judaismo": False, "leitura_judaica": "",
        "manuscrito": {"tipo": "Não disponível com licença confirmada", "imagem": None,
                       "legenda": "Imagem de manuscrito pendente de licença para este versículo.",
                       "licenca": "A confirmar.", "fonte_nome": "", "fonte_url": ""},
        "artigos": [],
    }

def main():
    write = "--write" in sys.argv
    gr = load_greek()
    pt = load_pt()
    print(f"  grego: {len(gr)} versículos | português (NT): {len(pt)} versículos")

    existing = json.loads(OUT.read_text(encoding="utf-8"))
    present = {v["referencia"] for v in existing}

    refs = sorted(set(gr) | set(pt), key=lambda k: (k[1], k[2]))
    # ordem canônica dos livros do NT
    nt_index = {pt_nome: i for i, (_, pt_nome) in enumerate(NT_ORDER)}
    refs.sort(key=lambda k: (nt_index[k[0]], k[1], k[2]))

    added = 0
    for (livro, ch, vs) in refs:
        ref = f"{livro} {ch}:{vs}"
        if ref in present:           # nunca sobrescreve o que já existe
            continue
        existing.append(make_verse(livro, ch, vs, gr.get((livro,ch,vs),""), pt.get((livro,ch,vs),"")))
        added += 1

    # reordena tudo em ordem canônica (Gênesis → Apocalipse)
    BOOK_ORDER = ["Gênesis","Êxodo","Levítico","Números","Deuteronômio","Josué","Juízes","Rute",
    "1 Samuel","2 Samuel","1 Reis","2 Reis","1 Crônicas","2 Crônicas","Esdras","Neemias","Ester",
    "Jó","Salmos","Provérbios","Eclesiastes","Cânticos","Isaías","Jeremias","Lamentações","Ezequiel",
    "Daniel","Oseias","Joel","Amós","Obadias","Jonas","Miquéias","Naum","Habacuque","Sofonias","Ageu",
    "Zacarias","Malaquias"] + [pt for _, pt in NT_ORDER]
    def key(v):
        bi = BOOK_ORDER.index(v["livro"]) if v["livro"] in BOOK_ORDER else len(BOOK_ORDER)
        m = re.search(r"(\d+):(\d+)", v["referencia"])
        return (bi, int(m.group(1)), int(m.group(2))) if m else (bi, 0, 0)
    existing.sort(key=key)

    com_gr = sum(1 for v in existing if v["idioma"]=="grego" and v["original"])
    com_pt_nt = sum(1 for v in existing if v["idioma"]=="grego" and v["texto_pt"])
    print(f"\nNT adicionado: {added} versículos novos")
    print(f"  com grego: {com_gr} | com PT: {com_pt_nt}")
    print(f"  total no verses.json: {len(existing)}")

    if write:
        OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nGRAVADO em {OUT}")
        print("Agora rode: python3 scripts/build.py")
    else:
        print("\n(dry-run — use --write para gravar)")

if __name__ == "__main__":
    main()
