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

    # temas, léxico e atlas: dados curados, cada um com uma referência que
    # existe e uma que não existe (para checar que o build ignora a que falta)
    topic_refs = {"criacao": ["Gênesis 1:1", "Ageu 9:9"]}
    glossary = [{
        "slug": "logos", "termo": "Logos", "original": "λόγος", "translit": "logos",
        "idioma": "grego", "dir": "ltr", "definicao": "Palavra, razão, discurso.",
        "refs": ["João 1:1", "Ageu 9:9"],
    }]
    places = [{
        "slug": "eden", "nome": "Éden", "tipo": "Região", "regiao": "Origens",
        "descricao": "O jardim da criação.", "lat": 33.1, "lon": 44.2,
        "refs": ["Gênesis 1:1"],
    }]

    plans = [{
        "slug": "joao-2-dias", "titulo": "João em 2 dias",
        "descricao": "Leitura curta de exemplo.",
        "dias": [["João 1"], ["João 2", "Salmo desconhecido"]],
    }]

    (data_dir / "verses.json").write_text(json.dumps(verses, ensure_ascii=False), "utf-8")
    (data_dir / "articles.json").write_text(json.dumps(articles, ensure_ascii=False), "utf-8")
    (data_dir / "topics.json").write_text(json.dumps(topics, ensure_ascii=False), "utf-8")
    (data_dir / "sources.json").write_text(json.dumps(sources, ensure_ascii=False), "utf-8")
    (data_dir / "reading-plans.json").write_text(json.dumps(plans, ensure_ascii=False), "utf-8")
    (data_dir / "topic-refs.json").write_text(json.dumps(topic_refs, ensure_ascii=False), "utf-8")
    (data_dir / "glossary.json").write_text(json.dumps(glossary, ensure_ascii=False), "utf-8")
    (data_dir / "places.json").write_text(json.dumps(places, ensure_ascii=False), "utf-8")
    # João 1:1 marcado como fala de Jesus só para exercitar o destaque; Gênesis
    # fica de fora para provar que o resto do texto não vira vermelho
    (data_dir / "red-letters.json").write_text(
        json.dumps({"João 1:1": True}, ensure_ascii=False), "utf-8")
    (data_dir / "commentary.json").write_text(json.dumps(
        {"Gênesis 1:1": [{"perspectiva": "Contexto", "texto": "Abre a Torá."}]},
        ensure_ascii=False), "utf-8")

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
    # Navegação enxuta: Estudar foi fundida no Workspace; Comunidade está
    # pausada (redirects antigos seguem existindo, mas sem seção própria).
    home = (site / "index.html").read_text("utf-8")
    for label in ("Início", "Bíblia", "Workspace"):
        assert label in home
    assert 'class="mobile-primary-nav"' in home
    assert 'href="workspace/"' in home
    assert 'href="ler/"' in home
    # O Workspace carrega a seção fundida de Estudar (com a aba Criar plano).
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    assert 'id="estudar"' in ws and 'id="criar-plano"' in ws
    assert 'id="comunidade"' not in ws
    # Os endereços antigos seguem vivos como redirects (noindex).
    estudar = (site / "estudar" / "index.html").read_text("utf-8")
    comunidade = (site / "comunidade" / "index.html").read_text("utf-8")
    salas = (site / "comunidade" / "salas" / "index.html").read_text("utf-8")
    assert "url=../workspace/#estudar" in estudar
    assert "url=../workspace/" in comunidade
    assert "url=../../workspace/" in salas
    for page in (estudar, comunidade, salas):
        assert "noindex" in page


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
    # Painel de progresso (missões diárias, semanais e medalhas) no Workspace.
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    for hook in ("data-progress-panel", "data-mission-list", "data-weekly-list", "data-medal-grid"):
        assert hook in ws
    # O motor conhece o catálogo semanal e credita por evento real de leitura.
    for token in ("FALLBACK", "weekly", "weeklyByMetric", "renderMissions"):
        assert token in game
    # Dual-write autoritativo: emite eventos validados via RPC record_event.
    for token in ("record_event", "recordEvent", "emitCountEvents"):
        assert token in game
    app = (site / "assets" / "app.js").read_text("utf-8")
    # Marcar um trecho (não abrir o capítulo) é o que credita a leitura.
    assert "read_chapters" in app and "readingRanges" in app
    # Cartão de nível com barra de XP até o próximo nível.
    for hook in ("level-card", "data-progress-tier", "data-progress-xptonext", "data-xp-bar"):
        assert hook in ws
    # Missões e medalhas ficam recolhidas (expande/retrai) com contadores no título.
    for hook in ('details class="collap', "data-mission-count", "data-weekly-count", "data-medal-count"):
        assert hook in ws
    # O motor expõe o nível para travas de recurso (ex.: criar sala no nível 3).
    assert "level:function" in game
    # Resumo "Seu dia" na Início, alimentado pelo mesmo estado local.
    for hook in ("data-home-progress", "data-home-streak", "data-home-level",
                 "data-home-tier", "data-home-missions", "data-home-xp-bar"):
        assert hook in home
    # O motor expõe os cálculos de nível/faixa reutilizados nesses hooks.
    for fn in ("tierFromLevel", "xpToNext", "renderHomeSummary"):
        assert fn in game
    # A conta expõe a ponte usada por game.js.
    auth = (site / "assets" / "auth.js").read_text("utf-8")
    assert "BEC_ACCOUNT" in auth


