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
import json, html, re, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = SITE / "data"

BASE_URL = "https://alusionbr.github.io/bibliaonline"  # domínio do GitHub Pages
SITE_NAME = "Bíblia em Contexto"

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def esc(s):
    return html.escape(s or "", quote=True)

def script_class(idioma, direction):
    # aramaico bíblico usa o alfabeto hebraico (rtl); transliterações no grego usam grego
    if direction == "rtl":
        return "scr-hebrew"
    return "scr-greek"

def lang_label(idioma):
    return {"hebraico":"Hebraico","grego":"Grego","aramaico":"Aramaico"}.get(idioma, idioma.title())

# nome de cada livro no Sefaria (inglês), para montar o link de comentário rabínico
SEFARIA = {
 "Gênesis":"Genesis","Êxodo":"Exodus","Levítico":"Leviticus","Números":"Numbers",
 "Deuteronômio":"Deuteronomy","Josué":"Joshua","Juízes":"Judges","Rute":"Ruth",
 "1 Samuel":"I Samuel","2 Samuel":"II Samuel","1 Reis":"I Kings","2 Reis":"II Kings",
 "1 Crônicas":"I Chronicles","2 Crônicas":"II Chronicles","Esdras":"Ezra","Neemias":"Nehemiah",
 "Ester":"Esther","Jó":"Job","Salmos":"Psalms","Provérbios":"Proverbs","Eclesiastes":"Ecclesiastes",
 "Cânticos":"Song of Songs","Isaías":"Isaiah","Jeremias":"Jeremiah","Lamentações":"Lamentations",
 "Ezequiel":"Ezekiel","Daniel":"Daniel","Oseias":"Hosea","Joel":"Joel","Amós":"Amos",
 "Obadias":"Obadiah","Jonas":"Jonah","Miquéias":"Micah","Naum":"Nahum","Habacuque":"Habakkuk",
 "Sofonias":"Zephaniah","Ageu":"Haggai","Zacarias":"Zechariah","Malaquias":"Malachi",
}
# fac-símile do manuscrito-fonte (Códice de Leningrado, base do texto hebraico)
MANUSCRITO_FACSIMILE = "https://commons.wikimedia.org/wiki/Leningrad_Codex"

def ref_chvs(referencia):
    m = re.search(r"(\d+):(\d+)", referencia)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

def sefaria_url(livro, ch, vs):
    book = SEFARIA.get(livro)
    if not book:
        return ""
    return f"https://www.sefaria.org/{book.replace(' ', '_')}.{ch}.{vs}?lang=bi&with=all"

# ordem canônica dos livros (folhear a Bíblia de Gênesis a Apocalipse)
BOOK_ORDER = ["Gênesis","Êxodo","Levítico","Números","Deuteronômio","Josué","Juízes","Rute",
"1 Samuel","2 Samuel","1 Reis","2 Reis","1 Crônicas","2 Crônicas","Esdras","Neemias","Ester",
"Jó","Salmos","Provérbios","Eclesiastes","Cânticos","Isaías","Jeremias","Lamentações","Ezequiel",
"Daniel","Oseias","Joel","Amós","Obadias","Jonas","Miquéias","Naum","Habacuque","Sofonias","Ageu",
"Zacarias","Malaquias","Mateus","Marcos","Lucas","João","Atos","Romanos","1 Coríntios","2 Coríntios",
"Gálatas","Efésios","Filipenses","Colossenses","1 Tessalonicenses","2 Tessalonicenses","1 Timóteo",
"2 Timóteo","Tito","Filemom","Hebreus","Tiago","1 Pedro","2 Pedro","1 João","2 João","3 João","Judas","Apocalipse"]

def verse_sort_key(v):
    livro = v.get("livro","")
    bi = BOOK_ORDER.index(livro) if livro in BOOK_ORDER else len(BOOK_ORDER)
    m = re.search(r"(\d+):(\d+)", v.get("referencia",""))
    ch, vs = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    return (bi, ch, vs)

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
<link rel="stylesheet" href="{prefix}assets/styles.css">{ld}
</head>
<body>
<a class="skip" href="#main">Pular para o conteúdo</a>"""

def nav(prefix):
    return f"""
<nav class="nav">
  <div class="nav-in">
    <a class="brand" href="{prefix}index.html">
      <span class="brand-mark">ב</span>
      <span class="brand-name">Bíblia em Contexto</span>
    </a>
    <button class="menu-btn" aria-label="Abrir menu" data-menu>☰</button>
    <div class="nav-links" data-links>
      <a href="{prefix}index.html#versiculos">Versículos</a>
      <a href="{prefix}index.html#temas">Temas</a>
      <a href="{prefix}index.html#artigos">Artigos</a>
      <a href="{prefix}index.html#fontes">Fontes</a>
    </div>
  </div>
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
        <a href="{prefix}index.html#versiculos">Versículos</a>
        <a href="{prefix}index.html#temas">Temas</a>
        <a href="{prefix}index.html#artigos">Artigos</a>
      </div>
      <div>
        <a href="{prefix}index.html#fontes">Fontes e licenças</a>
        <a href="{prefix}index.html#metodologia">Metodologia</a>
        <a href="{prefix}index.html#topo">Voltar ao topo ↑</a>
      </div>
    </div>
  </div>
