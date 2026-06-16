#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_translit.py — gera transliteração fonética (aproximada) do hebraico/aramaico
para o campo `transliteracao` de cada versículo do verses.json.

É uma transliteração de leitura (para quem não lê o alfabeto hebraico), não um
sistema acadêmico estrito: trata begadkefat (dagesh), shuruq/holam com vav,
shin/sin e as vogais (niqqud). Boa para ler em voz alta, não perfeita.

Uso:
    python scripts/gen_translit.py            # relatório (dry-run)
    python scripts/gen_translit.py --write    # grava o verses.json
"""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site" / "data" / "verses.json"

# consoantes (forma normal e final compartilham som)
CONS = {
    "א": "", "ב": "v", "ג": "g", "ד": "d", "ה": "h",
    "ו": "v", "ז": "z", "ח": "ch", "ט": "t", "י": "y",
    "ך": "kh", "כ": "kh", "ל": "l", "ם": "m", "מ": "m",
    "ן": "n", "נ": "n", "ס": "s", "ע": "", "ף": "f",
    "פ": "f", "ץ": "ts", "צ": "ts", "ק": "q", "ר": "r",
    "ש": "sh", "ת": "t",
}
# vogais (niqqud)
VOWEL = {
    "ְ": "e",  # sheva (vocal aproximada)
    "ֱ": "e", "ֲ": "a", "ֳ": "o",  # hatafs
    "ִ": "i",  # hiriq
    "ֵ": "e", "ֶ": "e",  # tsere, segol
    "ַ": "a", "ָ": "a",  # patah, qamats
    "ֹ": "o", "ֺ": "o",  # holam
    "ֻ": "u",  # qubuts
}
DAGESH = "ּ"
SHIN_DOT = "ׁ"
SIN_DOT = "ׂ"
# begadkefat: com dagesh muda o som
BEGAD = {"ב": "b", "כ": "k", "פ": "p"}


def translit_word(w):
    out = []
    i, n = 0, len(w)
    while i < n:
        c = w[i]
        if c not in CONS:
            i += 1
            continue
        # coleta marcas combinantes seguintes
        marks = []
        j = i + 1
        while j < n and ("ְ" <= w[j] <= "ׂ"):
            marks.append(w[j]); j += 1
        has_dag = DAGESH in marks
        # vav: shuruq (וּ) ou holam male (וֹ)
        if c == "ו":
            if has_dag and not any(m in VOWEL for m in marks):
                out.append("u"); i = j; continue
            if "ֹ" in marks or "ֺ" in marks:
                out.append("o"); i = j; continue
            base = "v"
        elif c == "ש":  # shin/sin
            base = "s" if SIN_DOT in marks else "sh"
        elif c in BEGAD and has_dag:
            base = BEGAD[c]
        else:
            base = CONS[c]
        out.append(base)
        for m in marks:
            if m in VOWEL:
                out.append(VOWEL[m])
        i = j
    return "".join(out)


def transliterate(text):
    return " ".join(translit_word(w) for w in text.split() if w).strip()


def main():
    write = "--write" in sys.argv
    verses = json.loads(OUT.read_text(encoding="utf-8"))
    done = 0
    samples = []
    for v in verses:
        if v.get("idioma") in ("hebraico", "aramaico") and v.get("original"):
            t = transliterate(v["original"])
            v["transliteracao"] = t
            if t:
                done += 1
                if v["referencia"] in ("Gênesis 1:1", "Salmos 23:1", "Êxodo 20:2"):
                    samples.append((v["referencia"], t))
    print(f"Transliteração gerada para {done} versículos.")
    for ref, t in samples:
        print(f"  {ref}: {t}")
    if write:
        OUT.write_text(json.dumps(verses, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"GRAVADO em {OUT}")
    else:
        print("(dry-run — use --write para gravar)")


if __name__ == "__main__":
    main()
