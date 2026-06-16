# -*- coding: utf-8 -*-
"""Testes da reconciliação de numeração hebraico↔Almeida (fill_pt.py).

Usa dicionários sintéticos pequenos no lugar do download da Almeida, exercitando
a função pura resolve_pt() — onde moram os "ímãs" de erro de um-a-mais/um-a-menos.
"""


def test_ref_chvs(fill_pt):
    assert fill_pt.ref_chvs("Salmos 23:1") == (23, 1)
    assert fill_pt.ref_chvs("1 Coríntios 13:4") == (13, 4)


def test_capitulo_direto_quando_tamanhos_batem(fill_pt):
    # A == H: casamento direto, versículo a versículo
    amap = {("Gênesis", 1, 1): "No princípio..."}
    assert fill_pt.resolve_pt("Gênesis", 1, 1, amap, A=31, H=31) == "No princípio..."


def test_numeracao_divergente_fica_em_branco(fill_pt):
    # A != H e não é caso especial: NÃO inventa, devolve ""
    amap = {("Gênesis", 1, 1): "qualquer coisa"}
    assert fill_pt.resolve_pt("Gênesis", 1, 1, amap, A=30, H=31) == ""


def test_salmos_deslocamento_de_titulo(fill_pt):
    # Hebraico conta a inscrição como v1 (H = A + 1). v1 (título) fica em branco;
    # v2 hebraico = v1 da Almeida.
    amap = {("Salmos", 3, 1): "Senhor, como se multiplicam..."}
    # k = H - A = 1
    assert fill_pt.resolve_pt("Salmos", 3, 1, amap, A=8, H=9) == ""   # título
    assert fill_pt.resolve_pt("Salmos", 3, 2, amap, A=8, H=9) == "Senhor, como se multiplicam..."


def test_salmos_sem_titulo(fill_pt):
    # k = 0: casamento direto
    amap = {("Salmos", 1, 1): "Bem-aventurado o varão..."}
    assert fill_pt.resolve_pt("Salmos", 1, 1, amap, A=6, H=6) == "Bem-aventurado o varão..."


def test_salmos_titulo_duplo(fill_pt):
    # alguns salmos têm 2 linhas de título (k = 2)
    amap = {("Salmos", 51, 1): "Tem misericórdia de mim..."}
    # v3 hebraico = v1 da Almeida
    assert fill_pt.resolve_pt("Salmos", 51, 3, amap, A=19, H=21) == "Tem misericórdia de mim..."
    assert fill_pt.resolve_pt("Salmos", 51, 1, amap, A=19, H=21) == ""
    assert fill_pt.resolve_pt("Salmos", 51, 2, amap, A=19, H=21) == ""


def test_joel_remapeamento_de_capitulos(fill_pt):
    # Hebraico: 4 caps | Almeida: 3 caps.
    amap = {
        ("Joel", 1, 1): "cap1 da Almeida",
        ("Joel", 2, 1): "cap2 v1 da Almeida",
        ("Joel", 2, 28): "cap2 v28 da Almeida (= Hb 3:1)",
        ("Joel", 3, 1): "cap3 da Almeida (= Hb 4:1)",
    }
    assert fill_pt.resolve_pt("Joel", 1, 1, amap, A=0, H=0) == "cap1 da Almeida"
    assert fill_pt.resolve_pt("Joel", 2, 1, amap, A=0, H=0) == "cap2 v1 da Almeida"
    # Hb 3:1 -> Almeida (2, 27+1)
    assert fill_pt.resolve_pt("Joel", 3, 1, amap, A=0, H=0) == "cap2 v28 da Almeida (= Hb 3:1)"
    # Hb 4:1 -> Almeida (3, 1)
    assert fill_pt.resolve_pt("Joel", 4, 1, amap, A=0, H=0) == "cap3 da Almeida (= Hb 4:1)"


def test_name_fix_aplicado(fill_pt):
    # Lamentações e Oseias têm nomes diferentes na fonte Almeida
    amap = {("Lamentações de Jeremias", 1, 1): "Como está sentada solitária..."}
    assert fill_pt.resolve_pt("Lamentações", 1, 1, amap, A=22, H=22) == \
        "Como está sentada solitária..."
