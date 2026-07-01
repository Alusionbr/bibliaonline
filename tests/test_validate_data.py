# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load_validate_data():
    spec = importlib.util.spec_from_file_location("validate_data", SCRIPTS / "validate_data.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validate_all_aceita_dataset_minimo():
    validate_data = load_validate_data()
    verses = [{
        "slug": "genesis-1-1",
        "referencia": "Gênesis 1:1",
        "livro": "Gênesis",
        "idioma": "hebraico",
        "dir": "rtl",
        "original": "בראשית",
        "original_fonte": "WLC",
        "transliteracao": "bereshiyt",
        "texto_pt": "No princípio criou Deus os céus e a terra.",
        "texto_pt_fonte": "Almeida 1911",
        "palavras": ["criacao"],
        "contexto": "abertura",
        "origem": "",
        "judaismo": False,
        "leitura_judaica": "",
        "artigos": ["origem"],
        "manuscrito": {},
    }]
    articles = [{
        "slug": "origem",
        "titulo": "Origem",
        "resumo": "Resumo",
        "conteudo": [{"h": "Secao", "p": "Texto"}],
    }]

    assert validate_data.validate_all(verses, articles) == []


def test_validate_all_pega_slug_duplicado_e_artigo_inexistente():
    validate_data = load_validate_data()
    base = {
        "slug": "genesis-1-1",
        "referencia": "Gênesis 1:1",
        "livro": "Gênesis",
        "idioma": "hebraico",
        "dir": "rtl",
        "original": "בראשית",
        "original_fonte": "WLC",
        "transliteracao": "bereshiyt",
        "texto_pt": "",
        "texto_pt_fonte": "Almeida 1911",
        "palavras": [],
        "contexto": "",
        "origem": "",
        "judaismo": False,
        "leitura_judaica": "",
        "artigos": ["faltando"],
        "manuscrito": {},
    }
    verses = [dict(base), dict(base, referencia="Gênesis 1:2")]
    articles = [{"slug": "origem", "titulo": "Origem", "resumo": "Resumo", "conteudo": []}]

    errors = validate_data.validate_all(verses, articles)

    assert any("slugs duplicados" in error for error in errors)
    assert any("artigo inexistente: faltando" in error for error in errors)


def test_validate_all_pega_dir_e_slug_incoerentes():
    validate_data = load_validate_data()
    verses = [{
        "slug": "slug-errado",
        "referencia": "João 1:1",
        "livro": "João",
        "idioma": "grego",
        "dir": "rtl",
        "original": "Ἐν ἀρχῇ",
        "original_fonte": "Nestle 1904",
        "transliteracao": "",
        "texto_pt": "",
        "texto_pt_fonte": "Almeida 1911",
        "palavras": [],
        "contexto": "",
        "origem": "",
        "judaismo": False,
        "leitura_judaica": "",
        "artigos": [],
        "manuscrito": {},
    }]
    articles = []

    errors = validate_data.validate_all(verses, articles)

    assert any("dir esperado para grego" in error for error in errors)
    assert any("slug esperado 'joao-1-1'" in error for error in errors)
