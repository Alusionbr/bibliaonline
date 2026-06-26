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
    topics = [{"slug": "criacao", "titulo": "Criação", "icone": "✶", "descricao": "o início"}]
    sources = [{"nome": "WLC", "licenca": "domínio público", "status": "ok", "url": "https://x"}]
    topic_refs = {"criacao": ["Gênesis 1:1"]}
    cross_refs = {"Gênesis 1:1": ["João 1:1"]}
    glossary = [
        {"slug": "logos", "termo": "Lógos", "original": "λόγος", "translit": "logos",
         "idioma": "grego", "dir": "ltr", "definicao": "Palavra, verbo.", "refs": ["João 1:1"]},
        {"slug": "elohim", "termo": "Elohim", "original": "אֱלֹהִים", "translit": "elohiym",
         "idioma": "hebraico", "dir": "rtl", "definicao": "Deus.", "refs": ["Gênesis 1:1"]},
    ]
    commentary = {"Gênesis 1:1": [{"perspectiva": "Contexto", "texto": "Tudo começa em Deus."}]}
    jewish_readings = {"Gênesis 1:1": [{"angulo": "Sentido do hebraico", "texto": "O verbo bara tem Deus como sujeito."}]}
    places = [{
        "slug": "jerusalem", "nome": "Jerusalém", "tipo": "Cidade",
        "regiao": "Terra de Israel", "descricao": "Cidade do Templo.",
        "lat": 31.78, "lon": 35.23, "refs": ["Gênesis 1:1"],
    }]
    plans = [{
        "slug": "joao-1-dia", "titulo": "João em 1 dia", "descricao": "Leitura curta.",
        "dias": [["João 1"]],
    }]

    (data_dir / "verses.json").write_text(json.dumps(verses, ensure_ascii=False), "utf-8")
    (data_dir / "articles.json").write_text(json.dumps(articles, ensure_ascii=False), "utf-8")
    (data_dir / "topics.json").write_text(json.dumps(topics, ensure_ascii=False), "utf-8")
    (data_dir / "sources.json").write_text(json.dumps(sources, ensure_ascii=False), "utf-8")
    (data_dir / "topic-refs.json").write_text(json.dumps(topic_refs, ensure_ascii=False), "utf-8")
    (data_dir / "cross-references.json").write_text(json.dumps(cross_refs, ensure_ascii=False), "utf-8")
    (data_dir / "glossary.json").write_text(json.dumps(glossary, ensure_ascii=False), "utf-8")
    (data_dir / "commentary.json").write_text(json.dumps(commentary, ensure_ascii=False), "utf-8")
    (data_dir / "jewish-readings.json").write_text(json.dumps(jewish_readings, ensure_ascii=False), "utf-8")
    (data_dir / "places.json").write_text(json.dumps(places, ensure_ascii=False), "utf-8")
    (data_dir / "reading-plans.json").write_text(json.dumps(plans, ensure_ascii=False), "utf-8")
    red_letters = {"João 1:1": True}
    (data_dir / "red-letters.json").write_text(json.dumps(red_letters, ensure_ascii=False), "utf-8")

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


def test_gera_navegacao_livro_capitulo(site):
    # índice de livros, página do livro e leitura de capítulo
    assert (site / "ler" / "index.html").exists()
    assert (site / "ler" / "genesis" / "index.html").exists()
    assert (site / "ler" / "genesis" / "1" / "index.html").exists()
    assert (site / "ler" / "joao" / "1" / "index.html").exists()
    # a página de capítulo mostra o versículo e linka para a página completa dele
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "No princípio criou Deus" in cap
    assert "versiculos/genesis-1-1/" in cap
    grego = (site / "ler" / "joao" / "1" / "index.html").read_text("utf-8")
    assert 'class="original-toggle"' in grego
    assert "Mostrar texto grego" in grego
    assert 'class="translit-toggle"' not in grego


def test_gera_ferramentas_de_estudo(site):
    # script de estudo + página de anotações com botões de exportar
    assert (site / "assets" / "study.js").exists()
    anot = (site / "anotacoes" / "index.html").read_text("utf-8")
    assert 'id="anotacoes"' in anot
    for botao in ("anot-copy", "anot-txt", "anot-json", "anot-clear"):
        assert f'id="{botao}"' in anot
    # cada versículo expõe sua referência (gancho para grifar/anotar) e carrega o study.js
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert 'data-ref="Gênesis 1:1"' in cap
    assert "assets/study.js" in cap
    vp = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert 'data-ref="Gênesis 1:1"' in vp