def test_sincronizacao_ampliada(site):
    # O sync cobre planos, coleções e cadernos, com fallback para o
    # esquema v1 enquanto a migração não é aplicada.
    auth = (site / "assets" / "auth.js").read_text("utf-8")
    for token in ("study_plans", "collections", "notebooks", "legacyColumns", "bec.planProgress"):
        assert token in auth


def test_gamificacao_nao_inunda_o_banco(site):
    # Regressão: a gamificação não pode escrever no banco a cada evento de
    # página/sync (isso travava a leitura logado no Safari mobile).
    # O catálogo é buscado uma vez e o envio é agendado só quando há progresso.
    game = (site / "assets" / "game.js").read_text("utf-8")
    assert "schedulePush" in game        # envio debounced/deduplicado
    assert "catalogLoaded" in game       # catálogo carregado uma vez por sessão
    # Restaurar grifos/notas ao abrir a página (paintAll) não deve, por si só,
    # marcar o estado como sujo para sincronizar — só a ação do usuário grava.
    study = (site / "assets" / "study.js").read_text("utf-8")
    assert "function paintAll(" in study
    assert "function setHlColor(" in study


def test_reportar_bug(site):
    # O asset de reporte é gerado e carregado nas páginas.
    assert (site / "assets" / "report.js").exists()
    report = (site / "assets" / "report.js").read_text("utf-8")
    # Reusa os RPCs existentes; não faz insert direto na tabela.
    assert "submit_suggestion" in report
    assert "review_suggestion" in report
    assert ".from('suggestions').insert" not in report
    home = (site / "index.html").read_text("utf-8")
    assert "assets/report.js" in home
    # O Workspace tem o bloco de administração (oculto por padrão).
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    assert "data-admin-reports" in ws


def test_comunidade_pausada(site):
    # Comunidade/Salas de Estudo está pausada por decisão de produto (será
    # reformulada antes de voltar) — o código fonte com a integração Supabase
    # continua em scripts/community.asset.js, mas nada disso é gerado nem
    # carregado no site publicado.
    assert not (site / "assets" / "community.js").exists()
    home = (site / "index.html").read_text("utf-8")
    assert "assets/community.js" not in home
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    assert "data-community-app" not in ws
    assert "assets/community.js" not in ws
    sw = (site / "sw.js").read_text("utf-8")
    assert "community.js" not in sw
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "data-room-suggest" not in cap


def test_sem_ancoras_mortas_nem_metricas_falsas(site):
    # Cards não apontam para âncoras que nunca são geradas.
    estudar = (site / "estudar" / "index.html").read_text("utf-8")
    assert 'href="#planos"' not in estudar
    assert "biblioteca/#grifos" not in estudar
    comunidade = (site / "comunidade" / "index.html").read_text("utf-8")
    for morta in ('href="#perguntas"', 'href="#oracao"', 'href="#testemunhos"', 'href="#estudos-publicos"'):
        assert morta not in comunidade
    # Números demonstrativos apresentados como dados reais saíram.
    assert "pessoas lendo" not in comunidade
    verso = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert "pessoas lendo hoje" not in verso
    assert "Dados demonstrativos" not in verso


