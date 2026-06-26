// home: menu + busca local (índice embutido em window.__INDEX__)
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
