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
import json, re, shutil, sys, unicodedata, hashlib
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
    "core.asset.js": "core.js",
    "auth.asset.js": "auth.js",
    "app.asset.js": "app.js",
    "study.asset.js": "study.js",
    "lexicon.asset.js": "lexicon.js",
    "gamification.asset.js": "game.js",
    "community.asset.js": "community.js",
    "library.asset.js": "library.js",
    "report.asset.js": "report.js",
}


def asset_ver():
    # Cache-busting: muda quando o gerador, os assets-fonte ou o CSS mudam.
    h = hashlib.sha1()
    for path in [
        Path(__file__),
        SCRIPTS_DIR / "build_config.py",
        SCRIPTS_DIR / "build_utils.py",
        SCRIPTS_DIR / "sw.asset.js",
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
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index, follow, noai, noimageai">
<link rel="canonical" href="{esc(canonical)}">
<meta name="theme-color" content="#efe4d0">
<link rel="icon" href="{prefix}assets/icons/icon.svg" type="image/svg+xml">
<link rel="icon" href="{prefix}assets/icons/icon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{prefix}assets/icons/icon-180.png">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:url" content="{esc(canonical)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<link rel="manifest" href="{prefix}manifest.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Spectral:wght@400;500;600&family=Inter:wght@400;600;700&family=Frank+Ruhl+Libre:wght@400;500;700&family=Gentium+Book+Plus:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/styles.css?v={ASSET_VER}">{ld}
</head>
<body data-prefix="{esc(prefix)}">
<script>(function(){{try{{var d=document.documentElement;var t=localStorage.getItem('bec.theme');if(t==='dark')d.classList.add('dark');else if(t==='sepia')d.classList.add('sepia');else if(!t&&window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches){{d.classList.add('dark');t='dark';}}var f=localStorage.getItem('bec.fontscale');if(f)d.classList.add('fs-'+f);if(localStorage.getItem('bec.origmode')==='1')d.classList.add('orig-on');var tc=document.querySelector('meta[name="theme-color"]');if(tc)tc.setAttribute('content',t==='dark'?'#07111f':(t==='sepia'?'#d6c09b':'#efe4d0'));}}catch(e){{}}}})();</script>
<a class="skip" href="#main">Pular para o conteúdo</a>
<div class="beta-banner" data-beta-banner hidden role="status">
  <span class="beta-tag">Beta</span>
  <span class="beta-text">Você está numa versão de testes. Seu estudo é salvo e sincronizado neste navegador.</span>
  <button type="button" class="beta-dismiss" data-beta-dismiss aria-label="Ocultar aviso beta">×</button>
</div>"""

# Ícones de linha (24x24, currentColor) usados na barra inferior tipo app e
# em outros pontos estruturais da navegação — nada de emoji nesses lugares
# para ficar consistente entre sistemas/fontes.
MNAV_ICONS = {
    "home": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v9.5h5V14h3v5.5h5V10"/>',
    "book": ('<path d="M4 6c2.2-1.1 5.4-1.1 8 1c2.6-2.1 5.8-2.1 8-1v13c-2.2-1.1-5.4-1.1-8 1'
              'c-2.6-2.1-5.8-2.1-8-1z"/><path d="M12 7v13"/>'),
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.6-4.6"/>',
    "grid": ('<rect x="3.5" y="3.5" width="7.5" height="7.5" rx="2"/>'
             '<rect x="13" y="3.5" width="7.5" height="7.5" rx="2"/>'
             '<rect x="3.5" y="13" width="7.5" height="7.5" rx="2"/>'
             '<rect x="13" y="13" width="7.5" height="7.5" rx="2"/>'),
}


def mnav_icon(name):
    return f'<svg class="mnav-ic" viewBox="0 0 24 24" aria-hidden="true">{MNAV_ICONS[name]}</svg>'


def nav(prefix):
    # Navegação enxuta: Estudar e Comunidade viveram como páginas próprias e
    # foram fundidos no Workspace (seções #estudar e #comunidade); os endereços
    # antigos redirecionam para lá.
    links = [
        ("Início", f"{prefix}index.html"),
        ("Bíblia", f"{prefix}ler/"),
        ("Workspace", f"{prefix}workspace/"),
    ]
    nav_links = "\n      ".join(f'<a href="{url}">{label}</a>' for label, url in links)
    # a barra inferior (mobile) ganha um 4º item, "Buscar" — é uma ferramenta
    # (abre o overlay já existente), não uma área de navegação nova; as áreas
    # continuam sendo só Início/Bíblia/Workspace.
    mobile_items = [
        ("home", "Início", f"{prefix}index.html", "a"),
        ("book", "Bíblia", f"{prefix}ler/", "a"),
        ("search", "Buscar", None, "button"),
        ("grid", "Workspace", f"{prefix}workspace/", "a"),
    ]
    mobile_links = "\n  ".join(
        (f'<a href="{href}">{mnav_icon(icon)}<span>{label}</span></a>' if tag == "a"
         else f'<button type="button" data-search-open>{mnav_icon(icon)}<span>{label}</span></button>')
        for icon, label, href, tag in mobile_items
    )
    return f"""
<nav class="nav">
  <div class="nav-in">
    <a class="brand" href="{prefix}index.html">
      <span class="brand-mark">ב</span>
      <span class="brand-name">Bíblia em Contexto</span>
    </a>
    <div class="reader-tools">
      <button type="button" class="rt" data-search-open aria-label="Buscar na Bíblia" title="Buscar">🔍</button>
      <button type="button" class="rt" data-rt="font-dec" aria-label="Diminuir fonte">A−</button>
      <button type="button" class="rt" data-rt="font-inc" aria-label="Aumentar fonte">A+</button>
      <button type="button" class="rt" data-rt="orig" aria-pressed="false" aria-label="Mostrar idioma original e transliteração" title="Idioma original">א/A</button>
      <button type="button" class="rt" data-rt="theme" aria-label="Tema: claro, sépia ou escuro" title="Tema (claro/sépia/escuro)">🌙</button>
      <button type="button" class="rt" data-report-open aria-label="Reportar um problema" title="Reportar um problema">🐞</button>
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
</nav>
<div class="search-overlay" data-search-overlay hidden>
  <div class="search-overlay-in">
    <div class="search-overlay-head">
      <input type="search" data-search-input placeholder="Buscar versículo, palavra, tema… (ex: livro:joão, ‘vida eterna’)" aria-label="Buscar na Bíblia">
      <button type="button" class="btn ghost" data-search-close aria-label="Fechar busca">Fechar</button>
    </div>
    <div class="search-overlay-results" data-search-results></div>
  </div>
</div>"""

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
        <a href="{prefix}workspace/#estudar">Estudar</a>
        <a href="{prefix}planos/">Planos</a>
        <a href="{prefix}workspace/">Workspace</a>
      </div>
      <div>
        <a href="{prefix}workspace/#comunidade">Comunidade</a>
        <a href="{prefix}biblioteca/">Biblioteca</a>
        <a href="{prefix}index.html#fontes">Fontes e licenças</a>
      </div>
      <div>
        <a href="{prefix}dicionario/">Dicionário</a>
        <a href="{prefix}mapas/">Mapas</a>
        <a href="{prefix}linha-do-tempo/">Linha do tempo</a>
        <a href="{prefix}index.html#artigos">Artigos</a>
      </div>
    </div>
  </div>
</footer>
<script src="{prefix}assets/core.js?v={ASSET_VER}"></script>
<script src="{prefix}assets/supabase-config.js?v={ASSET_VER}" defer></script>
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js" defer></script>
<script src="{prefix}assets/auth.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/app.js?v={ASSET_VER}"></script>
<script src="{prefix}assets/study.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/lexicon.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/game.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/community.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/library.js?v={ASSET_VER}" defer></script>
<script src="{prefix}assets/report.js?v={ASSET_VER}" defer></script>
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
    out = []
    for item in items:
        label, title, text, url = item[:4]
        extra = item[4] if len(item) > 4 else ""
        out.append(f"""
    <a class="study-card link-card" href="{esc(url)}"{extra}>
      <span>{esc(label)}</span>
      <h3>{esc(title)}</h3>
      <p>{esc(text)}</p>
    </a>""")
    return "".join(out)


def study_continue_module(prefix, livro, ch=None, vs=None):
    """Bloco único e compacto de continuidade: atalhos pessoais + Salas de
    Estudo relacionadas. Substitui os antigos módulos "Estude em comunidade"
    e "Mesa de Estudo", que duplicavam links entre si."""
    place = f"{livro} {ch}:{vs}" if vs else (f"{livro} {ch}" if ch else livro)
    return f"""
  <section class="study-continue">
    <div class="study-continue-head">
      <p class="eyebrow">Continue estudando</p>
      <h2>{esc(place)}</h2>
    </div>
    <div class="desk-tabs" aria-label="Continuar o estudo">
      <a href="{prefix}anotacoes/">🗒 Minhas notas</a>
      <a href="{prefix}colecoes/">🗂 Coleções</a>
      <a href="{prefix}planos/">🗓 Planos</a>
      <a href="{prefix}dicionario/">📖 Dicionário</a>
    </div>
    <div class="room-suggest" data-room-suggest data-room-ref="{esc(place)}" hidden>
      <p class="eyebrow">Salas abertas estudando este livro</p>
      <div class="room-suggest-list" data-room-suggest-list></div>
      <a class="room-suggest-more" href="{prefix}workspace/#comunidade">Pedir para entrar na Comunidade →</a>
    </div>
    <p class="map-actions"><a class="btn quiet" href="{prefix}workspace/#comunidade">Ver Salas de Estudo →</a></p>
  </section>"""


def study_fraction_module(prefix, livro, ch, vnums):
    """Progresso por trecho: marcar do versiculo X ao Y sem exigir o capitulo
    inteiro. Persistido em bec.readingRanges e sincronizado como preferencia.
    Recolhido por padrão (details/summary) para não competir com o texto."""
    if not vnums:
        return ""
    ref = f"{livro} {ch}"
    opts = "".join(f'<option value="{n}">{n}</option>' for n in vnums)
    return f"""
  <details class="collap study-frac" data-study-frac data-chapter-ref="{esc(ref)}" data-total="{len(vnums)}">
    <summary>
      <span class="collap-title">Progresso por trecho</span>
      <span class="collap-count" data-sf-pct>0%</span>
      <span class="collap-chev" aria-hidden="true">▾</span>
    </summary>
    <div class="sf-body">
      <p class="sf-hint">Salve o trecho estudado, do versículo inicial ao final, sem precisar concluir o capítulo inteiro. Fica salvo neste navegador e sincroniza quando você entra na conta.</p>
      <div class="sf-bar" data-sf-bar role="img" aria-label="Trechos estudados neste capítulo"></div>
      <div class="sf-controls">
        <button type="button" class="btn quiet sf-mark" data-sf-mark="start" aria-pressed="false">Marcar início</button>
        <button type="button" class="btn quiet sf-mark" data-sf-mark="end" aria-pressed="false">Marcar fim</button>
        <span class="sf-range" data-sf-range aria-live="polite">Início: — · Fim: —</span>
        <button type="button" class="btn primary sf-save" data-sf-save>Salvar trecho</button>
      </div>
      <p class="sf-hint sf-mark-hint" data-sf-mark-hint hidden>Toque no versículo onde começou a leitura.</p>
      <div class="sf-controls sf-precise">
        <span class="sf-field">Ajuste fino: do versículo <select data-sf-start aria-label="Versículo inicial do trecho">{opts}</select></span>
        <span class="sf-field">até <select data-sf-end aria-label="Versículo final do trecho">{opts}</select></span>
      </div>
      <ul class="sf-list" data-sf-list aria-live="polite"></ul>
    </div>
  </details>"""


def reader_fab(prefix, has_fraction=True):
    """Painel único de ferramentas de leitura (celular e desktop). Reúne o
    que antes eram 3 controles flutuantes concorrentes (ferramentas de
    leitura, ferramentas de estudo e reportar) num só, com posição salva e
    lista personalizável de atalhos visíveis."""
    mark = ""
    if has_fraction:
        mark = (
            '<button type="button" class="rfb" data-tool="mark-start" data-fab-mark="start">⇢<span>Início</span></button>'
            '<button type="button" class="rfb" data-tool="mark-end" data-fab-mark="end">✓<span>Fim</span></button>'
            '<button type="button" class="rfb" data-tool="save" data-fab-save>★<span>Salvar</span></button>'
        )
    return f"""
<div class="reader-fab" data-reader-fab>
  <div class="reader-fab-panel" data-reader-fab-panel hidden>
    <button type="button" class="rfb" data-tool="font-dec" data-rt="font-dec">A−<span>Fonte</span></button>
    <button type="button" class="rfb" data-tool="font-inc" data-rt="font-inc">A+<span>Fonte</span></button>
    <button type="button" class="rfb" data-tool="orig" data-rt="orig">א/A<span>Original</span></button>
    <button type="button" class="rfb" data-tool="theme" data-rt="theme">🌙<span>Tema</span></button>
    <button type="button" class="rfb" data-tool="search" data-search-open>🔍<span>Buscar</span></button>
    <button type="button" class="rfb" data-tool="focus" data-focus-toggle>☉<span>Foco</span></button>
    {mark}<a class="rfb" data-tool="study-notes" href="{prefix}anotacoes/">🗒<span>Anotações</span></a>
    <button type="button" class="rfb" data-tool="study-share" data-study-share>📝<span>Compartilhar estudo</span></button>
    <button type="button" class="rfb" data-tool="study-export" data-study-export>📄<span>Baixar .txt</span></button>
    <button type="button" class="rfb" data-tool="study-clear" data-study-clear>🗑<span>Apagar tudo</span></button>
    <button type="button" class="rfb" data-tool="report" data-report-open>🐞<span>Reportar</span></button>
    <button type="button" class="reader-fab-config-btn" data-reader-fab-config aria-expanded="false" aria-label="Personalizar ferramentas">⚙ Personalizar</button>
    <div class="reader-fab-config" data-reader-fab-config-panel hidden></div>
  </div>
  <button type="button" class="reader-fab-btn" data-reader-fab-toggle aria-label="Ferramentas de leitura (arraste para reposicionar)" aria-expanded="false">⚙</button>
</div>
<button type="button" class="focus-exit" data-focus-toggle>Sair do modo leitura</button>
{('<div class="focus-progress" data-focus-progress>'
  '<span data-focus-remaining>Boa leitura</span>'
  '<button type="button" class="fp-mark" data-focus-mark hidden>Marcar capítulo como lido</button>'
  '</div>') if has_fraction else ''}"""


def build_redirect_page(out_path, prefix, target, title):
    """Página-ponte: o endereço antigo continua existindo, mas leva direto ao
    novo lugar (Estudar e Comunidade foram fundidos no Workspace). Mantém os
    links espalhados por rodapés, capítulos e favoritos de usuários vivos."""
    url = f"{prefix}{target}"
    html = f"""<!doctype html>
<html lang="pt-BR"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} | {SITE_NAME}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{BASE_URL}/workspace/">
<meta http-equiv="refresh" content="0; url={url}">
<script>location.replace('{url}');</script>
</head><body>
<p>Esta área agora vive no Workspace. <a href="{url}">Continuar para o Workspace</a>.</p>
</body></html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_file(out_path, html)


def build_merged_redirects():
    build_redirect_page(SITE / "estudar" / "index.html", "../", "workspace/#estudar", "Estudar")
    build_redirect_page(SITE / "comunidade" / "index.html", "../", "workspace/#comunidade", "Comunidade")
    build_redirect_page(SITE / "comunidade" / "salas" / "index.html", "../../", "workspace/#comunidade", "Salas de Estudo")


def build_workspace_page():
    prefix = "../"
    title = f"Workspace | {SITE_NAME}"
    desc = "Seu espaço de estudo: leitura, progresso, missões, planos, biblioteca, anotações e Salas de Estudo em um só lugar."
    canonical = f"{BASE_URL}/workspace/"
    cards = action_cards([
        ("Leitura", "Continuar leitura", "Retome o último capítulo ou versículo aberto.", f"{prefix}ler/", " data-ws-continue"),
        ("Planos", "Planos de leitura", "Acompanhe leituras guiadas dia a dia.", f"{prefix}planos/"),
        ("Biblioteca", "Minha biblioteca", "Tudo junto: notas, grifos, favoritos, planos e artigos.", f"{prefix}biblioteca/"),
        ("Explorar", "Linha do tempo", "Os livros na ordem histórica dos acontecimentos.", f"{prefix}linha-do-tempo/"),
        ("Histórico", "Histórico", "Continue a leitura recente.", "#historico"),
    ])
    explore_cards = action_cards([
        ("Léxico", "Dicionário", "Palavras-chave do hebraico e do grego, com significado.", f"{prefix}dicionario/"),
        ("Geografia", "Mapas", "Lugares bíblicos e os versículos ligados a eles.", f"{prefix}mapas/"),
        ("Assuntos", "Temas de estudo", "Ansiedade, fé, perdão e outros pontos de entrada.", f"{prefix}index.html#temas"),
        ("Contexto", "Artigos", "Estudos originais sobre palavras, traduções e história do texto.", f"{prefix}index.html#artigos"),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Workspace</p>
  <header class="hub-hero">
    <p class="eyebrow">Seu espaço de estudo</p>
    <h1>Workspace</h1>
    <p>Leitura, progresso, ferramentas de estudo e comunidade — tudo ao redor do texto, em um só lugar.</p>
    <div class="hub-cta">
      <a class="btn primary" href="{prefix}ler/">Continuar leitura</a>
      <a class="btn green" href="#progresso">Ver progresso</a>
      <a class="btn quiet" href="#comunidade">Salas de Estudo</a>
    </div>
  </header>
  <section class="hub-section progresso" id="progresso" data-progress-panel hidden>
    <div class="section-title"><h2>Seu progresso</h2><span data-progress-note>Entre na conta para salvar entre aparelhos</span></div>
    <div class="level-card">
      <div class="level-badge"><span class="level-num" data-progress-level>1</span><span class="level-word">nível</span></div>
      <div class="level-body">
        <div class="level-head"><b data-progress-tier>Semente</b><span><span data-progress-xptonext>100</span> XP para o próximo nível</span></div>
        <div class="xp-bar"><i data-xp-bar style="width:0%"></i></div>
        <p class="level-foot"><span data-progress-xpinto>0</span>/<span data-progress-xpneed>100</span> XP neste nível</p>
      </div>
    </div>
    <div class="progress-stats">
      <div class="pstat"><b data-progress-streak>0</b><span>dias seguidos</span></div>
      <div class="pstat"><b data-progress-level>1</b><span>nível</span></div>
      <div class="pstat"><b data-progress-xp>0</b><span>pontos (XP)</span></div>
      <div class="pstat"><b data-progress-medals>0</b><span>medalhas</span></div>
    </div>
    <div class="stats-grid" data-stats-grid>
      <div class="stat-tile"><b data-stat-chapters>0</b><span>capítulos estudados</span></div>
      <div class="stat-tile"><b data-stat-bible-pct>0%</b><span>da Bíblia</span></div>
      <div class="stat-tile"><b data-stat-notes>0</b><span>notas</span></div>
      <div class="stat-tile"><b data-stat-highlights>0</b><span>grifos</span></div>
      <div class="stat-tile"><b data-stat-favs>0</b><span>favoritos</span></div>
    </div>
    <div class="stats-heatmap" data-stats-heatmap aria-label="Dias de leitura nas últimas semanas"></div>
    <details class="collap mission-block">
      <summary><span class="collap-title">Missões de hoje</span><span class="collap-count" data-mission-count>0/0</span><span class="collap-chev" aria-hidden="true">▾</span></summary>
      <div class="mission-list" data-mission-list></div>
    </details>
    <details class="collap mission-block">
      <summary><span class="collap-title">Missões da semana</span><span class="collap-count" data-weekly-count>0/0</span><span class="collap-chev" aria-hidden="true">▾</span></summary>
      <div class="mission-list" data-weekly-list></div>
    </details>
    <details class="collap medal-block">
      <summary><span class="collap-title">Medalhas</span><span class="collap-count" data-medal-count>0/0</span><span class="collap-chev" aria-hidden="true">▾</span></summary>
      <div class="medal-grid" data-medal-grid></div>
    </details>
  </section>
  <section class="hub-section" id="estudar">
    <div class="section-title"><h2>Estudar</h2><a href="#criar-plano">Criar plano</a></div>
    <div class="ws-tabs" role="tablist" aria-label="Ferramentas de estudo" data-ws-tabs>
      <button type="button" class="ws-tab on" role="tab" aria-selected="true" data-ws-tab="atalhos">Atalhos</button>
      <button type="button" class="ws-tab" role="tab" aria-selected="false" data-ws-tab="anotacoes">Anotações</button>
      <button type="button" class="ws-tab" role="tab" aria-selected="false" data-ws-tab="favoritos">Favoritos</button>
      <button type="button" class="ws-tab" role="tab" aria-selected="false" data-ws-tab="colecoes">Coleções</button>
      <button type="button" class="ws-tab" role="tab" aria-selected="false" data-ws-tab="cadernos">Cadernos</button>
    </div>
    <div class="ws-panel" role="tabpanel" data-ws-panel="atalhos">
      <div class="study-card-grid">{cards}
      </div>
    </div>
    <div class="ws-panel" role="tabpanel" data-ws-panel="anotacoes" hidden>
      <div id="anotacoes" class="anot-list"></div>
      <p class="map-actions"><a class="btn ghost" href="{prefix}anotacoes/">Abrir página completa (copiar, baixar, importar) →</a></p>
    </div>
    <div class="ws-panel" role="tabpanel" data-ws-panel="favoritos" hidden>
      <div class="library-rows" data-fav-full-list></div>
    </div>
    <div class="ws-panel" role="tabpanel" data-ws-panel="colecoes" hidden>
      <div class="collections-app" data-collections-app></div>
    </div>
    <div class="ws-panel" role="tabpanel" data-ws-panel="cadernos" hidden>
      <div class="notebooks-app" data-notebooks-app></div>
    </div>
  </section>
  <section class="hub-section" id="explorar">
    <div class="section-title"><h2>Explorar</h2><span>Léxico, mapas, temas e artigos de contexto</span></div>
    <div class="study-card-grid">{explore_cards}
    </div>
  </section>
  <section class="hub-section plan-builder" id="criar-plano">
    <div class="section-title"><h2>Criar Plano</h2><span>Gera um cronograma dia a dia</span></div>
    <form class="plan-form" data-plan-form>
      <label>O que deseja estudar?
        <select name="tipo" data-plan-tipo>
          <option value="livro">Um livro da Bíblia</option>
          <option value="tema">Um tema</option>
        </select>
      </label>
      <label data-plan-field="livro">Livro <select name="livro" data-plan-book-select></select></label>
      <label data-plan-field="tema" hidden>Tema <input name="conteudo" placeholder="oração, fé, aliança, sofrimento..."></label>
      <label>Duração
        <select name="duracao">
          <option value="7">7 dias</option><option value="14">14 dias</option><option value="21">21 dias</option><option value="30" selected>30 dias</option>
        </select>
      </label>
      <button type="submit" class="btn primary">Gerar plano</button>
    </form>
    <div class="saved-plans" data-plan-list></div>
  </section>
  <section class="hub-section comunidade" id="comunidade">
    <div class="section-title"><h2>Comunidade</h2><span>Salas de Estudo por livro, capítulo, tema ou plano</span></div>
    <p class="muted-line">Cada sala nasce de um conteúdo bíblico: crie a sua (a partir do nível 3), convide pelo código e conduza discussões ligadas ao texto. Sem feed genérico.</p>
    <div class="community-app" data-community-app>
      <p class="muted-line" data-community-fallback>Carregando salas…</p>
    </div>
  </section>
  <section class="hub-section" id="historico">
    <div class="section-title"><h2>Histórico de leitura</h2><span>Últimas páginas abertas</span></div>
    <div class="library-rows" data-history-list><p class="muted-line">Carregando histórico…</p></div>
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
    <p class="muted-line">Preferências de leitura salvas neste navegador e sincronizadas quando você entra na conta.</p>
    <div class="settings-grid" data-settings-panel>
      <div class="settings-row">
        <b>Tema</b>
        <div class="settings-opts" role="group" aria-label="Tema de leitura">
          <button type="button" class="btn quiet settings-opt" data-set-theme="light">Claro</button>
          <button type="button" class="btn quiet settings-opt" data-set-theme="sepia">Sépia</button>
          <button type="button" class="btn quiet settings-opt" data-set-theme="dark">Escuro</button>
        </div>
      </div>
      <div class="settings-row">
        <b>Tamanho da fonte</b>
        <div class="settings-opts" role="group" aria-label="Tamanho da fonte">
          <button type="button" class="btn quiet settings-opt" data-set-font="0">A</button>
          <button type="button" class="btn quiet settings-opt" data-set-font="1">A</button>
          <button type="button" class="btn quiet settings-opt" data-set-font="2">A</button>
          <button type="button" class="btn quiet settings-opt" data-set-font="3">A</button>
        </div>
      </div>
      <div class="settings-row">
        <b>Idioma original</b>
        <label class="settings-toggle"><input type="checkbox" data-set-orig> Mostrar hebraico/grego e transliteração</label>
      </div>
      <div class="settings-row">
        <b>Ordem dos livros</b>
        <div class="settings-opts" role="group" aria-label="Ordem dos livros">
          <button type="button" class="btn quiet settings-opt" data-set-order="bib">Bíblica</button>
          <button type="button" class="btn quiet settings-opt" data-set-order="alpha">Alfabética</button>
          <button type="button" class="btn quiet settings-opt" data-set-order="chron">Cronológica</button>
        </div>
      </div>
      <div class="settings-row">
        <b>Meus dados</b>
        <div class="settings-opts">
          <button type="button" class="btn quiet" data-settings-export>Baixar backup (.json)</button>
          <button type="button" class="btn quiet" data-settings-import>Importar backup</button>
          <input type="file" accept="application/json" data-settings-import-file hidden>
          <button type="button" class="btn danger ghost" data-settings-clear>Apagar tudo deste navegador</button>
        </div>
        <span class="settings-note" data-settings-status></span>
      </div>
    </div>
  </section>
  <section class="hub-section" id="reportes" data-admin-reports hidden>
    <div class="section-title"><h2>Reportes recebidos</h2><span>Somente administradores</span></div>
    <div class="library-rows" data-admin-reports-list><p class="muted-line">Carregando reportes…</p></div>
  </section>
</main>"""
    out = SITE / "workspace" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_library_page():
    prefix = "../"
    title = f"Biblioteca | {SITE_NAME}"
    desc = "Biblioteca pessoal com notas, grifos, favoritos, planos, artigos, coleções e cadernos."
    canonical = f"{BASE_URL}/biblioteca/"
    cards = action_cards([
        ("Notas", "Notas", "Anotações por versículo, capítulo e tema.", f"{prefix}anotacoes/"),
        ("Grifos", "Grifos", "Marcações por palavra e por versículo.", f"{prefix}anotacoes/"),
        ("Favoritos", "Favoritos", "Versículos salvos para revisão.", "#favoritos"),
        ("Planos", "Planos", "Leituras estruturadas e progresso.", f"{prefix}planos/"),
        ("Artigos", "Artigos", "Estudos contextuais e materiais de apoio.", f"{prefix}index.html#artigos"),
        ("Coleções", "Coleções", "Agrupe versículos favoritos por tema.", f"{prefix}colecoes/"),
        ("Cadernos", "Cadernos", "Estudos em texto livre: notas, perguntas e referências.", f"{prefix}cadernos/"),
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Biblioteca</p>
  <header class="hub-hero"><p class="eyebrow">Biblioteca</p><h1>Biblioteca</h1><p>Guarde e organize tudo que nasce do estudo bíblico.</p></header>
  <section class="hub-section"><div class="study-card-grid">{cards}</div></section>
  <section class="hub-section" id="favoritos">
    <div class="section-title"><h2>Favoritos</h2><span>Versículos salvos para revisão</span></div>
    <div class="library-rows" data-fav-full-list><p class="muted-line">Carregando favoritos…</p></div>
  </section>
</main>"""
    out = SITE / "biblioteca" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_collections_page():
    prefix = "../"
    title = f"Coleções | {SITE_NAME}"
    desc = "Coleções para guardar versículos, capítulos, artigos, mapas, manuscritos, planos e discussões."
    canonical = f"{BASE_URL}/colecoes/"
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Coleções</p>
  <header class="hub-hero"><p class="eyebrow">Coleções</p><h1>Coleções</h1><p>Reúna versículos favoritos em coleções por tema. Tudo fica salvo neste navegador e sincroniza quando você entra na conta.</p></header>
  <section class="hub-section">
    <div class="library-app" data-collections-app><p class="muted-line">Carregando coleções…</p></div>
  </section>
</main>"""
    out = SITE / "colecoes" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def build_notebooks_page():
    prefix = "../"
    title = f"Cadernos | {SITE_NAME}"
    desc = "Cadernos para organizar notas, perguntas, grifos, coleções, planos e referências."
    canonical = f"{BASE_URL}/cadernos/"
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Cadernos</p>
  <header class="hub-hero"><p class="eyebrow">Cadernos</p><h1>Cadernos</h1><p>Escreva estudos em texto livre: notas, perguntas e referências. Tudo fica salvo neste navegador e sincroniza quando você entra na conta.</p></header>
  <section class="hub-section">
    <div class="library-app" data-notebooks-app><p class="muted-line">Carregando cadernos…</p></div>
  </section>
</main>"""
    out = SITE / "cadernos" / "index.html"
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))


def load_reading_plans():
    """Planos curados de site/data/reading-plans.json; tolera ausência do arquivo."""
    path = DATA / "reading-plans.json"
    if not path.exists():
        return []
    try:
        plans = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return []
    return [p for p in plans if p.get("slug") and p.get("titulo") and p.get("dias")]


def plan_ref_url(ref, prefix=""):
    """Transforma "João 3" na URL de leitura do capítulo; None se não reconhecer."""
    parts = str(ref).rsplit(" ", 1)
    if len(parts) == 2 and parts[0] in BOOK_ORDER and parts[1].isdigit():
        return f"{prefix}ler/{book_slug(parts[0])}/{int(parts[1])}/"
    return None


def plan_ref_link(ref, prefix):
    """Transforma "João 3" em link para a leitura do capítulo; texto puro se não reconhecer."""
    url = plan_ref_url(ref, prefix)
    return f'<a href="{url}">{esc(ref)}</a>' if url else esc(str(ref))


def build_plan_index():
    """site/data/plan-index.json: planos curados com URLs raiz-relativas, para
    o leitor detectar "você está no Dia N do plano X" (ver app.asset.js)."""
    plans = load_reading_plans()
    index = [
        {
            "slug": p["slug"],
            "titulo": p["titulo"],
            "dias": [
                [{"label": ref, "url": plan_ref_url(ref)} for ref in refs]
                for refs in p["dias"]
            ],
        }
        for p in plans
    ]
    write_file(DATA / "plan-index.json", json.dumps(index, ensure_ascii=False))


def build_chapter_verse_counts(order, struct):
    """site/data/chapter-verses.json: {slug: {capitulo: n_versiculos}} — usado
    para saber se um dia de plano com 2+ capítulos foi lido por completo."""
    counts = {
        book_slug(livro): {str(ch): len(verses) for ch, verses in struct[livro].items()}
        for livro in order
    }
    write_file(DATA / "chapter-verses.json", json.dumps(counts, ensure_ascii=False, separators=(",", ":")))


def build_reading_plans_pages():
    plans = load_reading_plans()
    if not plans:
        return []
    prefix = "../"
    cards = action_cards([
        ("Plano", p["titulo"], f"{len(p['dias'])} dias. {p.get('descricao', '')}", f"{p['slug']}/")
        for p in plans
    ])
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Planos de leitura</p>
  <header class="hub-hero">
    <p class="eyebrow">Planos de leitura</p>
    <h1>Planos</h1>
    <p>Leituras guiadas dia a dia. O progresso fica salvo neste navegador e sincroniza quando você entra na conta.</p>
  </header>
  <section class="hub-section"><div class="study-card-grid">{cards}</div></section>
</main>"""
    write_file(
        SITE / "planos" / "index.html",
        head(f"Planos de leitura | {SITE_NAME}", "Planos de leitura bíblica guiados dia a dia, com progresso salvo.",
             f"{BASE_URL}/planos/", prefix) + nav(prefix) + body + footer(prefix),
    )
    for p in plans:
        build_reading_plan_page(p)
    return [p["slug"] for p in plans]


def build_reading_plan_page(plan):
    prefix = "../../"
    slug = plan["slug"]
    dias = plan["dias"]
    days_html = "".join(
        f"""
    <li class="plan-day">
      <label class="plan-check"><input type="checkbox" data-plan="{esc(slug)}" data-day="{i}"><span>Dia {i + 1}</span></label>
      <span class="plan-chapters">{" · ".join(plan_ref_link(ref, prefix) for ref in refs)}</span>
    </li>"""
        for i, refs in enumerate(dias)
    )
    body = f"""
<main id="main" class="wrap hub-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="../">Planos</a> · {esc(plan["titulo"])}</p>
  <header class="hub-hero">
    <p class="eyebrow">Plano de leitura</p>
    <h1>{esc(plan["titulo"])}</h1>
    <p>{esc(plan.get("descricao", ""))}</p>
  </header>
  <section class="hub-section">
    <div class="section-title"><h2>Sua leitura</h2><span class="plan-progress" data-plan-progress data-plan-slug="{esc(slug)}">0 de {len(dias)} dias</span></div>
    <ol class="plan-days">{days_html}
    </ol>
    <p class="map-actions"><button type="button" class="btn ghost" data-plan-reset="{esc(slug)}">Recomeçar plano</button></p>
  </section>
</main>"""
    write_file(
        SITE / "planos" / slug / "index.html",
        head(f"{plan['titulo']} | {SITE_NAME}", plan.get("descricao", "Plano de leitura bíblica."),
             f"{BASE_URL}/planos/{slug}/", prefix) + nav(prefix) + body + footer(prefix),
    )


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
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="{prefix}ler/">Livros</a> · {esc(v['referencia'])}</p>
  <header class="verse-head">
    <span class="lang-tag lang-{esc(v['idioma'])}">{lang_label(v['idioma'])}</span>
    <h1>{esc(v['referencia'])}</h1>
  </header>

  <div class="verse-hero verse-tap reveal">
    <p class="orig {sc}"{dir_attr} data-lang="{esc(speech_lang(v.get('idioma','')))}">{esc(v['original'])}</p>
    <p class="translit">{esc(v['transliteracao'])}</p>
    {pt_html}
    <p class="src-line">{esc(v.get('contexto',''))}</p>
  </div>
  <p class="verse-tap-hint">Toque no texto para grifar, anotar, favoritar, ouvir ou compartilhar.</p>

  {specimen_block(v)}
  {blocks}
  {kw_html}
  {rel}
  <section class="block xref-block" data-xref data-xref-ref="{esc(v['referencia'])}" hidden>
    <h2><span class="dot"></span>Referências cruzadas</h2>
    <div class="xref-list" data-xref-list></div>
  </section>
  {study_continue_module(prefix, v['livro'], ch, vs)}
  {src_note}
  {pager}
  </article>
  <div class="vs-sentinel" aria-hidden="true"></div>
  <p class="vs-loading" aria-live="polite"></p>
  <p class="backline"><a href="{prefix}ler/">← Todos os livros</a></p>
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
  {study_continue_module(prefix, livro)}
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
    vnums = []
    rows = ""
    for v in verses:
        _, vs = ref_chvs(v["referencia"])
        vnums.append(vs)
        dir_attr = ' dir="rtl"' if v.get("dir")=="rtl" else ' dir="ltr"'
        pt = esc(v.get("texto_pt","")) or '<span class="pt-missing">—</span>'
        rows += f"""
    <div class="ch-verse" id="v{vs}" data-ref="{esc(v['referencia'])}">
      <a class="ch-num" href="{prefix}versiculos/{esc(v['slug'])}/" aria-label="Versículo {vs}">{vs}</a>
      <div class="ch-body verse-tap">
        <p class="orig {sc}"{dir_attr} data-lang="{esc(speech_lang(v.get('idioma','')))}">{esc(v.get('original',''))}</p>
        <p class="translit">{esc(v.get('transliteracao',''))}</p>
        <p class="pt">{pt}</p>
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
    <button type="button" class="btn quiet focus-btn" data-focus-toggle title="Esconde menus e ferramentas para focar só no texto">☉ Modo leitura</button>
  </header>
  <div class="plan-context" data-plan-context hidden></div>
  {book_jump(prefix, order, livro)}
  {study_fraction_module(prefix, livro, ch, vnums)}
  <div class="chapter">{rows}
  </div>
  {study_continue_module(prefix, livro, ch)}
  <nav class="pager" aria-label="Folhear capítulos">{prev_html}{next_html}</nav>
  <p class="backline"><a href="../">← Todos os capítulos de {esc(livro)}</a></p>
</main>
{reader_fab(prefix, has_fraction=bool(vnums))}"""
    out = SITE / "ler" / bslug / str(ch) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_file(out, head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix))

def build_search_index(verses, articles, topics):
    """Índice de busca em arquivo externo (carregado sob demanda pela home),
    em vez de embutido no index.html — reduz a página de ~20 MB para poucos KB."""
    # "k" guarda só o texto de busca que NÃO está em titulo/desc (o cliente
    # concatena titulo+desc+k antes de dobrar acentos) — evita duplicar
    # referência e tradução inteiras dentro do próprio índice.
    index = []
    for v in verses:
        index.append({"t":"Versículo","titulo":v["referencia"],"desc":v.get("texto_pt",""),
                      "url":f"versiculos/{v['slug']}/",
                      "k":(v.get("contexto","")+" "+" ".join(v.get("palavras",[]))).lower()})
    for a in articles:
        index.append({"t":"Artigo","titulo":a["titulo"],"desc":a.get("resumo",""),
                      "url":f"artigos/{a['slug']}/","k":a.get("versiculo","").lower()})
    for t in topics:
        index.append({"t":"Tema","titulo":t["titulo"],"desc":t.get("descricao",""),
                      "url":"ler/","k":""})
    write_file(DATA / "search-index.json", json.dumps(index, ensure_ascii=False))
    return len(index)

def build_home(topics, verses, articles, sources, order, struct):
    prefix = ""
    title = f"{SITE_NAME} — a Bíblia com os idiomas originais, manuscritos e fontes"
    desc = "Leia cada versículo no idioma original (hebraico, grego, aramaico), com tradução de domínio público, foto do manuscrito quando há, e comentário rabínico ou explicação de origem."
    canonical = BASE_URL + "/"

    featured = next(v for v in verses if v["slug"]=="genesis-1-1")
    fsc = script_class(featured["idioma"], featured.get("dir","ltr"))

    # temas (os livros saíram da home e vivem na seção própria em /ler/)
    chips = "".join(
        f'<a class="chip" href="ler/"><span class="gl">{esc(t["icone"])}</span>{esc(t["titulo"])}</a>'
        for t in topics)

    n_books = len(order)
    n_chapters = sum(len(struct[livro]) for livro in order)

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
<header class="hero home-top" id="topo">
  <div class="hero-in">
    <div>
      <p class="eyebrow on-dark">Hebraico · Grego · Manuscritos · Sem anúncios</p>
      <h1>Estude a Bíblia na língua em que foi escrita.</h1>
      <p class="lead">Cada versículo com o original palavra por palavra, léxico com número de Strong, manuscritos reais e planos de leitura — salvo neste navegador, no celular e no computador, até offline.</p>
      <div class="hero-cta">
        <a class="btn primary" href="ler/">Ler a Bíblia</a>
        <a class="btn ghost" href="workspace/">Abrir o Workspace</a>
      </div>
      <ul class="hero-feats">
        <li>Palavra a palavra</li>
        <li>Manuscritos reais</li>
        <li>Funciona offline</li>
        <li>Planos de leitura</li>
      </ul>
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
      <article class="home-block home-today" data-home-progress>
        <span>Seu dia</span>
        <h3>Progresso de estudo</h3>
        <div class="home-today-stats">
          <div><b data-home-streak>0</b><small>dias seguidos</small></div>
          <div><b data-home-level>1</b><small>nível · <span data-home-tier>Semente</span></small></div>
          <div><b data-home-missions>0/0</b><small>missões de hoje</small></div>
        </div>
        <div class="xp-bar"><i data-home-xp-bar style="width:0%"></i></div>
        <a href="workspace/#progresso">Ver progresso completo</a>
      </article>
      <article class="home-block continue-block">
        <span>Leitura</span>
        <h3>Continuar leitura</h3>
        <a id="continue-read" class="continue-read" href="#" hidden></a>
        <p class="fallback-read">Abra um capítulo para o Workspace lembrar onde você parou.</p>
      </article>
      <article class="home-block" data-home-plan>
        <span>Hoje</span>
        <h3>Plano de hoje</h3>
        <div data-home-plan-body>
          <p>Crie um plano de leitura dia a dia, por livro ou por tema.</p>
          <a href="workspace/#criar-plano">Criar plano</a>
        </div>
      </article>
      <article class="home-block" data-home-notes>
        <span>Caderno</span>
        <h3>Últimas anotações</h3>
        <div data-home-notes-body>
          <p>Revise suas notas locais e exporte quando precisar.</p>
          <a href="anotacoes/">Abrir anotações</a>
        </div>
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
        <p>Estude um livro, capítulo ou tema junto com um grupo.</p>
        <a href="workspace/#comunidade">Ver Salas de Estudo</a>
      </article>
    </div>
  </section>

  <section id="biblia">
    <div class="sec-head">
      <p class="eyebrow">Leia a Bíblia inteira</p>
      <h2>Livros da Bíblia</h2>
      <p>Os livros ganharam uma seção própria: {n_books} livros e {n_chapters} capítulos, por ordem alfabética ou cronológica, cada um no idioma original com tradução e transliteração.</p>
    </div>
    <div class="wrap home-books-cta">
      <a class="btn primary" href="ler/">Abrir os livros</a>
      <a class="btn ghost" href="linha-do-tempo/">Ver a linha do tempo</a>
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

  <section class="hero apresentacao" id="apresentacao">
    <div class="hero-in">
      <div>
        <p class="eyebrow on-dark">Idiomas originais · manuscritos · fontes rastreáveis</p>
        <h2>Leia o versículo na língua em que foi escrito.</h2>
        <p class="lead">Para cada texto: o original em hebraico, grego ou aramaico, uma tradução de domínio público, a foto do manuscrito quando existe e o comentário rabínico ou a explicação da origem. Sem poluição, feito para ler no celular.</p>
        <div class="hero-cta">
          <a class="btn primary" href="ler/">Explorar os livros</a>
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

def build_core_js():
    write_asset("core.asset.js", "core.js")

def build_app_js(order, struct):
    books = [{"nome": livro, "slug": book_slug(livro), "cap": len(struct[livro])} for livro in order]
    js = read_asset("app.asset.js")
    write_file(SITE / "assets" / "app.js", f"var BEC_BOOKS={json.dumps(books, ensure_ascii=False)};\n" + js)

def build_auth_js():
    write_asset("auth.asset.js", "auth.js")

def build_study_js():
    js = read_asset("study.asset.js")
    write_file(SITE / "assets" / "study.js", f"var BEC_BASE={json.dumps(BASE_URL)};\n" + js)

def build_lexicon_js():
    lex_path = DATA / "hebrew-lexicon.json"
    lex = json.loads(lex_path.read_text(encoding="utf-8")) if lex_path.exists() else {}
    js = read_asset("lexicon.asset.js")
    write_file(SITE / "assets" / "lexicon.js", f"var BEC_LEXICON={json.dumps(lex, ensure_ascii=False)};\n" + js)

def build_lexicon_shards():
    """Fragmenta hebrew-tokens.json (tokenização palavra-a-palavra do WLC) em
    um arquivo por livro, carregado sob demanda pelo léxico interativo."""
    out_dir = SITE / "data" / "tokens"
    shutil.rmtree(out_dir, ignore_errors=True)
    src = DATA / "hebrew-tokens.json"
    if not src.exists():
        return
    tokens = json.loads(src.read_text(encoding="utf-8"))
    by_book = {}
    for ref, toks in tokens.items():
        m = re.match(r"^(.*?)\s+(\d+):(\d+)$", ref)
        if not m:
            continue
        livro, ch, vs = m.group(1), m.group(2), m.group(3)
        by_book.setdefault(livro, {})[f"{ch}:{vs}"] = toks
    for livro, verses_map in by_book.items():
        write_file(out_dir / f"{book_slug(livro)}.json",
                   json.dumps(verses_map, ensure_ascii=False, separators=(",", ":")))

def build_game_js():
    write_asset("gamification.asset.js", "game.js")

def build_community_js():
    write_asset("community.asset.js", "community.js")

def build_library_js():
    write_asset("library.asset.js", "library.js")

def build_report_js():
    write_asset("report.asset.js", "report.js")

def build_sw_js():
    js = read_asset("sw.asset.js").replace("__ASSET_VER__", ASSET_VER)
    write_file(SITE / "sw.js", js)

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

def build_meta(verses, articles, order, struct, plan_slugs=()):
    # sitemap
    # /estudar/ e /comunidade/ viraram redirects (noindex) para o Workspace e
    # por isso ficam fora do sitemap.
    urls = [
        BASE_URL + "/",
        f"{BASE_URL}/ler/",
        f"{BASE_URL}/workspace/",
        f"{BASE_URL}/biblioteca/",
        f"{BASE_URL}/colecoes/",
        f"{BASE_URL}/cadernos/",
        f"{BASE_URL}/privacidade/",
        f"{BASE_URL}/linha-do-tempo/",
    ]
    if plan_slugs:
        urls.append(f"{BASE_URL}/planos/")
        urls += [f"{BASE_URL}/planos/{slug}/" for slug in plan_slugs]
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
        "id": "/", "name": SITE_NAME, "short_name": "Bíblia em Contexto", "lang": "pt-BR",
        "start_url": "./", "scope": "./",
        "display": "standalone", "display_override": ["standalone", "minimal-ui"],
        "background_color": "#efe4d0", "theme_color": "#efe4d0",
        "description": "A Bíblia com os idiomas originais, manuscritos e fontes.",
        "categories": ["books", "education", "lifestyle"],
        "icons": [
            {"src": "assets/icons/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
            {"src": "assets/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "assets/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "assets/icons/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
        "shortcuts": [
            {"name": "Ler a Bíblia", "url": "ler/", "description": "Voltar direto para a leitura"},
            {"name": "Workspace", "url": "workspace/", "description": "Progresso, planos e comunidade"},
            {"name": "Planos de leitura", "url": "planos/", "description": "Continuar um plano de leitura"},
        ],
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
    build_core_js()
    build_auth_js()
    build_app_js(order, struct)
    build_study_js()
    build_lexicon_js()
    build_lexicon_shards()
    build_game_js()
    build_community_js()
    build_library_js()
    build_report_js()
    build_sw_js()
    build_annotations_page()
    build_workspace_page()
    build_merged_redirects()
    build_library_page()
    build_collections_page()
    build_notebooks_page()
    plan_slugs = build_reading_plans_pages()
    build_plan_index()
    build_chapter_verse_counts(order, struct)
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

    build_meta(verses, inputs.articles, order, struct, plan_slugs)
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
