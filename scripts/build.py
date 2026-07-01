#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador do site estático "Bíblia em Contexto".
Lê os JSON em site/data e gera HTML estático (home + página por versículo +
página por artigo), sitemap e robots. Não precisa de internet.

Uso:
    python scripts/build.py
Opcional: defina o domínio final em BASE_URL antes de publicar.
"""
import json, shutil, sys, unicodedata, hashlib
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build_config import (
    BASE_URL,
    BOOK_ORDER,
    CHRON_INDEX,
    DATA,
    GENERATED_DIRS,
    MANUSCRITO_FACSIMILE,
    SEFARIA,
    SITE,
    SITE_NAME,
    TIMELINE,
)
from build_utils import (
    book_slug,
    esc,
    group_by_book_chapter,
    lang_label,
    ref_chvs,
    script_class,
    speech_lang,
    verse_sort_key,
)

SOURCE_ASSETS = {
    "auth.asset.js": "auth.js",
    "app.asset.js": "app.js",
    "study.asset.js": "study.js",
    "gamification.asset.js": "game.js",
}


def asset_ver():
    # Cache-busting: muda quando o gerador, os assets-fonte ou o CSS mudam.
    h = hashlib.sha1()
    for path in [
        Path(__file__),
        SCRIPTS_DIR / "build_config.py",
        SCRIPTS_DIR / "build_utils.py",
        *(SCRIPTS_DIR / name for name in SOURCE_ASSETS),
        SITE / "assets" / "styles.css",
    ]:
        if path.exists():
            h.update(path.read_bytes())
    return h.hexdigest()[:8]

ASSET_VER = asset_ver()

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def read_asset(name):
    return (SCRIPTS_DIR / name).read_text(encoding="utf-8")


def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    content = "\n".join(line.rstrip() for line in content.splitlines())
    if content:
        content += "\n"
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def write_asset(source_name, target_name):
    write_file(SITE / "assets" / target_name, read_asset(source_name))


def sefaria_url(livro, ch, vs):
    book = SEFARIA.get(livro)
    if not book:
        return ""
    return f"https://www.sefaria.org/{book.replace(' ', '_')}.{ch}.{vs}?lang=bi&with=all"

def translit_disclosure(text):
    text = (text or "").strip()
    if not text:
        return ""
    return (
        '<details class="translit-toggle">'
        '<summary>Mostrar transliteração</summary>'
        f'<p class="translit">{esc(text)}</p>'
        '</details>'
    )

def original_html(v):
    original = (v.get("original") or "").strip()
    if not original:
        return ""
    idioma = v.get("idioma", "")
    direction = v.get("dir", "")
    sc = script_class(idioma, direction)
    dir_attr = f' dir="{esc(direction)}"' if direction else ""
    body = f'<p class="orig {sc}"{dir_attr}>{esc(original)}</p>'
    if idioma == "grego":
        return (
            '<details class="original-toggle">'
            f'<summary>Mostrar texto {esc(lang_label(idioma).lower())}</summary>'
            f'{body}</details>'
        )
    return body

def verse_url(prefix, slug):
    return f"{prefix}versiculos/{slug}/"

def audio_button(label, text, lang, transcript="", transcript_label="Transcrição do áudio original"):
    if not (text or "").strip():
        return ""
    trans_attr = f' data-transcript="{esc(transcript)}"' if (transcript or "").strip() else ""
    label_attr = f' data-transcript-label="{esc(transcript_label)}"' if (transcript or "").strip() else ""
    return (f'<button type="button" class="listen" data-speak="{esc(text)}" '
            f'data-lang="{esc(lang)}"{trans_attr}{label_attr}>{esc(label)}</button>')

def fav_button(ref, url):
    return (f'<button type="button" class="listen fav" data-fav data-ref="{esc(ref)}" '
            f'data-url="{esc(url)}" aria-pressed="false">☆ Favoritar</button>')

def verse_tools(v, prefix):
    transcript = v.get("transliteracao", "") if v.get("idioma") in ("hebraico", "aramaico") else ""
    transcript_label = f"Transcrição do áudio {lang_label(v.get('idioma', '')).lower()}"
    original = audio_button("Ouvir original", v.get("original", ""), speech_lang(v.get("idioma", "")), transcript, transcript_label)
    pt = audio_button("Ouvir PT", v.get("texto_pt", ""), "pt-BR")
    fav = fav_button(v.get("referencia", ""), verse_url(prefix, v.get("slug", "")))
    return f'<div class="verse-tools">{original}{pt}{fav}</div>'

def book_data_attrs(livro):
    # atributos para reordenar os cartões no cliente (bíblica/alfabética/cronológica)
    pos = BOOK_ORDER.index(livro) if livro in BOOK_ORDER else 999
    nome = unicodedata.normalize("NFKD", livro).encode("ascii","ignore").decode().lower()
    return f' data-pos="{pos}" data-name="{esc(nome)}" data-chron="{CHRON_INDEX.get(livro, 999)}"'

def order_toggle(prefix):
    # controle de ordenação no topo da grade de livros (cliente, persistido)
    return f"""
  <div class="order-toggle" role="group" aria-label="Ordenar livros">
    <span class="ot-lbl">Ordenar:</span>
    <button type="button" class="ot on" data-sort="bib">Bíblica</button>
    <button type="button" class="ot" data-sort="alpha">Alfabética</button>
    <button type="button" class="ot" data-sort="chron">Cronológica</button>
    <a class="ot-link" href="{prefix}linha-do-tempo/">linha do tempo →</a>
  </div>"""

# ---------- shells ----------
def head(title, description, canonical, prefix, jsonld=None):
    ld = f'\n<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index, follow, noai, noimageai">
<link rel="canonical" href="{esc(canonical)}">
<meta name="theme-color" content="#1a1610">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:site_name" content="{SITE_NAME}">
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Spectral:wght@400;500;600&family=Inter:wght@400;600;700&family=Frank+Ruhl+Libre:wght@400;500;700&family=Gentium+Book+Plus:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/styles.css?v={ASSET_VER}">{ld}
</head>
<body>
<script>(function(){{try{{var d=document.documentElement;if(localStorage.getItem('bec.theme')==='dark')d.classList.add('dark');var f=localStorage.getItem('bec.fontscale');if(f)d.classList.add('fs-'+f);}}catch(e){{}}}})();</script>
<a class="skip" href="#main">Pular para o conteúdo</a>
<div class="beta-banner" data-beta-banner hidden role="status">
  <span class="beta-tag">Beta</span>
  <span class="beta-text">Você está numa versão de testes. Seu estudo é salvo e sincronizado; recursos da comunidade estão em construção.</span>
  <button type="button" class="beta-dismiss" data-beta-dismiss aria-label="Ocultar aviso beta">×</button>
</div>"""

def nav(prefix):
    links = [
        ("Início", f"{prefix}index.html"),
        ("Bíblia", f"{prefix}ler/"),
        ("Estudar", f"{prefix}estudar/"),
        ("Comunidade", f"{prefix}comunidade/"),
        ("Workspace", f"{prefix}workspace/"),
    ]
    nav_links = "\n      ".join(f'<a href="{url}">{label}</a>' for label, url in links)
    mobile_links = "\n  ".join(f'<a href="{url}">{label}</a>' for label, url in links)
    return f"""
<nav class="nav">
  <div class="nav-in">
    <a class="brand" href="{prefix}index.html">
      <span class="brand-mark">ב</span>
      <span class="brand-name">Bíblia em Contexto</span>
    </a>
    <div class="reader-tools">
      <button type="button" class="rt" data-rt="font-dec" aria-label="Diminuir fonte">A−</button>
      <button type="button" class="rt" data-rt="font-inc" aria-label="Aumentar fonte">A+</button>
      <button type="button" class="rt" data-rt="theme" aria-label="Modo noturno" title="Modo noturno">🌙</button>
    </div>
    <span class="account-wrap">
      <button type="button" class="auth-trigger" data-auth-open>Entrar</button>
      <span class="account-badge" data-account-badge hidden></span>
    </span>
    <button class="menu-btn" aria-label="Abrir menu" data-menu>☰</button>
    <div class="nav-links" data-links>
      {nav_links}
    </div>
  </div>
</nav>
<nav class="mobile-primary-nav" aria-label="Navegação principal">
  {mobile_links}
</nav>"""

