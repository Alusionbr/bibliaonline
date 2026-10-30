"""Paginas de referencia da Biblioteca: temas, dicionario, atlas, lexico
hebraico e panorama dos livros.

Este modulo so monta o conteudo (o <main> de cada pagina e seus metadados).
Quem escreve os arquivos, com head/nav/footer, e o build.py — assim o modulo
nao depende de SITE/DATA e pode ser testado isolado.
"""
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass

from build_config import BOOK_ORDER
from build_utils import book_slug, esc, lang_label, script_class


@dataclass
class Page:
    url: str            # caminho relativo à raiz, ex.: "temas/ansiedade/"
    title: str
    description: str
    body: str
    jsonld: dict = None

    @property
    def prefix(self):
        return "../" * self.url.count("/")


def fold(s):
    base = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return base.lower()


def plural(n, singular, plural_form=None):
    return f"{n} {singular if n == 1 else (plural_form or singular + 's')}"


def verse_card(ref, verses_by_ref, prefix):
    """Cartão de versículo (referência + texto pt) que abre a página completa."""
    v = verses_by_ref.get(ref)
    if not v:
        return ""
    return (f'<a class="result" href="{prefix}versiculos/{v["slug"]}/">'
            f'<span class="kind">Versículo</span><h4>{esc(ref)}</h4>'
            f'<p>{esc(v.get("texto_pt", ""))}</p></a>')


def related_articles(key, articles, prefix):
    key = fold(key)
    rels = [a for a in articles
            if key and key in fold(a.get("titulo", "") + " " + a.get("resumo", "") + " " + a.get("slug", ""))]
    if not rels:
        return ""
    items = "".join(
        f'<a class="result" href="{prefix}artigos/{a["slug"]}/"><span class="kind">Artigo</span>'
        f'<h4>{esc(a["titulo"])}</h4><p>{esc(a.get("resumo", ""))}</p></a>'
        for a in rels)
    return f"""
  <section class="hub-section">
    <div class="section-title"><h2>Para aprofundar</h2><span>Artigos</span></div>
    <div class="related-list">{items}</div>
  </section>"""


def ref_card(label, title, text, url, extra=""):
    return f"""
    <a class="study-card link-card" href="{esc(url)}">
      <span>{esc(label)}</span>
      <h3>{title}</h3>
      <p>{esc(text)}</p>{extra}
    </a>"""


def hub(prefix, crumbs, eyebrow, h1, intro, sections):
    trail = " · ".join(
        [f'<a href="{prefix}index.html">Início</a>']
        + [f'<a href="{url}">{esc(label)}</a>' if url else esc(label) for label, url in crumbs])
    return f"""
<main id="main" class="wrap hub-page ref-page">
  <p class="crumb">{trail}</p>
  <header class="hub-hero"><p class="eyebrow">{esc(eyebrow)}</p><h1>{h1}</h1><p>{intro}</p></header>
  {sections}
</main>"""


def verses_section(title, refs, verses_by_ref, prefix):
    cards = "".join(verse_card(r, verses_by_ref, prefix) for r in refs)
    if not cards:
        return ""
    return f"""
  <section class="hub-section">
    <div class="section-title"><h2>{esc(title)}</h2><span>Toque para ler com o original</span></div>
    <div class="related-list">{cards}</div>
  </section>"""


# ---------- temas ----------
def topic_pages(topics, topic_refs, verses_by_ref, articles):
    topics = [t for t in topics if t.get("slug")]
    if not topics:
        return []
    cards = "".join(
        ref_card("Tema", f'<span class="gl">{esc(t.get("icone", ""))}</span> {esc(t["titulo"])}',
                 t.get("descricao", ""), f'{t["slug"]}/',
                 f'<em class="ref-count">{plural(len(topic_refs.get(t["slug"], [])), "versículo")}</em>')
        for t in topics)
    pages = [Page(
        url="temas/",
        title="Temas de estudo da Bíblia",
        description="Estude a Bíblia por assunto: ansiedade, medo, fé, oração, perdão e mais, com versículos que abrem a página completa com original e contexto.",
        body=hub("../", [("Temas", "")], "Biblioteca", "Temas de estudo",
                 "Pontos de entrada para quem busca um assunto, não uma referência exata. Cada tema reúne versículos curados.",
                 f'<section class="hub-section"><div class="study-card-grid">{cards}</div></section>'),
    )]
    for t in topics:
        prefix = "../../"
        sections = (verses_section("Versículos", topic_refs.get(t["slug"], []), verses_by_ref, prefix)
                    + related_articles(t["titulo"].split()[0], articles, prefix))
        pages.append(Page(
            url=f'temas/{t["slug"]}/',
            title=f'{t["titulo"]} na Bíblia: versículos e contexto',
            description=t.get("descricao") or f'Versículos sobre {t["titulo"]} na Bíblia, com original e contexto.',
            body=hub(prefix, [("Temas", "../"), (t["titulo"], "")], "Tema",
                     f'<span class="gl">{esc(t.get("icone", ""))}</span> {esc(t["titulo"])}',
                     esc(t.get("descricao", "")), sections),
            jsonld={"@context": "https://schema.org", "@type": "CollectionPage",
                    "name": t["titulo"], "inLanguage": "pt-BR"},
        ))
    return pages