</footer>
<script src="{prefix}assets/app.js"></script>
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
  <article class="verse-cont" data-slug="{esc(v['slug'])}" data-title="{esc(title)}">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="{prefix}index.html#versiculos">Versículos</a> · {esc(v['referencia'])}</p>
  <header class="verse-head">
    <span class="lang-tag lang-{esc(v['idioma'])}">{lang_label(v['idioma'])}</span>
    <h1>{esc(v['referencia'])}</h1>
  </header>

  <div class="verse-hero reveal">
    <p class="orig {sc}"{dir_attr}>{esc(v['original'])}</p>
    <p class="translit">{esc(v['transliteracao'])}</p>
    {pt_html}
    <p class="src-line">{esc(v.get('contexto',''))}</p>
  </div>

  {specimen_block(v)}
  {blocks}
  {kw_html}
  {rel}
  {src_note}
  {pager}
  </article>
  <div class="vs-sentinel" aria-hidden="true"></div>
  <p class="vs-loading" aria-live="polite"></p>
  <p class="backline"><a href="{prefix}index.html#versiculos">← Todos os versículos</a></p>
</main>"""
    out = SITE / "versiculos" / v["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix, jsonld) + nav(prefix) + body + footer(prefix), encoding="utf-8")

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
    out.write_text(head(title, desc, canonical, prefix, jsonld) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_home(topics, verses, articles, sources):
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

    # versículos
    vcards = ""
    for v in verses:
        sc = script_class(v["idioma"], v.get("dir","ltr"))
        dir_attr = ' dir="rtl"' if v.get("dir")=="rtl" else ' dir="ltr"'
        vcards += f"""
    <a class="card" href="versiculos/{v['slug']}/">
      <div class="ref-row"><h3>{esc(v['referencia'])}</h3><span class="lang-tag lang-{esc(v['idioma'])}">{lang_label(v['idioma'])}</span></div>
      <p class="orig-mini {sc}"{dir_attr}>{esc(v['original'][:60])}</p>
      <p class="pt-mini">{esc(v['texto_pt'][:110])}{'…' if len(v['texto_pt'])>110 else ''}</p>
      <span class="more">Ver no original →</span>
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

    # índice de busca embutido (funciona offline, sem fetch)
    index = []
    for v in verses:
        index.append({"t":"Versículo","titulo":v["referencia"],"desc":v["texto_pt"],
                      "url":f"versiculos/{v['slug']}/","k":(v["referencia"]+" "+v["texto_pt"]+" "+v.get("contexto","")+" "+" ".join(v.get("palavras",[]))).lower()})
    for a in articles:
        index.append({"t":"Artigo","titulo":a["titulo"],"desc":a["resumo"],
                      "url":f"artigos/{a['slug']}/","k":(a["titulo"]+" "+a["resumo"]+" "+a.get("versiculo","")).lower()})
    for t in topics:
        index.append({"t":"Tema","titulo":t["titulo"],"desc":t["descricao"],
                      "url":"#versiculos","k":(t["titulo"]+" "+t["descricao"]).lower()})
    index_js = json.dumps(index, ensure_ascii=False)

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
  </section>

  <section id="versiculos">
    <div class="sec-head">
      <p class="eyebrow">O texto, camada por camada</p>
      <h2>Versículos no original</h2>
      <p>Cada cartão abre uma página com o original, a tradução livre, o manuscrito e o comentário.</p>
    </div>
    <div class="cards verses wrap">{vcards}
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
</main>

<script>window.__INDEX__ = {index_js};</script>"""

    out = SITE / "index.html"
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_app_js():
    js = r"""// home: menu + busca local (índice embutido em window.__INDEX__)
document.addEventListener('click',function(e){
  if(e.target.closest('[data-menu]')){document.querySelector('[data-links]').classList.toggle('open');}
});
(function(){
  var q=document.getElementById('q'), out=document.getElementById('results');
  if(!q||!out||!window.__INDEX__) return;
  function render(term){
    out.innerHTML='';
    term=(term||'').trim().toLowerCase();
    if(!term) return;
    var res=window.__INDEX__.filter(function(i){return i.k.indexOf(term)>-1;}).slice(0,8);
    if(!res.length){out.innerHTML='<p class="empty">Nada encontrado. Tente “Salmo 23”, “shalom”, “logos” ou “aramaico”.</p>';return;}
    res.forEach(function(i){
      var a=document.createElement('a');a.className='result';a.href=i.url;
      a.innerHTML='<span class="kind">'+i.t+'</span><h4>'+i.titulo+'</h4><p>'+i.desc+'</p>';
      out.appendChild(a);
    });
  }
  q.addEventListener('input',function(e){render(e.target.value);});
})();
// reveal
if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
  var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.style.animationDelay='0s';en.target.classList.add('reveal');io.unobserve(en.target);}});});
  document.querySelectorAll('.card').forEach(function(c){io.observe(c);});
}

