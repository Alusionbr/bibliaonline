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
    assert (site / "estudar" / "index.html").exists()
    assert (site / "workspace" / "index.html").exists()
    assert (site / "comunidade" / "index.html").exists()
    assert (site / "comunidade" / "salas" / "index.html").exists()
    assert (site / "biblioteca" / "index.html").exists()
    assert (site / "colecoes" / "index.html").exists()
    assert (site / "cadernos" / "index.html").exists()
    assert (site / "versiculos" / "genesis-1-1" / "index.html").exists()
    assert (site / "versiculos" / "joao-1-1" / "index.html").exists()
    assert (site / "artigos" / "meu-artigo" / "index.html").exists()
    assert (site / "assets" / "app.js").exists()


def test_nova_navegacao_principal(site):
    home = (site / "index.html").read_text("utf-8")
    for label in ("Início", "Bíblia", "Estudar", "Comunidade", "Workspace"):
        assert label in home
    assert 'class="mobile-primary-nav"' in home
    assert 'href="estudar/"' in home
    assert 'href="comunidade/"' in home
    assert 'href="workspace/"' in home


def test_conta_fica_simples(site):
    auth = (site / "assets" / "auth.js").read_text("utf-8")
    for label in ("Meu perfil", "Configurações", "Sincronização", "Privacidade", "Sair"):
        assert label in auth
    for label in ("Meus estudos", "grupos", "Biblioteca", "Favoritos", "Notas"):
        assert label not in auth


def test_gamificacao_e_beta(site):
    # Asset da gamificação é gerado e carregado nas páginas.
    assert (site / "assets" / "game.js").exists()
    game = (site / "assets" / "game.js").read_text("utf-8")
    assert "BEC_GAME" in game
    home = (site / "index.html").read_text("utf-8")
    assert "assets/game.js" in home
    # Selo Beta e banner de versão de testes presentes.
    assert "data-beta-banner" in home
    assert "data-account-badge" in home
    # Painel de progresso (missões + medalhas) no Workspace.
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    for hook in ("data-progress-panel", "data-mission-list", "data-medal-grid"):
        assert hook in ws
    # A conta expõe a ponte usada por game.js.
    auth = (site / "assets" / "auth.js").read_text("utf-8")
    assert "BEC_ACCOUNT" in auth


def test_salas_de_estudo_reais(site):
    # O app de comunidade é gerado e a página de Salas o carrega.
    assert (site / "assets" / "community.js").exists()
    community = (site / "assets" / "community.js").read_text("utf-8")
    for rpc in ("create_group", "join_group", "create_topic", "add_post"):
        assert rpc in community
    salas = (site / "comunidade" / "salas" / "index.html").read_text("utf-8")
    assert "data-community-app" in salas
    assert "assets/community.js" in salas
    # As antigas salas de demonstração saíram.
    assert "Sala Evangelho de João" not in salas


def test_sem_produto_de_ia_no_html_gerado(site):
    proibidos = ("IA Bíblica", "Bíblia com IA", "assistente IA")
    pages = [
        site / "index.html",
        site / "estudar" / "index.html",
        site / "workspace" / "index.html",
        site / "comunidade" / "index.html",
        site / "ler" / "joao" / "1" / "index.html",
        site / "versiculos" / "joao-1-1" / "index.html",
    ]
    for page in pages:
        html = page.read_text("utf-8")
        for termo in proibidos:
            assert termo not in html


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


def test_audio_e_favoritos(site):
    app = (site / "assets" / "app.js").read_text("utf-8")
    for gancho in ("speechSynthesis", "SpeechSynthesisUtterance", "data-speak",
                   "data-lang", "bec.favs", "data-fav", "favorite-home"):
        assert gancho in app, gancho
    home = (site / "index.html").read_text("utf-8")
    assert 'id="favorite-home"' in home and 'id="favorite-list"' in home
    vp = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert "Ouvir original" in vp and "Ouvir PT" in vp and "Favoritar" in vp
    assert 'data-lang="he-IL"' in vp and 'data-lang="pt-BR"' in vp
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "Ouvir original" in cap and "Favoritar" in cap


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
    for path in (
        "/estudar/",
        "/workspace/",
        "/comunidade/",
        "/comunidade/salas/",
        "/biblioteca/",
        "/colecoes/",
        "/cadernos/",
    ):
        assert path in sitemap


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
