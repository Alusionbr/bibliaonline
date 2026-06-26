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
import json, html, re, shutil, unicodedata, hashlib, base64
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = SITE / "data"

BASE_URL = "https://alusionbr.github.io/bibliaonline"  # domínio do GitHub Pages
SITE_NAME = "Bíblia em Contexto"

def asset_ver():
    # versão dos assets (cache-busting): muda quando o build (que gera o JS) ou
    # o CSS mudam, forçando o navegador a baixar styles.css/app.js/study.js novos.
    h = hashlib.sha1()
    h.update(Path(__file__).read_bytes())
    css = SITE / "assets" / "styles.css"
    if css.exists():
        h.update(css.read_bytes())
    return h.hexdigest()[:8]

ASSET_VER = asset_ver()

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def load_opt(name, default):
    # carga opcional: usada para dados curados que podem não existir (ex.: em testes)
    p = DATA / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def esc(s):
    return html.escape(s or "", quote=True)

def fold(s):
    # remove acentos e baixa caixa (para casar texto sem depender de acentuação)
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()

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

# Linha do tempo (didática; datas APROXIMADAS — estimativas variam entre estudiosos).
# Cada livro entra UMA vez, pelo período histórico associado. NÃO altera o texto bíblico.
TIMELINE = [
 {"nome":"Primórdios","periodo":"antes de ~2000 a.C.","descricao":"Da criação ao dilúvio e à dispersão dos povos.","livros":["Gênesis"]},
 {"nome":"Patriarcas","periodo":"~2000–1700 a.C.","descricao":"Abraão, Isaque, Jacó e José — as promessas a Israel.","livros":["Jó"]},
 {"nome":"Êxodo e a Lei","periodo":"~1500–1400 a.C.","descricao":"A saída do Egito, a aliança e a Lei no Sinai.","livros":["Êxodo","Levítico","Números","Deuteronômio"]},
 {"nome":"Conquista e Juízes","periodo":"~1400–1050 a.C.","descricao":"A entrada em Canaã e o período dos juízes.","livros":["Josué","Juízes","Rute"]},
 {"nome":"Monarquia Unida","periodo":"~1050–930 a.C.","descricao":"Saul, Davi e Salomão; salmos e sabedoria.","livros":["1 Samuel","2 Samuel","1 Reis","1 Crônicas","Salmos","Provérbios","Eclesiastes","Cânticos"]},
 {"nome":"Reinos Divididos e Profetas","periodo":"~930–586 a.C.","descricao":"Israel e Judá se dividem; os profetas advertem.","livros":["2 Reis","2 Crônicas","Isaías","Jeremias","Lamentações","Oseias","Joel","Amós","Obadias","Jonas","Miquéias","Naum","Habacuque","Sofonias"]},
 {"nome":"Exílio","periodo":"~586–538 a.C.","descricao":"Judá no cativeiro na Babilônia.","livros":["Ezequiel","Daniel"]},
 {"nome":"Pós-exílio e Restauração","periodo":"~538–430 a.C.","descricao":"O retorno, a reconstrução de Jerusalém e do Templo.","livros":["Esdras","Neemias","Ester","Ageu","Zacarias","Malaquias"]},
 {"nome":"Período intertestamentário","periodo":"~430–6 a.C.","descricao":"Cerca de 400 anos entre Malaquias e os Evangelhos (sem livros no cânon protestante).","livros":[]},
 {"nome":"Vida de Jesus","periodo":"~6 a.C.–30 d.C.","descricao":"O nascimento, ministério, morte e ressurreição de Jesus.","livros":["Mateus","Marcos","Lucas","João"]},
 {"nome":"Igreja primitiva","periodo":"~30–95 d.C.","descricao":"A expansão da Igreja e as cartas apostólicas.","livros":["Atos","Romanos","1 Coríntios","2 Coríntios","Gálatas","Efésios","Filipenses","Colossenses","1 Tessalonicenses","2 Tessalonicenses","1 Timóteo","2 Timóteo","Tito","Filemom","Hebreus","Tiago","1 Pedro","2 Pedro","1 João","2 João","3 João","Judas"]},
 {"nome":"Visão final","periodo":"~95 d.C.","descricao":"A revelação do fim e da nova criação.","livros":["Apocalipse"]},
]
CHRON_INDEX = {}
for _era in TIMELINE:
    for _b in _era["livros"]:
        CHRON_INDEX[_b] = len(CHRON_INDEX)

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

def book_slug(livro):
    base = unicodedata.normalize("NFKD", livro).encode("ascii","ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")

def ref_to_slug(ref):
    # "Livro c:v" -> slug do versículo (mesma regra usada na geração das páginas)
    m = re.match(r"^(.*?)\s+(\d+):(\d+)$", ref or "")
    if not m:
        return None
    return f"{book_slug(m.group(1))}-{m.group(2)}-{m.group(3)}"

def group_by_book_chapter(verses):
    """Agrupa os versículos (já em ordem canônica) em {livro: {capítulo: [versículos]}},
    preservando a ordem dos livros. Base para navegação livro→capítulo→versículo."""
    order = []
    struct = defaultdict(lambda: defaultdict(list))
    for v in verses:
        livro = v["livro"]
        if livro not in struct:
            order.append(livro)
        ch, _ = ref_chvs(v["referencia"])
        struct[livro][ch].append(v)
    return order, struct

# ---------- segurança (CSP + cabeçalhos via <meta>) ----------
# Único script inline da página: aplica tema/fonte antes da pintura para evitar
# "flash" de tema claro. Fica numa constante para o hash da CSP ficar em sincronia.
THEME_BOOTSTRAP = (
    "(function(){try{var d=document.documentElement;"
    "if(localStorage.getItem('bec.theme')==='dark')d.classList.add('dark');"
    "var f=localStorage.getItem('bec.fontscale');if(f)d.classList.add('fs-'+f);"
    "}catch(e){}})();"
)

def _sha256_b64(s):
    return base64.b64encode(hashlib.sha256(s.encode("utf-8")).digest()).decode()

# CSP estrita: sem 'unsafe-inline' em scripts (o único inline é liberado por hash).
# Estilos inline (atributos style="...") usam 'unsafe-inline' — baixo risco.
# Imagens de manuscrito vêm de domínios públicos externos (https). Fetch/SW: mesma origem.
CSP = "; ".join([
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    f"script-src 'self' 'sha256-{_sha256_b64(THEME_BOOTSTRAP)}'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data: https:",
    "connect-src 'self'",
    "manifest-src 'self'",
    "worker-src 'self'",
    "form-action 'self'",
    "upgrade-insecure-requests",
])

# ---------- shells ----------
def head(title, description, canonical, prefix, jsonld=None):
    ld = f'\n<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<meta name="referrer" content="strict-origin-when-cross-origin">
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
<script>{THEME_BOOTSTRAP}</script>
<a class="skip" href="#main">Pular para o conteúdo</a>"""

def nav(prefix):
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
    <button class="menu-btn" aria-label="Abrir menu" data-menu>☰</button>
    <div class="nav-links" data-links>
      <a href="{prefix}ler/">Bíblia</a>
      <a href="{prefix}planos/">Planos</a>
      <a href="{prefix}temas/">Temas</a>
      <a href="{prefix}dicionario/">Dicionário</a>
      <a href="{prefix}mapas/">Mapas</a>
      <a href="{prefix}linha-do-tempo/">Linha do tempo</a>
      <a href="{prefix}anotacoes/">Anotações</a>
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
        <a href="{prefix}temas/">Temas</a>
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
<script src="{prefix}assets/app.js?v={ASSET_VER}"></script>
<script src="{prefix}assets/study.js?v={ASSET_VER}" defer></script>
</body></html>"""

# ---------- componentes ----------
def translit_disclosure(text, indent=4):
    text = esc(text)
    if not text.strip():
        return ""
    pad = " " * indent
    inner = " " * (indent + 2)
    return (
        f'{pad}<details class="translit-toggle">\n'
        f'{inner}<summary><span class="translit-arrow" aria-hidden="true">&gt;</span><span class="sr-only">Mostrar transliteração</span></summary>\n'
        f'{inner}<p class="translit">{text}</p>\n'
        f'{pad}</details>'
    )

# tokens hebraicos (lemma+morph por palavra) carregados uma vez em main();
# alimentam a interação palavra-a-palavra (significado + gramática) no hebraico.
HEBREW_TOKENS = {}

def hebrew_inner(v):
    # monta o texto hebraico/aramaico com cada palavra interativa quando há tokens
    # alinhados. Cada palavra vira <span class="w hw" ...>: "w"+data-f/data-i para
    # o grifo/marca-texto (study.js), "hw"+data-l/data-m para o popover (significado
    # + gramática). Retorna (html, tokenizado?). Sem tokens: texto simples (fallback).
    original = v.get("original", "")
    if v.get("idioma") not in ("hebraico", "aramaico"):
        return esc(original), False
    toks = HEBREW_TOKENS.get(v.get("referencia", ""))
    words = original.split()
    if not toks or len(toks) != len(words):
        return esc(original), False
    spans = []
    for i, (w, lm) in enumerate(zip(words, toks)):
        lemma, morph = (lm + ["", ""])[:2]
        spans.append(f'<span class="w hw" data-f="orig" data-i="{i}" '
                     f'data-l="{esc(lemma)}" data-m="{esc(morph)}">{esc(w)}</span>')
    return " ".join(spans), True

def original_html(v, indent=4):
    sc = script_class(v["idioma"], v.get("dir","ltr"))
    dir_attr = ' dir="rtl"' if v.get("dir")=="rtl" else ' dir="ltr"'
    inner_txt, tokenized = hebrew_inner(v) if v.get("idioma") != "grego" else (esc(v.get("original","")), False)
    # já pré-tokenizado no servidor -> study.js não deve re-embrulhar (data-wrapped)
    wrapped = ' data-wrapped="1"' if tokenized else ''
    if v.get("idioma") != "grego":
        return f'{" " * indent}<p class="orig {sc}"{dir_attr}{wrapped}>{inner_txt}</p>'
    pad = " " * indent
    inner = " " * (indent + 2)
    return (
        f'{pad}<details class="original-toggle">\n'
        f'{inner}<summary><span class="translit-arrow" aria-hidden="true">&gt;</span><span class="sr-only">Mostrar texto grego</span></summary>\n'
        f'{inner}<p class="orig {sc}"{dir_attr}{wrapped}>{inner_txt}</p>\n'
        f'{pad}</details>'
    )

def verse_result_card(ref, verses_by_ref, prefix):
    # cartão de versículo (referência + texto pt) que aponta para a página completa
    v = verses_by_ref.get(ref)
    slug = ref_to_slug(ref)
    if not slug:
        return ""
    pt = esc(v.get("texto_pt", "")) if v else ""
    return (f'<a class="result" href="{prefix}versiculos/{slug}/">'
            f'<span class="kind">Versículo</span><h4>{esc(ref)}</h4>'
            f'<p>{pt}</p></a>')

def osm_url(lat, lon):
    # link (nao embed) para o OpenStreetMap — funciona offline como texto e nao
    # carrega scripts/tiles externos, mantendo a CSP estrita e o modo offline
    return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=8/{lat}/{lon}"

def chapter_link(prefix, ch_str):
    # "Livro C" -> link para a pagina de leitura do capitulo (/ler/<livro>/<c>/)
    m = re.match(r"^(.*?)\s+(\d+)$", ch_str or "")
    if not m:
        return esc(ch_str)
    livro, ch = m.group(1), m.group(2)
    return f'<a href="{prefix}ler/{book_slug(livro)}/{ch}/">{esc(ch_str)}</a>'

def places_block(v, places_by_ref, prefix):
    # lugares biblicos mencionados neste versiculo, ligando ao atlas (/mapas/)
    places = places_by_ref.get(v["referencia"]) if places_by_ref else None
    if not places:
        return ""
    chips = "".join(
        f'<a class="place-chip" href="{prefix}mapas/{esc(p["slug"])}/">'
        f'<span class="place-pin" aria-hidden="true">◉</span>{esc(p["nome"])}</a>'
        for p in places)
    return f"""
  <section class="block" id="lugares">
    <h2><span class="dot"></span>Lugares</h2>
    <div class="place-chips">{chips}</div>
  </section>"""

def commentary_block(v, commentary):
    # comentário teológico (resumo ORIGINAL, curado) na página do versículo
    items = commentary.get(v["referencia"]) if commentary else None
    if not items:
        return ""
    rows = ""
    for c in items:
        rows += (f'<div class="comm-item"><span class="comm-tag">{esc(c.get("perspectiva",""))}</span>'
                 f'<p>{esc(c.get("texto",""))}</p></div>')
    return f"""
  <section class="block" id="comentario">
    <h2><span class="dot"></span>Comentário</h2>
    <p class="block-note">Resumo original da Bíblia em Contexto — não reproduz comentários protegidos.</p>
    <div class="comm-list">{rows}</div>
  </section>"""