def footer(prefix):
    return f"""
<footer class="footer">
  <div class="footer-in">
    <div>
      <strong>Bíblia em Contexto</strong>
      <p>Estudo bíblico com os idiomas originais, manuscritos e fontes rastreáveis. Texto bíblico de domínio público; comentários originais.</p>
    </div>
    <div class="cols">
      <div>
        <a href="{prefix}ler/">Bíblia</a>
        <a href="{prefix}estudar/">Estudar</a>
        <a href="{prefix}workspace/">Workspace</a>
      </div>
      <div>
        <a href="{prefix}comunidade/">Comunidade</a>
        <a href="{prefix}biblioteca/">Biblioteca</a>
        <a href="{prefix}index.html#fontes">Fontes e licenças</a>
      </div>
    </div>
  </div>
</footer>
<script src="{prefix}assets/supabase-config.js?v={ASSET_VER}" defer></script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js" defer></script>
<script src="{prefix}assets/auth.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/app.js?v={ASSET_VER}"></script>
<script src="{prefix}assets/study.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/game.js?v={ASSET_VER}" defer></script>
</body></html>"""

# ---------- componentes ----------
def verse_stack(v, big=False):
    sc = script_class(v["idioma"], v.get("dir","ltr"))
    dir_attr = ' dir="rtl"' if v.get("dir")=="rtl" else ' dir="ltr"'
    return f"""
    <p class="orig {sc}"{dir_attr}>{esc(v['original'])}</p>
    <p class="translit">{esc(v['transliteracao'])}</p>
    <p class="pt">{esc(v['texto_pt'])}</p>"""

def specimen_block(v):
    m = v.get("manuscrito") or {}
    img = m.get("imagem")
    cap = esc(m.get("legenda",""))
    lic = esc(m.get("licenca",""))
    fonte_nome = esc(m.get("fonte_nome",""))
    fonte_url = esc(m.get("fonte_url",""))
    seal = "Domínio público" if "domínio público" in (m.get("licenca","").lower()) else "Verificar licença"
    if img:
        frame = (f'<div class="frame"><img loading="lazy" alt="{cap}" src="{esc(img)}" '
                 f'onerror="this.closest(\'.specimen\').querySelector(\'.frame\').innerHTML=\'<div class=&quot;ph&quot;><b>✶</b>Imagem indisponível no momento. Veja no acervo da fonte.</div>\'"></div>')
    else:
        frame = ('<div class="frame"><div class="ph"><b>✶</b>'
                 'Manuscritos são fotografados por página, não por versículo. '
                 'Veja o fac-símile completo do códice-fonte.</div></div>')
    link = f' · <a href="{fonte_url}" target="_blank" rel="noopener">{fonte_nome} ↗</a>' if fonte_url else ""
    cap_txt = cap or "Texto hebraico do Códice de Leningrado (Westminster Leningrad Codex)."
    fac = (f'<div class="lic"><a class="ext-link" href="{MANUSCRITO_FACSIMILE}" target="_blank" '
           f'rel="noopener">Ver o manuscrito (Códice de Leningrado) ↗</a></div>') if not img else ""
    return f"""
  <figure class="specimen">
    {frame}
    <figcaption class="cap">
      <p>{cap_txt}</p>
      <div class="lic"><span class="seal">{esc(seal)}</span> {lic}{link}</div>
      {fac}
    </figcaption>
  </figure>"""

def mini_cards(items):
    return "".join(
        f"""
    <article class="study-card">
      <span>{esc(label)}</span>
      <h3>{esc(title)}</h3>
      <p>{esc(text)}</p>
    </article>"""
        for label, title, text in items
    )


def action_cards(items):
    return "".join(
        f"""
    <a class="study-card link-card" href="{esc(url)}">
      <span>{esc(label)}</span>
      <h3>{esc(title)}</h3>
      <p>{esc(text)}</p>
    </a>"""
        for label, title, text, url in items
    )


def study_map_module(prefix, livro, ch=None, vs=None):
    place = f"{livro} {ch}:{vs}" if vs else (f"{livro} {ch}" if ch else livro)
    return f"""
  <section class="study-map">
    <div class="study-map-head">
      <p class="eyebrow">Mapa de Estudos</p>
      <h2>{esc(place)}</h2>
      <p>Dados demonstrativos para organizar pessoas, perguntas e salas pelo conteúdo bíblico estudado.</p>
    </div>
    <div class="metric-grid">
      <div><b>24</b><span>pessoas lendo hoje</span></div>
      <div><b>8</b><span>discussões</span></div>
      <div><b>15</b><span>perguntas</span></div>
      <div><b>4</b><span>estudos públicos</span></div>
    </div>
    <div class="study-card-grid">
      {mini_cards([
        ("Salas relacionadas", f"Sala {place}", "Leitura guiada com discussões por trecho e materiais de apoio."),
        ("Perguntas recentes", "Contexto e aplicação", "Perguntas organizadas por livro, capítulo e versículo."),
        ("Coleções públicas", "Referências do estudo", "Versículos, artigos, mapas e manuscritos reunidos por tema."),
      ])}
    </div>
    <p class="map-actions"><a class="btn primary" href="{prefix}comunidade/salas/">Ver Salas de Estudo</a><a class="btn quiet" href="{prefix}estudar/">Abrir ferramentas de estudo</a></p>
  </section>"""


def study_desk_module(prefix, livro, ch=None):
    title = f"Mesa de Estudo: {livro} {ch}" if ch else f"Mesa de Estudo: {livro}"
    return f"""
  <section class="study-desk">
    <div>
      <p class="eyebrow">Mesa de Estudo</p>
      <h2>{esc(title)}</h2>
      <p>Um ponto de encontro entre Bíblia, notas, coleções, perguntas, manuscritos, plano e progresso.</p>
    </div>
    <div class="desk-tabs" aria-label="Ferramentas da Mesa de Estudo">
      <a href="{prefix}ler/">Bíblia</a>
      <a href="{prefix}anotacoes/">Minhas notas</a>
      <a href="{prefix}colecoes/">Coleções</a>
      <a href="{prefix}comunidade/">Pessoas estudando</a>
      <a href="{prefix}comunidade/">Perguntas</a>
      <a href="{prefix}linha-do-tempo/">Mapa</a>
      <a href="{prefix}estudar/">Plano</a>
    </div>
  </section>"""


