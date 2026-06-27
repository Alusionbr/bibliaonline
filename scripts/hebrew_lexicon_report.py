#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Relatório de cobertura do léxico hebraico (READ-ONLY).

Lê `site/data/hebrew-tokens.json` (lemas OSHB por palavra) e
`site/data/hebrew-lexicon.json` (glosas PT curadas) e imprime:

- a % de OCORRÊNCIAS de palavras do AT já cobertas por uma glosa PT;
- os top-N lemas (Strong) mais FREQUENTES ainda SEM glosa, para priorizar a
  próxima rodada de curadoria.

A normalização do lema espelha `headLemma()` do `app.js`: usa o ÚLTIMO número
do lema (descarta prefixos como `b/`, `d/`, `c/` e sufixos de letra). Lemas sem
número (preposições puras `l`/`b` etc.) não têm glosa por Strong e são ignorados
— corretamente, pois são palavras de função (a gramática já as descreve).

Uso:
    python scripts/hebrew_lexicon_report.py [N]

Não altera nenhum arquivo; não faz parte do build nem dos testes obrigatórios.
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS = os.path.join(ROOT, "site", "data", "hebrew-tokens.json")
LEXICON = os.path.join(ROOT, "site", "data", "hebrew-lexicon.json")


def head_strong(lemma):
    """Último número do lema (mesma regra de headLemma no app.js)."""
    for seg in reversed(str(lemma).split("/")):
        m = re.search(r"(\d+)", seg)
        if m:
            return m.group(1)
    return None


def main():
    topn = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    with open(TOKENS, encoding="utf-8") as fh:
        tokens = json.load(fh)
    with open(LEXICON, encoding="utf-8") as fh:
        lexicon = json.load(fh)
    have = set(lexicon.keys())

    counts = Counter()
    for verse in tokens.values():
        for word in verse:
            strong = head_strong(word[0])
            if strong:
                counts[strong] += 1

    total = sum(counts.values())
    covered = sum(c for k, c in counts.items() if k in have)
    pct = (100.0 * covered / total) if total else 0.0

    print("Léxico hebraico — cobertura")
    print("  lemas curados (entradas no JSON): %d" % len(have))
    print("  lemas distintos nos tokens:       %d" % len(counts))
    print("  ocorrências totais:               %d" % total)
    print("  ocorrências cobertas:             %d (%.1f%%)" % (covered, pct))
    print()
    print("Top %d lemas SEM glosa (por frequência):" % topn)
    missing = [(k, c) for k, c in counts.most_common() if k not in have]
    for strong, freq in missing[:topn]:
        print("  H%-6s %5d" % (strong, freq))


if __name__ == "__main__":
    main()