def test_ferramentas_pessoais_vivem_no_workspace(site):
    # Coleções, cadernos e favoritos são apps locais reais — e existem em um
    # lugar só. /colecoes/ e /cadernos/ eram duplicatas literais das abas
    # (mesmos containers), e /biblioteca/ era um portal cujo único conteúdo
    # próprio, a lista de favoritos, a aba Favoritos já mostra.
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    for marca in ("data-collections-app", "data-notebooks-app", "data-fav-full-list",
                  'id="historico"', "data-history-list"):
        assert marca in ws, marca
    assert "Exemplo" not in ws and "Caderno Romanos" not in ws
    # os endereços antigos continuam existindo, agora como ponte (noindex)
    for pasta, destino in (("biblioteca", "workspace/#favoritos"),
                           ("colecoes", "workspace/#colecoes"),
                           ("cadernos", "workspace/#cadernos")):
        page = (site / pasta / "index.html").read_text("utf-8")
        assert destino in page, pasta
        assert 'name="robots" content="noindex"' in page, pasta
    # o hash precisa achar a aba: sem id, o redirect chegaria e não rolaria
    for tab in ("favoritos", "colecoes", "cadernos"):
        assert f'id="{tab}"' in ws, tab
    library = (site / "assets" / "library.js").read_text("utf-8")
    for key in ("bec.collections", "bec.notebooks"):
        assert key in library
    assert "assets/library.js" in ws
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "bec.history" in app


def test_workspace_abas_biblioteca_embutida(site):
    # Anotações, favoritos, coleções e cadernos ficam embutidos como abas no
    # Workspace (além de continuarem existindo como páginas próprias).
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    assert "data-ws-tabs" in ws
    for tab in ("anotacoes", "favoritos", "colecoes", "cadernos", "criar-plano"):
        assert f'data-ws-tab="{tab}"' in ws and f'data-ws-panel="{tab}"' in ws
    # "Atalhos" era uma grade de links dentro de uma aba, e abria por padrão:
    # a seção Estudar apresentava links em vez do trabalho da pessoa.
    assert 'data-ws-tab="atalhos"' not in ws
    assert 'data-ws-tab="anotacoes">Anotações' in ws.replace('class="ws-tab on" role="tab" aria-selected="true" ', '')
    assert 'id="anotacoes"' in ws
    assert "data-fav-full-list" in ws
    assert "data-collections-app" in ws
    assert "data-notebooks-app" in ws
    # seção "Explorar" desorfaniza dicionário/mapas/temas/artigos
    assert 'id="explorar"' in ws
    assert f'href="../dicionario/"' in ws and f'href="../mapas/"' in ws
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "data-ws-tabs" in app and "bec.wsTab" in app
    home = (site / "index.html").read_text("utf-8")
    assert 'href="dicionario/"' in home or "dicionario/" in home


def test_planos_de_leitura_reais(site):
    # Índice e página do plano são gerados com a navegação atual.
    index = (site / "planos" / "index.html").read_text("utf-8")
    assert "João em 2 dias" in index
    assert "mobile-primary-nav" in index
    plano = (site / "planos" / "joao-2-dias" / "index.html").read_text("utf-8")
    # Dias com checkbox persistível e referência conhecida vira link de leitura.
    assert 'data-plan="joao-2-dias"' in plano
    assert 'data-day="1"' in plano
    assert 'data-plan-reset="joao-2-dias"' in plano
    assert 'href="../../ler/joao/1/"' in plano
    # Referência desconhecida degrada para texto puro, sem link quebrado.
    assert "Salmo desconhecido" in plano
    assert 'ler/salmo-desconhecido' not in plano
    # O app.js sabe guardar o progresso e o sitemap lista as páginas.
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "bec.planProgress" in app
    sitemap = (site / "sitemap.xml").read_text("utf-8")
    assert "/planos/</loc>" in sitemap
    assert "/planos/joao-2-dias/</loc>" in sitemap