def test_caneta_marca_texto_e_doacao(site):
    # marca-texto por caneta (arrastar) + cores + cartão de doação por engajamento
    study = (site / "assets" / "study.js").read_text("utf-8")
    for gancho in ("pen-toggle", "hl-mode", "pen-colors", "pointerdown",
                   "pointercancel", "elementFromPoint", "DONATE_EVERY", "markCount"):
        assert gancho in study, gancho
    # a barra de seleção não tem mais o botão "Grifar" (agora é a caneta)
    assert 'data-sel="hl"' not in study
    # botão de compartilhar no verso
    assert 'data-act="share"' in study


def test_anotacoes_importar_e_compartilhar(site):
    anot = (site / "anotacoes" / "index.html").read_text("utf-8")
    assert 'id="anot-import"' in anot and 'id="anot-import-file"' in anot
    assert 'id="anot-share"' in anot


def test_ferramentas_de_leitura_e_versiculo_aleatorio(site):
    app = (site / "assets" / "app.js").read_text("utf-8")
    for gancho in ("font-inc", "font-dec", "bec.theme", "bec.fontscale",
                   "lastRead", "random-verse", "random.json"):
        assert gancho in app, gancho
    # controles no nav e botões na home
    home = (site / "index.html").read_text("utf-8")
    assert 'data-rt="theme"' in home and 'id="random-verse"' in home and 'id="continue-read"' in home
    # script anti-flash de tema/fonte no <head>
    assert "bec.theme" in home and "classList.add('dark')" in home
    # pool aleatório gerado
    pool = json.loads((site / "data" / "random.json").read_text("utf-8"))
    assert len(pool) >= 1 and all(isinstance(s, str) for s in pool)


def test_lote2_cartao_ferramentas_modal(site):
    study = (site / "assets" / "study.js").read_text("utf-8")
    # base do site injetada + cartão-imagem + compartilhar versículo + ferramentas + modal
    assert study.startswith("var BEC_BASE=")
    for gancho in ("makeVerseCard", "canShare", "toBlob", "shareVerse",
                   "tools-fab", "tools-panel", "bec-modal", "confirmModal"):
        assert gancho in study, gancho


def test_lote2_seletor_ir_para_livro(site):
    cap = (site / "ler" / "joao" / "1" / "index.html").read_text("utf-8")
    assert 'class="book-jump"' in cap
    assert "Antigo Testamento" in cap and "Novo Testamento" in cap
    # o seletor leva a outros livros (valor com caminho de leitura)
    assert "ler/genesis/" in cap
    # também presente na página do livro
    book = (site / "ler" / "joao" / "index.html").read_text("utf-8")
    assert 'class="book-jump"' in book
    # wiring no app.js
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "book-jump" in app


def test_lote2_bloqueio_de_ias(site):
    robots = (site / "robots.txt").read_text("utf-8")
    assert "GPTBot" in robots and "Disallow: /" in robots
    assert "ClaudeBot" in robots and "CCBot" in robots
    # meta noai em todas as páginas (via head)
    home = (site / "index.html").read_text("utf-8")
    assert "noai" in home and "noimageai" in home


def test_home_nao_embute_indice_gigante(site):
    # o índice de busca saiu da página (não mais inline) e virou arquivo externo
    html = (site / "index.html").read_text("utf-8")
    assert "window.__INDEX__" not in html
    assert (site / "data" / "search-index.json").exists()


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
    index = json.loads((site / "data" / "search-index.json").read_text("utf-8"))
    titulos = {i["titulo"] for i in index}
    assert "Gênesis 1:1" in titulos
    assert "Sobre o logos" in titulos
    # cada entrada tem a chave de busca usada pelo app.js
    assert all("k" in i and "url" in i for i in index)


def test_sitemap_lista_todas_as_urls(site):
    sitemap = (site / "sitemap.xml").read_text("utf-8")
    assert "/versiculos/genesis-1-1/" in sitemap
    assert "/versiculos/joao-1-1/" in sitemap
    assert "/artigos/meu-artigo/" in sitemap