def study_disclosure(section_id, title, body_html):
    # bloco de estudo RECOLHIDO por padrão (disclosure nativo <details>): aparece
    # compacto, só abre para quem tem interesse — não atrapalha quem não quer.
    # Sem JS inline (CSP): <details> é nativo.
    return f"""
  <section class="block jewish" id="{section_id}">
    <details class="study-toggle">
      <summary><span class="dot"></span><span class="study-title">{esc(title)}</span><span class="translit-arrow study-arrow" aria-hidden="true">&gt;</span></summary>
{body_html}
    </details>
  </section>"""

def jewish_reading_block(v, jewish_readings):
    # leitura judaica como CONTEXTO (linguístico/histórico) — resumo ORIGINAL, curado.
    # Apresentada com respeito, ao lado da leitura cristã; não a substitui nem contradiz.
    items = jewish_readings.get(v["referencia"]) if jewish_readings else None
    if not items:
        return ""
    rows = ""
    for c in items:
        rows += (f'<div class="comm-item"><span class="comm-tag">{esc(c.get("angulo",""))}</span>'
                 f'<p>{esc(c.get("texto",""))}</p></div>')
    body = (f'      <p class="block-note">Resumo original da Bíblia em Contexto, oferecido como contexto histórico e linguístico da tradição judaica. Apresentado com respeito — não substitui nem contradiz a leitura cristã.</p>\n'
            f'      <div class="comm-list">{rows}</div>')
    return study_disclosure("leitura-judaica", "Leitura judaica (contexto)", body)

def glossary_terms_block(v, glossary_by_ref, prefix):
    # palavras-chave do original presentes neste versículo, ligando ao dicionário
    terms = glossary_by_ref.get(v["referencia"]) if glossary_by_ref else None
    if not terms:
        return ""
    chips = "".join(
        f'<a class="gloss-chip" href="{prefix}dicionario/{esc(t["slug"])}/">'
        f'<span class="gloss-orig {script_class(t["idioma"], t.get("dir","ltr"))}">{esc(t["original"])}</span>'
        f'<span class="gloss-term">{esc(t["termo"])}</span></a>'
        for t in terms)
    return f"""
  <section class="block" id="palavras-originais">
    <h2><span class="dot"></span>Palavras do original</h2>
    <div class="gloss-chips">{chips}</div>
  </section>"""

def cross_ref_block(v, cross_refs, verses_by_ref):
    # bloco "Referências cruzadas" na página do versículo (links irmãos: ../slug/)
    refs = cross_refs.get(v["referencia"]) if cross_refs else None
    if not refs:
        return ""
    items = ""
    for r in refs:
        slug = ref_to_slug(r)
        if not slug:
            continue
        rv = verses_by_ref.get(r)
        pt = esc(rv.get("texto_pt", "")) if rv else ""
        items += (f'<a class="result" href="../{slug}/">'
                  f'<span class="kind">Versículo</span><h4>{esc(r)}</h4>'
                  f'<p>{pt}</p></a>')
    if not items:
        return ""
    return f"""
  <section class="block" id="referencias">
    <h2><span class="dot"></span>Referências cruzadas</h2>
    <p class="block-note">Passagens que dialogam com este versículo — seleção curada, em expansão.</p>
    <div class="related-list xref-list">{items}</div>
  </section>"""

def audio_bar():
    # controle de leitura em voz alta (TTS). Começa oculto; app.js revela se o
    # navegador tiver Web Speech API. Lê os parágrafos em português na ordem.
    return ("""
  <div class="audio-bar" data-audio hidden>
    <button type="button" class="abtn" data-audio-play aria-label="Ouvir">🔊 Ouvir</button>
    <button type="button" class="abtn abtn-stop" data-audio-stop aria-label="Parar" hidden>⏹</button>
    <span class="audio-hint">leitura em voz alta</span>
  </div>""")

def verse_stack(v, big=False):
    return f"""
{original_html(v, 4)}
{translit_disclosure(v.get('transliteracao',''), 4)}
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
        # sem onerror inline (CSP estrita): a falha é tratada por app.js via data-fallback
        frame = (f'<div class="frame"><img loading="lazy" alt="{cap}" src="{esc(img)}" '
                 f'data-fallback="manuscript"></div>')
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
def build_verse_page(v, articles_by_slug, prev_v=None, next_v=None, cross_refs=None,
                     verses_by_ref=None, commentary=None, glossary_by_ref=None,
                     places_by_ref=None, red_letters=None, jewish_readings=None):
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
    ch, vs = ref_chvs(v["referencia"])

    # blocos: origem (se houver) e comentário rabínico (link Sefaria).
    # A leitura judaica curada é renderizada por jewish_reading_block (seção canônica).
    blocks = ""
    if v.get("origem","").strip():
        blocks += f"""
  <section class="block" id="origem">
    <h2><span class="dot"></span>Origem e transmissão</h2>
    <p>{esc(v.get('origem',''))}</p>
  </section>"""
    sef = sefaria_url(v["livro"], ch, vs)
    if sef:
        sef_body = (f'      <p>Leia este versículo ao lado dos comentaristas judaicos clássicos — Rashi, Talmud, Midrash, Ibn Ezra — no acervo aberto do Sefaria.</p>\n'
                    f'      <p><a class="ext-link" href="{sef}" target="_blank" rel="noopener">Abrir {esc(v["referencia"])} no Sefaria ↗</a></p>')
        blocks += study_disclosure("rabinico", "Comentário rabínico", sef_body)

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
        is_jesus = red_letters and v["referencia"] in red_letters
        pt_class = "pt pt-jesus" if is_jesus else "pt"
        pt_html = f'<p class="{pt_class}">{esc(v["texto_pt"])}</p>'
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
  {audio_bar()}

  <div class="verse-hero reveal">
{original_html(v, 4)}
{translit_disclosure(v.get('transliteracao',''), 4)}
    {pt_html}
    <p class="src-line">{esc(v.get('contexto',''))}</p>
  </div>

  {specimen_block(v)}
  {commentary_block(v, commentary)}
  {jewish_reading_block(v, jewish_readings or {})}
  {blocks}
  {glossary_terms_block(v, glossary_by_ref, prefix)}
  {places_block(v, places_by_ref, prefix)}
  {cross_ref_block(v, cross_refs, verses_by_ref or {})}
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
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

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
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

# ---------- temas (índice de tópicos) ----------
def topic_articles(topic, articles):
    # artigos relacionados ao tema por correspondência simples de termo (sem acento)
    key = fold(topic["titulo"]).split()[0]
    rel = []
    for a in articles:
        hay = fold(a.get("titulo","") + " " + a.get("resumo","") + " " + a.get("slug",""))
        if key and key in hay:
            rel.append(a)
    return rel

def build_topics_index(topics, topic_refs):
    prefix = "../"
    title = f"Temas de estudo da Bíblia | {SITE_NAME}"
    desc = "Estude a Bíblia por assunto: ansiedade, medo, fé, oração, perdão e mais — versículos curados que abrem a página completa com original e contexto."
    canonical = f"{BASE_URL}/temas/"
    cards = ""
    for t in topics:
        refs = topic_refs.get(t["slug"], [])
        n = len(refs)
        cards += f"""
    <a class="card topic-card" href="{esc(t['slug'])}/">
      <div class="ref-row"><h3><span class="gl">{esc(t.get('icone',''))}</span> {esc(t['titulo'])}</h3></div>
      <p class="pt-mini">{esc(t.get('descricao',''))}</p>
      <span class="topic-count">{n} versículo{'s' if n!=1 else ''}</span>
    </a>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Temas</p>
  <header class="verse-head"><h1>Temas de estudo</h1></header>
  <p class="read" style="color:var(--muted)">Pontos de entrada para quem busca um assunto, não uma referência exata. Cada tema reúne versículos curados; clique para ler cada um no idioma original, com contexto.</p>
  <div class="cards verses">{cards}
  </div>
</main>"""
    out = SITE / "temas" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_topic_page(topic, refs, verses_by_ref, articles):
    prefix = "../../"
    slug = topic["slug"]
    title = f"{topic['titulo']} — versículos e contexto | {SITE_NAME}"
    desc = topic.get("descricao","") or f"Versículos sobre {topic['titulo']} na Bíblia, com original, transliteração e contexto."
    canonical = f"{BASE_URL}/temas/{slug}/"
    jsonld = {"@context":"https://schema.org","@type":"CollectionPage","name":topic["titulo"],
              "inLanguage":"pt-BR","isPartOf":{"@type":"WebSite","name":SITE_NAME,"url":BASE_URL}}
    cards = "".join(verse_result_card(r, verses_by_ref, prefix) for r in refs)
    # artigos para aprofundar
    rels = topic_articles(topic, articles)
    rel_html = ""
    if rels:
        items = "".join(
            f'<a class="result" href="{prefix}artigos/{a["slug"]}/"><span class="kind">Artigo</span><h4>{esc(a["titulo"])}</h4><p>{esc(a.get("resumo",""))}</p></a>'
            for a in rels)
        rel_html = f"""
  <section class="block">
    <h2><span class="dot"></span>Para aprofundar</h2>
    <div class="related-list">{items}</div>
  </section>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="../">Temas</a> · {esc(topic['titulo'])}</p>
  <header class="verse-head">
    <span class="lang-tag lang-hebraico">Tema</span>
    <h1><span class="gl">{esc(topic.get('icone',''))}</span> {esc(topic['titulo'])}</h1>
  </header>
  <p class="read" style="color:var(--muted)">{esc(topic.get('descricao',''))}</p>
  <div class="related-list">{cards}</div>
  {rel_html}
  <p class="backline"><a href="../">← Todos os temas</a></p>
</main>"""
    out = SITE / "temas" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix, jsonld) + nav(prefix) + body + footer(prefix), encoding="utf-8")

# ---------- dicionário (glossário integrado) ----------
def _gloss_orig_html(t, cls_extra=""):
    sc = script_class(t["idioma"], t.get("dir","ltr"))
    d = "rtl" if t.get("dir")=="rtl" else "ltr"
    return f'<p class="gloss-orig {sc}{cls_extra}" dir="{d}">{esc(t["original"])}</p>'

def build_dictionary_index(glossary):
    prefix = "../"
    title = f"Dicionário bíblico — hebraico, grego e aramaico | {SITE_NAME}"
    desc = "Palavras-chave da Bíblia no idioma original (shalom, hesed, logos, ágape, abba e mais) com significado e versículos de exemplo."
    canonical = f"{BASE_URL}/dicionario/"
    sections = ""
    for idi, label in [("hebraico","Hebraico"),("aramaico","Aramaico"),("grego","Grego")]:
        terms = [t for t in glossary if t.get("idioma")==idi]
        if not terms:
            continue
        cards = ""
        for t in terms:
            cards += f"""
    <a class="card gloss-card" href="{esc(t['slug'])}/">
      <div class="ref-row"><h3>{esc(t['termo'])}</h3><span class="lang-tag lang-{esc(t['idioma'])}">{lang_label(t['idioma'])}</span></div>
      {_gloss_orig_html(t)}
      <p class="pt-mini">{esc(t['definicao'])}</p>
    </a>"""
        sections += f"""
  <h2 class="gloss-group">{esc(label)}</h2>
  <div class="cards verses">{cards}
  </div>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Dicionário</p>
  <header class="verse-head"><h1>Dicionário bíblico</h1></header>
  <p class="read" style="color:var(--muted)">Palavras-chave no idioma original, com o sentido por trás da tradução e versículos onde aparecem. Conjunto inicial, em expansão.</p>
  {sections}
</main>"""
    out = SITE / "dicionario" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_dictionary_term_page(t, verses_by_ref, articles):
    prefix = "../../"
    slug = t["slug"]
    title = f"{t['termo']} ({t['translit']}) — significado no original | {SITE_NAME}"
    desc = t["definicao"]
    canonical = f"{BASE_URL}/dicionario/{slug}/"
    jsonld = {"@context":"https://schema.org","@type":"DefinedTerm","name":t["termo"],
              "description":t["definicao"],"inLanguage":"pt-BR",
              "isPartOf":{"@type":"WebSite","name":SITE_NAME,"url":BASE_URL}}
    cards = "".join(verse_result_card(r, verses_by_ref, prefix) for r in t.get("refs",[]))
    # artigos relacionados ao termo (correspondência simples por nome do termo)
    key = fold(t["termo"])
    rels = [a for a in articles if key and key in fold(a.get("titulo","")+" "+a.get("resumo","")+" "+a.get("slug",""))]
    rel_html = ""
    if rels:
        items = "".join(
            f'<a class="result" href="{prefix}artigos/{a["slug"]}/"><span class="kind">Artigo</span><h4>{esc(a["titulo"])}</h4><p>{esc(a.get("resumo",""))}</p></a>'
            for a in rels)
        rel_html = f"""
  <section class="block">
    <h2><span class="dot"></span>Para aprofundar</h2>
    <div class="related-list">{items}</div>
  </section>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="../">Dicionário</a> · {esc(t['termo'])}</p>
  <header class="verse-head">
    <span class="lang-tag lang-{esc(t['idioma'])}">{lang_label(t['idioma'])}</span>
    <h1>{esc(t['termo'])}</h1>
  </header>
  <div class="verse-hero gloss-hero">
    {_gloss_orig_html(t, " gloss-big")}
    <p class="translit">{esc(t['translit'])}</p>
    <p class="pt">{esc(t['definicao'])}</p>
  </div>
  <section class="block">
    <h2><span class="dot"></span>Onde aparece</h2>
    <div class="related-list">{cards}</div>
  </section>
  {rel_html}
  <p class="backline"><a href="../">← Todo o dicionário</a></p>