def build_study_page():
    prefix = "../"
    title = f"Estudar | {SITE_NAME}"
    desc = "Ferramentas de estudo bíblico: planos, biblioteca, favoritos, anotações, marcações, histórico e exploração por temas."
    canonical = f"{BASE_URL}/estudar/"
    tool_cards = action_cards([
        ("Estudos", "Meus estudos", "Organize estudos em andamento e retome pelo último trecho.", "#meus-estudos"),
        ("Planos", "Planos", "Acompanhe leituras de 7, 14, 21 ou 30 dias.", "#planos"),
        ("Biblioteca", "Biblioteca", "Notas, grifos, favoritos, artigos, coleções e cadernos.", f"{prefix}biblioteca/"),
        ("Favoritos", "Favoritos", "Versículos salvos para voltar depois.", f"{prefix}biblioteca/#favoritos"),
        ("Anotações", "Anotações", "Notas salvas neste navegador e sincronizáveis quando houver conta.", f"{prefix}anotacoes/"),
        ("Marcações", "Marcações", "Grifos por palavra e por versículo.", f"{prefix}biblioteca/#grifos"),
        ("Histórico", "Histórico", "Continue a leitura recente.", f"{prefix}workspace/#historico"),
        ("Explorar", "Explorar", "Temas, livros, manuscritos e linha do tempo.", f"{prefix}index.html#temas"),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Estudar</p>
  <header class="hub-hero">
    <p class="eyebrow">Área de estudo</p>
    <h1>Estudar</h1>
    <p>Reúna planos, biblioteca, favoritos, anotações, marcações e histórico sem tirar a Bíblia do centro.</p>
  </header>
  <section class="hub-section" id="meus-estudos">
    <div class="section-title"><h2>Ferramentas</h2><a href="#criar-plano">Criar plano</a></div>
    <div class="study-card-grid">{tool_cards}
    </div>
  </section>
  <section class="hub-section plan-builder" id="criar-plano">
    <div class="section-title"><h2>Criar Plano</h2><span>Primeira versão local</span></div>
    <form class="plan-form" data-plan-form>
      <label>O que deseja estudar?
        <select name="tipo">
          <option>Livro</option><option>Tema</option><option>Personagem</option><option>Palavra</option><option>Profecia</option>
        </select>
      </label>
      <label>Escolher conteúdo <input name="conteudo" placeholder="Romanos, Salmos, oração, aliança..." required></label>
      <label>Duração
        <select name="duracao">
          <option>7 dias</option><option>14 dias</option><option>21 dias</option><option>30 dias</option><option>Personalizado</option>
        </select>
      </label>
      <label>Ritmo
        <select name="ritmo"><option>Leve</option><option>Normal</option><option>Profundo</option></select>
      </label>
      <label>Salvar como
        <select name="visibilidade"><option>Privado</option><option>Público</option><option>Apenas uma Sala de Estudo</option></select>
      </label>
      <button type="submit" class="btn primary">Salvar plano</button>
    </form>
    <div class="saved-plans" data-plan-list></div>
  </section>
</main>"""
    out = SITE / "estudar" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_workspace_page():
    prefix = "../"
    title = f"Workspace | {SITE_NAME}"
    desc = "Espaço pessoal para continuar leitura, acompanhar planos, biblioteca, salas, coleções, cadernos e progresso."
    canonical = f"{BASE_URL}/workspace/"
    cards = action_cards([
        ("Leitura", "Continuar leitura", "Retome o último capítulo ou versículo aberto.", f"{prefix}ler/"),
        ("Hoje", "Plano de hoje", "Veja o trecho reservado para o dia.", f"{prefix}estudar/#planos"),
        ("Estudos", "Meus estudos", "Planos e estudos pessoais em andamento.", f"{prefix}estudar/#meus-estudos"),
        ("Biblioteca", "Minha biblioteca", "Notas, grifos, favoritos, planos e artigos.", f"{prefix}biblioteca/"),
        ("Salas", "Minhas salas", "Salas de Estudo conectadas ao conteúdo bíblico.", f"{prefix}comunidade/salas/"),
        ("Coleções", "Coleções", "Guarde versículos, capítulos, artigos, mapas, manuscritos e planos.", f"{prefix}colecoes/"),
        ("Cadernos", "Cadernos", "Organize notas, perguntas, grifos, coleções e referências.", f"{prefix}cadernos/"),
        ("Progresso", "Progresso", "Dias estudando, planos concluídos e calendário.", "#progresso"),
        ("Perfil", "Perfil", "Seu perfil de estudo e contribuições.", "#perfil"),
        ("Configurações", "Configurações", "Preferências, privacidade e sincronização.", "#configuracoes"),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Workspace</p>
  <header class="hub-hero">
    <p class="eyebrow">Espaço pessoal</p>
    <h1>Workspace</h1>
    <p>Sua mesa pessoal para ler, estudar, guardar materiais e acompanhar progresso.</p>
  </header>
  <section class="hub-section">
    <div class="study-card-grid">{cards}
    </div>
  </section>
  <section class="hub-section progresso" id="progresso" data-progress-panel hidden>
    <div class="section-title"><h2>Seu progresso</h2><span data-progress-note>Entre na conta para salvar entre aparelhos</span></div>
    <div class="progress-stats">
      <div class="pstat"><b data-progress-streak>0</b><span>dias seguidos</span></div>
      <div class="pstat"><b data-progress-level>1</b><span>nível</span></div>
      <div class="pstat"><b data-progress-xp>0</b><span>pontos (XP)</span></div>
      <div class="pstat"><b data-progress-medals>0</b><span>medalhas</span></div>
    </div>
    <div class="mission-block">
      <h3>Missões de hoje</h3>
      <div class="mission-list" data-mission-list></div>
    </div>
    <div class="medal-block">
      <h3>Medalhas</h3>
      <div class="medal-grid" data-medal-grid></div>
    </div>
  </section>
  <section class="hub-section profile-study" id="perfil">
    <div class="section-title"><h2>Perfil de estudo</h2><span>Sem seguidores ou ranking</span></div>
    <div class="profile-grid">
      <div><b>Nome</b><span data-profile-name>Seu nome público</span></div>
      <div><b>Conta</b><span data-profile-status>Visitante (estudo salvo neste navegador)</span></div>
      <div><b>Dias seguidos</b><span data-profile-streak>0</span></div>
      <div><b>Anotações</b><span data-profile-notes>0</span></div>
      <div><b>Favoritos</b><span data-profile-favs>0</span></div>
      <div><b>Grifos</b><span data-profile-highlights>0</span></div>
    </div>
  </section>
  <section class="hub-section" id="configuracoes">
    <div class="section-title"><h2>Configurações e sincronização</h2><a href="{prefix}privacidade/">Privacidade</a></div>
    <p class="muted-line">A conta fica restrita a perfil, configurações, privacidade, sincronização e sair. Ferramentas de estudo permanecem no Workspace e em Estudar.</p>
  </section>
</main>"""
    out = SITE / "workspace" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_community_page():
    prefix = "../"
    title = f"Comunidade | {SITE_NAME}"
    desc = "Comunidade organizada por estudo bíblico: salas, perguntas, oração, testemunhos, estudos públicos e discussões por livro ou capítulo."
    canonical = f"{BASE_URL}/comunidade/"
    cards = action_cards([
        ("Salas de Estudo", "Salas de Estudo", "Estude um livro, capítulo ou tema com plano vinculado.", f"{prefix}comunidade/salas/"),
        ("Perguntas", "Perguntas por trecho", "Dúvidas conectadas a livro, capítulo e versículo.", "#perguntas"),
        ("Oração", "Pedidos de oração", "Pedidos organizados com discrição e contexto.", "#oracao"),
        ("Testemunhos", "Testemunhos", "Relatos ligados ao estudo e à caminhada.", "#testemunhos"),
        ("Estudos públicos", "Estudos públicos", "Planos, notas e coleções compartilhadas.", "#estudos-publicos"),
        ("Discussões", "Por livro e capítulo", "Conversas ao redor do conteúdo bíblico.", f"{prefix}ler/"),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Comunidade</p>
  <header class="hub-hero">
    <p class="eyebrow">Comunidade por conteúdo</p>
    <h1>Comunidade</h1>
    <p>Encontre pessoas pelo livro, capítulo, tema ou plano que estão estudando. Sem feed genérico.</p>
  </header>
  <section class="hub-section">
    <div class="study-card-grid">{cards}
    </div>
  </section>
  <section class="hub-section">
    <div class="section-title"><h2>Pessoas estudando o mesmo conteúdo</h2><span>Preparado para dados reais</span></div>
    <div class="metric-grid">
      <div><b>24</b><span>pessoas lendo João 3 hoje</span></div>
      <div><b>8</b><span>discussões</span></div>
      <div><b>15</b><span>perguntas</span></div>
      <div><b>4</b><span>estudos públicos</span></div>
    </div>
  </section>
</main>"""
    out = SITE / "comunidade" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_study_rooms_page():
    prefix = "../../"
    title = f"Salas de Estudo | {SITE_NAME}"
    desc = "Salas de Estudo com tema bíblico, plano vinculado, discussões, materiais e progresso coletivo."
    canonical = f"{BASE_URL}/comunidade/salas/"
    rooms = mini_cards([
        ("João", "Sala Evangelho de João", "Tema: João. Plano vinculado: 21 dias. Discussões por capítulo e materiais de apoio."),
        ("Romanos", "Sala Romanos verso a verso", "Tema: Romanos. Plano vinculado: 30 dias. Progresso coletivo por seção."),
        ("Salmos", "Sala Salmos para oração", "Tema: Salmos. Plano vinculado: 14 dias. Pedidos de oração e caderno comum."),
        ("Família", "Sala Casais cristãos", "Tema: casamento. Plano vinculado: 21 dias. Perguntas e estudos públicos relacionados."),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="../">Comunidade</a> · Salas de Estudo</p>
  <header class="hub-hero">
    <p class="eyebrow">Salas de Estudo</p>
    <h1>Salas de Estudo</h1>
    <p>Cada sala nasce de um livro, capítulo, tema ou plano. Participantes, discussões, materiais e progresso ficam ligados ao conteúdo.</p>
  </header>
  <section class="hub-section">
    <div class="study-card-grid">{rooms}
    </div>
  </section>
</main>"""
    out = SITE / "comunidade" / "salas" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_library_page():
    prefix = "../"
    title = f"Biblioteca | {SITE_NAME}"
    desc = "Biblioteca pessoal com notas, grifos, favoritos, planos, artigos, coleções e cadernos."
    canonical = f"{BASE_URL}/biblioteca/"
    cards = action_cards([
        ("Notas", "Notas", "Anotações por versículo, capítulo e tema.", f"{prefix}anotacoes/"),
        ("Grifos", "Grifos", "Marcações por palavra e por versículo.", "#grifos"),
        ("Favoritos", "Favoritos", "Versículos salvos para revisão.", "#favoritos"),
        ("Planos", "Planos", "Leituras estruturadas e progresso.", f"{prefix}estudar/#planos"),
        ("Artigos", "Artigos", "Estudos contextuais e materiais de apoio.", f"{prefix}index.html#artigos"),
        ("Coleções", "Coleções", "Conjuntos de versículos, capítulos, artigos, mapas e manuscritos.", f"{prefix}colecoes/"),
        ("Cadernos", "Cadernos", "Notas, perguntas, grifos, coleções, planos e referências.", f"{prefix}cadernos/"),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Biblioteca</p>
  <header class="hub-hero"><p class="eyebrow">Biblioteca</p><h1>Biblioteca</h1><p>Guarde e organize tudo que nasce do estudo bíblico.</p></header>
  <section class="hub-section"><div class="study-card-grid">{cards}</div></section>
</main>"""
    out = SITE / "biblioteca" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_collections_page():
    prefix = "../"
    title = f"Coleções | {SITE_NAME}"
    desc = "Coleções para guardar versículos, capítulos, artigos, mapas, manuscritos, planos e discussões."
    canonical = f"{BASE_URL}/colecoes/"
    cards = mini_cards([
        ("Exemplo", "Versículos sobre oração", "Versículos, capítulos e perguntas reunidos para revisão."),
        ("Exemplo", "Mapas de viagens de Paulo", "Mapas, lugares, artigos e referências cruzadas."),
        ("Exemplo", "Manuscritos do Novo Testamento", "Artigos, fac-símiles e notas de transmissão textual."),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Coleções</p>
  <header class="hub-hero"><p class="eyebrow">Coleções</p><h1>Coleções</h1><p>Coleções podem guardar versículos, capítulos, artigos, mapas, lugares, manuscritos, planos, perguntas e discussões.</p></header>
  <section class="hub-section"><div class="study-card-grid">{cards}</div></section>
</main>"""
    out = SITE / "colecoes" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_notebooks_page():
    prefix = "../"
    title = f"Cadernos | {SITE_NAME}"
    desc = "Cadernos para organizar notas, perguntas, grifos, coleções, planos e referências."
    canonical = f"{BASE_URL}/cadernos/"
    cards = mini_cards([
        ("Caderno", "Caderno Romanos", "Notas, perguntas e referências para leitura verso a verso."),
        ("Caderno", "Caderno Casamento", "Planos, coleções e perguntas para estudo do tema."),
        ("Caderno", "Caderno Profecias", "Referências cruzadas, mapas e manuscritos."),
        ("Caderno", "Caderno Salmos", "Orações, grifos e coleções para meditação."),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Cadernos</p>
  <header class="hub-hero"><p class="eyebrow">Cadernos</p><h1>Cadernos</h1><p>Cada caderno reúne notas, perguntas, grifos, coleções, planos e referências.</p></header>
  <section class="hub-section"><div class="study-card-grid">{cards}</div></section>
</main>"""
    out = SITE / "cadernos" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_privacy_page():
    prefix = "../"
    title = f"Privacidade | {SITE_NAME}"
    desc = "Resumo de privacidade da conta, dados locais e sincronização."
    canonical = f"{BASE_URL}/privacidade/"
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Privacidade</p>
  <header class="hub-hero"><p class="eyebrow">Conta</p><h1>Privacidade</h1><p>Notas, favoritos e marcações ficam no navegador e só sincronizam quando a conta estiver configurada e conectada.</p></header>
  <section class="hub-section"><div class="study-card-grid">
    {mini_cards([
      ("Local", "Dados no navegador", "Anotações, grifos, favoritos e preferências usam localStorage."),
      ("Sincronização", "Supabase", "Quando habilitado, a conta sincroniza estado privado de estudo."),
      ("Conta", "Menu simples", "Perfil, configurações, sincronização, privacidade e sair."),
    ])}
  </div></section>
</main>"""
    out = SITE / "privacidade" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

# ---------- páginas ----------
def build_verse_page(v, articles_by_slug, prev_v=None, next_v=None):
    prefix = "../../"
    title = f"{v['referencia']} — original, tradução e contexto | {SITE_NAME}"
    desc = f"{v['referencia']} ({lang_label(v['idioma'])}): texto original, transliteração, tradução Almeida 1911 e {'comentário rabínico' if v.get('judaismo') else 'origem do texto'}."
    canonical = f"{BASE_URL}/versiculos/{v['slug']}/"
    jsonld = {
        "@context":"https://schema.org","@type":"Article",
        "headline":f"{v['referencia']} em contexto",
        "inLanguage":"pt-BR","isPartOf":{"@type":"WebSite","name":SITE_NAME,"url":BASE_URL},
        "about":v["referencia"],"keywords":", ".join(v.get("palavras",[]))
    }
    sc = script_class(v["idioma"], v.get("dir","ltr"))
    dir_attr = ' dir="rtl"' if v.get("dir")=="rtl" else ' dir="ltr"'
    ch, vs = ref_chvs(v["referencia"])

    # blocos: origem (se houver), comentário rabínico (Sefaria) e leitura curada
    blocks = ""
    if v.get("origem","").strip():
        blocks += f"""
  <section class="block" id="origem">
    <h2><span class="dot"></span>Origem e transmissão</h2>
    <p>{esc(v.get('origem',''))}</p>
  </section>"""
    if v.get("judaismo") and v.get("leitura_judaica"):
        blocks += f"""
  <section class="block jewish" id="leitura-judaica">
    <h2><span class="dot"></span>Leitura judaica e comentário rabínico</h2>
    <p>{esc(v['leitura_judaica'])}</p>
  </section>"""
    sef = sefaria_url(v["livro"], ch, vs)
    if sef:
        blocks += f"""
  <section class="block jewish" id="rabinico">
    <h2><span class="dot"></span>Comentário rabínico</h2>
    <p>Leia este versículo ao lado dos comentaristas judaicos clássicos — Rashi, Talmud, Midrash, Ibn Ezra — no acervo aberto do Sefaria.</p>
    <p><a class="ext-link" href="{sef}" target="_blank" rel="noopener">Abrir {esc(v['referencia'])} no Sefaria ↗</a></p>
  </section>"""

    # palavras
    kw = "".join(f'<span class="tag">{esc(p)}</span>' for p in v.get("palavras",[]))
    kw_html = f"""
  <section class="block">
    <h2><span class="dot"></span>Palavras-chave</h2>
    <div class="kw">{kw}</div>
  </section>""" if kw else ""

    # artigos relacionados
    rel = ""
    rels = [articles_by_slug[s] for s in v.get("artigos",[]) if s in articles_by_slug]
    if rels:
        items = "".join(
            f'<a class="result" href="{prefix}artigos/{a["slug"]}/"><span class="kind">Artigo</span><h4>{esc(a["titulo"])}</h4><p>{esc(a["resumo"])}</p></a>'
            for a in rels)
        rel = f"""
  <section class="block">
    <h2><span class="dot"></span>Para aprofundar</h2>
    <div class="related-list">{items}</div>
  </section>"""

    src_note = f"""
  <p class="src-note">Original: {esc(v.get('original_fonte',''))} · Tradução: {esc(v.get('texto_pt_fonte',''))}</p>"""

    # navegação "folhear" (anterior / próximo em ordem bíblica)
    prev_html = (f'<a class="pg prev" href="../{prev_v["slug"]}/"><span>← Anterior</span>'
                 f'<b>{esc(prev_v["referencia"])}</b></a>') if prev_v else '<span class="pg empty"></span>'
    next_html = (f'<a class="pg next" href="../{next_v["slug"]}/"><span>Próximo →</span>'
                 f'<b>{esc(next_v["referencia"])}</b></a>') if next_v else '<span class="pg empty"></span>'
    pager = f"""
  <nav class="pager" aria-label="Folhear versículos">{prev_html}{next_html}</nav>"""

    next_url = f"../{next_v['slug']}/" if next_v else ""
    if v.get("texto_pt","").strip():
        pt_html = f'<p class="pt">{esc(v["texto_pt"])}</p>'
    else:
        pt_html = ('<p class="pt pt-missing">Tradução em português deste trecho em revisão '
                   '(diferença de numeração entre o hebraico e a edição Almeida 1911).</p>')

    body = f"""
<main id="main" class="wrap verse-page" data-next="{next_url}">
  <article class="verse-cont" data-slug="{esc(v['slug'])}" data-ref="{esc(v['referencia'])}" data-title="{esc(title)}">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="{prefix}index.html#versiculos">Versículos</a> · {esc(v['referencia'])}</p>
  <header class="verse-head">
    <span class="lang-tag lang-{esc(v['idioma'])}">{lang_label(v['idioma'])}</span>
    <h1>{esc(v['referencia'])}</h1>
  </header>

  <div class="verse-hero reveal">
    <p class="orig {sc}"{dir_attr}>{esc(v['original'])}</p>
    <p class="translit">{esc(v['transliteracao'])}</p>
    {pt_html}
    {verse_tools(v, prefix)}
    <p class="src-line">{esc(v.get('contexto',''))}</p>
  </div>

  {specimen_block(v)}
  {blocks}
  {kw_html}
  {rel}
  {study_map_module(prefix, v['livro'], ch, vs)}
  {src_note}
  {pager}
  </article>
  <div class="vs-sentinel" aria-hidden="true"></div>
  <p class="vs-loading" aria-live="polite"></p>
  <p class="backline"><a href="{prefix}index.html#versiculos">← Todos os versículos</a></p>
</main>"""
    out = SITE / "versiculos" / v["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix, jsonld) + nav(prefix) + body + footer(prefix))

def build_article_page(a):
    prefix = "../../"
    title = f"{a['titulo']} | {SITE_NAME}"
    desc = a.get("resumo","")
    canonical = f"{BASE_URL}/artigos/{a['slug']}/"
    jsonld = {"@context":"https://schema.org","@type":"Article","headline":a["titulo"],
              "inLanguage":"pt-BR","isPartOf":{"@type":"WebSite","name":SITE_NAME,"url":BASE_URL}}
    secs = "".join(f"<h2>{esc(s['h'])}</h2><p>{esc(s['p'])}</p>" for s in a.get("conteudo",[]))
    notice = f'<div class="notice">{esc(a.get("fonte_status",""))}</div>' if a.get("fonte_status") else ""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="{prefix}index.html#artigos">Artigos</a> · {esc(a['titulo'])}</p>
  <header class="verse-head">
    <span class="lang-tag lang-hebraico">Artigo</span>
    <h1>{esc(a['titulo'])}</h1>
  </header>
  <article class="article-body">
    <p style="font-size:1.12rem;color:var(--ink-soft)">{esc(a.get('resumo',''))}</p>
    {secs}
    {notice}
  </article>
  <p class="backline"><a href="{prefix}index.html#artigos">← Todos os artigos</a></p>
</main>"""
    out = SITE / "artigos" / a["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix, jsonld) + nav(prefix) + body + footer(prefix))

# ---------- navegação livro → capítulo → versículo ----------
def build_books_index(order, struct):
    prefix = "../"
    title = f"Livros da Bíblia | {SITE_NAME}"
    desc = "Navegue pela Bíblia livro a livro: escolha um livro e leia capítulo por capítulo no idioma original, com tradução e transliteração."
    canonical = f"{BASE_URL}/ler/"
    cards = ""
    for livro in order:
        n_caps = len(struct[livro])
        idioma = struct[livro][min(struct[livro])][0].get("idioma","hebraico")
        cards += f"""
    <a class="card book-card" href="{book_slug(livro)}/"{book_data_attrs(livro)}>
      <div class="ref-row"><h3>{esc(livro)}</h3><span class="lang-tag lang-{esc(idioma)}">{lang_label(idioma)}</span></div>
      <p class="pt-mini">{n_caps} capítulo{'s' if n_caps!=1 else ''}</p>
    </a>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Livros</p>
  <header class="verse-head"><h1>Livros da Bíblia</h1></header>
  <p class="read" style="color:var(--muted)">Escolha um livro para ler capítulo a capítulo. Cada versículo abre a página completa com manuscrito e contexto.</p>
  {order_toggle(prefix)}
  <div class="cards verses" data-booklist>{cards}
  </div>
</main>"""
    out = SITE / "ler" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

def build_timeline_page(order, struct):
    prefix = "../"
    title = f"Linha do tempo da Bíblia | {SITE_NAME}"
    desc = "A Bíblia em ordem histórica: os livros agrupados por períodos, de Gênesis ao Apocalipse (datas aproximadas)."
    canonical = f"{BASE_URL}/linha-do-tempo/"
    present = set(order)
    eras_html = ""
    for era in TIMELINE:
        livros = [b for b in era["livros"] if b in present]
        cards = ""
        for b in livros:
            idioma = struct[b][min(struct[b])][0].get("idioma","hebraico")
            cards += f"""
      <a class="card book-card" href="{prefix}ler/{book_slug(b)}/">
        <div class="ref-row"><h3>{esc(b)}</h3><span class="lang-tag lang-{esc(idioma)}">{lang_label(idioma)}</span></div>
      </a>"""
        grade = f'<div class="cards verses">{cards}\n    </div>' if livros else '<p class="era-gap-note">Cerca de 400 anos sem registro no cânon protestante.</p>'
        eras_html += f"""
  <section class="era">
    <div class="era-head"><h2>{esc(era['nome'])}</h2><span class="era-period">{esc(era['periodo'])}</span></div>
    <p class="era-desc">{esc(era['descricao'])}</p>
    {grade}
  </section>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Linha do tempo</p>
  <header class="verse-head"><h1>Linha do tempo da Bíblia</h1></header>
  <p class="read" style="color:var(--muted)">Os livros na ordem histórica dos acontecimentos, de Gênesis ao Apocalipse. <b>Datas aproximadas</b> — as estimativas variam entre estudiosos.</p>
  {eras_html}
  <p class="backline"><a href="{prefix}ler/">← Todos os livros</a></p>
</main>"""
    out = SITE / "linha-do-tempo" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

def book_jump(prefix, order, current):
    # seletor "Ir para livro" (Antigo/Novo Testamento) para pular entre livros sem voltar ao menu
    at, nt = [], []
    for b in order:
        idx = BOOK_ORDER.index(b) if b in BOOK_ORDER else 999
        (at if idx < 39 else nt).append(b)
    def opts(books):
        return "".join(
            f'<option value="{prefix}ler/{book_slug(b)}/"{" selected" if b==current else ""}>{esc(b)}</option>'
            for b in books)
    return f"""
  <div class="book-jump-wrap">
    <label class="book-jump-lbl" for="book-jump">📖 Ir para livro:</label>
    <select class="book-jump" id="book-jump" aria-label="Ir para outro livro da Bíblia">
      <optgroup label="Antigo Testamento">{opts(at)}</optgroup>
      <optgroup label="Novo Testamento">{opts(nt)}</optgroup>
    </select>
  </div>"""

def build_book_page(livro, chapters, order):
    prefix = "../../"
    title = f"{livro} — capítulos | {SITE_NAME}"
    desc = f"Leia {livro} capítulo por capítulo: texto no idioma original, transliteração e tradução Almeida 1911."
    canonical = f"{BASE_URL}/ler/{book_slug(livro)}/"
    chips = "".join(
        f'<a class="chip chapter-chip" href="{ch}/">{ch}</a>' for ch in sorted(chapters))
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="../">Livros</a> · {esc(livro)}</p>
  <header class="verse-head"><h1>{esc(livro)}</h1></header>
  {book_jump(prefix, order, livro)}
  <p class="read" style="color:var(--muted)">Escolha um capítulo:</p>
  <div class="chips chapter-grid">{chips}
  </div>
  {study_map_module(prefix, livro)}
  {study_desk_module(prefix, livro)}
</main>"""
    out = SITE / "ler" / book_slug(livro) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

def build_chapter_page(livro, ch, verses, n_chapters, order):
    prefix = "../../../"
    bslug = book_slug(livro)
    title = f"{livro} {ch} — original, transliteração e tradução | {SITE_NAME}"
    desc = f"{livro} {ch}: capítulo completo no idioma original, com transliteração e tradução Almeida 1911."
    canonical = f"{BASE_URL}/ler/{bslug}/{ch}/"
    idioma = verses[0].get("idioma","hebraico") if verses else "hebraico"
    sc = script_class(idioma, verses[0].get("dir","ltr") if verses else "ltr")
    rows = ""
    for v in verses:
        _, vs = ref_chvs(v["referencia"])
        dir_attr = ' dir="rtl"' if v.get("dir")=="rtl" else ' dir="ltr"'
        pt = esc(v.get("texto_pt","")) or '<span class="pt-missing">—</span>'
        rows += f"""
    <div class="ch-verse" id="v{vs}" data-ref="{esc(v['referencia'])}">
      <a class="ch-num" href="{prefix}versiculos/{esc(v['slug'])}/" aria-label="Versículo {vs}">{vs}</a>
      <div class="ch-body">
        <p class="orig {sc}"{dir_attr}>{esc(v.get('original',''))}</p>
        <p class="translit">{esc(v.get('transliteracao',''))}</p>
        <p class="pt">{pt}</p>
        {verse_tools(v, prefix)}
      </div>
    </div>"""
    prev_html = (f'<a class="pg prev" href="../{ch-1}/"><span>← Capítulo</span><b>{livro} {ch-1}</b></a>'
                 if ch > 1 else '<span class="pg empty"></span>')
    next_html = (f'<a class="pg next" href="../{ch+1}/"><span>Capítulo →</span><b>{livro} {ch+1}</b></a>'
                 if ch < n_chapters else '<span class="pg empty"></span>')
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="{prefix}ler/">Livros</a> · <a href="../">{esc(livro)}</a> · {ch}</p>
  <header class="verse-head">
    <span class="lang-tag lang-{esc(idioma)}">{lang_label(idioma)}</span>
    <h1>{esc(livro)} {ch}</h1>
  </header>
  {book_jump(prefix, order, livro)}
  <div class="chapter">{rows}
  </div>
  {study_map_module(prefix, livro, ch)}
  {study_desk_module(prefix, livro, ch)}
  <nav class="pager" aria-label="Folhear capítulos">{prev_html}{next_html}</nav>
  <p class="backline"><a href="../">← Todos os capítulos de {esc(livro)}</a></p>
</main>"""
    out = SITE / "ler" / bslug / str(ch) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

def build_search_index(verses, articles, topics):
    """Índice de busca em arquivo externo (carregado sob demanda pela home),
    em vez de embutido no index.html — reduz a página de ~20 MB para poucos KB."""
    index = []
    for v in verses:
        index.append({"t":"Versículo","titulo":v["referencia"],"desc":v.get("texto_pt",""),
                      "url":f"versiculos/{v['slug']}/",
                      "k":(v["referencia"]+" "+v.get("texto_pt","")+" "+v.get("contexto","")+" "+" ".join(v.get("palavras",[]))).lower()})
    for a in articles:
        index.append({"t":"Artigo","titulo":a["titulo"],"desc":a.get("resumo",""),
                      "url":f"artigos/{a['slug']}/","k":(a["titulo"]+" "+a.get("resumo","")+" "+a.get("versiculo","")).lower()})
    for t in topics:
        index.append({"t":"Tema","titulo":t["titulo"],"desc":t.get("descricao",""),
                      "url":"#versiculos","k":(t["titulo"]+" "+t.get("descricao","")).lower()})
    write_file(DATA / "search-index.json", json.dumps(index, ensure_ascii=False))
    return len(index)

def build_home(topics, verses, articles, sources, order, struct):
    prefix = ""
    title = f"{SITE_NAME} — a Bíblia com os idiomas originais, manuscritos e fontes"
    desc = "Leia cada versículo no idioma original (hebraico, grego, aramaico), com tradução de domínio público, foto do manuscrito quando há, e comentário rabínico ou explicação de origem."
    canonical = BASE_URL + "/"

    featured = next(v for v in verses if v["slug"]=="genesis-1-1")
    fsc = script_class(featured["idioma"], featured.get("dir","ltr"))

    # temas
    chips = "".join(
        f'<a class="chip" href="#versiculos"><span class="gl">{esc(t["icone"])}</span>{esc(t["titulo"])}</a>'
        for t in topics)

    # navegação por livro (substitui o despejo de 23k cartões na home)
    bcards = ""
    for livro in order:
        n_caps = len(struct[livro])
        idioma = struct[livro][min(struct[livro])][0].get("idioma","hebraico")
        bcards += f"""
    <a class="card book-card" href="ler/{book_slug(livro)}/"{book_data_attrs(livro)}>
      <div class="ref-row"><h3>{esc(livro)}</h3><span class="lang-tag lang-{esc(idioma)}">{lang_label(idioma)}</span></div>
      <p class="pt-mini">{n_caps} capítulo{'s' if n_caps!=1 else ''}</p>
    </a>"""

    # artigos
    acards = ""
    for a in articles:
        acards += f"""
    <a class="card article-card" href="artigos/{a['slug']}/">
      <div class="meta"><span>{esc(a.get('tempo',''))}</span> · <span>{esc(a.get('nivel',''))}</span> · <span>{esc(a.get('versiculo',''))}</span></div>
      <h3>{esc(a['titulo'])}</h3>
      <p class="pt-mini">{esc(a['resumo'])}</p>
      <span class="more">Ler estudo →</span>
    </a>"""

    # fontes
    scards = ""
    for s in sources:
        scards += f"""
    <div class="src">
      <h3>{esc(s['nome'])}</h3>
      <p><b>Licença:</b> {esc(s['licenca'])}</p>
      <span class="status">{esc(s['status'])}</span><br>
      <a href="{esc(s['url'])}" target="_blank" rel="noopener">Abrir fonte oficial ↗</a>
    </div>"""

    body = f"""
<header class="hero" id="topo">
  <div class="hero-in">
    <div>
      <p class="eyebrow on-dark">Idiomas originais · manuscritos · fontes rastreáveis</p>
      <h1>Leia o versículo na língua em que foi escrito.</h1>
      <p class="lead">Para cada texto: o original em hebraico, grego ou aramaico, uma tradução de domínio público, a foto do manuscrito quando existe e o comentário rabínico ou a explicação da origem. Sem poluição, feito para ler no celular.</p>
      <div class="hero-cta">
        <a class="btn primary" href="#versiculos">Explorar versículos</a>
        <a class="btn ghost" href="#fontes">Ver fontes e licenças</a>
      </div>
    </div>
    <div class="specimen-card reveal">
      <div class="ref-row"><span>{esc(featured['referencia'])}</span><span class="lang-tag lang-{esc(featured['idioma'])}">{lang_label(featured['idioma'])}</span></div>
      <div class="verse-stack">
        <p class="orig {fsc}" dir="rtl">{esc(featured['original'])}</p>
        <p class="translit">{esc(featured['transliteracao'])}</p>
        <p class="pt">{esc(featured['texto_pt'])}</p>
        <p class="pt-src">{esc(featured['texto_pt_fonte'])}</p>
      </div>
    </div>
  </div>
</header>

<main id="main">
  <section class="search-section">
    <div class="searchbox">
      <span class="ico">⌕</span>
      <input id="q" type="search" placeholder="Buscar: Salmo 23, shalom, aramaico, logos…" autocomplete="off" aria-label="Buscar">
    </div>
    <div id="results" class="search-results"></div>
    <div class="home-panel wrap">
      <article class="home-block continue-block">
        <span>Leitura</span>
        <h3>Continuar leitura</h3>
        <a id="continue-read" class="continue-read" href="#" hidden></a>
        <p class="fallback-read">Abra um capítulo para o Workspace lembrar onde você parou.</p>
      </article>
      <article class="home-block">
        <span>Hoje</span>
        <h3>Plano de hoje</h3>
        <p>Romanos 1 · leitura leve com notas e grifos.</p>
        <a href="estudar/#criar-plano">Criar plano</a>
      </article>
      <article class="home-block">
        <span>Caderno</span>
        <h3>Últimas anotações</h3>
        <p>Revise suas notas locais e exporte quando precisar.</p>
        <a href="anotacoes/">Abrir anotações</a>
      </article>
      <article class="home-block" id="favorite-home" hidden>
        <span>Biblioteca</span>
        <h3>Favoritos recentes</h3>
        <div id="favorite-list" class="favorite-list"></div>
      </article>
      <article class="home-block">
        <span>Descobrir</span>
        <h3>Explorar um trecho</h3>
        <p>Receba um versículo e abra o contexto completo.</p>
        <button type="button" id="random-verse" class="inline-action">Um versículo para você</button>
      </article>
      <article class="home-block">
        <span>Salas</span>
        <h3>Relacionadas ao estudo</h3>
        <p>Sala Evangelho de João, Romanos verso a verso e Salmos para oração.</p>
        <a href="comunidade/salas/">Ver Salas de Estudo</a>
      </article>
    </div>
  </section>

  <section id="versiculos">
    <div class="sec-head">
      <p class="eyebrow">Leia a Bíblia inteira</p>
      <h2>Livros</h2>
      <p>Escolha um livro e leia capítulo por capítulo no idioma original. Cada versículo abre a página completa com manuscrito e contexto.</p>
    </div>
    {order_toggle("")}
    <div class="cards verses wrap" data-booklist>{bcards}
    </div>
  </section>

  <section id="temas" style="background:var(--vellum-2)">
    <div class="sec-head">
      <p class="eyebrow">Por onde começar</p>
      <h2>Temas de estudo</h2>
      <p>Pontos de entrada para quem busca um assunto, não uma referência exata.</p>
    </div>
    <div class="chips wrap">{chips}
    </div>
  </section>

  <section id="artigos">
    <div class="sec-head">
      <p class="eyebrow">Leitura mais longa</p>
      <h2>Artigos contextuais</h2>
      <p>Estudos originais sobre palavras, traduções e história do texto.</p>
    </div>
    <div class="cards articles wrap">{acards}
    </div>
  </section>

  <section id="fontes" class="sources">
    <div class="sec-head">
      <p class="eyebrow on-dark">Transparência</p>
      <h2>Fontes e licenças</h2>
      <p>O site só publica texto e imagem com origem e licença claras. Abaixo, o que usamos e em que condições.</p>
    </div>
    <div class="src-list wrap">{scards}
    </div>
  </section>

  <section id="metodologia" style="background:var(--vellum-2)">
    <div class="sec-head">
      <p class="eyebrow">Metodologia</p>
      <h2>Como tratamos o texto</h2>
    </div>
    <div class="read">
      <p>O texto bíblico em português é a <b>Almeida Revista e Corrigida de 1911</b>, a edição mais recente de Almeida em domínio público no Brasil. O hebraico e o aramaico vêm do <b>Westminster Leningrad Codex</b> (Open Scriptures Hebrew Bible); o grego, da edição <b>Nestle 1904</b> — todos de uso livre.</p>
      <p>Os comentários rabínicos são <b>resumos originais</b>, escritos por nós e citando as fontes pelo nome (Rashi, Talmud, Midrash, Ibn Ezra, Targum). Não reproduzimos traduções modernas protegidas. Imagens de manuscrito só aparecem quando há um arquivo em domínio público, sempre com crédito.</p>
    </div>
  </section>
</main>"""

    out = SITE / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

def build_app_js():
    write_asset("app.asset.js", "app.js")

def build_auth_js():
    write_asset("auth.asset.js", "auth.js")

def build_study_js():
    js = read_asset("study.asset.js")
    write_file(SITE / "assets" / "study.js", f"var BEC_BASE={json.dumps(BASE_URL)};\n" + js)

def build_game_js():
    write_asset("gamification.asset.js", "game.js")

def build_annotations_page():
    prefix = "../"
    title = f"Minhas anotações | {SITE_NAME}"
    desc = "Suas marcações e anotações de estudo, salvas neste navegador. Copie ou baixe para uso externo."
    canonical = f"{BASE_URL}/anotacoes/"
    body = """
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="../index.html">Início</a> · Anotações</p>
  <header class="verse-head"><h1>Minhas anotações</h1></header>
  <p class="read" style="color:var(--muted)">Suas marcações e notas ficam salvas <b>neste navegador</b> (offline, sem servidor). Use os botões para copiar ou baixar tudo para uso externo.</p>
  <div class="anot-actions">
    <button type="button" id="anot-copy" class="btn primary">Copiar tudo</button>
    <button type="button" id="anot-share" class="btn ghost">Compartilhar</button>
    <button type="button" id="anot-txt" class="btn ghost">Baixar .txt</button>
    <button type="button" id="anot-json" class="btn ghost">Backup .json (outro aparelho)</button>
    <button type="button" id="anot-import" class="btn ghost">Importar backup</button>
    <input type="file" id="anot-import-file" accept="application/json,.json" hidden>
    <button type="button" id="anot-clear" class="btn ghost">Limpar</button>
  </div>
  <div id="anotacoes" class="anot-list"></div>
</main>"""
    out = SITE / "anotacoes" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

def build_meta(verses, articles, order, struct):
    # sitemap
    urls = [
        BASE_URL + "/",
        f"{BASE_URL}/ler/",
        f"{BASE_URL}/estudar/",
        f"{BASE_URL}/workspace/",
        f"{BASE_URL}/comunidade/",
        f"{BASE_URL}/comunidade/salas/",
        f"{BASE_URL}/biblioteca/",
        f"{BASE_URL}/colecoes/",
        f"{BASE_URL}/cadernos/",
        f"{BASE_URL}/privacidade/",
        f"{BASE_URL}/linha-do-tempo/",
    ]
    urls += [f"{BASE_URL}/ler/{book_slug(livro)}/" for livro in order]
    urls += [f"{BASE_URL}/ler/{book_slug(livro)}/{ch}/" for livro in order for ch in sorted(struct[livro])]
    urls += [f"{BASE_URL}/versiculos/{v['slug']}/" for v in verses]
    urls += [f"{BASE_URL}/artigos/{a['slug']}/" for a in articles]
    items = "".join(f"<url><loc>{u}</loc><changefreq>monthly</changefreq></url>\n" for u in urls)
    write_file(
        SITE / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+items+'</urlset>\n',
    )
    # robots: libera buscadores normais; pede que crawlers de IA/scrapers não copiem (advisory)
    ai_bots = ["GPTBot","ChatGPT-User","OAI-SearchBot","ClaudeBot","anthropic-ai","Claude-Web",
               "CCBot","Google-Extended","Applebot-Extended","PerplexityBot","Bytespider","Amazonbot",
               "Diffbot","Omgilibot","ImagesiftBot","cohere-ai","FacebookBot","Meta-ExternalAgent"]
    ai_block = "".join(f"\nUser-agent: {b}\nDisallow: /\n" for b in ai_bots)
    write_file(SITE / "robots.txt", f"User-agent: *\nAllow: /\n{ai_block}\nSitemap: {BASE_URL}/sitemap.xml\n")
    write_file(SITE / "manifest.webmanifest", json.dumps({
        "name":SITE_NAME,"short_name":"Bíblia em Contexto","lang":"pt-BR",
        "start_url":"./","display":"standalone","background_color":"#f4eee2","theme_color":"#1a1610",
        "description":"A Bíblia com os idiomas originais, manuscritos e fontes."
    }, ensure_ascii=False, indent=2))

def build_404():
    prefix = ""
    body = """
<main id="main" class="wrap verse-page" style="text-align:center">
  <header class="verse-head" style="margin-top:30px">
    <span class="lang-tag lang-hebraico">404</span>
    <h1>Página não encontrada</h1>
  </header>
  <p class="read" style="color:var(--muted)">O versículo ou a página que você procura não está aqui. Talvez tenha mudado de lugar.</p>
  <p class="backline" style="text-align:center"><a href="index.html">← Voltar ao início</a></p>
</main>"""
    out = SITE / "404.html"
    write_file(out, head("Página não encontrada | "+SITE_NAME, "Página não encontrada.", BASE_URL+"/404.html", prefix)
                   + nav(prefix) + body + footer(prefix))

def build_random_pool(verses):
    # pool de slugs para "Versículo para meditar" (aleatório no cliente).
    # amostra distribuída (determinística) de versículos COM tradução PT, evitando
    # trechos áridos e mantendo o arquivo leve. Carregado sob demanda na home.
    slugs = [v["slug"] for v in verses if v.get("texto_pt","").strip()]
    alvo = 1500
    if len(slugs) > alvo:
        passo = len(slugs) // alvo
        slugs = slugs[::passo][:alvo]
    write_file(DATA / "random.json", json.dumps(slugs, ensure_ascii=False))
    return len(slugs)

@dataclass
class BuildInputs:
    topics: list
    verses: list
    articles: list
    sources: list


@dataclass
class BuildContext:
    inputs: BuildInputs
    verses: list
    order: list
    struct: dict
    articles_by_slug: dict


@dataclass
class BuildSummary:
    verses: int
    books: int
    chapters: int
    articles: int
    search_index: int

    def message(self):
        return (
            f"OK: home + {self.verses} versículos + {self.books} livros + "
            f"{self.chapters} capítulos + {self.articles} artigos + "
            f"índice de busca ({self.search_index}) + sitemap + 404"
        )


def load_build_inputs():
    return BuildInputs(
        topics=load("topics.json"),
        verses=load("verses.json"),
        articles=load("articles.json"),
        sources=load("sources.json"),
    )


def prepare_build_context(inputs):
    verses = sorted(inputs.verses, key=verse_sort_key)
    order, struct = group_by_book_chapter(verses)
    return BuildContext(
        inputs=inputs,
        verses=verses,
        order=order,
        struct=struct,
        articles_by_slug={a["slug"]: a for a in inputs.articles},
    )


def clean_generated_output():
    for dirname in GENERATED_DIRS:
        shutil.rmtree(SITE / dirname, ignore_errors=True)


def build_site(context):
    inputs = context.inputs
    verses = context.verses
    order = context.order
    struct = context.struct

    clean_generated_output()
    build_home(inputs.topics, verses, inputs.articles, inputs.sources, order, struct)
    build_auth_js()
    build_app_js()
    build_study_js()
    build_game_js()
    build_annotations_page()
    build_study_page()
    build_workspace_page()
    build_community_page()
    build_study_rooms_page()
    build_library_page()
    build_collections_page()
    build_notebooks_page()
    build_privacy_page()
    n_idx = build_search_index(verses, inputs.articles, inputs.topics)
    build_random_pool(verses)

    n = len(verses)
    for i, v in enumerate(verses):
        prev_v = verses[i - 1] if i > 0 else None
        next_v = verses[i + 1] if i < n - 1 else None
        build_verse_page(v, context.articles_by_slug, prev_v, next_v)
    for article in inputs.articles:
        build_article_page(article)

    build_books_index(order, struct)
    build_timeline_page(order, struct)
    n_chapters = 0
    for livro in order:
        chapters = struct[livro]
        build_book_page(livro, chapters, order)
        total_caps = max(chapters)
        for ch in sorted(chapters):
            build_chapter_page(livro, ch, chapters[ch], total_caps, order)
            n_chapters += 1

    build_meta(verses, inputs.articles, order, struct)
    build_404()
    return BuildSummary(
        verses=len(verses),
        books=len(order),
        chapters=n_chapters,
        articles=len(inputs.articles),
        search_index=n_idx,
    )


def main():
    summary = build_site(prepare_build_context(load_build_inputs()))
    print(summary.message())

if __name__=="__main__":
    main()