def test_plan_index(site):
    # Dados de ponte para o leitor saber em que dia de plano o capítulo está.
    index = json.loads((site / "data" / "plan-index.json").read_text("utf-8"))
    plan = next(p for p in index if p["slug"] == "joao-2-dias")
    assert plan["titulo"] == "João em 2 dias"
    assert plan["dias"][0][0] == {"label": "João 1", "url": "ler/joao/1/"}
    # Referência desconhecida degrada para url None (sem link quebrado).
    dia2 = {d["label"]: d["url"] for d in plan["dias"][1]}
    assert dia2["João 2"] == "ler/joao/2/"
    assert dia2["Salmo desconhecido"] is None


def test_chapter_verse_counts(site):
    counts = json.loads((site / "data" / "chapter-verses.json").read_text("utf-8"))
    assert counts["genesis"]["1"] == 1
    assert counts["joao"]["1"] == 1


def test_versiculo_do_dia(site):
    # Pool curado com slug + referência + texto, para montar o cartão sem 2ª requisição.
    # Refs ausentes do dataset são ignoradas (aqui só existem Gênesis 1:1 e João 1:1).
    daily = json.loads((site / "data" / "daily.json").read_text("utf-8"))
    assert len(daily) >= 1
    for item in daily:
        assert set(item) == {"slug", "ref", "pt"}
        assert item["slug"] and item["ref"] and item["pt"]
    refs = {d["ref"] for d in daily}
    assert "Gênesis 1:1" in refs
    # Cartão na home mantém o botão de sorteio (id preservado) e ganha share/streak.
    home = (site / "index.html").read_text("utf-8")
    for hook in ('data-daily-verse', 'data-daily-share', 'data-daily-streak', 'id="random-verse"'):
        assert hook in home, hook
    # JS: rotação estável por dia + reforço de hábito + share reutilizado.
    app = (site / "assets" / "app.js").read_text("utf-8")
    for token in ("data-daily-verse", "daily.json", "86400000", "bec.dailySeen", "shareCard"):
        assert token in app, token
    study = (site / "assets" / "study.js").read_text("utf-8")
    assert "BEC.shareCard" in study


def test_gesto_swipe_entre_capitulos(site):
    # Livro de um só capítulo não expõe nenhum destino de swipe (sem vizinhos).
    cap1 = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "data-prev-chapter" not in cap1 and "data-next-chapter" not in cap1
    # JS do gesto presente, com as travas contra seleção/folha aberta/grifo.
    app = (site / "assets" / "app.js").read_text("utf-8")
    for token in ("touchstart", "data-prev-chapter", "data-next-chapter",
                  "swiping-", "sheet-open", "hl-mode", "getSelection"):
        assert token in app, token


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


def test_grifo_colorido_por_versiculo(site):
    # A caneta morta (arrastar palavra a palavra) e o cartão de doação (link
    # quebrado) saíram; grifo agora é por versículo, com paleta de 4 cores,
    # acionado pela folha de ferramentas única.
    study = (site / "assets" / "study.js").read_text("utf-8")
    for gancho in ("vs-color", "setHlColor", "hlColor", "verse-sheet", "openSheet", 'data-vs-act="share"'):
        assert gancho in study, gancho
    for morto in ("pen-toggle", "makePenTools", "DONATE_URL", "DONATE_EVERY"):
        assert morto not in study, morto


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
    # FAB do leitor: ferramentas configuráveis + posição arrastável salva.
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    for hook in ('data-reader-fab-config', 'data-reader-fab-config-panel', 'data-tool="theme"'):
        assert hook in cap, hook
    for token in ("bec.readerTools", "bec.fabPos", "pointerdown", "setPointerCapture"):
        assert token in app, token


