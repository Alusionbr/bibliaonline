# -*- coding: utf-8 -*-
"""Testes dos helpers de geração do site (build.py)."""


# ---- ref_chvs ----

def test_ref_chvs_normal(build):
    assert build.ref_chvs("Gênesis 1:1") == (1, 1)
    assert build.ref_chvs("Salmos 119:176") == (119, 176)


def test_ref_chvs_malformado(build):
    # referência sem padrão "cap:vers" devolve (0, 0) em vez de quebrar
    assert build.ref_chvs("sem numero") == (0, 0)
    assert build.ref_chvs("") == (0, 0)


# ---- sefaria_url ----

def test_sefaria_url_livro_conhecido(build):
    assert build.sefaria_url("Gênesis", 1, 1) == \
        "https://www.sefaria.org/Genesis.1.1?lang=bi&with=all"


def test_sefaria_url_substitui_espaco(build):
    # "1 Samuel" -> "I Samuel" -> "I_Samuel"
    assert build.sefaria_url("1 Samuel", 1, 1) == \
        "https://www.sefaria.org/I_Samuel.1.1?lang=bi&with=all"


def test_sefaria_url_livro_desconhecido(build):
    # livro fora do mapa (ex.: NT, que não está no Sefaria daqui) devolve ""
    assert build.sefaria_url("Mateus", 1, 1) == ""
    assert build.sefaria_url("Inexistente", 1, 1) == ""


# ---- esc (escape de HTML — proteção contra injeção) ----

def test_esc_escapa_caracteres_perigosos(build):
    assert build.esc('<a href="x">&') == "&lt;a href=&quot;x&quot;&gt;&amp;"


def test_esc_none_vira_string_vazia(build):
    assert build.esc(None) == ""
    assert build.esc("") == ""


# ---- translit_disclosure ----

def test_translit_disclosure_recolhe_e_escapa_transliteracao(build):
    html = build.translit_disclosure('<bereshiyt>')
    assert '<details class="translit-toggle">' in html
    assert '<summary>' in html
    assert '<p class="translit">&lt;bereshiyt&gt;</p>' in html
    assert '&gt;' in html


def test_translit_disclosure_vazio_nao_renderiza_controle(build):
    assert build.translit_disclosure("") == ""
    assert build.translit_disclosure("   ") == ""


# ---- script_class / lang_label ----

def test_script_class(build):
    assert build.script_class("hebraico", "rtl") == "scr-hebrew"
    assert build.script_class("grego", "ltr") == "scr-greek"
    # qualquer coisa que não seja rtl cai no grego
    assert build.script_class("aramaico", "ltr") == "scr-greek"


def test_lang_label(build):
    assert build.lang_label("hebraico") == "Hebraico"
    assert build.lang_label("grego") == "Grego"
    assert build.lang_label("aramaico") == "Aramaico"
    # idioma fora do mapa: title-case do próprio valor
    assert build.lang_label("latim") == "Latim"


# ---- verse_sort_key (ordem canônica Gênesis -> Apocalipse) ----

def test_verse_sort_key_ordem_canonica(build):
    gen = build.verse_sort_key({"livro": "Gênesis", "referencia": "Gênesis 1:1"})
    apoc = build.verse_sort_key({"livro": "Apocalipse", "referencia": "Apocalipse 22:21"})
    assert gen < apoc


def test_verse_sort_key_capitulo_e_versiculo(build):
    v1 = build.verse_sort_key({"livro": "Salmos", "referencia": "Salmos 23:1"})
    v2 = build.verse_sort_key({"livro": "Salmos", "referencia": "Salmos 23:2"})
    v3 = build.verse_sort_key({"livro": "Salmos", "referencia": "Salmos 119:1"})
    assert v1 < v2 < v3


def test_verse_sort_key_livro_desconhecido_por_ultimo(build):
    conhecido = build.verse_sort_key({"livro": "Gênesis", "referencia": "Gênesis 1:1"})
    desconhecido = build.verse_sort_key({"livro": "Zzz", "referencia": "Zzz 1:1"})
    assert conhecido < desconhecido