</main>"""
    out = SITE / "dicionario" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix, jsonld) + nav(prefix) + body + footer(prefix), encoding="utf-8")

# ---------- mapas (atlas de lugares bíblicos, estático/offline) ----------
# Ordem das regiões na página (norte→sul / leste→oeste, didática).
PLACE_REGIONS = ["Mesopotâmia e origens", "Egito e o Êxodo", "Terra de Israel",
                 "Mundo do Novo Testamento"]

def build_atlas_index(places):
    prefix = "../"
    title = f"Atlas bíblico — lugares da Bíblia | {SITE_NAME}"
    desc = "Lugares da Bíblia agrupados por região: Mesopotâmia, Egito, Terra de Israel e o mundo do Novo Testamento — com versículos e localização."
    canonical = f"{BASE_URL}/mapas/"
    by_region = defaultdict(list)
    for p in places:
        by_region[p.get("regiao","Outros")].append(p)
    regions = PLACE_REGIONS + [r for r in by_region if r not in PLACE_REGIONS]
    sections = ""
    for r in regions:
        items = by_region.get(r, [])
        if not items:
            continue
        cards = ""
        for p in items:
            cards += f"""
    <a class="card place-card" href="{esc(p['slug'])}/">
      <div class="ref-row"><h3>{esc(p['nome'])}</h3><span class="place-type">{esc(p.get('tipo',''))}</span></div>
      <p class="pt-mini">{esc(p.get('descricao',''))}</p>
    </a>"""
        sections += f"""
  <h2 class="place-group">{esc(r)}</h2>
  <div class="cards verses">{cards}
  </div>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Mapas</p>
  <header class="verse-head"><h1>Atlas bíblico</h1></header>
  <p class="read" style="color:var(--muted)">Os lugares onde a história aconteceu, por região. Cada lugar abre com os versículos em que aparece e um link para o mapa. Conjunto inicial, em expansão.</p>
  {sections}
</main>"""
    out = SITE / "mapas" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_place_page(p, verses_by_ref):
    prefix = "../../"
    slug = p["slug"]
    title = f"{p['nome']} na Bíblia — versículos e localização | {SITE_NAME}"
    desc = p.get("descricao","")
    canonical = f"{BASE_URL}/mapas/{slug}/"
    jsonld = {"@context":"https://schema.org","@type":"Place","name":p["nome"],
              "description":p.get("descricao",""),
              "geo":{"@type":"GeoCoordinates","latitude":p.get("lat"),"longitude":p.get("lon")}}
    cards = "".join(verse_result_card(r, verses_by_ref, prefix) for r in p.get("refs",[]))
    osm = osm_url(p.get("lat"), p.get("lon")) if p.get("lat") is not None else ""
    map_html = (f'<p class="read"><a class="ext-link" href="{osm}" target="_blank" rel="noopener">Ver no mapa (OpenStreetMap) ↗</a></p>'
                if osm else "")
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="../">Mapas</a> · {esc(p['nome'])}</p>
  <header class="verse-head">
    <span class="lang-tag lang-hebraico">{esc(p.get('tipo','Lugar'))}</span>
    <h1>{esc(p['nome'])}</h1>
  </header>
  <p class="read" style="color:var(--muted)">{esc(p.get('descricao',''))}</p>
  {map_html}
  <section class="block">
    <h2><span class="dot"></span>Onde aparece</h2>
    <div class="related-list">{cards}</div>
  </section>
  <p class="backline"><a href="../">← Todo o atlas</a></p>
</main>"""
    out = SITE / "mapas" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix, jsonld) + nav(prefix) + body + footer(prefix), encoding="utf-8")

# ---------- planos de leitura (progresso no localStorage) ----------
def build_plans_index(plans):
    prefix = "../"
    title = f"Planos de leitura da Bíblia | {SITE_NAME}"
    desc = "Planos de leitura para criar um hábito: o Evangelho de João em 21 dias, Provérbios em 31 dias e a história da salvação em 10 dias."
    canonical = f"{BASE_URL}/planos/"
    cards = ""
    for pl in plans:
        n = len(pl.get("dias", []))
        cards += f"""
    <a class="card plan-card" href="{esc(pl['slug'])}/">
      <div class="ref-row"><h3>{esc(pl['titulo'])}</h3><span class="place-type">{n} dias</span></div>
      <p class="pt-mini">{esc(pl.get('descricao',''))}</p>
    </a>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · Planos</p>
  <header class="verse-head"><h1>Planos de leitura</h1></header>
  <p class="read" style="color:var(--muted)">Escolha um plano e marque cada dia conforme avança. Seu progresso fica salvo <b>neste navegador</b> (offline, sem servidor).</p>
  <div class="cards verses">{cards}
  </div>
</main>"""
    out = SITE / "planos" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_plan_page(pl):
    prefix = "../../"
    slug = pl["slug"]
    title = f"{pl['titulo']} | {SITE_NAME}"
    desc = pl.get("descricao","")
    canonical = f"{BASE_URL}/planos/{slug}/"
    dias = pl.get("dias", [])
    rows = ""
    for i, day in enumerate(dias):
        chs = " · ".join(chapter_link(prefix, c) for c in day)
        rows += f"""
      <li class="plan-day">
        <label class="plan-check"><input type="checkbox" data-day="{i}"> <span>Dia {i+1}</span></label>
        <div class="plan-chapters">{chs}</div>
      </li>"""
    body = f"""
<main id="main" class="wrap verse-page">
  <p class="crumb"><a href="{prefix}index.html">Início</a> · <a href="../">Planos</a> · {esc(pl['titulo'])}</p>
  <header class="verse-head"><h1>{esc(pl['titulo'])}</h1></header>
  <p class="read" style="color:var(--muted)">{esc(pl.get('descricao',''))}</p>
  <div class="plan" data-plan="{esc(slug)}">
    <div class="plan-progress">
      <div class="plan-bar-track"><div class="plan-bar" data-plan-bar></div></div>
      <span class="plan-count" data-plan-count>0/{len(dias)}</span>
      <button type="button" class="btn ghost plan-reset" data-plan-reset>Recomeçar</button>
    </div>
    <ol class="plan-days">{rows}
    </ol>
  </div>
  <p class="backline"><a href="../">← Todos os planos</a></p>
</main>"""
    out = SITE / "planos" / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

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
</main>"""
    out = SITE / "ler" / book_slug(livro) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_chapter_page(livro, ch, verses, n_chapters, order, red_letters=None):
    prefix = "../../../"
    bslug = book_slug(livro)
    title = f"{livro} {ch} — original, transliteração e tradução | {SITE_NAME}"
    desc = f"{livro} {ch}: capítulo completo no idioma original, com transliteração e tradução Almeida 1911."
    canonical = f"{BASE_URL}/ler/{bslug}/{ch}/"
    idioma = verses[0].get("idioma","hebraico") if verses else "hebraico"
    rows = ""
    for v in verses:
        _, vs = ref_chvs(v["referencia"])
        is_jesus = red_letters and v["referencia"] in red_letters
        pt_class = "pt pt-jesus" if is_jesus else "pt"
        pt_text = esc(v.get("texto_pt",""))
        pt = f'<p class="{pt_class}">{pt_text}</p>' if pt_text else '<p class="pt pt-missing">—</p>'
        rows += f"""
    <div class="ch-verse" id="v{vs}" data-ref="{esc(v['referencia'])}">
      <a class="ch-num" href="{prefix}versiculos/{esc(v['slug'])}/" aria-label="Versículo {vs}">{vs}</a>
      <div class="ch-body">
{original_html(v, 8)}
{translit_disclosure(v.get('transliteracao',''), 8)}
        {pt}
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
  {audio_bar()}
  {book_jump(prefix, order, livro)}
  <div class="chapter">{rows}
  </div>
  <nav class="pager" aria-label="Folhear capítulos">{prev_html}{next_html}</nav>
  <p class="backline"><a href="../">← Todos os capítulos de {esc(livro)}</a></p>
</main>"""
    out = SITE / "ler" / bslug / str(ch) / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_search_index(verses, articles, topics, glossary=None, places=None, plans=None):
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
                      "url":f"temas/{t['slug']}/","k":(t["titulo"]+" "+t.get("descricao","")).lower()})
    for g in (glossary or []):
        index.append({"t":"Termo","titulo":g["termo"],"desc":g.get("definicao",""),
                      "url":f"dicionario/{g['slug']}/",
                      "k":(g["termo"]+" "+g.get("translit","")+" "+g.get("original","")+" "+g.get("definicao","")).lower()})
    for p in (places or []):
        index.append({"t":"Lugar","titulo":p["nome"],"desc":p.get("descricao",""),
                      "url":f"mapas/{p['slug']}/",
                      "k":(p["nome"]+" "+p.get("tipo","")+" "+p.get("regiao","")+" "+p.get("descricao","")).lower()})
    for pl in (plans or []):
        index.append({"t":"Plano","titulo":pl["titulo"],"desc":pl.get("descricao",""),
                      "url":f"planos/{pl['slug']}/",
                      "k":(pl["titulo"]+" "+pl.get("descricao","")).lower()})
    (DATA / "search-index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return len(index)

def build_home(topics, verses, articles, sources, order, struct, topic_refs=None):
    prefix = ""
    topic_refs = topic_refs or {}
    title = f"{SITE_NAME} — a Bíblia com os idiomas originais, manuscritos e fontes"
    desc = "Leia cada versículo no idioma original (hebraico, grego, aramaico), com tradução de domínio público, foto do manuscrito quando há, e comentário rabínico ou explicação de origem."
    canonical = BASE_URL + "/"

    featured = next(v for v in verses if v["slug"]=="genesis-1-1")
    fsc = script_class(featured["idioma"], featured.get("dir","ltr"))

    # temas (apontam para as páginas de tema reais)
    chips = "".join(
        f'<a class="chip" href="temas/{esc(t["slug"])}/"><span class="gl">{esc(t["icone"])}</span>{esc(t["titulo"])}</a>'
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
      <input id="q" type="search" placeholder="Buscar: Salmo 23, shalom, &quot;no princípio&quot;, logos…" autocomplete="off" aria-label="Buscar">
    </div>
    <div class="search-filters" role="group" aria-label="Filtrar resultados da busca">
      <button type="button" class="sf on" data-filter="all">Tudo</button>
      <button type="button" class="sf" data-filter="Versículo">Versículos</button>
      <button type="button" class="sf" data-filter="Artigo">Artigos</button>
      <button type="button" class="sf" data-filter="Tema">Temas</button>
    </div>
    <div id="results" class="search-results"></div>
    <a id="continue-read" class="continue-read" href="#" hidden></a>
    <div class="quick-actions">
      <button type="button" id="random-verse" class="btn ghost">🕊️ Um versículo para você</button>
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
      <p>Pontos de entrada para quem busca um assunto, não uma referência exata. Cada tema reúne versículos curados.</p>
    </div>
    <div class="chips wrap">{chips}
    </div>
    <p class="read" style="text-align:center;margin-top:18px"><a href="temas/">Ver todos os temas →</a></p>
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
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_offline_page():
    prefix = "../"
    title = f"Sem conexão | {SITE_NAME}"
    body = """
<main id="main" class="wrap verse-page" style="text-align:center">
  <header class="verse-head" style="margin-top:30px">
    <span class="lang-tag lang-hebraico">offline</span>
    <h1>Você está sem conexão</h1>
  </header>
  <p class="read" style="color:var(--muted)">Esta página ainda não foi salva para leitura offline. As páginas que você
  já abriu continuam disponíveis sem internet. Reconecte para carregar novos trechos.</p>
  <p class="backline" style="text-align:center"><a href="../index.html">← Início (salvo offline)</a></p>
</main>"""
    out = SITE / "offline" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head(title, "Sem conexão.", BASE_URL+"/offline/", prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_sw_js():
    # Service worker (modo offline). Pré-cacheia o app-shell e guarda as páginas
    # visitadas. O nome do cache leva ASSET_VER: cada deploy invalida o cache antigo.
    js = r"""/* Service worker do Bíblia em Contexto — gerado por build.py. Não editar à mão. */
