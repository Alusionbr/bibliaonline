"""Funcoes puras usadas pelo gerador estatico."""
import html
import re
import unicodedata
from collections import defaultdict

from build_config import BOOK_ORDER


def esc(s):
    return html.escape(s or "", quote=True)


def script_class(idioma, direction):
    # Aramaico biblico usa o alfabeto hebraico (rtl); transliteracoes gregas usam grego.
    if direction == "rtl":
        return "scr-hebrew"
    return "scr-greek"


def lang_label(idioma):
    return {
        "hebraico": "Hebraico",
        "grego": "Grego",
        "aramaico": "Aramaico",
    }.get(idioma, idioma.title())


def ref_chvs(referencia):
    match = re.search(r"(\d+):(\d+)", referencia)
    return (int(match.group(1)), int(match.group(2))) if match else (0, 0)


def speech_lang(idioma):
    if idioma in ("hebraico", "aramaico"):
        return "he-IL"
    if idioma == "grego":
        return "el-GR"
    return "pt-BR"


def book_slug(livro):
    base = unicodedata.normalize("NFKD", livro).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def verse_sort_key(v):
    livro = v.get("livro", "")
    book_index = BOOK_ORDER.index(livro) if livro in BOOK_ORDER else len(BOOK_ORDER)
    match = re.search(r"(\d+):(\d+)", v.get("referencia", ""))
    chapter, verse = (int(match.group(1)), int(match.group(2))) if match else (0, 0)
    return (book_index, chapter, verse)


def group_by_book_chapter(verses):
    """Agrupa versiculos ordenados em {livro: {capitulo: [versiculos]}}."""
    order = []
    struct = defaultdict(lambda: defaultdict(list))
    for verse in verses:
        livro = verse["livro"]
        if livro not in struct:
            order.append(livro)
        chapter, _ = ref_chvs(verse["referencia"])
        struct[livro][chapter].append(verse)
    return order, struct