# ---------- dicionário ----------
def gloss_orig(t, big=False):
    sc = script_class(t.get("idioma", ""), t.get("dir", "ltr"))
    d = "rtl" if t.get("dir") == "rtl" else "ltr"
    return f'<p class="gloss-orig {sc}{" gloss-big" if big else ""}" dir="{d}" lang="{"he" if d == "rtl" else "el"}">{esc(t.get("original", ""))}</p>'


def dictionary_pages(glossary, verses_by_ref, articles):
    if not glossary:
        return []
    sections = ""
    for idioma in ("hebraico", "aramaico", "grego"):
        terms = [t for t in glossary if t.get("idioma") == idioma]
        if not terms:
            continue
        cards = "".join(
            ref_card(lang_label(idioma), esc(t["termo"]), t.get("definicao", ""), f'{t["slug"]}/', gloss_orig(t))
            for t in terms)
        sections += f"""
  <section class="hub-section">
    <div class="section-title"><h2>{esc(lang_label(idioma))}</h2><span>{plural(len(terms), "verbete")}</span></div>
    <div class="study-card-grid">{cards}</div>
  </section>"""
    sections += """
  <section class="hub-section">
    <div class="section-title"><h2>Léxico completo</h2><span>Hebraico palavra por palavra</span></div>
    <div class="study-card-grid">""" + ref_card(
        "Léxico", "Léxico hebraico", "Cada palavra hebraica curada, com significado, frequência e onde aparece.",
        "../lexico/hebraico/") + """</div>
  </section>"""
    pages = [Page(
        url="dicionario/",
        title="Dicionário bíblico: hebraico, grego e aramaico",
        description="Palavras-chave da Bíblia no idioma original (shalom, hesed, logos, ágape, abba e mais) com significado e versículos de exemplo.",
        body=hub("../", [("Dicionário", "")], "Biblioteca", "Dicionário bíblico",
                 "Palavras-chave no idioma original, com o sentido por trás da tradução e os versículos onde aparecem.",
                 sections),
    )]
    for t in glossary:
        prefix = "../../"
        hero = f"""
  <section class="hub-section ref-hero">
    {gloss_orig(t, big=True)}
    <p class="translit">{esc(t.get("translit", ""))}</p>
    <p class="ref-def">{esc(t.get("definicao", ""))}</p>
  </section>"""
        pages.append(Page(
            url=f'dicionario/{t["slug"]}/',
            title=f'{t["termo"]} ({t.get("translit", "")}): significado no original',
            description=t.get("definicao", ""),
            body=hub(prefix, [("Dicionário", "../"), (t["termo"], "")], lang_label(t.get("idioma", "")),
                     esc(t["termo"]), "Verbete do dicionário bíblico.",
                     hero + verses_section("Onde aparece", t.get("refs", []), verses_by_ref, prefix)
                     + related_articles(t["termo"], articles, prefix)),
            jsonld={"@context": "https://schema.org", "@type": "DefinedTerm", "name": t["termo"],
                    "description": t.get("definicao", ""), "inLanguage": "pt-BR"},
        ))
    return pages


# ---------- atlas ----------
PLACE_REGIONS = ["Mesopotâmia e origens", "Egito e o Êxodo", "Terra de Israel", "Mundo do Novo Testamento"]


def osm_url(lat, lon):
    # link (não embed) para o OpenStreetMap: mantém a CSP estrita e o modo offline
    return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=8/{lat}/{lon}"