def test_ajustes_ios_notas(site):
    # menu flutuante: salvar nas Notas (texto) + baixar .txt; .json saiu do menu
    study = (site / "assets" / "study.js").read_text("utf-8")
    assert "Salvar tudo (.json)" not in study
    assert 'data-t="txt"' in study
    assert "Salvar nas Notas" in study
    # página Anotações: .json vira "backup", importar vira "Importar backup" (ids preservados)
    anot = (site / "anotacoes" / "index.html").read_text("utf-8")
    assert "Backup .json" in anot and "Importar backup" in anot
    assert 'id="anot-json"' in anot and 'id="anot-import"' in anot


def test_painel_ferramentas_minimiza():
    # o atributo hidden precisa vencer o display:flex, senão o painel fica sempre aberto
    from pathlib import Path
    css = (Path(__file__).resolve().parents[1] / "site" / "assets" / "styles.css").read_text("utf-8")
    assert ".tools-panel[hidden]" in css


def test_lote4_ordenacao_dos_livros(site):
    # toggle de ordenação + atributos de ordenação nos cartões, no /ler/ e na home
    for page in (site / "ler" / "index.html", site / "index.html"):
        html = page.read_text("utf-8")
        assert 'data-sort="alpha"' in html and 'data-sort="chron"' in html
        assert "data-booklist" in html
        assert "data-chron=" in html and "data-pos=" in html and "data-name=" in html
    # wiring + persistência no app.js
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "bec.bookorder" in app and "data-booklist" in app


def test_lote4_linha_do_tempo(site):
    tl = (site / "linha-do-tempo" / "index.html")
    assert tl.exists()
    html = tl.read_text("utf-8")
    # eras (rendizadas mesmo quando vazias no dataset de teste) + aviso de datas
    assert "Monarquia Unida" in html and "Igreja primitiva" in html
    assert "Datas aproximadas" in html or "datas aproximadas" in html
    # leva às páginas de livro presentes
    assert "ler/genesis/" in html
    # link na navegação e no sitemap
    assert "Linha do tempo" in html
    assert "/linha-do-tempo/" in (site / "sitemap.xml").read_text("utf-8")


def test_fase2_indice_de_temas(site):
    # índice de temas + página do tema com versículo curado
    idx = (site / "temas" / "index.html")
    assert idx.exists()
    idx_html = idx.read_text("utf-8")
    assert "Temas de estudo" in idx_html
    assert 'href="criacao/"' in idx_html
    page = (site / "temas" / "criacao" / "index.html")
    assert page.exists()
    page_html = page.read_text("utf-8")
    # o tema lista o versículo curado e aponta para a página completa dele
    assert "Gênesis 1:1" in page_html
    assert "versiculos/genesis-1-1/" in page_html
    # a home e a nav apontam para os temas reais (não mais #temas)
    home = (site / "index.html").read_text("utf-8")
    assert 'href="temas/criacao/"' in home
    assert 'href="temas/"' in home
    # sitemap inclui as páginas de tema
    sitemap = (site / "sitemap.xml").read_text("utf-8")
    assert "/temas/" in sitemap and "/temas/criacao/" in sitemap


def test_fase2_referencias_cruzadas(site):
    # a página do versículo mostra o bloco de referências cruzadas curadas
    vp = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert "Referências cruzadas" in vp
    assert 'id="referencias"' in vp
    # link irmão para o versículo relacionado (João 1:1)
    assert "../joao-1-1/" in vp
    # versículo sem cross-ref curada não cria o bloco
    joao = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert 'id="referencias"' not in joao


