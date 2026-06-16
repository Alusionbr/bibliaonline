# -*- coding: utf-8 -*-
"""Teste de fumaça (integração) do build.py.

Roda o gerador inteiro contra um dataset minúsculo, num diretório temporário,
e verifica que as páginas, o sitemap e o índice de busca saem como esperado.
Pega regressões de integração que os testes unitários não enxergam.
"""
import json

import pytest


@pytest.fixture
def site(tmp_path, build, monkeypatch):
    """Monta um site/ temporário com 2 versículos + 1 artigo e aponta o build
    para ele (sem tocar no site/ real do repositório)."""
    site_dir = tmp_path / "site"
    data_dir = site_dir / "data"
    (site_dir / "assets").mkdir(parents=True)
    data_dir.mkdir(parents=True)

    verses = [
        {
            "slug": "genesis-1-1", "referencia": "Gênesis 1:1", "livro": "Gênesis",
            "idioma": "hebraico", "dir": "rtl", "original": "בְּרֵאשִׁית",
            "original_fonte": "WLC", "transliteracao": "bereshiyt",
            "texto_pt": "No princípio criou Deus os céus e a terra.",
            "texto_pt_fonte": "Almeida 1911", "palavras": ["criação"], "contexto": "abertura",
            "origem": "", "judaismo": False, "leitura_judaica": "", "artigos": ["meu-artigo"],
            "manuscrito": {},
        },
        {
            "slug": "joao-1-1", "referencia": "João 1:1", "livro": "João",
            "idioma": "grego", "dir": "ltr", "original": "Ἐν ἀρχῇ ἦν ὁ λόγος",
            "original_fonte": "Nestle 1904", "transliteracao": "", "texto_pt": "No princípio era o Verbo.",
            "texto_pt_fonte": "Almeida 1911", "palavras": ["logos"], "contexto": "prólogo",
            "origem": "", "judaismo": False, "leitura_judaica": "", "artigos": [],
            "manuscrito": {},
        },
    ]
    articles = [{
        "slug": "meu-artigo", "titulo": "Sobre o logos", "resumo": "um resumo",
        "conteudo": [{"h": "Seção", "p": "parágrafo"}],
    }]
    topics = [{"titulo": "Criação", "icone": "✶", "descricao": "o início"}]
    sources = [{"nome": "WLC", "licenca": "domínio público", "status": "ok", "url": "https://x"}]

    (data_dir / "verses.json").write_text(json.dumps(verses, ensure_ascii=False), "utf-8")
    (data_dir / "articles.json").write_text(json.dumps(articles, ensure_ascii=False), "utf-8")
    (data_dir / "topics.json").write_text(json.dumps(topics, ensure_ascii=False), "utf-8")
    (data_dir / "sources.json").write_text(json.dumps(sources, ensure_ascii=False), "utf-8")

    monkeypatch.setattr(build, "SITE", site_dir)
    monkeypatch.setattr(build, "DATA", data_dir)
    build.main()
    return site_dir


def test_gera_paginas_principais(site):
    assert (site / "index.html").exists()
    assert (site / "404.html").exists()
    assert (site / "versiculos" / "genesis-1-1" / "index.html").exists()
    assert (site / "versiculos" / "joao-1-1" / "index.html").exists()
    assert (site / "artigos" / "meu-artigo" / "index.html").exists()
    assert (site / "assets" / "app.js").exists()


def test_pager_liga_versiculos_em_ordem(site):
    # genesis-1-1 vem antes de joao-1-1 na ordem canônica
    gen = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    joao = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    # genesis aponta o próximo para joao e não tem "anterior"
    assert 'data-next="../joao-1-1/"' in gen
    assert "Próximo" in gen and "Anterior" not in gen
    # joao aponta o anterior para genesis e não tem próximo
    assert "../genesis-1-1/" in joao
    assert "Anterior" in joao and "Próximo" not in joao


def test_indice_de_busca_e_json_valido(site):
    html = (site / "index.html").read_text("utf-8")
    marca = "window.__INDEX__ = "
    inicio = html.index(marca) + len(marca)
    fim = html.index(";</script>", inicio)
    index = json.loads(html[inicio:fim])
    titulos = {i["titulo"] for i in index}
    assert "Gênesis 1:1" in titulos
    assert "Sobre o logos" in titulos


def test_sitemap_lista_todas_as_urls(site):
    sitemap = (site / "sitemap.xml").read_text("utf-8")
    assert "/versiculos/genesis-1-1/" in sitemap
    assert "/versiculos/joao-1-1/" in sitemap
    assert "/artigos/meu-artigo/" in sitemap
