# -*- coding: utf-8 -*-
"""Testes dos helpers de montagem do verses.json (expand_verses.py)."""

import pytest


# ---- is_aramaic: as faixas de aramaico bíblico ----

@pytest.mark.parametrize("osis,ch,vs,esperado", [
    ("Dan", 2, 4, True),    # começa em Daniel 2:4
    ("Dan", 2, 3, False),   # 2:3 ainda é hebraico
    ("Dan", 5, 1, True),    # 3..7 inteiros
    ("Dan", 7, 28, True),
    ("Dan", 8, 1, False),   # volta ao hebraico
    ("Ezra", 4, 8, True),   # Esdras 4:8 em diante
    ("Ezra", 4, 7, False),
    ("Ezra", 5, 1, True),
    ("Ezra", 6, 18, True),
    ("Ezra", 6, 19, False),
    ("Ezra", 7, 12, True),  # 7:12-26
    ("Ezra", 7, 26, True),
    ("Ezra", 7, 27, False),
    ("Jer", 10, 11, True),  # um único versículo
    ("Jer", 10, 10, False),
    ("Gen", 31, 47, True),  # duas palavras aramaicas
    ("Gen", 1, 1, False),
])
def test_is_aramaic(expand_verses, osis, ch, vs, esperado):
    assert expand_verses.is_aramaic(osis, ch, vs) is esperado


# ---- slugify ----

def test_slugify_remove_acentos(expand_verses):
    assert expand_verses.slugify("Gênesis", 1, 1) == "genesis-1-1"
    assert expand_verses.slugify("Êxodo", 20, 2) == "exodo-20-2"


def test_slugify_numero_e_espaco(expand_verses):
    assert expand_verses.slugify("1 Coríntios", 13, 4) == "1-corintios-13-4"
    assert expand_verses.slugify("2 Samuel", 7, 12) == "2-samuel-7-12"


def test_slugs_unicos_entre_todos_os_livros(expand_verses):
    # garante que nomes de livros diferentes não colidem no mesmo slug base
    bases = {}
    for osis, pt in expand_verses.OSIS_PT.items():
        base = expand_verses.slugify(pt, 1, 1)[:-4]  # remove "-1-1"
        assert base not in bases, f"colisão de slug: {pt} e {bases[base]} -> {base}"
        bases[base] = pt


# ---- strip_cantillation ----

def test_strip_cantillation_remove_teamim(expand_verses):
    # mantém letras e niqqud, remove só os acentos de cantilação (U+0591..U+05AF)
    assert expand_verses.strip_cantillation("בָּרָ֑א") == "בָּרָא"


def test_strip_cantillation_sem_acentos_inalterado(expand_verses):
    texto = "שָׁלוֹם"
    assert expand_verses.strip_cantillation(texto) == texto


# ---- mapas de referência ----

def test_nt_subconjunto_de_osis(expand_verses):
    # todo livro do NT precisa ter nome PT mapeado
    assert expand_verses.NT.issubset(set(expand_verses.OSIS_PT))


def test_osis_pt_tem_66_livros(expand_verses):
    assert len(expand_verses.OSIS_PT) == 66
