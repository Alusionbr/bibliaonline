#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera um protótipo navegável de arquivo único (inline CSS + dados + SPA JS)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = SITE / "data"
OUT = Path("/mnt/user-data/outputs/prototipo-biblia-em-contexto.html")

css = (SITE / "assets" / "styles.css").read_text(encoding="utf-8")
verses = json.loads((DATA / "verses.json").read_text(encoding="utf-8"))
topics = json.loads((DATA / "topics.json").read_text(encoding="utf-8"))
sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))

data_js = json.dumps({"verses": verses, "topics": topics, "sources": sources}, ensure_ascii=False)

html = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Protótipo — Bíblia em Contexto</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Spectral:wght@400;500;600&family=Inter:wght@400;600;700&family=Frank+Ruhl+Libre:wght@400;500;700&family=Gentium+Book+Plus:wght@400;700&display=swap" rel="stylesheet">
<style>
__CSS__
/* faixa de aviso só do protótipo */
.proto-bar{background:#241e16;color:#e7d6ab;font-family:"Inter",sans-serif;font-size:.78rem;
  text-align:center;padding:7px 14px;letter-spacing:.02em}
</style>
</head>
<body>
<div class="proto-bar">Protótipo navegável · toque em um versículo para ver a página completa</div>
<div id="app"></div>
<script>
const DB = __DATA__;
const VBY = Object.fromEntries(DB.verses.map(v=>[v.slug,v]));
function scrClass(v){return v.dir==='rtl' ? 'scr-hebrew' : 'scr-greek';}
function langLabel(i){return ({hebraico:'Hebraico',grego:'Grego',aramaico:'Aramaico'})[i]||i;}
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function dirAttr(v){return v.dir==='rtl'?' dir="rtl"':' dir="ltr"';}

