#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida os JSON curados usados pelo build.

Uso:
    python scripts/validate_data.py
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site" / "data"

VALID_LANGS = {"hebraico", "aramaico", "grego"}
VALID_DIRS = {"rtl", "ltr"}
EXPECTED_DIR_BY_LANG = {
    "hebraico": "rtl",
    "aramaico": "rtl",
    "grego": "ltr",
}

REQUIRED_VERSE_FIELDS = {
    "slug",
    "referencia",
    "livro",
    "idioma",
    "dir",
    "original",
    "original_fonte",
    "transliteracao",
    "texto_pt",
    "texto_pt_fonte",
    "palavras",
    "contexto",
    "origem",
    "judaismo",
    "leitura_judaica",
    "artigos",
    "manuscrito",
}

REQUIRED_ARTICLE_FIELDS = {
    "slug",
    "titulo",
    "resumo",
    "conteudo",
}


def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def duplicate_values(rows, key):
    counts = Counter(row.get(key, "") for row in rows)
    return sorted(value for value, count in counts.items() if value and count > 1)


def slugify_book_ref(livro, referencia):
    match = re.search(r"(\d+):(\d+)", referencia or "")
    if not match:
        return ""
    base = unicodedata.normalize("NFKD", livro or "").encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    return f"{base}-{int(match.group(1))}-{int(match.group(2))}"


def validate_verses(verses, article_slugs):
    errors = []
    duplicate_slugs = duplicate_values(verses, "slug")
    if duplicate_slugs:
        errors.append(f"verses.json: slugs duplicados: {', '.join(duplicate_slugs[:20])}")

    duplicate_refs = duplicate_values(verses, "referencia")
    if duplicate_refs:
        errors.append(f"verses.json: referencias duplicadas: {', '.join(duplicate_refs[:20])}")

    for index, verse in enumerate(verses):
        label = verse.get("referencia") or verse.get("slug") or f"linha {index}"
        missing = sorted(REQUIRED_VERSE_FIELDS - set(verse))
        if missing:
            errors.append(f"verses.json:{label}: campos ausentes: {', '.join(missing)}")
        if verse.get("idioma") not in VALID_LANGS:
            errors.append(f"verses.json:{label}: idioma invalido: {verse.get('idioma')!r}")
        if verse.get("dir") not in VALID_DIRS:
            errors.append(f"verses.json:{label}: dir invalido: {verse.get('dir')!r}")
        expected_dir = EXPECTED_DIR_BY_LANG.get(verse.get("idioma"))
        if expected_dir and verse.get("dir") != expected_dir:
            errors.append(
                f"verses.json:{label}: dir esperado para {verse.get('idioma')} e {expected_dir!r}"
            )
        if not re.search(r"\d+:\d+", verse.get("referencia", "")):
            errors.append(f"verses.json:{label}: referencia sem capitulo:versiculo")
        expected_slug = slugify_book_ref(verse.get("livro"), verse.get("referencia"))
        if expected_slug and verse.get("slug") != expected_slug:
            errors.append(f"verses.json:{label}: slug esperado {expected_slug!r}")
        if not isinstance(verse.get("palavras", []), list):
            errors.append(f"verses.json:{label}: palavras deve ser lista")
        if not isinstance(verse.get("artigos", []), list):
            errors.append(f"verses.json:{label}: artigos deve ser lista")
        for article_slug in verse.get("artigos", []):
            if article_slug not in article_slugs:
                errors.append(f"verses.json:{label}: artigo inexistente: {article_slug}")
    return errors


def validate_articles(articles):
    errors = []
    duplicate_slugs = duplicate_values(articles, "slug")
    if duplicate_slugs:
        errors.append(f"articles.json: slugs duplicados: {', '.join(duplicate_slugs[:20])}")

    for index, article in enumerate(articles):
        label = article.get("slug") or f"linha {index}"
        missing = sorted(REQUIRED_ARTICLE_FIELDS - set(article))
        if missing:
            errors.append(f"articles.json:{label}: campos ausentes: {', '.join(missing)}")
        if not isinstance(article.get("conteudo", []), list):
            errors.append(f"articles.json:{label}: conteudo deve ser lista")
            continue
        for block_index, block in enumerate(article.get("conteudo", [])):
            if not isinstance(block, dict) or not {"h", "p"} <= set(block):
                errors.append(f"articles.json:{label}: bloco {block_index} deve conter h e p")
    return errors


def validate_all(verses, articles):
    article_slugs = {article.get("slug") for article in articles}
    errors = []
    errors.extend(validate_articles(articles))
    errors.extend(validate_verses(verses, article_slugs))
    return errors


def main():
    errors = validate_all(load_json("verses.json"), load_json("articles.json"))
    if errors:
        print("VALIDACAO FALHOU")
        for error in errors:
            print(f"- {error}")
        return 1
    print("OK: dados curados validos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