def test_fase3_dicionario(site):
    # índice do dicionário + página do termo com versículo de exemplo
    idx = (site / "dicionario" / "index.html")
    assert idx.exists()
    idx_html = idx.read_text("utf-8")
    assert "Dicionário" in idx_html
    assert 'href="logos/"' in idx_html and 'href="elohim/"' in idx_html
    term = (site / "dicionario" / "logos" / "index.html")
    assert term.exists()
    term_html = term.read_text("utf-8")
    assert "λόγος" in term_html
    assert "versiculos/joao-1-1/" in term_html  # leva ao versículo de exemplo
    # a página do versículo João 1:1 mostra "Palavras do original" ligando ao termo
    joao = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert "Palavras do original" in joao
    assert "dicionario/logos/" in joao
    # nav e sitemap
    assert 'href="dicionario/"' in (site / "index.html").read_text("utf-8")
    assert "/dicionario/" in (site / "sitemap.xml").read_text("utf-8")
    # termo no índice de busca
    index = json.loads((site / "data" / "search-index.json").read_text("utf-8"))
    assert any(i["t"] == "Termo" and i["titulo"] == "Lógos" for i in index)


def test_fase3_comentario_teologico(site):
    # versículo com comentário curado mostra o bloco; sem comentário, não mostra
    gen = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert 'id="comentario"' in gen
    assert "Tudo começa em Deus." in gen
    assert "resumo original" in gen.lower()  # nota de autoria/licença
    joao = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert 'id="comentario"' not in joao


def test_leitura_judaica_contexto(site):
    # versículo com leitura judaica curada mostra o bloco de contexto + nota de respeito;
    # versículo sem curadoria não mostra a seção
    gen = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert 'id="leitura-judaica"' in gen
    assert "Leitura judaica (contexto)" in gen
    assert "O verbo bara tem Deus como sujeito." in gen
    assert "não substitui nem contradiz a leitura cristã" in gen  # enquadramento respeitoso
    # recolhido por padrão: dentro de um <details> (sem atributo open)
    sec = gen.split('id="leitura-judaica"', 1)[1][:600]
    assert '<details class="study-toggle">' in sec
    assert "<details class=\"study-toggle\" open" not in sec
    joao = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert 'id="leitura-judaica"' not in joao


def test_fase4_mapas(site):
    # atlas + página do lugar com versículo e link de mapa
    idx = (site / "mapas" / "index.html")
    assert idx.exists()
    idx_html = idx.read_text("utf-8")
    assert "Atlas" in idx_html and 'href="jerusalem/"' in idx_html
    place = (site / "mapas" / "jerusalem" / "index.html")
    assert place.exists()
    place_html = place.read_text("utf-8")
    assert "versiculos/genesis-1-1/" in place_html       # versículo de exemplo
    assert "openstreetmap.org" in place_html             # link externo (não embed)
    # o versículo Gênesis 1:1 mostra o bloco "Lugares" ligando ao atlas
    gen = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert 'id="lugares"' in gen and "mapas/jerusalem/" in gen
    # nav + sitemap + busca
    assert 'href="mapas/"' in (site / "index.html").read_text("utf-8")
    assert "/mapas/jerusalem/" in (site / "sitemap.xml").read_text("utf-8")
    index = json.loads((site / "data" / "search-index.json").read_text("utf-8"))
    assert any(i["t"] == "Lugar" and i["titulo"] == "Jerusalém" for i in index)


def test_fase4_planos_de_leitura(site):
    # índice de planos + página do plano com checkbox de dia e barra de progresso
    idx = (site / "planos" / "index.html")
    assert idx.exists()
    assert 'href="joao-1-dia/"' in idx.read_text("utf-8")
    plan = (site / "planos" / "joao-1-dia" / "index.html")
    assert plan.exists()
    plan_html = plan.read_text("utf-8")
    assert 'data-plan="joao-1-dia"' in plan_html
    assert 'data-day="0"' in plan_html
    assert "ler/joao/1/" in plan_html                    # liga ao capítulo
    assert "data-plan-bar" in plan_html                  # barra de progresso
    # wiring + persistência no app.js
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "bec.plan." in app and "data-plan" in app
    # nav + sitemap
    assert 'href="planos/"' in (site / "index.html").read_text("utf-8")
    assert "/planos/joao-1-dia/" in (site / "sitemap.xml").read_text("utf-8")


def test_letras_vermelhas_jesus(site):
    # versículo marcado em red-letters.json recebe class="pt pt-jesus"
    joao = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert 'class="pt pt-jesus"' in joao
    cap = (site / "ler" / "joao" / "1" / "index.html").read_text("utf-8")
    assert 'class="pt pt-jesus"' in cap
    # versículo não marcado não recebe a classe
    gen = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert "pt-jesus" not in gen