var VERSION = '__VER__';
var SHELL_CACHE = 'bec-shell-' + VERSION;
var PAGE_CACHE  = 'bec-pages-'  + VERSION;
// app-shell mínimo (relativo ao escopo do SW = raiz do site)
var SHELL = [
  './',
  './index.html',
  './offline/',
  './manifest.webmanifest',
  './assets/styles.css?v=' + VERSION,
  './assets/app.js?v=' + VERSION,
  './assets/study.js?v=' + VERSION,
  './data/hebrew-lexicon.json'
];

self.addEventListener('install', function(e){
  e.waitUntil(
    caches.open(SHELL_CACHE).then(function(c){
      // addAll falha tudo se um item falhar; tolera ausências com Promise.allSettled-like
      return Promise.all(SHELL.map(function(u){
        return c.add(u).catch(function(){});
      }));
    }).then(function(){ return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function(e){
  e.waitUntil(
    caches.keys().then(function(keys){
      return Promise.all(keys.map(function(k){
        if(k !== SHELL_CACHE && k !== PAGE_CACHE) return caches.delete(k);
      }));
    }).then(function(){ return self.clients.claim(); })
  );
});

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;
  var url = new URL(req.url);
  // só tratamos requisições da mesma origem; terceiros (fontes/imagens) passam direto
  if(url.origin !== self.location.origin) return;

  // navegações (HTML): rede primeiro, cai para cache e, por fim, página offline
  if(req.mode === 'navigate'){
    e.respondWith(
      fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(PAGE_CACHE).then(function(c){ c.put(req, copy); });
        return res;
      }).catch(function(){
        return caches.match(req).then(function(hit){
          return hit || caches.match('./offline/') || caches.match('./index.html');
        });
      })
    );
    return;
  }

  // assets versionados (?v=) são imutáveis: cache primeiro
  if(url.search.indexOf('v=') > -1){
    e.respondWith(
      caches.match(req).then(function(hit){
        return hit || fetch(req).then(function(res){
          var copy = res.clone();
          caches.open(SHELL_CACHE).then(function(c){ c.put(req, copy); });
          return res;
        });
      })
    );
    return;
  }

  // demais (json de dados, imagens locais): stale-while-revalidate
  e.respondWith(
    caches.match(req).then(function(hit){
      var net = fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(PAGE_CACHE).then(function(c){ c.put(req, copy); });
        return res;
      }).catch(function(){ return hit; });
      return hit || net;
    })
  );
});
"""
    js = js.replace("__VER__", ASSET_VER)
    (SITE / "sw.js").write_text(js, encoding="utf-8")

def build_app_js():
    js = r"""// home: menu + busca local (índice embutido em window.__INDEX__)
