#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importa a Treasury of Scripture Knowledge (TSK, compilação de Torrey/Canne,
1880s — domínio público) para site/data/tsk-crossrefs.json, que
build.py fragmenta por livro em build_xref_shards() (mesmo padrão de
build_hebrew_tokens.py para o léxico).

Rodado manualmente, uma vez (ou quando a fonte mudar) — não faz parte do
`python scripts/build.py` normal, que continua sem precisar de internet.

Fonte recomendada: o módulo "TSK" do projeto SWORD/CrossWire
(https://www.crosswire.org/sword/modules/ModInfo.jsp?modName=TSK), listado
como domínio público no catálogo de módulos. Exporte-o (ou baixe uma cópia
já em texto simples) para um arquivo de entrada onde cada linha tem o
formato:

    Livro C:V<TAB>ref; ref; ref...

com o versículo-âncora em inglês (ex.: "Gen 1:1") e as referências alvo
separadas por ";" ou ",", cada uma como "Livro C:V" ou "Livro C:V-V"
(intervalo dentro do mesmo capítulo). Não usar o cross_references.txt do
OpenBible.info — é licenciado CC-BY, incompatível com a política de só
domínio público do site (ver site/data/sources.json).

Uso:
    python scripts/import_tsk.py caminho/para/tsk-bruto.txt

Referências que não seguem esse formato, ou cujo alvo não existe em
verses.json (a Almeida 1911 tem numeração própria em alguns livros), são
descartadas silenciosamente — um link quebrado é pior que uma referência a
menos. O resultado é limitado a MAX_REFS por versículo-âncora.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_config import BOOK_ORDER, DATA  # noqa: E402

MAX_REFS = 20

# Nomes em inglês (KJV/TSK tradicionais, incluindo abreviações comuns) -> nome
# em português usado no site (BOOK_ORDER). Cobre o cânon inteiro (AT + NT).
EN_TO_PT = {
    "Genesis": "Gênesis", "Gen": "Gênesis", "Ge": "Gênesis",
    "Exodus": "Êxodo", "Exod": "Êxodo", "Exo": "Êxodo",
    "Leviticus": "Levítico", "Lev": "Levítico",
    "Numbers": "Números", "Num": "Números",
    "Deuteronomy": "Deuteronômio", "Deut": "Deuteronômio", "Deu": "Deuteronômio",
    "Joshua": "Josué", "Josh": "Josué", "Jos": "Josué",
    "Judges": "Juízes", "Judg": "Juízes", "Jdg": "Juízes",
    "Ruth": "Rute", "Rth": "Rute",
    "1 Samuel": "1 Samuel", "1Sam": "1 Samuel", "1Sa": "1 Samuel", "I Samuel": "1 Samuel",
    "2 Samuel": "2 Samuel", "2Sam": "2 Samuel", "2Sa": "2 Samuel", "II Samuel": "2 Samuel",
    "1 Kings": "1 Reis", "1Kgs": "1 Reis", "1Ki": "1 Reis", "I Kings": "1 Reis",
    "2 Kings": "2 Reis", "2Kgs": "2 Reis", "2Ki": "2 Reis", "II Kings": "2 Reis",
    "1 Chronicles": "1 Crônicas", "1Chr": "1 Crônicas", "1Ch": "1 Crônicas", "I Chronicles": "1 Crônicas",
    "2 Chronicles": "2 Crônicas", "2Chr": "2 Crônicas", "2Ch": "2 Crônicas", "II Chronicles": "2 Crônicas",
    "Ezra": "Esdras", "Ezr": "Esdras",
    "Nehemiah": "Neemias", "Neh": "Neemias",
    "Esther": "Ester", "Esth": "Ester", "Est": "Ester",
    "Job": "Jó", "Jb": "Jó",
    "Psalms": "Salmos", "Psalm": "Salmos", "Ps": "Salmos", "Psa": "Salmos",
    "Proverbs": "Provérbios", "Prov": "Provérbios", "Pro": "Provérbios",
    "Ecclesiastes": "Eclesiastes", "Eccl": "Eclesiastes", "Ecc": "Eclesiastes",
    "Song of Solomon": "Cânticos", "Song of Songs": "Cânticos", "Song": "Cânticos", "SOS": "Cânticos",
    "Isaiah": "Isaías", "Isa": "Isaías",
    "Jeremiah": "Jeremias", "Jer": "Jeremias",
    "Lamentations": "Lamentações", "Lam": "Lamentações",
    "Ezekiel": "Ezequiel", "Ezek": "Ezequiel", "Eze": "Ezequiel",
    "Daniel": "Daniel", "Dan": "Daniel",
    "Hosea": "Oseias", "Hos": "Oseias",
    "Joel": "Joel",
    "Amos": "Amós",
    "Obadiah": "Obadias", "Obad": "Obadias", "Oba": "Obadias",
    "Jonah": "Jonas", "Jon": "Jonas",
    "Micah": "Miquéias", "Mic": "Miquéias",
    "Nahum": "Naum", "Nah": "Naum",
    "Habakkuk": "Habacuque", "Hab": "Habacuque",
    "Zephaniah": "Sofonias", "Zeph": "Sofonias", "Zep": "Sofonias",
    "Haggai": "Ageu", "Hag": "Ageu",
    "Zechariah": "Zacarias", "Zech": "Zacarias", "Zec": "Zacarias",
    "Malachi": "Malaquias", "Mal": "Malaquias",
    "Matthew": "Mateus", "Matt": "Mateus", "Mat": "Mateus",
    "Mark": "Marcos", "Mrk": "Marcos",
    "Luke": "Lucas", "Luk": "Lucas",
    "John": "João", "Jhn": "João",
    "Acts": "Atos", "Act": "Atos",
    "Romans": "Romanos", "Rom": "Romanos",
    "1 Corinthians": "1 Coríntios", "1Cor": "1 Coríntios", "1Co": "1 Coríntios", "I Corinthians": "1 Coríntios",
    "2 Corinthians": "2 Coríntios", "2Cor": "2 Coríntios", "2Co": "2 Coríntios", "II Corinthians": "2 Coríntios",
    "Galatians": "Gálatas", "Gal": "Gálatas",
    "Ephesians": "Efésios", "Eph": "Efésios",
    "Philippians": "Filipenses", "Phil": "Filipenses", "Php": "Filipenses",
    "Colossians": "Colossenses", "Col": "Colossenses",
    "1 Thessalonians": "1 Tessalonicenses", "1Thess": "1 Tessalonicenses", "1Th": "1 Tessalonicenses", "I Thessalonians": "1 Tessalonicenses",
    "2 Thessalonians": "2 Tessalonicenses", "2Thess": "2 Tessalonicenses", "2Th": "2 Tessalonicenses", "II Thessalonians": "2 Tessalonicenses",
    "1 Timothy": "1 Timóteo", "1Tim": "1 Timóteo", "1Ti": "1 Timóteo", "I Timothy": "1 Timóteo",
    "2 Timothy": "2 Timóteo", "2Tim": "2 Timóteo", "2Ti": "2 Timóteo", "II Timothy": "2 Timóteo",
    "Titus": "Tito", "Tit": "Tito",
    "Philemon": "Filemom", "Phlm": "Filemom", "Phm": "Filemom",
    "Hebrews": "Hebreus", "Heb": "Hebreus",
    "James": "Tiago", "Jas": "Tiago",
    "1 Peter": "1 Pedro", "1Pet": "1 Pedro", "1Pe": "1 Pedro", "I Peter": "1 Pedro",
    "2 Peter": "2 Pedro", "2Pet": "2 Pedro", "2Pe": "2 Pedro", "II Peter": "2 Pedro",
    "1 John": "1 João", "1Jn": "1 João", "I John": "1 João",
    "2 John": "2 João", "2Jn": "2 João", "II John": "2 João",
    "3 John": "3 João", "3Jn": "3 João", "III John": "3 João",
    "Jude": "Judas", "Jud": "Judas",
    "Revelation": "Apocalipse", "Rev": "Apocalipse",
}
assert set(BOOK_ORDER) <= set(EN_TO_PT.values()), "faltam livros no mapeamento EN_TO_PT"

# "Livro C:V" ou "Livro C:V-V" — livro pode ter prefixo numérico (1/2/3) e
# espaço, sem pontuação no meio do nome.
REF_RE = re.compile(r"^\s*([1-3]?\s?[A-Za-zÀ-ÖØ-öø-ÿ.]+)\s+(\d+):(\d+)(?:-(\d+))?\s*$")


def parse_ref(token, book_map):
    m = REF_RE.match(token)
    if not m:
        return []
    livro_en = m.group(1).strip().rstrip(".")
    livro = book_map.get(livro_en)
    if not livro:
        return []
    ch = int(m.group(2))
    v0 = int(m.group(3))
    v1 = int(m.group(4)) if m.group(4) else v0
    if v1 < v0 or v1 - v0 > 30:  # faixa absurda: provavelmente erro de parsing
        return []
    return [f"{livro} {ch}:{v}" for v in range(v0, v1 + 1)]


def load_known_refs():
    verses = json.loads((DATA / "verses.json").read_text(encoding="utf-8"))
    return {v["referencia"] for v in verses}


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    known = load_known_refs()
    out = defaultdict(list)
    skipped_anchor = skipped_target = 0

    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip() or "\t" not in line:
            continue
        anchor_raw, targets_raw = line.split("\t", 1)
        anchors = parse_ref(anchor_raw.strip(), EN_TO_PT)
        if not anchors or anchors[0] not in known:
            skipped_anchor += 1
            continue
        anchor = anchors[0]  # âncora não é expandida por intervalo (só o alvo pode ser)
        for token in re.split(r"[;,]", targets_raw):
            for ref in parse_ref(token.strip(), EN_TO_PT):
                if ref == anchor or ref not in known:
                    skipped_target += 1
                    continue
                if ref not in out[anchor] and len(out[anchor]) < MAX_REFS:
                    out[anchor].append(ref)

    dest = DATA / "tsk-crossrefs.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} versículos-âncora, {sum(len(v) for v in out.values())} referências -> {dest}")
    print(f"(descartados: {skipped_anchor} âncoras fora do dataset, {skipped_target} alvos fora do dataset)")


if __name__ == "__main__":
    main()