def test_audio_e_favoritos(site):
    # Os botões por versículo saíram do HTML: favoritar/ouvir agora vivem na
    # folha de ferramentas única (study.js), acionada ao tocar no texto.
    app = (site / "assets" / "app.js").read_text("utf-8")
    for gancho in ("speechSynthesis", "SpeechSynthesisUtterance", "BEC.speak",
                   "bec.favs", "data-fav", "BEC.favs", "favorite-home"):
        assert gancho in app, gancho
    home = (site / "index.html").read_text("utf-8")
    assert 'id="favorite-home"' in home and 'id="favorite-list"' in home
    vp = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert 'data-lang="he-IL"' in vp and "verse-tap" in vp
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert 'data-lang="he-IL"' in cap and "verse-tap" in cap
    study = (site / "assets" / "study.js").read_text("utf-8")
    for gancho in ('data-vs-act="fav"', 'data-vs-act="speak-orig"', 'data-vs-act="speak-pt"'):
        assert gancho in study, gancho


def test_lote2_cartao_ferramentas_modal(site):
    study = (site / "assets" / "study.js").read_text("utf-8")
    # base do site injetada + cartão-imagem + compartilhar versículo + folha única
    assert study.startswith("var BEC_BASE=")
    for gancho in ("makeVerseCard", "canShare", "toBlob", "shareVerse", "verse-sheet", "confirmModal"):
        assert gancho in study, gancho
    # confirmModal/bec-modal foram centralizados no core.js compartilhado
    core = (site / "assets" / "core.js").read_text("utf-8")
    assert "bec-modal" in core and "function confirmModal(" in core
    # o antigo painel de ferramentas flutuante próprio saiu: foi absorvido
    # pelo painel único de leitura (reader-fab)
    assert "tools-fab" not in study and "tools-panel" not in study
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "data-study-export" in cap and "data-study-share" in cap and "data-study-clear" in cap


def test_seletor_de_livro_e_capitulo_abre_do_leitor(site):
    # o gatilho aparece nas duas páginas do leitor, já sabendo onde o leitor está
    cap = (site / "ler" / "joao" / "1" / "index.html").read_text("utf-8")
    assert 'data-refp-book="joao"' in cap and 'data-refp-chapter="1"' in cap
    book = (site / "ler" / "joao" / "index.html").read_text("utf-8")
    assert 'data-ref-picker' in book and 'data-refp-chapter' not in book
    # sem JavaScript continua sendo um link para a lista de livros
    assert 'href="../../ler/"' in book
    # e também está entre as ferramentas do leitor
    assert 'data-tool="goto"' in cap
    # o painel é montado no cliente a partir de BEC_BOOKS (livro + nº de capítulos)
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "data-ref-picker" in app and "refp-chapters" in app
    assert '"cap":' in app and '"t":' in app


def test_workspace_poe_ferramentas_antes_do_placar(site):
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    # Estudar vinha depois de quase duas telas de gamificação; agora abre a página
    assert ws.index('id="estudar"') < ws.index('id="progresso"')
    # e a página ganhou índice, porque tinha várias telas sem forma de pular
    assert "ws-sections" in ws
    # o botão principal é o que sabe onde a pessoa parou
    assert 'data-ws-continue' in ws and 'class="btn primary"' in ws


def test_referencias_cruzadas_vem_em_shard_por_capitulo(site):
    # O consumidor busca data/xrefs/<livro>/<cap>.json, não um arquivo único:
    # eram 39 versículos em 3 KB, agora são ~93 mil ligações, e carregar tudo
    # de uma vez repetiria o erro do índice de busca (6,3 MB por consulta).
    study = (site / "assets" / "study.js").read_text("utf-8")
    assert "data/xrefs/" in study
    assert "cross-references.json" not in study.replace(
        "cross-references.json de 3 KB", "")
    # a chave do capítulo sai do helper que já existe no core
    assert "bookSlugFromRef" in study
    # e o arquivo único antigo não é mais publicado
    assert not (site / "data" / "cross-references.json").exists()


def test_workspace_sabe_onde_a_pessoa_parou(site):
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    # o bloco nasce oculto: sem leitura salva não há o que dizer
    assert "data-ws-focus" in ws and "Onde você parou" in ws
    assert "ws-focus" in ws and "hidden" in ws.split("data-ws-focus")[1][:40]
    # ele cruza último capítulo, trecho estudado, notas daquele capítulo e plano
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert '"Onde você parou"' in app, "módulo não encontrado no app.js"
    modulo = app.split('"Onde você parou"', 1)[1].split("\n})();", 1)[0]
    for chave in ("bec.lastRead", "bec.readingRanges", "bec.notes", "planData",
                  "ws-focus-facts"):
        assert chave in modulo, chave