function nav(){
  return `<nav class="nav"><div class="nav-in">
    <a class="brand" href="#/"><span class="brand-mark">ב</span><span class="brand-name">Bíblia em Contexto</span></a>
    <button class="menu-btn" id="mb" aria-label="Menu">☰</button>
    <div class="nav-links" id="nl">
      <a href="#/">Versículos</a><a href="#temas">Temas</a><a href="#fontes">Fontes</a>
    </div></div></nav>`;
}
function footer(){
  return `<footer class="footer"><div class="footer-in">
    <div><strong>Bíblia em Contexto</strong><p>Estudo bíblico com os idiomas originais, manuscritos e fontes rastreáveis.</p></div>
    <div class="cols"><div><a href="#/">Versículos</a><a href="#temas">Temas</a></div>
    <div><a href="#fontes">Fontes e licenças</a><a href="#/">Voltar ao topo ↑</a></div></div>
  </div></footer>`;
}
function specimen(v){
  const m=v.manuscrito||{};
  const seal=(m.licenca||'').toLowerCase().includes('domínio público')?'Domínio público':'Verificar licença';
  let frame;
  if(m.imagem){
    frame=`<div class="frame"><img loading="lazy" alt="${esc(m.legenda)}" src="${esc(m.imagem)}"
      onerror="this.closest('.specimen').querySelector('.frame').innerHTML='&lt;div class=&quot;ph&quot;&gt;&lt;b&gt;✶&lt;/b&gt;Imagem indisponível na prévia. No site publicado ela carrega do acervo.&lt;/div&gt;'"></div>`;
  }else{
    frame=`<div class="frame"><div class="ph"><b>✶</b>Imagem de manuscrito pendente de licença para este versículo.</div></div>`;
  }
  const link=m.fonte_url?` · <a href="${esc(m.fonte_url)}" target="_blank" rel="noopener">${esc(m.fonte_nome)} ↗</a>`:'';
  return `<figure class="specimen">${frame}<figcaption class="cap"><p>${esc(m.legenda)}</p>
    <div class="lic"><span class="seal">${esc(seal)}</span> ${esc(m.licenca)}${link}</div></figcaption></figure>`;
}
function home(){
  const f=VBY['genesis-1-1'];
  const chips=DB.topics.map(t=>`<a class="chip" href="#/"><span class="gl">${esc(t.icone)}</span>${esc(t.titulo)}</a>`).join('');
  const cards=DB.verses.map(v=>`<a class="card" href="#/v/${v.slug}">
    <div class="ref-row"><h3>${esc(v.referencia)}</h3><span class="lang-tag lang-${v.idioma}">${langLabel(v.idioma)}</span></div>
    <p class="orig-mini ${scrClass(v)}"${dirAttr(v)}>${esc(v.original.slice(0,60))}</p>
    <p class="pt-mini">${esc(v.texto_pt.slice(0,110))}${v.texto_pt.length>110?'…':''}</p>
    <span class="more">Ver no original →</span></a>`).join('');
  const src=DB.sources.slice(0,4).map(s=>`<div class="src"><h3>${esc(s.nome)}</h3>
    <p><b>Licença:</b> ${esc(s.licenca)}</p><span class="status">${esc(s.status)}</span></div>`).join('');
  return nav()+`
  <header class="hero" id="topo"><div class="hero-in">
    <div><p class="eyebrow on-dark">Idiomas originais · manuscritos · fontes</p>
      <h1>Leia o versículo na língua em que foi escrito.</h1>
      <p class="lead">Para cada texto: o original em hebraico, grego ou aramaico, uma tradução de domínio público, a foto do manuscrito quando existe e o comentário rabínico ou a origem.</p>
      <div class="hero-cta"><a class="btn primary" href="#/">Explorar versículos</a><a class="btn ghost" href="#fontes">Fontes e licenças</a></div>
    </div>
    <div class="specimen-card"><div class="ref-row"><span>${esc(f.referencia)}</span><span class="lang-tag lang-${f.idioma}">${langLabel(f.idioma)}</span></div>
      <div class="verse-stack"><p class="orig ${scrClass(f)}" dir="rtl">${esc(f.original)}</p>
      <p class="translit">${esc(f.transliteracao)}</p><p class="pt">${esc(f.texto_pt)}</p>
      <p class="pt-src">${esc(f.texto_pt_fonte)}</p></div></div>
  </div></header>
  <main>
    <section class="search-section"><div class="searchbox"><span class="ico">⌕</span>
      <input id="q" type="search" placeholder="Buscar: Salmo 23, shalom, logos, aramaico…" autocomplete="off"></div>
      <div id="results" class="search-results"></div></section>
    <section id="versiculos"><div class="sec-head"><p class="eyebrow">O texto, camada por camada</p>
      <h2>Versículos no original</h2><p>Cada cartão abre a página com original, tradução, manuscrito e comentário.</p></div>
      <div class="cards verses wrap">${cards}</div></section>
    <section id="temas" style="background:var(--vellum-2)"><div class="sec-head"><p class="eyebrow">Por onde começar</p>
      <h2>Temas de estudo</h2></div><div class="chips wrap">${chips}</div></section>
    <section id="fontes" class="sources"><div class="sec-head"><p class="eyebrow on-dark">Transparência</p>
      <h2>Fontes e licenças</h2><p>Só publicamos texto e imagem com origem e licença claras.</p></div>
      <div class="src-list wrap">${src}</div></section>
  </main>`+footer();
}
function verse(slug){
  const v=VBY[slug]; if(!v) return home();
  const idx=DB.verses.findIndex(x=>x.slug===slug);
  const prev=idx>0?DB.verses[idx-1]:null, next=idx<DB.verses.length-1?DB.verses[idx+1]:null;
  const prevH=prev?`<a class="pg prev" href="#/v/${prev.slug}"><span>← Anterior</span><b>${esc(prev.referencia)}</b></a>`:'<span class="pg empty"></span>';
  const nextH=next?`<a class="pg next" href="#/v/${next.slug}"><span>Próximo →</span><b>${esc(next.referencia)}</b></a>`:'<span class="pg empty"></span>';
  let blocks=`<section class="block"><h2><span class="dot"></span>Origem e transmissão</h2><p>${esc(v.origem)}</p></section>`;
  if(v.judaismo && v.leitura_judaica){
    blocks+=`<section class="block jewish"><h2><span class="dot"></span>Leitura judaica e comentário rabínico</h2><p>${esc(v.leitura_judaica)}</p></section>`;
  }
  const kw=(v.palavras||[]).map(p=>`<span class="tag">${esc(p)}</span>`).join('');
  return nav()+`<main class="wrap verse-page">
    <p class="crumb"><a href="#/">Início</a> · <a href="#/">Versículos</a> · ${esc(v.referencia)}</p>
    <header class="verse-head"><span class="lang-tag lang-${v.idioma}">${langLabel(v.idioma)}</span><h1>${esc(v.referencia)}</h1></header>
    <div class="verse-hero"><p class="orig ${scrClass(v)}"${dirAttr(v)}>${esc(v.original)}</p>
      <p class="translit">${esc(v.transliteracao)}</p><p class="pt">${esc(v.texto_pt)}</p>
      <p class="src-line">${esc(v.contexto)}</p></div>
    ${specimen(v)}
    ${blocks}
    <section class="block"><h2><span class="dot"></span>Palavras-chave</h2><div class="kw">${kw}</div></section>
    <p class="src-note">Original: ${esc(v.original_fonte)} · Tradução: ${esc(v.texto_pt_fonte)}</p>
    <nav class="pager" aria-label="Folhear">${prevH}${nextH}</nav>
    <p class="backline"><a href="#/">← Todos os versículos</a></p>
  </main>`+footer();
}
function runSearch(term){
  const out=document.getElementById('results'); if(!out) return;
  out.innerHTML=''; term=(term||'').trim().toLowerCase(); if(!term) return;
  const terms=term.split(/\s+/).filter(Boolean);
  const res=DB.verses.filter(v=>{
    const k=(v.referencia+' '+v.texto_pt+' '+v.contexto+' '+(v.palavras||[]).join(' ')).toLowerCase();
    return terms.every(t=>k.includes(t));
  }).sort((a,b)=>{
    const ka=(a.referencia+' '+a.texto_pt+' '+a.contexto).toLowerCase();
    const kb=(b.referencia+' '+b.texto_pt+' '+b.contexto).toLowerCase();
    return (kb.includes(term)?1:0)-(ka.includes(term)?1:0);
  }).slice(0,8);
  if(!res.length){out.innerHTML='<p class="empty">Nada encontrado. Tente “Salmo 23”, “logos” ou “aramaico”.</p>';return;}
  out.innerHTML=res.map(v=>`<a class="result" href="#/v/${v.slug}"><span class="kind">Versículo</span><h4>${esc(v.referencia)}</h4><p>${esc(v.texto_pt)}</p></a>`).join('');
}
function route(){
  const h=location.hash||'#/';
  const app=document.getElementById('app');
  if(h.startsWith('#/v/')){app.innerHTML=verse(h.slice(4)); window.scrollTo(0,0);}
  else{app.innerHTML=home();
    const q=document.getElementById('q'); if(q) q.addEventListener('input',e=>runSearch(e.target.value));
    if(h.length>2){const t=document.querySelector(h); if(t) setTimeout(()=>t.scrollIntoView({behavior:'smooth'}),60);}
  }
  const mb=document.getElementById('mb'); if(mb) mb.onclick=()=>document.getElementById('nl').classList.toggle('open');
}
window.addEventListener('hashchange',route);
route();
</script>
</body></html>"""

html = html.replace("__CSS__", css).replace("__DATA__", data_js)
OUT.write_text(html, encoding="utf-8")
print("OK:", OUT, f"({len(html)//1024} KB)")