def atlas_pages(places, verses_by_ref):
    if not places:
        return []
    by_region = defaultdict(list)
    for p in places:
        by_region[p.get("regiao", "Outros")].append(p)
    regions = PLACE_REGIONS + [r for r in by_region if r not in PLACE_REGIONS]
    sections = ""
    for region in regions:
        items = by_region.get(region, [])
        if not items:
            continue
        cards = "".join(ref_card(p.get("tipo", "Lugar"), esc(p["nome"]), p.get("descricao", ""), f'{p["slug"]}/')
                        for p in items)
        sections += f"""
  <section class="hub-section">
    <div class="section-title"><h2>{esc(region)}</h2><span>{plural(len(items), "lugar", "lugares")}</span></div>
    <div class="study-card-grid">{cards}</div>
  </section>"""
    pages = [Page(
        url="mapas/",
        title="Atlas bíblico: lugares da Bíblia",
        description="Lugares da Bíblia agrupados por região: Mesopotâmia, Egito, Terra de Israel e o mundo do Novo Testamento, com versículos e localização.",
        body=hub("../", [("Mapas", "")], "Biblioteca", "Atlas bíblico",
                 "Os lugares onde a história aconteceu, por região. Cada lugar abre com os versículos em que aparece e um link para o mapa.",
                 sections),
    )]
    for p in places:
        prefix = "../../"
        has_geo = p.get("lat") is not None and p.get("lon") is not None
        map_link = (f'<section class="hub-section"><p class="map-actions"><a class="btn ghost" '
                    f'href="{osm_url(p["lat"], p["lon"])}" target="_blank" rel="noopener">'
                    f'Ver no mapa (OpenStreetMap) ↗</a></p></section>') if has_geo else ""
        jsonld = {"@context": "https://schema.org", "@type": "Place", "name": p["nome"],
                  "description": p.get("descricao", "")}
        if has_geo:
            jsonld["geo"] = {"@type": "GeoCoordinates", "latitude": p["lat"], "longitude": p["lon"]}
        pages.append(Page(
            url=f'mapas/{p["slug"]}/',
            title=f'{p["nome"]} na Bíblia: versículos e localização',
            description=p.get("descricao", ""),
            body=hub(prefix, [("Mapas", "../"), (p["nome"], "")], p.get("tipo", "Lugar"), esc(p["nome"]),
                     esc(p.get("descricao", "")),
                     map_link + verses_section("Onde aparece", p.get("refs", []), verses_by_ref, prefix)),
            jsonld=jsonld,
        ))
    return pages


# ---------- léxico hebraico ----------
def strong_of(token):
    """'b/7225' -> '7225'; '1254 a' -> '1254'; 'c/d/776' -> '776'."""
    last = str(token).split("/")[-1].strip()
    m = re.match(r"\d+", last)
    return m.group(0) if m else ""


def lexicon_occurrences(hebrew_tokens):
    """{strong: [referências em ordem canônica]} a partir da tokenização do WLC."""
    occ = defaultdict(list)
    for ref, toks in hebrew_tokens.items():
        seen = set()
        for tok in toks:
            s = strong_of(tok[0]) if tok else ""
            if s and s not in seen:
                seen.add(s)
                occ[s].append(ref)
    return occ


def ref_book(ref):
    return ref.rsplit(" ", 1)[0]


LEXICON_SAMPLE = 12