def test_conta_sai_do_workspace(site):
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    conta = (site / "conta" / "index.html").read_text("utf-8")
    # perfil e configurações ocupavam 27% do Workspace e não são estudo
    for marca in ('id="perfil"', 'id="configuracoes"', "data-settings-panel", "data-profile-name"):
        assert marca not in ws, marca
        assert marca in conta, marca
    # a conta tem o shell atual e volta para o Workspace
    assert "mobile-primary-nav" in conta and 'href="../workspace/"' in conta
    # o menu da conta aponta para o novo endereço
    auth = (site / "assets" / "auth.js").read_text("utf-8")
    assert "conta/#perfil" in auth and "conta/#configuracoes" in auth
    assert "workspace/#perfil" not in auth


def test_progresso_nao_aparece_zerado_para_quem_nunca_leu(site):
    game = (site / "assets" / "game.js").read_text("utf-8")
    # o painel só é revelado quando há atividade real, não incondicionalmente
    assert "panel.hidden=true; return;" in game
    assert "bec.readingRanges" in game


def test_palavras_de_jesus_saem_em_vermelho_com_legenda(site):
    cap = (site / "ler" / "joao" / "1" / "index.html").read_text("utf-8")
    assert 'class="pt jesus"' in cap
    # texto vermelho sem explicação é só uma cor: o capítulo traz a legenda
    assert "palavras de Jesus" in cap and "red-dot" in cap
    verso = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert 'class="pt jesus"' in verso and "Em vermelho: palavras de Jesus" in verso
    # o Antigo Testamento não é marcado
    gen = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "jesus" not in gen and "red-note" not in gen


def test_comentario_curado_aparece_no_versiculo(site):
    gen = (site / "versiculos" / "genesis-1-1" / "index.html").read_text("utf-8")
    assert "cmt-block" in gen and "Abre a Torá." in gen and "Contexto" in gen
    # versículo sem comentário não ganha a seção vazia
    joao = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert "cmt-block" not in joao


def test_lista_de_livros_tem_filtro_e_progresso(site):
    ler = (site / "ler" / "index.html").read_text("utf-8")
    assert "data-book-filter" in ler
    assert 'data-testament="at"' in ler and 'data-testament="nt"' in ler
    # cada cartão traz o selo de progresso, oculto até haver leitura marcada
    assert 'data-book-prog="João"' in ler
    assert "data-booklist-empty" in ler
    # a grade de capítulos expõe o número para o cliente marcar o que já foi lido
    book = (site / "ler" / "joao" / "index.html").read_text("utf-8")
    assert 'data-chapter-grid data-book="João"' in book
    assert 'data-ch="1"' in book
    # o progresso vem de bec.readingRanges, não do HTML publicado
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "data-book-prog" in app and "readingRanges" in app


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
    assert all("url" in i for i in index)
    # "k" é o texto extra de busca e só existe quando há o que acrescentar:
    # no versículo saía sempre em branco (contexto/palavras estão vazios em
    # todo o dataset) e o cliente já lê o campo como opcional.
    assert not any("k" in i for i in index if i["t"] == "Versículo")
    assert all("k" in i for i in index if i["t"] == "Artigo")


def test_sitemap_lista_todas_as_urls(site):
    sitemap = (site / "sitemap.xml").read_text("utf-8")
    assert "/versiculos/genesis-1-1/" in sitemap
    assert "/versiculos/joao-1-1/" in sitemap
    assert "/artigos/meu-artigo/" in sitemap
    for path in ("/workspace/", "/conta/"):
        assert path in sitemap
    # Redirects (noindex) ficam fora do sitemap — incluindo os três que foram
    # consolidados no Workspace.
    for path in ("/estudar/</loc>", "/comunidade/</loc>", "/comunidade/salas/</loc>",
                 "/biblioteca/</loc>", "/colecoes/</loc>", "/cadernos/</loc>"):
        assert path not in sitemap