document.addEventListener('click',function(e){
  if(e.target.closest('[data-menu]')){document.querySelector('[data-links]').classList.toggle('open');}
});
(function(){
  var q=document.getElementById('q'), out=document.getElementById('results');
  if(!q||!out) return;
  var filterBar=document.querySelector('.search-filters');
  var curFilter='all';
  function escHtml(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  // busca sem acento: "genesis" encontra "Gênesis", "joao" encontra "João".
  function fold(s){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
  // índice carregado sob demanda (arquivo externo, não embutido na página)
  var idxPromise=null;
  function getIndex(){
    if(!idxPromise){
      idxPromise=fetch('data/search-index.json').then(function(r){return r.json();}).then(function(data){
        data.forEach(function(i){i.kf=fold(i.k);});  // chave sem acento (1x)
        return data;
      });
    }
    return idxPromise;
  }
  function render(IDX, term){
    out.innerHTML='';
    term=fold((term||'').trim().toLowerCase());
    if(!term) return;
    // casa por tokens: cada palavra digitada precisa aparecer na chave.
    // assim "salmo 23", "salmos 23" e "23:1" encontram o versículo direto
    // (e não só os artigos relacionados).
    // frases entre "aspas" casam contíguas; tokens soltos em qualquer posição
    var phrases=[], rest=term;
    rest=rest.replace(/"([^"]+)"/g, function(_, p){ phrases.push(p.trim()); return ' '; });
    phrases=phrases.filter(Boolean);
    var terms=rest.split(/\s+/).filter(Boolean);
    if(!phrases.length && !terms.length) return;
    var res=IDX.filter(function(i){
      if(curFilter!=='all' && i.t!==curFilter) return false;
      var okP=phrases.every(function(p){return i.kf.indexOf(p)>-1;});
      var okT=terms.every(function(t){return i.kf.indexOf(t)>-1;});
      return okP && okT;
    });
    // quem casa o termo inteiro e contíguo vem primeiro (ordenação estável)
    res.sort(function(a,b){return (b.kf.indexOf(term)>-1)-(a.kf.indexOf(term)>-1);});
    var total=res.length;
    res=res.slice(0,12);
    if(!res.length){out.innerHTML='<p class="empty">Nada encontrado. Tente “Salmo 23”, “shalom”, “logos” ou “aramaico”.</p>';return;}
    var hd=document.createElement('p'); hd.className='search-count';
    hd.textContent=total+(total===1?' resultado':' resultados')+(total>12?' (mostrando 12)':'');
    out.appendChild(hd);
    res.forEach(function(i){
      var a=document.createElement('a');a.className='result';a.href=i.url;
      a.innerHTML='<span class="kind">'+escHtml(i.t)+'</span><h4>'+escHtml(i.titulo)+'</h4><p>'+escHtml(i.desc)+'</p>';
      out.appendChild(a);
    });
  }
  q.addEventListener('input',function(e){
    var val=e.target.value;
    getIndex().then(function(IDX){
      if(q.value!==val) return;  // ignora respostas obsoletas
      render(IDX, val);
    }).catch(function(){ out.innerHTML='<p class="empty">Não foi possível carregar a busca. Recarregue a página.</p>'; });
  });
  if(filterBar){
    filterBar.addEventListener('click', function(e){
      var b=e.target.closest && e.target.closest('.sf'); if(!b) return;
      curFilter=b.getAttribute('data-filter')||'all';
      filterBar.querySelectorAll('.sf').forEach(function(x){ x.classList.toggle('on', x===b); });
      var val=q.value;
      if(val.trim()) getIndex().then(function(IDX){ render(IDX, val); }).catch(function(){});
    });
  }
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

// ferramentas de leitura: tamanho da fonte, modo noturno, continuar lendo, versículo para meditar
(function(){
  var d=document.documentElement;
  function applyFont(i){ d.classList.remove('fs-0','fs-1','fs-2','fs-3'); d.classList.add('fs-'+i); try{localStorage.setItem('bec.fontscale',i);}catch(e){} }
  function curFont(){ var f=parseInt(localStorage.getItem('bec.fontscale'),10); return isNaN(f)?1:f; }
  function setTheme(dark){ d.classList.toggle('dark',dark); try{localStorage.setItem('bec.theme',dark?'dark':'light');}catch(e){} }
  document.addEventListener('click',function(e){
    var b=e.target.closest && e.target.closest('[data-rt]'); if(!b) return;
    var rt=b.getAttribute('data-rt');
    if(rt==='font-inc') applyFont(Math.min(3,curFont()+1));
    else if(rt==='font-dec') applyFont(Math.max(0,curFont()-1));
    else if(rt==='theme') setTheme(!d.classList.contains('dark'));
  });
  // seletor "Ir para livro": navega ao escolher outro livro
  document.addEventListener('change',function(e){
    var s=e.target.closest && e.target.closest('.book-jump');
    if(s && s.value) location.href=s.value;
  });

  // continuar lendo: guarda a última leitura (capítulo/versículo) e mostra na home
  var h1=document.querySelector('.verse-head h1');
  var reading=document.querySelector('.ch-verse[data-ref], .verse-cont[data-ref]');
  if(reading && h1){
    try{ localStorage.setItem('bec.lastRead', JSON.stringify({url:location.pathname, label:h1.textContent.trim()})); }catch(e){}
  }
  var cont=document.getElementById('continue-read');
  if(cont){
    try{ var lr=JSON.parse(localStorage.getItem('bec.lastRead')||'null');
      if(lr&&lr.url){ cont.href=lr.url; cont.textContent='▶ Continuar de onde parei: '+lr.label; cont.hidden=false; } }catch(e){}
  }

  // versículo para meditar (aleatório — sem dado/sorteio)
  var rb=document.getElementById('random-verse');
  if(rb){
    rb.addEventListener('click',function(){
      rb.disabled=true;
      fetch('data/random.json').then(function(r){return r.json();}).then(function(list){
        if(list && list.length){ var s=list[Math.floor(Math.random()*list.length)]; location.href='versiculos/'+s+'/'; }
        else rb.disabled=false;
      }).catch(function(){ rb.disabled=false; });
    });
  }
})();

// ordenar livros: bíblica / alfabética / cronológica (persistido em bec.bookorder)
(function(){
  var lists=document.querySelectorAll('[data-booklist]'); if(!lists.length) return;
  function apply(mode){
    lists.forEach(function(list){
      var cards=[].slice.call(list.querySelectorAll('.book-card'));
      cards.sort(function(a,b){
        if(mode==='alpha') return (a.getAttribute('data-name')||'').localeCompare(b.getAttribute('data-name')||'');
        if(mode==='chron') return (+a.getAttribute('data-chron'))-(+b.getAttribute('data-chron'));
        return (+a.getAttribute('data-pos'))-(+b.getAttribute('data-pos'));
      });
      cards.forEach(function(c){ list.appendChild(c); });
    });
    document.querySelectorAll('.order-toggle .ot').forEach(function(b){ b.classList.toggle('on', b.getAttribute('data-sort')===mode); });
  }
  document.addEventListener('click', function(e){
    var b=e.target.closest && e.target.closest('.order-toggle .ot'); if(!b) return;
    var m=b.getAttribute('data-sort'); try{ localStorage.setItem('bec.bookorder', m); }catch(e){}
    apply(m);
  });
  var saved='bib'; try{ saved=localStorage.getItem('bec.bookorder')||'bib'; }catch(e){}
  if(saved!=='bib') apply(saved);
})();

// imagens de manuscrito que falham → placeholder (sem onerror inline, por causa da CSP)
document.addEventListener('error', function(e){
  var img=e.target;
  if(!img || img.tagName!=='IMG' || img.getAttribute('data-fallback')!=='manuscript') return;
  var frame=img.closest && img.closest('.frame');
  if(frame) frame.innerHTML='<div class="ph"><b>✶</b>Imagem indisponível no momento. Veja no acervo da fonte.</div>';
}, true);

// modo offline: registra o service worker (escopo = raiz do site, derivado do src deste script)
(function(){
  if(!('serviceWorker' in navigator)) return;
  var s=document.currentScript;
  if(!s){ var ss=document.querySelectorAll('script[src]'); for(var i=0;i<ss.length;i++){ if(/assets\/app\.js/.test(ss[i].src)){ s=ss[i]; break; } } }
  if(!s) return;
  var base=s.src.replace(/assets\/app\.js.*$/, '');
  window.addEventListener('load', function(){
    navigator.serviceWorker.register(base+'sw.js', {scope: base}).catch(function(){});
  });
})();

// áudio: ler o texto em português em voz alta (Web Speech API, pt-BR; sem servidor)
(function(){
  var bar=document.querySelector('[data-audio]');
  if(!bar || !('speechSynthesis' in window) || typeof SpeechSynthesisUtterance==='undefined') return;
  // alvos: parágrafos PT do capítulo ou do versículo (na ordem de leitura)
  var nodes=[].slice.call(document.querySelectorAll('.chapter .ch-verse .pt, .verse-cont .verse-hero .pt'))
                .filter(function(p){ var t=(p.textContent||'').trim(); return t && t!=='—'; });
  if(!nodes.length) return;
  bar.hidden=false;
  var playBtn=bar.querySelector('[data-audio-play]'),
      stopBtn=bar.querySelector('[data-audio-stop]');
  var idx=0, speaking=false, paused=false;
  function clearHi(){ nodes.forEach(function(n){ n.classList.remove('tts-current'); }); }
  function addPausesForProsody(text){
    return text
      .replace(/([.!?;])\s+/g, '$1  ')
      .replace(/([,:])\s+/g, '$1 ');
  }
  function setBtn(state){
    // state: 'play' | 'pause' | 'idle'
    if(state==='idle'){ playBtn.textContent='🔊 Ouvir'; playBtn.setAttribute('aria-label','Ouvir'); if(stopBtn) stopBtn.hidden=true; }
    else if(state==='pause'){ playBtn.textContent='⏸ Pausar'; playBtn.setAttribute('aria-label','Pausar'); if(stopBtn) stopBtn.hidden=false; }
    else { playBtn.textContent='▶ Continuar'; playBtn.setAttribute('aria-label','Continuar'); if(stopBtn) stopBtn.hidden=false; }
  }
  function speakFrom(i){
    if(i>=nodes.length){ stop(); return; }
    idx=i;
    var el=nodes[i];
    clearHi(); el.classList.add('tts-current');
    try{ el.scrollIntoView({block:'center', behavior:'smooth'}); }catch(e){}
    var text=(el.textContent||'').trim();
    text=addPausesForProsody(text);
    var u=new SpeechSynthesisUtterance(text);
    u.lang='pt-BR'; u.rate=0.95; u.pitch=1.1; u.volume=0.9;
    u.onend=function(){ if(speaking && !paused) speakFrom(i+1); };
    u.onerror=function(){ stop(); };
    speechSynthesis.speak(u);
  }
  function stop(){ speaking=false; paused=false; try{ speechSynthesis.cancel(); }catch(e){} clearHi(); setBtn('idle'); }
  function start(){ speaking=true; paused=false; setBtn('pause'); speakFrom(idx<nodes.length?idx:0); }
  playBtn.addEventListener('click', function(){
    if(!speaking){ start(); }
    else if(!paused){ paused=true; try{ speechSynthesis.pause(); }catch(e){} setBtn('play'); }
    else { paused=false; try{ speechSynthesis.resume(); }catch(e){} setBtn('pause'); }
  });
  if(stopBtn) stopBtn.addEventListener('click', stop);
  // segurança: cancela a fala ao sair da página
  window.addEventListener('beforeunload', function(){ try{ speechSynthesis.cancel(); }catch(e){} });
})();

// planos de leitura: progresso por dia salvo no localStorage (bec.plan.<slug>)
(function(){
  var root=document.querySelector('[data-plan]'); if(!root) return;
  var slug=root.getAttribute('data-plan'), key='bec.plan.'+slug;
  var boxes=[].slice.call(root.querySelectorAll('input[data-day]'));
  var bar=root.querySelector('[data-plan-bar]'),
      count=root.querySelector('[data-plan-count]'),
      reset=root.querySelector('[data-plan-reset]');
  function load(){ try{ return JSON.parse(localStorage.getItem(key)||'{}'); }catch(e){ return {}; } }
  function save(o){ try{ localStorage.setItem(key, JSON.stringify(o)); }catch(e){} }
  function refresh(){
    var st=load(), done=0;
    boxes.forEach(function(b){
      var d=b.getAttribute('data-day'), on=!!st[d];
      b.checked=on; if(on) done++;
      var li=b.closest('.plan-day'); if(li) li.classList.toggle('done', on);
    });
    var pct=boxes.length?Math.round(done/boxes.length*100):0;
    if(bar) bar.style.width=pct+'%';
    if(count) count.textContent=done+'/'+boxes.length;
  }
  root.addEventListener('change', function(e){
    var b=e.target.closest && e.target.closest('input[data-day]'); if(!b) return;
    var st=load(), d=b.getAttribute('data-day');
    if(b.checked) st[d]=1; else delete st[d];
    save(st); refresh();
  });
  if(reset) reset.addEventListener('click', function(){ save({}); refresh(); });
  refresh();
})();

// ---------- Hebraico palavra-a-palavra: significado + gramática (toque/hover) ----------
(function(){
  var hw=document.querySelector('.hw'); if(!hw) return;  // só em páginas com hebraico
  // base do site (resolve data/ a partir do <script src=".../assets/app.js">)
  function siteBase(){
    var s=document.querySelector('script[src*="assets/app.js"]');
    var src=s?s.getAttribute('src'):'';
    return src.replace(/assets\/app\.js.*$/,'');
  }
  var BASE=siteBase();
  // léxico (significados PT) carregado uma vez, sob demanda, e cacheado
  var lexPromise=null;
  function getLex(){
    if(!lexPromise){
      lexPromise=fetch(BASE+'data/hebrew-lexicon.json').then(function(r){return r.json();}).catch(function(){return {};});
    }
    return lexPromise;
  }
  // ---- decodificador de morfologia OSHM -> português (cobre toda palavra) ----
  var POS={A:'adjetivo',C:'conjunção',D:'advérbio',N:'substantivo',P:'pronome',
    R:'preposição',S:'sufixo',T:'partícula',V:'verbo'};
  var GEN={m:'masculino',f:'feminino',c:'comum',b:'masc./fem.'};
  var NUM={s:'singular',p:'plural',d:'dual'};
  var STATE={a:'absoluto',c:'construto',d:'determinado'};
  var NTYPE={c:'comum',g:'gentílico',p:'próprio'};
  var PTYPE={d:'demonstrativo',f:'indefinido',i:'interrogativo',p:'pessoal',r:'relativo'};
  var TTYPE={a:'de afirmação',d:'artigo definido',e:'de exortação',i:'interrogativa',
    j:'interjeição',m:'demonstrativa',n:'de negação',o:'marcador de objeto direto',r:'relativa'};
  var STEM={q:'Qal',N:'Nifal',p:'Piel',P:'Pual',h:'Hifil',H:'Hofal',t:'Hitpael',
    Q:'Qal passivo',o:'Polel',O:'Polal',r:'Hitpolel',m:'Poel',M:'Poal',l:'Pilpel',
    L:'Polpal',f:'Hitpalpel',D:'Nitpael',c:'Tifil',v:'Hishtafel'};
  var ASPECT={p:'perfeito',q:'perfeito sequencial',i:'imperfeito',w:'imperfeito sequencial (wayyiqtol)',
    h:'coortativo',j:'jussivo',v:'imperativo',r:'particípio ativo',s:'particípio passivo',
    a:'infinitivo absoluto',c:'infinitivo construto'};
  var PERSON={'1':'1ª pessoa','2':'2ª pessoa','3':'3ª pessoa'};
  function decodeOne(seg){
    if(!seg) return '';
    var pos=seg.charAt(0), rest=seg.slice(1), parts=[POS[pos]||pos];
    if(pos==='N'){
      if(NTYPE[rest.charAt(0)]){ if(rest.charAt(0)!=='c') parts.push(NTYPE[rest.charAt(0)]); rest=rest.slice(1); }
      if(GEN[rest.charAt(0)]) parts.push(GEN[rest.charAt(0)]);
      if(NUM[rest.charAt(1)]) parts.push(NUM[rest.charAt(1)]);
      if(STATE[rest.charAt(2)]) parts.push(STATE[rest.charAt(2)]);
    } else if(pos==='V'){
      parts.push(STEM[rest.charAt(0)]||rest.charAt(0));
      parts.push(ASPECT[rest.charAt(1)]||rest.charAt(1));
      var r2=rest.slice(2);
      // particípio/infinitivo: gênero/número/estado; finitos: pessoa/gênero/número
      if('rsac'.indexOf(rest.charAt(1))>-1){
        if(GEN[r2.charAt(0)]) parts.push(GEN[r2.charAt(0)]);
        if(NUM[r2.charAt(1)]) parts.push(NUM[r2.charAt(1)]);
        if(STATE[r2.charAt(2)]) parts.push(STATE[r2.charAt(2)]);
      } else {
        if(PERSON[r2.charAt(0)]) parts.push(PERSON[r2.charAt(0)]);
        if(GEN[r2.charAt(1)]) parts.push(GEN[r2.charAt(1)]);
        if(NUM[r2.charAt(2)]) parts.push(NUM[r2.charAt(2)]);
      }
    } else if(pos==='A'){
      var t=rest.charAt(0), off=0;
      if(t==='c'){parts.push('numeral cardinal');off=1;} else if(t==='o'){parts.push('numeral ordinal');off=1;}
      else if(t==='g'){parts.push('gentílico');off=1;}
      var ra=rest.slice(off);
      if(GEN[ra.charAt(0)]) parts.push(GEN[ra.charAt(0)]);
      if(NUM[ra.charAt(1)]) parts.push(NUM[ra.charAt(1)]);
      if(STATE[ra.charAt(2)]) parts.push(STATE[ra.charAt(2)]);
    } else if(pos==='P'){
      if(PTYPE[rest.charAt(0)]){ parts.push(PTYPE[rest.charAt(0)]); rest=rest.slice(1); }
      if(PERSON[rest.charAt(0)]) parts.push(PERSON[rest.charAt(0)]);
      if(GEN[rest.charAt(1)]) parts.push(GEN[rest.charAt(1)]);
      if(NUM[rest.charAt(2)]) parts.push(NUM[rest.charAt(2)]);
    } else if(pos==='S'){
      if(rest.charAt(0)==='p'){ rest=rest.slice(1); parts=['sufixo pronominal'];
        if(PERSON[rest.charAt(0)]) parts.push(PERSON[rest.charAt(0)]);
        if(GEN[rest.charAt(1)]) parts.push(GEN[rest.charAt(1)]);
        if(NUM[rest.charAt(2)]) parts.push(NUM[rest.charAt(2)]);
      } else if(rest.charAt(0)==='d'){ parts=['hê direcional (“para”)']; }
    } else if(pos==='T'){
      if(TTYPE[rest.charAt(0)]) parts.push(TTYPE[rest.charAt(0)]);
    }
    return parts.filter(Boolean).join(' · ');
  }
  function decodeMorph(code){
    if(!code) return '';
    code=code.replace(/^[HA]/,'');  // tira o prefixo de idioma
    return code.split('/').map(decodeOne).filter(Boolean).join('  +  ');
  }
  function headLemma(l){
    var segs=(l||'').split('/');
    for(var k=segs.length-1;k>=0;k--){ var m=segs[k].match(/(\d+)/); if(m) return m[1]; }
    return null;
  }
  // ---- popover ----
  var pop=null, openFor=null;
  function buildPop(el, lex){
    var word=el.textContent, lemma=el.getAttribute('data-l'), morph=el.getAttribute('data-m');
    var head=headLemma(lemma), entry=head?lex[head]:null;
    var html='<div class="hw-pop-word" dir="rtl" lang="he">'+word+'</div>';
    if(entry&&entry.tr) html+='<div class="hw-pop-tr">'+entry.tr+'</div>';
    if(entry&&entry.pt) html+='<div class="hw-pop-gloss">'+entry.pt+'</div>';
    else html+='<div class="hw-pop-gloss hw-pop-soft">significado em curadoria</div>';
    var g=decodeMorph(morph);
    if(g) html+='<div class="hw-pop-morph">'+g+'</div>';
    if(head) html+='<div class="hw-pop-foot">Strong H'+head+'</div>';
    return html;
  }
  function showPop(el){
    getLex().then(function(lex){
      if(openFor!==el) return;  // já fechou/mudou
      closePop2();
      pop=document.createElement('div'); pop.className='hw-pop'; pop.setAttribute('role','tooltip');
      pop.innerHTML=buildPop(el, lex);
      document.body.appendChild(pop);
      position(el);
    });
  }
  function closePop2(){ if(pop){ pop.remove(); pop=null; } }
  function position(el){
    if(!pop) return;
    var r=el.getBoundingClientRect(), pr=pop.getBoundingClientRect();
    var top=r.bottom+window.scrollY+6, left=r.left+window.scrollX+(r.width/2)-(pr.width/2);
    left=Math.max(8, Math.min(left, window.scrollX+document.documentElement.clientWidth-pr.width-8));
    if(r.bottom+pr.height+12>document.documentElement.clientHeight) top=r.top+window.scrollY-pr.height-6;
    pop.style.top=top+'px'; pop.style.left=left+'px';
  }
  var hoverCapable=!!(window.matchMedia && window.matchMedia('(hover: hover)').matches);
  // toque/click: no touch alterna o popover; no desktop o hover já cuida disso
  // (clicar com mouse fecharia o que o hover abriu) — só fechamos ao clicar fora.
  document.addEventListener('click', function(e){
    var el=e.target.closest && e.target.closest('.hw');
    if(!el){ if(openFor){ openFor=null; closePop2(); } return; }
    if(hoverCapable) return;                                  // desktop: hover comanda
    if(document.body.classList.contains('hl-mode')) return;   // caneta: deixa marcar
    if(openFor===el){ openFor=null; closePop2(); return; }
    openFor=el; showPop(el);
  });
  // hover (apenas onde há mouse de verdade)
  if(hoverCapable){
    var hoverEl=null;
    document.addEventListener('mouseover', function(e){
      var el=e.target.closest && e.target.closest('.hw'); if(!el||el===hoverEl) return;
      if(document.body.classList.contains('hl-mode')) return;
      hoverEl=el; if(openFor && openFor!==el){ openFor=null; closePop2(); }
      if(!openFor){ openFor=el; showPop(el); }
    });
    document.addEventListener('mouseout', function(e){
      var el=e.target.closest && e.target.closest('.hw'); if(!el) return;
      var to=e.relatedTarget;
      if(to && to.closest && (to.closest('.hw')===el || to.closest('.hw-pop'))) return;
      hoverEl=null; if(openFor===el){ openFor=null; closePop2(); }
    });
  }
  document.addEventListener('keydown', function(e){ if(e.key==='Escape'){ openFor=null; closePop2(); } });
  window.addEventListener('resize', function(){ if(openFor) position(openFor); });
})();
"""
    (SITE / "assets" / "app.js").write_text(js, encoding="utf-8")

def build_study_js():
    js = r"""// Ferramentas de estudo (offline): grifar palavra/versículo, anotar, exportar.
// Tudo salvo no localStorage deste navegador. Nada vai para servidor.
(function(){
  function load(k){try{return JSON.parse(localStorage.getItem('bec.'+k)||'{}');}catch(e){return{};}}
  function save(k,v){try{localStorage.setItem('bec.'+k,JSON.stringify(v));}catch(e){}}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  // referência "Livro c:v" → slug e URL absoluta do versículo (BEC_BASE injetado no build)
  function refToSlug(ref){
    var m=(ref||'').match(/^(.*?)\s+(\d+):(\d+)$/); if(!m) return '';
    var b=m[1].normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
    return b+'-'+m[2]+'-'+m[3];
  }
  function refToUrl(ref){ var s=refToSlug(ref); return s? BEC_BASE+'/versiculos/'+s+'/' : BEC_BASE; }
  function downloadBlob(name, blob){
    var u=URL.createObjectURL(blob); var a=document.createElement('a'); a.href=u; a.download=name;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(u);
  }

  // envolve cada palavra de um parágrafo em <span class="w"> para grifo por palavra
  function wrapWords(el, field){
    if(!el || el.dataset.wrapped) return;
    var parts=el.textContent.split(/(\s+)/), i=0;
    el.textContent='';
    parts.forEach(function(p){
      if(p===''||/^\s+$/.test(p)){ el.appendChild(document.createTextNode(p)); return; }
      var s=document.createElement('span'); s.className='w'; s.dataset.f=field; s.dataset.i=i;
      s.textContent=p; el.appendChild(s); i++;
    });
    el.dataset.wrapped='1';
  }

  function setup(cont){
    if(!cont || cont.dataset.studyReady) return;
    var ref=cont.getAttribute('data-ref'); if(!ref) return;
    wrapWords(cont.querySelector('.pt'),'pt');
    wrapWords(cont.querySelector('.orig'),'orig');
    var anchor=cont.querySelector('.verse-hero')||cont.querySelector('.ch-body')||cont;
    cont.classList.add('study-target');
    cont.setAttribute('tabindex','0');
    var nb=document.createElement('div'); nb.className='note-box'; nb.hidden=true;
    nb.innerHTML='<textarea placeholder="Sua anotação para '+esc(ref)+'..."></textarea>'+
      '<div class="note-actions"><button type="button" data-act="copy-note">⧉ Copiar versículo + nota</button></div>';
    anchor.appendChild(nb);
    cont.dataset.studyReady='1';
    apply(cont, ref);
  }

  function flash(btn, txt){
    var o=btn.textContent;
    if(btn.closest && btn.closest('.study-context')) btn.textContent = txt==='Falhou' ? '!' : '✓';
    else btn.textContent=txt;
    setTimeout(function(){btn.textContent=o;},1400);
  }
  function copyText(str, btn){
    (navigator.clipboard?navigator.clipboard.writeText(str):Promise.reject())
      .then(function(){ if(btn) flash(btn,'Copiado!'); })
      .catch(function(){ try{ var t=document.createElement('textarea'); t.value=str; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); if(btn) flash(btn,'Copiado!'); }catch(e){ if(btn) flash(btn,'Falhou'); } });
  }
  function verseText(cont, ref){
    var pt=cont.querySelector('.pt'); var t=pt?pt.textContent.trim():'';
    var note=load('notes')[ref];
    return ref + (t? '\n'+t : '') + (note? '\n\nAnotação: '+note : '');
  }
  function shareText(str, btn){
    if(navigator.share){ navigator.share({title:'Bíblia em Contexto', text:str}).catch(function(){}); }
    else copyText(str, btn);
  }
  // contador de palavras grifadas → cartão de doação a cada N (protótipo, sem backend)
  var DONATE_EVERY=500, DONATE_URL='https://www.buymeacoffee.com/';
  function bumpMark(){
    var n=(parseInt(localStorage.getItem('bec.markCount'),10)||0)+1;
    try{ localStorage.setItem('bec.markCount', n); }catch(e){}
    var milestone=Math.floor(n/DONATE_EVERY);
    var shown=parseInt(localStorage.getItem('bec.donateMilestone'),10)||0;
    if(milestone>shown) showDonate(milestone);
  }
  function showDonate(milestone){
    try{ localStorage.setItem('bec.donateMilestone', milestone); }catch(e){}
    if(document.querySelector('.donate')) return;
    var d=document.createElement('div'); d.className='donate';
    d.innerHTML='<button type="button" class="x" aria-label="Fechar">×</button>'+
      '<a href="'+DONATE_URL+'" target="_blank" rel="noopener">☕ Gostou? Apoie este projeto</a>';
    d.querySelector('.x').onclick=function(){ d.remove(); };
    document.body.appendChild(d);
  }

  // ---------- compartilhar cartão-imagem do versículo (+ link) ----------
  function wrapCanvas(ctx, text, maxW){
    var words=(text||'').split(/\s+/), lines=[], cur='';
    words.forEach(function(w){
      var t=cur?cur+' '+w:w;
      if(ctx.measureText(t).width>maxW && cur){ lines.push(cur); cur=w; } else cur=t;
    });
    if(cur) lines.push(cur);
    return lines;
  }
  function makeVerseCard(ref, pt){
    return new Promise(function(resolve, reject){
      try{
        var W=1080, H=1080, cv=document.createElement('canvas'); cv.width=W; cv.height=H;
        var ctx=cv.getContext && cv.getContext('2d'); if(!ctx){ reject(); return; }
        ctx.fillStyle='#f4eee2'; ctx.fillRect(0,0,W,H);
        ctx.fillStyle='#e7d6ab'; ctx.fillRect(0,0,W,14); ctx.fillRect(0,H-14,W,14);
        ctx.textBaseline='top';
        ctx.fillStyle='#8a6726'; ctx.font='600 54px Georgia, serif'; ctx.fillText(ref, 90, 110);
        ctx.fillStyle='#16120c';
        var size=66, maxW=W-180, lines=wrapCanvas(ctx, pt, maxW);
        ctx.font=size+'px Georgia, serif'; lines=wrapCanvas(ctx, pt, maxW);
        while(lines.length*size*1.35 > H-440 && size>30){ size-=4; ctx.font=size+'px Georgia, serif'; lines=wrapCanvas(ctx, pt, maxW); }
        var y=250, lh=size*1.35;
        lines.forEach(function(ln){ ctx.fillText(ln, 90, y); y+=lh; });
        ctx.fillStyle='#6f6453'; ctx.font='500 36px Georgia, serif'; ctx.fillText('Bíblia em Contexto', 90, H-150);
        ctx.fillStyle='#8a6726'; ctx.font='30px Georgia, serif'; ctx.fillText(BEC_BASE.replace(/^https?:\/\//,''), 90, H-100);
        if(cv.toBlob) cv.toBlob(function(b){ b?resolve(b):reject(); }, 'image/png'); else reject();
      }catch(e){ reject(); }
    });
  }
  function shareVerse(cont, ref, btn){
    var pt=cont.querySelector('.pt'); var t=pt?pt.textContent.trim():'';
    var url=refToUrl(ref), text=ref+(t?'\n'+t:'')+'\n'+url;
    makeVerseCard(ref, t).then(function(blob){
      var file; try{ file=new File([blob],'versiculo.png',{type:'image/png'}); }catch(e){ file=null; }
      if(file && navigator.canShare && navigator.canShare({files:[file]})){
        navigator.share({files:[file], text:ref+'\n'+url, title:'Bíblia em Contexto'}).catch(function(){});
      } else if(navigator.share){
        navigator.share({title:'Bíblia em Contexto', text:text}).catch(function(){});
      } else { copyText(text, btn); downloadBlob('versiculo.png', blob); }
    }).catch(function(){
      if(navigator.share){ navigator.share({title:'Bíblia em Contexto', text:text}).catch(function(){}); }
      else copyText(text, btn);
    });
  }

  // ---------- modal de confirmação (evita apagar por toque acidental) ----------
  function confirmModal(msg, onYes){
    var ov=document.createElement('div'); ov.className='bec-modal';
    ov.innerHTML='<div class="bec-modal-box"><p>'+esc(msg)+'</p>'+
      '<div class="bec-modal-actions"><button type="button" class="btn ghost" data-no>Cancelar</button>'+
      '<button type="button" class="btn danger" data-yes>Apagar tudo</button></div></div>';
    ov.addEventListener('click', function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-no]'))) ov.remove();
      else if(e.target.closest && e.target.closest('[data-yes]')){ ov.remove(); onYes(); }
    });
    document.body.appendChild(ov);
  }

  // ---------- seta de ferramentas ocultas (salvar/compartilhar, anotações, apagar) ----------
  function clearAll(){ ['notes','vhl','whl'].forEach(function(k){ localStorage.removeItem('bec.'+k); }); render(); }
  function studyText(){ var n=load('notes'),v=load('vhl'),w=load('whl'); return exportText(allRefs(n,v,w),n,v,w); }
  function makeToolsMenu(){
    if(document.querySelector('.tools-fab')) return;
    var fab=document.createElement('button'); fab.type='button'; fab.className='tools-fab';
    fab.setAttribute('aria-expanded','false'); fab.title='Ferramentas de estudo'; fab.textContent='↥';
    var panel=document.createElement('div'); panel.className='tools-panel'; panel.hidden=true;
    panel.innerHTML='<button type="button" data-t="share">📝 Salvar nas Notas / Compartilhar</button>'+
      '<button type="button" data-t="txt">📄 Baixar .txt</button>'+
      '<a href="'+BEC_BASE+'/anotacoes/" data-t="notes">🗒 Minhas anotações</a>'+
      '<button type="button" data-t="clear">🗑 Apagar tudo</button>';
    fab.onclick=function(){ var open=panel.hidden; panel.hidden=!open; fab.setAttribute('aria-expanded', open?'true':'false'); fab.textContent=open?'✕':'↥'; };
    panel.addEventListener('click', function(e){
      var b=e.target.closest && e.target.closest('[data-t]'); if(!b) return;
      var t=b.getAttribute('data-t');
      if(t==='share') shareText(studyText(), b);                       // iOS: folha de compartilhamento → Notas
      else if(t==='txt') download('meu-estudo.txt', studyText(), 'text/plain');
      else if(t==='clear') confirmModal('Apagar TODAS as marcações e anotações deste navegador? Esta ação não pode ser desfeita.', clearAll);
    });
    document.body.appendChild(fab); document.body.appendChild(panel);
  }

  var activeStudy=null;
  function getStudyBar(){
    var bar=document.querySelector('.study-context');
    if(bar) return bar;
    bar=document.createElement('div'); bar.className='study-context'; bar.hidden=true;
    bar.setAttribute('aria-label','Ferramentas do versículo selecionado');
    bar.innerHTML='<button type="button" data-act="vhl" aria-label="Grifar versículo" title="Grifar versículo">🖍</button>'+
      '<button type="button" data-act="note" aria-label="Anotar" title="Anotar">🗒</button>'+
      '<button type="button" data-act="copy" aria-label="Copiar versículo" title="Copiar versículo">⧉</button>'+
      '<button type="button" data-act="share" aria-label="Compartilhar" title="Compartilhar">↗</button>';
    document.body.appendChild(bar);
    return bar;
  }
  function refreshStudyBar(){
    var bar=getStudyBar();
    if(!activeStudy){ bar.hidden=true; return; }
    var ref=activeStudy.getAttribute('data-ref'), vhl=load('vhl');
    bar.hidden=false;
    bar.setAttribute('data-ref', ref||'');
    var h=bar.querySelector('[data-act="vhl"]');
    if(h) h.classList.toggle('on', !!vhl[ref]);
    var n=bar.querySelector('[data-act="note"]');
    if(n){
      var noteIsOpen=!!(activeStudy.querySelector('.note-box') && !activeStudy.querySelector('.note-box').hidden);
      n.classList.toggle('on', noteIsOpen);
      n.setAttribute('aria-expanded', noteIsOpen?'true':'false');
    }
  }
  function findStudyByRef(ref){
    if(!ref) return null;
    var items=document.querySelectorAll('.verse-cont[data-ref], .ch-verse[data-ref]');
    for(var i=0;i<items.length;i++){ if(items[i].getAttribute('data-ref')===ref) return items[i]; }
    return null;
  }
  function activateStudy(cont){
    if(!cont || !cont.getAttribute('data-ref')) return;
    if(activeStudy && activeStudy!==cont) activeStudy.classList.remove('study-active');
    activeStudy=cont;
    activeStudy.classList.add('study-active');
    refreshStudyBar();
  }
  function closeStudyBar(){
    if(activeStudy) activeStudy.classList.remove('study-active');
    activeStudy=null;
    refreshStudyBar();
  }
  function noteOpen(){
    return !!(activeStudy && activeStudy.querySelector('.note-box') && !activeStudy.querySelector('.note-box').hidden);
  }
  function setNoteOpen(cont, open){
    if(!cont) return;
    activateStudy(cont);
    var nb=cont.querySelector('.note-box');
    if(!nb) return;
    nb.hidden=!open;
    cont.classList.toggle('note-open', !!open);
    refreshStudyBar();
    if(open){
      var ta=nb.querySelector('textarea');
      setTimeout(function(){
        try{ nb.scrollIntoView({block:'nearest', behavior:'smooth'}); }catch(e){ nb.scrollIntoView(); }
        if(ta) ta.focus();
      }, 0);
    }
  }

  function apply(cont, ref){
    if(load('vhl')[ref]) cont.classList.add('v-hl');
    var notes=load('notes');
    if(notes[ref]){
      var ta=cont.querySelector('.note-box textarea');
      if(ta) ta.value=notes[ref];
      cont.classList.add('has-note');
    }
    var rec=load('whl')[ref]||{};
    Object.keys(rec).forEach(function(f){
      rec[f].forEach(function(o){
        var w=cont.querySelector('.w[data-f="'+f+'"][data-i="'+o.i+'"]');
        if(w){ w.classList.add('w-hl'); w.setAttribute('data-c', o.c||'y'); }
      });
    });
  }

  function toggleWord(w){
    var cont=w.closest('[data-ref]'); if(!cont) return;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var all=load('whl'), recd=all[ref]||{}, arr=recd[f]||[];
    var pos=-1; for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ pos=n; break; } }
    if(pos>-1){ arr.splice(pos,1); w.classList.remove('w-hl'); w.removeAttribute('data-c'); }
    else { arr.push({i:i,t:w.textContent,c:'y'}); w.classList.add('w-hl'); w.setAttribute('data-c','y'); }
    if(arr.length) recd[f]=arr; else delete recd[f];
    if(Object.keys(recd).length) all[ref]=recd; else delete all[ref];
    save('whl', all);
    bumpMark();
  }

  function toggleVerse(cont, ref, btn){
    var all=load('vhl');
    if(all[ref]){ delete all[ref]; cont.classList.remove('v-hl'); if(btn) btn.classList.remove('on'); }
    else { all[ref]=1; cont.classList.add('v-hl'); if(btn) btn.classList.add('on'); }
    save('vhl', all);
    refreshStudyBar();
  }

  document.addEventListener('click', function(e){
    var action=e.target.closest && e.target.closest('.study-context button, .note-actions button');
    if(action){
      var bar=action.closest && action.closest('.study-context');
      var cont=bar ? findStudyByRef(bar.getAttribute('data-ref')) : action.closest('[data-ref]');
      if(!cont && activeStudy && !(activeStudy.classList && activeStudy.classList.contains('study-context'))) cont=activeStudy;
      if(!cont) return;
      var ref=cont.getAttribute('data-ref'), act=action.dataset.act;
      activateStudy(cont);
      if(act==='vhl') toggleVerse(cont, ref, action);
      else if(act==='note'){ var nb=cont.querySelector('.note-box'); setNoteOpen(cont, !(nb && !nb.hidden)); }
      else if(act==='copy' || act==='copy-note') copyText(verseText(cont, ref), action);
      else if(act==='share') shareVerse(cont, ref, action);
      return;
    }
    if(e.target.closest && e.target.closest('.tools-fab,.tools-panel,.pen-toggle,.pen-colors,.sel-bar,.note-box,.translit-toggle,.original-toggle,.study-toggle summary,a,button,select,input,textarea')) return;
    var w=e.target.closest && e.target.closest('.w');
    if(w && w.closest('[data-ref]')){ if(penOn) return; activateStudy(w.closest('[data-ref]')); return; }
    var cont=e.target.closest && e.target.closest('.verse-cont[data-ref], .ch-verse[data-ref]');
    if(cont) activateStudy(cont);
    else if(!noteOpen()) closeStudyBar();
  });
  document.addEventListener('keydown', function(e){
    if(e.key!=='Enter' && e.key!==' ') return;
    var cont=e.target.closest && e.target.closest('.verse-cont[data-ref], .ch-verse[data-ref]');
    if(!cont || e.target.closest('button,a,select,input,textarea')) return;
    e.preventDefault();
    activateStudy(cont);
  });

  // ---------- caneta marca-texto: arrastar pinta as palavras (com cores) ----------
  var penOn=false, penColor='y', painting=false, activePointerId=null, pendingWhl=null, lastPenTap=null;
  var COLORS=['x','y','g','b','p'], CNAMES={x:'Desmarcar',y:'Amarelo',g:'Verde',b:'Azul',p:'Rosa'};
  function setPen(on){
    penOn=on; document.body.classList.toggle('hl-mode', on);
    var b=document.querySelector('.pen-toggle');
    if(b){ b.classList.toggle('on', on); b.setAttribute('aria-pressed', on?'true':'false'); }
    save('penmode', {on:on});
  }
  function setColor(c){
    penColor=c;
    var sw=document.querySelectorAll('.pen-colors button');
    for(var i=0;i<sw.length;i++){ sw[i].classList.toggle('on', sw[i].getAttribute('data-c')===c); }
    save('pencolor', {c:c});
  }
  function wordAtPoint(x,y){ var el=document.elementFromPoint(x,y); return el && el.closest ? el.closest('.w') : null; }
  function wordKey(w){
    var cont=w && w.closest('[data-ref]'); if(!cont) return '';
    return cont.getAttribute('data-ref')+'|'+w.dataset.f+'|'+w.dataset.i;
  }
  function removeWordMark(w, all){
    var cont=w && w.closest('[data-ref]'); if(!cont || !all) return false;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var recd=all[ref], arr=recd && recd[f], pos=-1;
    if(arr){ for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ pos=n; break; } } }
    if(pos<0) return false;
    arr.splice(pos,1); w.classList.remove('w-hl'); w.removeAttribute('data-c');
    if(!arr.length) delete recd[f];
    if(!Object.keys(recd).length) delete all[ref];
    return true;
  }
  function isRepeatTap(w){
    var now=Date.now(), key=wordKey(w);
    return !!(lastPenTap && lastPenTap.key===key && now-lastPenTap.t<520);
  }
  function paintWord(w){
    if(!w) return; var cont=w.closest('[data-ref]'); if(!cont) return;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var recd=pendingWhl[ref]||(pendingWhl[ref]={}); var arr=recd[f]||(recd[f]=[]);
    var found=null, pos=-1; for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ found=arr[n]; pos=n; break; } }
    if(penColor==='x'){
      if(found) removeWordMark(w, pendingWhl);
      return;
    }
    if(found){ if(found.c!==penColor){ found.c=penColor; w.setAttribute('data-c', penColor); } }
    else { arr.push({i:i,t:w.textContent,c:penColor}); w.classList.add('w-hl'); w.setAttribute('data-c', penColor); bumpMark(); }
  }
  function startPaint(e){
    if(!penOn) return;
    var w=(e.target.closest && e.target.closest('.w')); if(!w || !w.closest('[data-ref]')) return;
    e.preventDefault(); pendingWhl=load('whl');
    if(isRepeatTap(w) && removeWordMark(w, pendingWhl)){
      save('whl', pendingWhl); lastPenTap=null; painting=false; activePointerId=null; return;
    }
    painting=true; activePointerId=e.pointerId; paintWord(w);
    lastPenTap={key:wordKey(w), t:Date.now()};
  }
  function movePaint(e){ if(!painting || e.pointerId!==activePointerId) return; e.preventDefault(); var w=wordAtPoint(e.clientX, e.clientY); if(w && wordKey(w)!==(lastPenTap && lastPenTap.key)) lastPenTap=null; paintWord(w); }
  function endPaint(){ if(!painting) return; painting=false; activePointerId=null; save('whl', pendingWhl); }
  document.addEventListener('pointerdown', startPaint);
  document.addEventListener('pointermove', movePaint);
  document.addEventListener('pointerup', endPaint);
  document.addEventListener('pointercancel', endPaint);
  function makePenTools(){
    if(!document.querySelector('.verse-cont[data-ref], .ch-verse[data-ref]')) return;
    if(document.querySelector('.pen-toggle')) return;
    var btn=document.createElement('button'); btn.type='button'; btn.className='pen-toggle';
    btn.setAttribute('aria-pressed','false'); btn.title='Marca-texto (caneta)'; btn.textContent='🖍';
    btn.onclick=function(){ setPen(!penOn); };
    document.body.appendChild(btn);
    var pal=document.createElement('div'); pal.className='pen-colors';
    pal.innerHTML=COLORS.map(function(c){
      return '<button type="button" data-c="'+c+'" aria-label="'+CNAMES[c]+'" title="'+CNAMES[c]+'">'+(c==='x'?'x':'')+'</button>';
    }).join('');
    pal.addEventListener('click', function(e){ var b=e.target.closest('button'); if(b) setColor(b.getAttribute('data-c')); });
    document.body.appendChild(pal);
    setColor((load('pencolor').c)||'y');
    if(load('penmode').on) setPen(true);
  }

  // ---------- marca-texto por seleção: barra flutuante (Grifar / Copiar) ----------
  var selBar=null, selT=null;
  function getSelBar(){
    if(selBar) return selBar;
    selBar=document.createElement('div'); selBar.className='sel-bar'; selBar.hidden=true;
    selBar.innerHTML='<button type="button" data-sel="copy">⧉ Copiar seleção</button>';
    document.body.appendChild(selBar);
    selBar.addEventListener('mousedown', function(e){ e.preventDefault(); });  // preserva a seleção
    selBar.addEventListener('click', function(e){
      var b=e.target.closest('button'); if(b) copySelection(b);
    });
    return selBar;
  }
  function hideSelBar(){ if(selBar) selBar.hidden=true; }
  function selInfo(){
    var sel=window.getSelection();
    if(!sel || sel.isCollapsed || !sel.rangeCount) return null;
    var r=sel.getRangeAt(0), node=r.commonAncestorContainer;
    var el=node.nodeType===1?node:node.parentNode;
    var cont=el && el.closest ? el.closest('[data-ref]') : null;
    if(!cont) return null;
    var text=sel.toString().trim(); if(!text) return null;
    return {sel:sel, range:r, cont:cont, text:text};
  }
  function showSelBar(){
    var info=selInfo(); if(!info){ hideSelBar(); return; }
    var bar=getSelBar(); bar.hidden=false;
    try{
      var rect=info.range.getBoundingClientRect();
      var top=window.scrollY + rect.top - bar.offsetHeight - 8;
      if(top < window.scrollY+4) top = window.scrollY + rect.bottom + 8;
      var left=window.scrollX + rect.left + rect.width/2 - bar.offsetWidth/2;
      bar.style.top=Math.max(4,top)+'px';
      bar.style.left=Math.max(4,left)+'px';
    }catch(e){}
  }
  function copySelection(btn){ var info=selInfo(); if(info) copyText(info.text, btn); }
  function scheduleSelBar(){ clearTimeout(selT); selT=setTimeout(showSelBar, 10); }
  document.addEventListener('mouseup', scheduleSelBar);
  document.addEventListener('touchend', scheduleSelBar);
  document.addEventListener('selectionchange', function(){
    var s=window.getSelection(); if(!s || s.isCollapsed) hideSelBar();
  });
  document.addEventListener('mousedown', function(e){
    if(selBar && !selBar.hidden && !(e.target.closest && e.target.closest('.sel-bar'))) hideSelBar();
  });
  window.addEventListener('scroll', hideSelBar, {passive:true});
  document.addEventListener('input', function(e){
    if(e.target.matches && e.target.matches('.note-box textarea')){
      var cont=e.target.closest('[data-ref]'), ref=cont.getAttribute('data-ref');
      var notes=load('notes'), val=e.target.value.trim();
      if(val){ notes[ref]=val; cont.classList.add('has-note'); } else { delete notes[ref]; cont.classList.remove('has-note'); }
      save('notes', notes);
    }
  });

  function setupAll(root){ (root||document).querySelectorAll('.verse-cont[data-ref], .ch-verse[data-ref]').forEach(setup); }
  setupAll();
  makePenTools();
  makeToolsMenu();
  // versículos carregados por rolagem infinita também recebem as ferramentas
  if(window.MutationObserver){
    new MutationObserver(function(muts){
      muts.forEach(function(m){ Array.prototype.forEach.call(m.addedNodes, function(n){
        if(n.nodeType===1){ if(n.matches && n.matches('.verse-cont[data-ref]')) setup(n); setupAll(n); }
      }); });
    }).observe(document.body, {childList:true, subtree:true});
  }

  // ---------- página de Anotações: listar, copiar, baixar, limpar ----------
  function slugFromRef(ref){
    var m=ref.match(/^(.*?)\s+(\d+):(\d+)$/); if(!m) return '#';
    var b=m[1].normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
    return '../versiculos/'+b+'-'+m[2]+'-'+m[3]+'/';
  }
  function allRefs(notes, vhl, whl){
    var s={}; [notes,vhl,whl].forEach(function(o){ Object.keys(o).forEach(function(r){ s[r]=1; }); });
    return Object.keys(s).sort();
  }
  function exportText(keys, notes, vhl, whl){
    var out='Minhas anotações — Bíblia em Contexto\n\n';
    keys.forEach(function(ref){
      out+=ref+'\n';
      if(vhl[ref]) out+='  [versículo grifado]\n';
      var rec=whl[ref];
      if(rec){ Object.keys(rec).forEach(function(f){
        out+='  palavras grifadas ('+f+'): '+rec[f].map(function(o){return o.t;}).join(' · ')+'\n';
      }); }
      if(notes[ref]) out+='  Nota: '+notes[ref]+'\n';
      out+='\n';
    });
    return out;
  }
  function download(name, text, type){
    var b=new Blob([text], {type:type}), u=URL.createObjectURL(b);
    var a=document.createElement('a'); a.href=u; a.download=name; document.body.appendChild(a);
    a.click(); a.remove(); URL.revokeObjectURL(u);
  }
  function importData(obj){
    var n=load('notes'), v=load('vhl'), w=load('whl');
    if(obj.notes) Object.keys(obj.notes).forEach(function(r){ n[r]=obj.notes[r]; });
    if(obj.vhl) Object.keys(obj.vhl).forEach(function(r){ v[r]=obj.vhl[r]; });
    if(obj.whl) Object.keys(obj.whl).forEach(function(r){
      var rec=obj.whl[r]; w[r]=w[r]||{};
      Object.keys(rec).forEach(function(f){
        var ex=w[r][f]||[], have={}; ex.forEach(function(o){ have[o.i]=1; });
        rec[f].forEach(function(o){ if(!have[o.i]) ex.push(o); }); w[r][f]=ex;
      });
    });
    save('notes',n); save('vhl',v); save('whl',w);
  }
  function render(){
    var box=document.getElementById('anotacoes'); if(!box) return;
    var notes=load('notes'), vhl=load('vhl'), whl=load('whl'), keys=allRefs(notes,vhl,whl);
    if(!keys.length){ box.innerHTML='<p class="empty">Você ainda não grifou nem anotou nada. Abra um versículo (ou um capítulo) e use “Grifar” ou “Anotar”.</p>'; return; }
    box.innerHTML=keys.map(function(ref){
      var h='<div class="anot"><h3><a href="'+slugFromRef(ref)+'">'+esc(ref)+'</a></h3>';
      if(vhl[ref]) h+='<p class="anot-tag">✶ versículo grifado</p>';
      var rec=whl[ref];
      if(rec){ Object.keys(rec).forEach(function(f){
        h+='<p class="anot-tag">palavras: '+rec[f].map(function(o){return esc(o.t);}).join(' · ')+'</p>';
      }); }
      if(notes[ref]) h+='<p class="anot-note">'+esc(notes[ref])+'</p>';
      return h+'</div>';
    }).join('');
  }
  function wire(){
    var box=document.getElementById('anotacoes'); if(!box) return;
    render();
    var c=document.getElementById('anot-copy'), t=document.getElementById('anot-txt'),
        j=document.getElementById('anot-json'), x=document.getElementById('anot-clear');
    function data(){ var n=load('notes'),v=load('vhl'),w=load('whl'); return {keys:allRefs(n,v,w),notes:n,vhl:v,whl:w}; }
    if(c) c.onclick=function(){ var d=data(); var txt=exportText(d.keys,d.notes,d.vhl,d.whl);
      (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){ c.textContent='Copiado!'; setTimeout(function(){c.textContent='Copiar tudo';},1500); })
      .catch(function(){ download('anotacoes.txt',txt,'text/plain'); }); };
    if(t) t.onclick=function(){ var d=data(); download('anotacoes.txt', exportText(d.keys,d.notes,d.vhl,d.whl), 'text/plain'); };
    if(j) j.onclick=function(){ download('anotacoes.json', JSON.stringify({notes:load('notes'),vhl:load('vhl'),whl:load('whl')}, null, 2), 'application/json'); };
    if(x) x.onclick=function(){ confirmModal('Apagar TODAS as marcações e anotações deste navegador? Esta ação não pode ser desfeita.', function(){ ['notes','vhl','whl'].forEach(function(k){localStorage.removeItem('bec.'+k);}); render(); }); };
    var sh=document.getElementById('anot-share');
    if(sh) sh.onclick=function(){ var d=data(); var txt=exportText(d.keys,d.notes,d.vhl,d.whl);
      if(navigator.share){ navigator.share({title:'Minhas anotações — Bíblia em Contexto', text:txt}).catch(function(){}); }
      else (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){ sh.textContent='Copiado!'; setTimeout(function(){sh.textContent='Compartilhar';},1500); }).catch(function(){ download('anotacoes.txt',txt,'text/plain'); }); };
    var imp=document.getElementById('anot-import'), impf=document.getElementById('anot-import-file');
    if(imp && impf){
      imp.onclick=function(){ impf.click(); };
      impf.onchange=function(){
        var f=impf.files[0]; if(!f) return;
        var rd=new FileReader();
        rd.onload=function(){ try{ importData(JSON.parse(rd.result)); render(); imp.textContent='Importado!'; }catch(e){ imp.textContent='Arquivo inválido'; } setTimeout(function(){imp.textContent='Importar backup';},1800); };
        rd.readAsText(f); impf.value='';
      };
    }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', wire); else wire();
})();
"""
    (SITE / "assets" / "study.js").write_text(
        f"var BEC_BASE={json.dumps(BASE_URL)};\n" + js, encoding="utf-8")

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
    out.write_text(head(title, desc, canonical, prefix) + nav(prefix) + body + footer(prefix), encoding="utf-8")

def build_meta(verses, articles, order, struct, topics=None, glossary=None, places=None, plans=None):
    # sitemap
    urls = [BASE_URL + "/", f"{BASE_URL}/ler/", f"{BASE_URL}/linha-do-tempo/", f"{BASE_URL}/temas/"]
    if topics:
        urls += [f"{BASE_URL}/temas/{t['slug']}/" for t in topics]
    if glossary:
        urls += [f"{BASE_URL}/dicionario/"]
        urls += [f"{BASE_URL}/dicionario/{g['slug']}/" for g in glossary]
    if places:
        urls += [f"{BASE_URL}/mapas/"]
        urls += [f"{BASE_URL}/mapas/{p['slug']}/" for p in places]
    if plans:
        urls += [f"{BASE_URL}/planos/"]
        urls += [f"{BASE_URL}/planos/{pl['slug']}/" for pl in plans]
    urls += [f"{BASE_URL}/ler/{book_slug(livro)}/" for livro in order]
    urls += [f"{BASE_URL}/ler/{book_slug(livro)}/{ch}/" for livro in order for ch in sorted(struct[livro])]
    urls += [f"{BASE_URL}/versiculos/{v['slug']}/" for v in verses]
    urls += [f"{BASE_URL}/artigos/{a['slug']}/" for a in articles]
    items = "".join(f"<url><loc>{u}</loc><changefreq>monthly</changefreq></url>\n" for u in urls)
    (SITE / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+items+'</urlset>\n',
        encoding="utf-8")
    # robots: libera buscadores normais; pede que crawlers de IA/scrapers não copiem (advisory)
    ai_bots = ["GPTBot","ChatGPT-User","OAI-SearchBot","ClaudeBot","anthropic-ai","Claude-Web",
               "CCBot","Google-Extended","Applebot-Extended","PerplexityBot","Bytespider","Amazonbot",
               "Diffbot","Omgilibot","ImagesiftBot","cohere-ai","FacebookBot","Meta-ExternalAgent"]
    ai_block = "".join(f"\nUser-agent: {b}\nDisallow: /\n" for b in ai_bots)
    (SITE / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n{ai_block}\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
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

def build_random_pool(verses):
    # pool de slugs para "Versículo para meditar" (aleatório no cliente).
    # amostra distribuída (determinística) de versículos COM tradução PT, evitando
    # trechos áridos e mantendo o arquivo leve. Carregado sob demanda na home.
    slugs = [v["slug"] for v in verses if v.get("texto_pt","").strip()]
    alvo = 1500
    if len(slugs) > alvo:
        passo = len(slugs) // alvo
        slugs = slugs[::passo][:alvo]
    (DATA / "random.json").write_text(json.dumps(slugs, ensure_ascii=False), encoding="utf-8")
    return len(slugs)

def main():
    topics=load("topics.json"); verses=load("verses.json")
    articles=load("articles.json"); sources=load("sources.json")
    topic_refs=load_opt("topic-refs.json", {}); cross_refs=load_opt("cross-references.json", {})
    glossary=load_opt("glossary.json", []); commentary=load_opt("commentary.json", {})
    places=load_opt("places.json", []); plans=load_opt("reading-plans.json", [])
    red_letters=load_opt("red-letters.json", {})
    jewish_readings=load_opt("jewish-readings.json", {})
    # tokens hebraicos (lemma+morph por palavra) p/ interação palavra-a-palavra
    global HEBREW_TOKENS
    HEBREW_TOKENS = load_opt("hebrew-tokens.json", {})
    # garante slug em cada tema (deriva do título quando ausente)
    for t in topics:
        if not t.get("slug"):
            t["slug"] = book_slug(t.get("titulo",""))
    articles_by_slug={a["slug"]:a for a in articles}
    # índices referência -> termos/lugares que a citam (para os blocos no versículo)
    glossary_by_ref = defaultdict(list)
    for t in glossary:
        for r in t.get("refs", []):
            glossary_by_ref[r].append(t)
    places_by_ref = defaultdict(list)
    for p in places:
        for r in p.get("refs", []):
            places_by_ref[r].append(p)
    # ordem bíblica garantida (folhear de Gênesis a Apocalipse)
    verses = sorted(verses, key=verse_sort_key)
    order, struct = group_by_book_chapter(verses)
    verses_by_ref = {v["referencia"]: v for v in verses}
    # limpa saídas antigas
    for d in ["versiculos","artigos","ler","anotacoes","offline","temas","dicionario","mapas","planos"]:
        shutil.rmtree(SITE/d, ignore_errors=True)
    build_home(topics, verses, articles, sources, order, struct, topic_refs)
    build_app_js()
    build_study_js()
    build_sw_js()
    build_offline_page()
    build_annotations_page()
    n_idx = build_search_index(verses, articles, topics, glossary, places, plans)
    build_random_pool(verses)
    n = len(verses)
    for i, v in enumerate(verses):
        prev_v = verses[i-1] if i > 0 else None
        next_v = verses[i+1] if i < n-1 else None
        build_verse_page(v, articles_by_slug, prev_v, next_v, cross_refs, verses_by_ref,
                         commentary, glossary_by_ref, places_by_ref, red_letters,
                         jewish_readings)
    for a in articles: build_article_page(a)
    # navegação livro → capítulo → versículo
    build_books_index(order, struct)
    build_timeline_page(order, struct)
    # temas (índice de tópicos)
    build_topics_index(topics, topic_refs)
    for t in topics:
        build_topic_page(t, topic_refs.get(t["slug"], []), verses_by_ref, articles)
    # dicionário (glossário integrado)
    build_dictionary_index(glossary)
    for t in glossary:
        build_dictionary_term_page(t, verses_by_ref, articles)
    # mapas (atlas de lugares)
    build_atlas_index(places)
    for p in places:
        build_place_page(p, verses_by_ref)
    # planos de leitura
    build_plans_index(plans)
    for pl in plans:
        build_plan_page(pl)
    n_chapters = 0
    for livro in order:
        chapters = struct[livro]
        build_book_page(livro, chapters, order)
        total_caps = max(chapters)
        for ch in sorted(chapters):
            build_chapter_page(livro, ch, chapters[ch], total_caps, order, red_letters)
            n_chapters += 1
    build_meta(verses, articles, order, struct, topics, glossary, places, plans)
    build_404()
    print(f"OK: home + {len(verses)} versículos + {len(order)} livros + {n_chapters} capítulos "
          f"+ {len(articles)} artigos + {len(topics)} temas + {len(glossary)} termos "
          f"+ {len(places)} lugares + {len(plans)} planos "
          f"+ índice de busca ({n_idx}) + sitemap + 404")

if __name__=="__main__":
    main()