// rolagem infinita na página de versículo (mantém também os botões Anterior/Próximo)
(function(){
  var main=document.querySelector('main.verse-page[data-next]');
  if(!main) return;
  var sentinel=main.querySelector('.vs-sentinel');
  var loadingEl=main.querySelector('.vs-loading');
  if(!sentinel) return;
  var nextURL=main.getAttribute('data-next');
  var loading=false;

  // atualiza título e URL conforme cada versículo entra em foco
  var titleObs=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(en.isIntersecting){
        var slug=en.target.getAttribute('data-slug'), t=en.target.getAttribute('data-title');
        if(t) document.title=t;
        if(slug){ try{ history.replaceState(null,'','../'+slug+'/'); }catch(e){} }
      }
    });
  },{rootMargin:'-30% 0px -60% 0px'});
  document.querySelectorAll('.verse-cont').forEach(function(a){titleObs.observe(a);});

  function loadNext(){
    if(loading||!nextURL) return;
    loading=true;
    if(loadingEl) loadingEl.textContent='Carregando próximo versículo…';
    fetch(nextURL).then(function(r){return r.text();}).then(function(html){
      var doc=new DOMParser().parseFromString(html,'text/html');
      var art=doc.querySelector('.verse-cont');
      var nm=doc.querySelector('main.verse-page[data-next]');
      nextURL=nm?nm.getAttribute('data-next'):'';
      if(art){
        var sep=document.createElement('hr'); sep.className='verse-sep';
        main.insertBefore(sep,sentinel);
        var imp=document.importNode(art,true);
        main.insertBefore(imp,sentinel);
        titleObs.observe(imp);
      }
      loading=false;
      if(loadingEl) loadingEl.textContent = nextURL ? '' : '— fim dos versículos —';
    }).catch(function(){
      loading=false;
      if(loadingEl) loadingEl.textContent='Não foi possível carregar o próximo. Use os botões acima.';
    });
  }

  var io2=new IntersectionObserver(function(es){
    es.forEach(function(en){ if(en.isIntersecting) loadNext(); });
  },{rootMargin:'700px 0px'});
  io2.observe(sentinel);
})();
"""
    (SITE / "assets" / "app.js").write_text(js, encoding="utf-8")

def build_meta(verses, articles):
    # sitemap
    urls = [BASE_URL + "/"]
    urls += [f"{BASE_URL}/versiculos/{v['slug']}/" for v in verses]
    urls += [f"{BASE_URL}/artigos/{a['slug']}/" for a in articles]
    items = "".join(f"<url><loc>{u}</loc><changefreq>monthly</changefreq></url>\n" for u in urls)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+items+'</urlset>\n',
        encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    (SITE / "manifest.webmanifest").write_text(json.dumps({
        "name":SITE_NAME,"short_name":"Bíblia em Contexto","lang":"pt-BR",
        "start_url":"./","display":"standalone","background_color":"#f4eee2","theme_color":"#1a1610",
        "description":"A Bíblia com os idiomas originais, manuscritos e fontes."
    }, ensure_ascii=False, indent=2), encoding="utf-8")

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
    out.write_text(head("Página não encontrada | "+SITE_NAME, "Página não encontrada.", BASE_URL+"/404.html", prefix)
                   + nav(prefix) + body + footer(prefix), encoding="utf-8")

def main():
    topics=load("topics.json"); verses=load("verses.json")
    articles=load("articles.json"); sources=load("sources.json")
    articles_by_slug={a["slug"]:a for a in articles}
    # ordem bíblica garantida (folhear de Gênesis a Apocalipse)
    verses = sorted(verses, key=verse_sort_key)
    # limpa saídas antigas
    for d in ["versiculos","artigos"]:
        shutil.rmtree(SITE/d, ignore_errors=True)
    build_home(topics, verses, articles, sources)
    build_app_js()
    n = len(verses)
    for i, v in enumerate(verses):
        prev_v = verses[i-1] if i > 0 else None
        next_v = verses[i+1] if i < n-1 else None
        build_verse_page(v, articles_by_slug, prev_v, next_v)
    for a in articles: build_article_page(a)
    build_meta(verses, articles)
    build_404()
    print(f"OK: home + {len(verses)} versículos + {len(articles)} artigos + sitemap + 404")

if __name__=="__main__":
    main()