def test_ajustes_ios_notas(site):
    # painel de leitura: compartilhar estudo (folha nativa, "Salvar em Notas"
    # no iOS) + baixar .txt; .json saiu do menu
    study = (site / "assets" / "study.js").read_text("utf-8")
    assert "Salvar tudo (.json)" not in study
    assert "function shareStudyText(" in study
    assert "data-study-export" in study and "data-study-share" in study
    # página Anotações: .json vira "backup", importar vira "Importar backup" (ids preservados)
    anot = (site / "anotacoes" / "index.html").read_text("utf-8")
    assert "Backup .json" in anot and "Importar backup" in anot
    assert 'id="anot-json"' in anot and 'id="anot-import"' in anot


def test_painel_ferramentas_minimiza():
    # o atributo hidden precisa vencer o display:flex, senão o painel fica sempre aberto
    from pathlib import Path
    css = (Path(__file__).resolve().parents[1] / "site" / "assets" / "styles.css").read_text("utf-8")
    assert ".reader-fab-panel[hidden]" in css
    assert ".verse-sheet[hidden]" in css


def test_lote4_ordenacao_dos_livros(site):
    # toggle de ordenação + atributos de ordenação nos cartões, na seção própria /ler/
    html = (site / "ler" / "index.html").read_text("utf-8")
    assert 'data-sort="alpha"' in html and 'data-sort="chron"' in html
    assert "data-booklist" in html
    assert "data-chron=" in html and "data-pos=" in html and "data-name=" in html
    # a home não despeja mais os livros: aponta para a seção própria
    home = (site / "index.html").read_text("utf-8")
    assert "data-booklist" not in home
    assert 'id="biblia"' in home
    # wiring + persistência no app.js
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "bec.bookorder" in app and "data-booklist" in app


def test_home_reorganizada(site):
    # Apresentação (idiomas/manuscritos) foi para o final, entre artigos e fontes;
    # os livros saíram da home e viraram uma seção própria (/ler/).
    home = (site / "index.html").read_text("utf-8")
    ordem = [home.index(a) for a in ('id="biblia"', 'id="temas"', 'id="artigos"',
                                     'id="apresentacao"', 'id="fontes"', 'id="metodologia"')]
    assert ordem == sorted(ordem)
    # O topo convida direto para a leitura e o Workspace.
    assert home.index('href="ler/"') < home.index('id="biblia"')
    assert "Abrir o Workspace" in home
    # A apresentação mantém o versículo-assinatura (specimen).
    apres = home[home.index('id="apresentacao"'):home.index('id="fontes"')]
    assert "specimen-card" in apres and "Ver fontes e licenças" in apres
    # "Plano de hoje" e "Últimas anotações" viraram containers dinâmicos
    # (deixam de ser texto fixo fingindo ser dado real).
    assert "data-home-plan" in home and "data-home-plan-body" in home
    assert "data-home-notes" in home and "data-home-notes-body" in home
    assert "Romanos 1 · leitura leve" not in home
    ws = (site / "workspace" / "index.html").read_text("utf-8")
    assert "data-ws-continue" in ws
    app = (site / "assets" / "app.js").read_text("utf-8")
    for token in ("planData", "nextOpenDay", "notesMeta", "data-ws-continue"):
        assert token in app, token


def test_modo_leitura_foco(site):
    # O modo leitura esconde tudo menos o texto; entra pelo FAB ou pelo botão
    # no cabeçalho do capítulo, e tem botão fixo para sair.
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "data-focus-toggle" in cap
    assert "focus-exit" in cap
    assert 'data-tool="focus"' in cap
    app = (site / "assets" / "app.js").read_text("utf-8")
    assert "bec.focusRead" in app and "focus-read" in app
    from pathlib import Path
    css = (Path(__file__).resolve().parents[1] / "site" / "assets" / "styles.css").read_text("utf-8")
    assert "html.focus-read" in css
    # Páginas sem texto corrido não ativam o modo (guarda pela presença de .chapter).
    assert "isChapter" in app
    # Foco progressivo: versículo atual em destaque + contador "faltam N" +
    # "Marcar capítulo como lido" reusa o fluxo real que credita a missão.
    assert "data-focus-remaining" in cap and "data-focus-mark" in cap
    for token in ("fr-current", "requestAnimationFrame", "data-focus-mark"):
        assert token in app, token
    assert "fr-current" in css


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


