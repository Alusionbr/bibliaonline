# -*- coding: utf-8 -*-
"""Testes do transliterador de hebraico/aramaico (gen_translit.py).

É a lógica mais delicada do projeto (motor próprio, feito do zero), então
cobrimos os casos que mais erram: vav como u/o/v, shin vs. sin, begadkefat
com/sem dagesh, vogais e entradas degeneradas.
"""


def test_genesis_1_1(gen_translit):
    # versículo de referência usado pelo próprio script como amostra
    original = "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָֽרֶץ"
    assert gen_translit.transliterate(original) == \
        "bereshiyt bara elohiym et hashamayim veet haarets"


def test_shin_vs_sin(gen_translit):
    # shin (ponto à direita) soa "sh"; sin (ponto à esquerda) soa "s"
    assert gen_translit.translit_word("שָׁלוֹם") == "shalom"
    assert gen_translit.translit_word("שִׂים") == "siym"


def test_begadkefat_dagesh(gen_translit):
    # bet com dagesh = "b"; sem dagesh = "v" (mesma letra, som diferente)
    assert gen_translit.translit_word("בּ") == "b"
    assert gen_translit.translit_word("ב") == "v"
    # kaf e pe seguem a mesma regra
    assert gen_translit.translit_word("כּ") == "k"
    assert gen_translit.translit_word("כ") == "kh"
    assert gen_translit.translit_word("פּ") == "p"
    assert gen_translit.translit_word("פ") == "f"


def test_vav_shuruq_holam_consoante(gen_translit):
    # vav+dagesh sem outra vogal = shuruq "u"
    assert gen_translit.translit_word("וּ") == "u"
    # vav+holam = "o"
    assert gen_translit.translit_word("וֹ") == "o"
    # vav consoante puro = "v"
    assert gen_translit.translit_word("ו") == "v"


def test_silenciosas_alef_ayin(gen_translit):
    # alef e ayin não têm som consonantal próprio (só carregam a vogal)
    assert gen_translit.translit_word("אָ") == "a"
    assert gen_translit.translit_word("עִ") == "i"


def test_entradas_degeneradas(gen_translit):
    # vazio, espaços e caracteres não-hebraicos não quebram nem inventam saída
    assert gen_translit.transliterate("") == ""
    assert gen_translit.transliterate("   ") == ""
    assert gen_translit.transliterate("abc 123") == ""


def test_cantilacao_ignorada(gen_translit):
    # acentos de cantilação (te'amim) não devem virar letras
    com_acento = gen_translit.translit_word("בָּרָ֑א")
    sem_acento = gen_translit.translit_word("בָּרָא")
    assert com_acento == sem_acento == "bara"


def test_preserva_separacao_de_palavras(gen_translit):
    # cada palavra é transliterada e juntada por um único espaço
    assert gen_translit.transliterate("שָׁלוֹם שָׁלוֹם") == "shalom shalom"