def lexicon_pages(lexicon, hebrew_tokens, verses_by_ref):
    if not lexicon:
        return []
    occ = lexicon_occurrences(hebrew_tokens or {})
    canon = {livro: i for i, livro in enumerate(BOOK_ORDER)}

    entries = sorted(lexicon.items(), key=lambda kv: (-len(occ.get(kv[0], [])), int(kv[0])))
    rows = "".join(
        f"""
      <a class="lex-row" href="{num}/">
        <span class="lex-he scr-hebrew" dir="rtl" lang="he">{esc(e["he"])}</span>
        <span class="lex-tr">{esc(e["tr"])}</span>
        <span class="lex-pt">{esc(e["pt"])}</span>
        <span class="lex-n">{len(occ.get(num, []))} vers.</span>
      </a>"""
        for num, e in entries)
    pages = [Page(
        url="lexico/hebraico/",
        title="Léxico hebraico da Bíblia: significado de cada palavra",
        description=f"{len(lexicon)} palavras do hebraico bíblico com transliteração, significado em português, frequência e os versículos onde aparecem.",
        body=hub("../../", [("Dicionário", "../../dicionario/"), ("Léxico hebraico", "")], "Biblioteca",
                 "Léxico hebraico",
                 "Palavras do Antigo Testamento hebraico, da mais frequente para a menos frequente. Numeração de Strong; frequência contada no texto do Codex de Leningrado (WLC).",
                 f'<section class="hub-section"><div class="lex-list">{rows}\n    </div></section>'),
    )]
    for num, e in lexicon.items():
        prefix = "../../../"
        refs = occ.get(num, [])
        per_book = Counter(ref_book(r) for r in refs)
        books = "".join(
            f'<a class="chip" href="{prefix}ler/{book_slug(livro)}/">{esc(livro)} <b>{n}</b></a>'
            for livro, n in sorted(per_book.items(), key=lambda kv: canon.get(kv[0], 999)))
        stats = (f'Aparece em <b>{len(refs)}</b> versículo{"s" if len(refs) != 1 else ""} '
                 f'de <b>{len(per_book)}</b> livro{"s" if len(per_book) != 1 else ""}.') if refs else \
            "Ocorrências ainda não mapeadas para esta palavra."
        hero = f"""
  <section class="hub-section ref-hero">
    <p class="gloss-orig scr-hebrew gloss-big" dir="rtl" lang="he">{esc(e["he"])}</p>
    <p class="translit">{esc(e["tr"])} · Strong H{esc(num)}</p>
    <p class="ref-def">{esc(e["pt"])}</p>
    <p class="muted-line">{stats}</p>
  </section>"""
        books_html = f"""
  <section class="hub-section">
    <div class="section-title"><h2>Por livro</h2><span>Versículos com a palavra</span></div>
    <div class="chips">{books}</div>
  </section>""" if books else ""
        sample = refs[:LEXICON_SAMPLE]
        pages.append(Page(
            url=f"lexico/hebraico/{num}/",
            title=f'{e["tr"]} ({e["he"]}): significado no hebraico bíblico',
            description=f'{e["tr"]} ({e["he"]}), Strong H{num}: {e["pt"]}. Frequência e versículos onde aparece.',
            body=hub(prefix, [("Léxico hebraico", "../"), (e["tr"], "")], "Léxico hebraico",
                     f'{esc(e["tr"])}', f"Palavra hebraica · Strong H{esc(num)}",
                     hero + books_html
                     + verses_section(f"Primeiras ocorrências ({len(sample)} de {len(refs)})" if refs else "Ocorrências",
                                      sample, verses_by_ref, prefix)),
            jsonld={"@context": "https://schema.org", "@type": "DefinedTerm", "name": e["tr"],
                    "alternateName": e["he"], "description": e["pt"], "termCode": f"H{num}",
                    "inLanguage": "pt-BR"},
        ))
    return pages


# ---------- panorama dos livros (introdução em /ler/<livro>/) ----------
def book_intro_html(intro, livro, prefix, verses_by_ref):
    """Seção "Panorama do livro" para a página do livro; "" se não houver."""
    if not intro:
        return ""
    slug = book_slug(livro)
    facts = "".join(
        f"<div><dt>{esc(label)}</dt><dd>{esc(intro[key])}</dd></div>"
        for key, label in (("autoria", "Autoria"), ("data", "Data"), ("destinatarios", "Destinatários"),
                           ("genero", "Gênero"))
        if intro.get(key))
    outline = "".join(
        f'<li><a href="{prefix}ler/{slug}/{item["de"]}/">'
        f'<span class="outline-ch">{item["de"]}{"–" + str(item["ate"]) if item.get("ate", item["de"]) != item["de"] else ""}</span>'
        f' {esc(item["titulo"])}</a></li>'
        for item in intro.get("esboco", []))
    temas = "".join(f"<li>{esc(t)}</li>" for t in intro.get("temas", []))
    paras = "".join(f"<p>{esc(p)}</p>" for p in intro.get("contexto", []))
    key_verses = "".join(verse_card(r, verses_by_ref, prefix) for r in intro.get("versiculos_chave", []))
    fontes = "; ".join(esc(f) for f in intro.get("fontes", []))
    return f"""
  <section class="book-intro" id="panorama">
    <div class="section-title"><h2>Panorama de {esc(livro)}</h2><span>Contexto do livro</span></div>
    <p class="book-intro-lead">{esc(intro.get("resumo", ""))}</p>
    <dl class="book-facts">{facts}</dl>
    <div class="book-intro-text">{paras}</div>
    {f'<h3>Esboço</h3><ol class="book-outline">{outline}</ol>' if outline else ""}
    {f'<h3>Temas principais</h3><ul class="book-themes">{temas}</ul>' if temas else ""}
    {f'<h3>Versículos-chave</h3><div class="related-list">{key_verses}</div>' if key_verses else ""}
    {f'<p class="book-intro-src">Fontes: {fontes}</p>' if fontes else ""}
  </section>"""