def test_leitor_conectado_ao_plano(site):
    # Banner de contexto (Dia N de T · Plano) no capítulo + auto-marcação do
    # dia ao ler o capítulo por completo.
    cap = (site / "ler" / "genesis" / "1" / "index.html").read_text("utf-8")
    assert "data-plan-context" in cap
    app = (site / "assets" / "app.js").read_text("utf-8")
    for token in ("bec:chapter-read", "plan-index.json", "chapter-verses.json",
                  "data-plan-context-mark", "planos/"):
        assert token in app, token
    # o link enganoso "Meu plano" (que levava ao criador, não à leitura) saiu
    assert "🗓 Meu plano" not in cap


def test_temas_dicionario_e_mapas_voltam_ao_build(site):
    """As três seções ficaram fora do gerador e congelaram com a navegação
    antiga (sem Workspace, sem barra inferior). Agora são geradas com o mesmo
    shell das demais páginas."""
    for path in (
        ("temas", "index.html"), ("temas", "criacao", "index.html"),
        ("dicionario", "index.html"), ("dicionario", "logos", "index.html"),
        ("mapas", "index.html"), ("mapas", "eden", "index.html"),
        ("offline", "index.html"),
    ):
        page = site.joinpath(*path)
        assert page.exists(), path
        html = page.read_text("utf-8")
        # shell atual: navegação de 3 áreas, barra inferior e overlay de busca
        assert 'class="mobile-primary-nav"' in html
        assert "workspace/" in html
        assert "data-search-overlay" in html
        # nada da navegação velha
        assert ">Linha do tempo</a>\n      <a" not in html
        assert 'data-rt="context"' not in html


def test_temas_ligam_versiculos_e_nao_caem_todos_em_ler(site):
    # Antes: os 12 chips da home apontavam todos para /ler/.
    home = (site / "index.html").read_text("utf-8")
    assert 'class="chip" href="temas/criacao/"' in home
    assert 'class="chip" href="ler/"' not in home
    tema = (site / "temas" / "criacao" / "index.html").read_text("utf-8")
    assert "versiculos/genesis-1-1/" in tema
    # referência curada que não existe no dataset é ignorada, não quebra o build
    assert "Ageu 9:9" not in tema
    # a busca também leva ao tema, não a /ler/
    index = json.loads((site / "data" / "search-index.json").read_text("utf-8"))
    temas = [i for i in index if i["t"] == "Tema"]
    assert temas and all(i["url"].startswith("temas/") for i in temas)


def test_dicionario_e_mapas_ligam_versiculos_e_fontes(site):
    gloss = (site / "dicionario" / "logos" / "index.html").read_text("utf-8")
    assert "versiculos/joao-1-1/" in gloss
    assert "λόγος" in gloss
    # artigo do mesmo termo entra em "Para aprofundar" quando existe
    mapa = (site / "mapas" / "eden" / "index.html").read_text("utf-8")
    assert "openstreetmap.org" in mapa
    assert "versiculos/genesis-1-1/" in mapa


def test_versiculo_volta_para_o_capitulo(site):
    # Antes o caminho versículo -> capítulo não existia: a trilha ia de
    # "Livros" direto para a referência.
    verso = (site / "versiculos" / "joao-1-1" / "index.html").read_text("utf-8")
    assert 'href="../../ler/joao/">João</a>' in verso
    assert 'href="../../ler/joao/1/">1</a>' in verso
    assert "Ler João 1 inteiro" in verso


def test_404_oferece_busca_e_saidas(site):
    html = (site / "404.html").read_text("utf-8")
    assert 'id="q"' in html and 'id="results"' in html
    for destino in ('href="ler/"', 'href="temas/"', 'href="workspace/"'):
        assert destino in html


def test_sitemap_inclui_temas_dicionario_e_mapas(site):
    sitemap = (site / "sitemap.xml").read_text("utf-8")
    for path in ("/temas/", "/temas/criacao/", "/dicionario/", "/dicionario/logos/",
                 "/mapas/", "/mapas/eden/", "/anotacoes/"):
        assert f"{path}</loc>" in sitemap
    # a página de fallback do service worker não é conteúdo indexável
    assert "/offline/</loc>" not in sitemap
