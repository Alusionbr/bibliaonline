// Sinaliza atividade para a gamificação (game.js). Se o game.js ainda não
// carregou (ordem dos <script>), enfileira em window.BEC_ACT para ele drenar.
function gameRecord(metric){
  try{
    if(window.BEC_GAME && window.BEC_GAME.record) window.BEC_GAME.record(metric);
    else (window.BEC_ACT=window.BEC_ACT||[]).push(metric);
  }catch(e){}
}

// Histórico de leitura: últimas páginas abertas (bec.history), mais recente primeiro
function becTouchHistory(url,label){
  try{
    var list=JSON.parse(localStorage.getItem('bec.history')||'[]')||[];
    list=list.filter(function(h){return h && h.url!==url;});
    list.unshift({url:url,label:label,at:new Date().toISOString()});
    localStorage.setItem('bec.history',JSON.stringify(list.slice(0,20)));
  }catch(e){}
}

// home: menu + busca local (índice embutido em window.__INDEX__)
document.addEventListener('click',function(e){
  if(e.target.closest('[data-menu]')){document.querySelector('[data-links]').classList.toggle('open');}
});
(function(){
  var q=document.getElementById('q'), out=document.getElementById('results');
  if(!q||!out) return;
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
    var terms=term.split(/\s+/).filter(Boolean);
    var res=IDX.filter(function(i){
      return terms.every(function(t){return i.kf.indexOf(t)>-1;});
    });
    // quem casa o termo inteiro e contíguo vem primeiro (ordenação estável)
    res.sort(function(a,b){return (b.kf.indexOf(term)>-1)-(a.kf.indexOf(term)>-1);});
    res=res.slice(0,8);
    if(!res.length){out.innerHTML='<p class="empty">Nada encontrado. Tente “Salmo 23”, “shalom”, “logos” ou “aramaico”.</p>';return;}
    res.forEach(function(i){
      var a=document.createElement('a');a.className='result';a.href=i.url;
      a.innerHTML='<span class="kind">'+i.t+'</span><h4>'+i.titulo+'</h4><p>'+i.desc+'</p>';
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
        try{
          var ref=en.target.getAttribute('data-ref')||'';
          if(ref){
            localStorage.setItem('bec.lastRead', JSON.stringify({url:location.pathname, label:ref}));
            becTouchHistory(location.pathname, ref);
          }
        }catch(e){}
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
        document.dispatchEvent(new CustomEvent('bec:content-added', {detail:{root:imp}}));
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
  var THEMES=['light','sepia','dark'];
  function applyFont(i){ d.classList.remove('fs-0','fs-1','fs-2','fs-3'); d.classList.add('fs-'+i); try{localStorage.setItem('bec.fontscale',i);}catch(e){} }
  function curFont(){ var f=parseInt(localStorage.getItem('bec.fontscale'),10); return isNaN(f)?1:f; }
  function curTheme(){ var t=localStorage.getItem('bec.theme'); return THEMES.indexOf(t)>-1?t:'light'; }
  function applyTheme(t){
    d.classList.remove('sepia','dark');
    if(t==='dark') d.classList.add('dark'); else if(t==='sepia') d.classList.add('sepia');
    try{localStorage.setItem('bec.theme',t);}catch(e){}
    if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
  }
  function origOn(){ return localStorage.getItem('bec.origmode')==='1'; }
  function syncOrigBtns(){
    var on=d.classList.contains('orig-on');
    document.querySelectorAll('[data-rt="orig"]').forEach(function(b){
      b.setAttribute('aria-pressed', on?'true':'false');
      b.classList.toggle('on', on);
    });
  }
  function applyOrig(on){
    d.classList.toggle('orig-on', on);
    try{localStorage.setItem('bec.origmode', on?'1':'0');}catch(e){}
    if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
    syncOrigBtns();
  }
  document.addEventListener('click',function(e){
    var b=e.target.closest && e.target.closest('[data-rt]'); if(!b) return;
    var rt=b.getAttribute('data-rt');
    if(rt==='font-inc') applyFont(Math.min(3,curFont()+1));
    else if(rt==='font-dec') applyFont(Math.max(0,curFont()-1));
    else if(rt==='theme'){ var i=THEMES.indexOf(curTheme()); applyTheme(THEMES[(i+1)%THEMES.length]); }
    else if(rt==='orig') applyOrig(!d.classList.contains('orig-on'));
  });
  syncOrigBtns();
  // reaplica preferências quando a sincronização traz mudanças de outro aparelho
  document.addEventListener('bec:study-sync',function(){
    var t=curTheme();
    d.classList.toggle('dark', t==='dark');
    d.classList.toggle('sepia', t==='sepia');
    d.classList.toggle('orig-on', origOn());
    d.classList.remove('fs-0','fs-1','fs-2','fs-3'); d.classList.add('fs-'+curFont());
    syncOrigBtns();
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
    try{
      localStorage.setItem('bec.lastRead', JSON.stringify({url:location.pathname, label:h1.textContent.trim()}));
      becTouchHistory(location.pathname, h1.textContent.trim());
    }catch(e){}
    // Abrir o capítulo NÃO conta como leitura: o progresso e a missão de leitura
    // só avançam quando o usuário marca um trecho como lido (ver bec.readingRanges).
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
      gameRecord('meditate');
      fetch('data/random.json').then(function(r){return r.json();}).then(function(list){
        if(list && list.length){ var s=list[Math.floor(Math.random()*list.length)]; location.href='versiculos/'+s+'/'; }
        else rb.disabled=false;
      }).catch(function(){ rb.disabled=false; });
    });
  }
})();

// audio de leitura + favoritos (sem arquivos de audio hospedados)
(function(){
  function loadFavs(){try{return JSON.parse(localStorage.getItem('bec.favs')||'{}');}catch(e){return{};}}
  function saveFavs(v){try{localStorage.setItem('bec.favs',JSON.stringify(v));}catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty();}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function updateFavButtons(){
    var favs=loadFavs();
    document.querySelectorAll('[data-fav]').forEach(function(b){
      var ref=b.getAttribute('data-ref')||'';
      var on=!!favs[ref];
      b.setAttribute('aria-pressed', on?'true':'false');
      b.classList.toggle('on', on);
      b.textContent=on?'★ Favorito':'☆ Favoritar';
    });
  }
  function renderFavHome(){
    var box=document.getElementById('favorite-home'), list=document.getElementById('favorite-list');
    if(!box||!list) return;
    var favs=loadFavs();
    var keys=Object.keys(favs).sort();
    if(!keys.length){ box.hidden=true; list.innerHTML=''; return; }
    box.hidden=false;
    list.innerHTML=keys.slice(0,8).map(function(ref){
      var item=favs[ref]||{};
      return '<a class="favorite-item" href="'+esc(item.url||'#')+'">'+esc(ref)+'</a>';
    }).join('');
  }
  function renderFavFull(){
    var box=document.querySelector('[data-fav-full-list]');
    if(!box) return;
    var favs=loadFavs();
    var keys=Object.keys(favs).sort();
    if(!keys.length){ box.innerHTML='<p class="muted-line">Nenhum versículo favoritado ainda. Toque em ☆ Favoritar durante a leitura.</p>'; return; }
    box.innerHTML=keys.map(function(ref){
      var item=favs[ref]||{};
      return '<div class="fav-row"><a href="'+esc(item.url||'#')+'">'+esc(ref)+'</a>'+
        '<button type="button" class="btn tiny ghost" data-fav-del="'+esc(ref)+'">Remover</button></div>';
    }).join('');
  }
  function speak(text, lang, btn){
    if(!('speechSynthesis' in window)){ if(btn){btn.textContent='Sem voz neste navegador';} return; }
    window.speechSynthesis.cancel();
    showTranscript(btn);
    var u=new SpeechSynthesisUtterance(text);
    u.lang=lang||'pt-BR';
    u.rate=(lang==='he-IL'||lang==='el-GR')?0.82:0.92;
    u.onend=function(){ if(btn && btn.dataset.oldText){btn.textContent=btn.dataset.oldText; delete btn.dataset.oldText;} };
    u.onerror=u.onend;
    if(btn){ btn.dataset.oldText=btn.textContent; btn.textContent='Pausar'; }
    window.speechSynthesis.speak(u);
  }
  function showTranscript(btn){
    if(!btn) return;
    var transcript=btn.getAttribute('data-transcript')||'';
    if(!transcript) return;
    var tools=btn.closest && btn.closest('.verse-tools');
    if(!tools) return;
    var box=tools.querySelector('.audio-transcript');
    if(!box){
      box=document.createElement('p');
      box.className='audio-transcript';
      tools.appendChild(box);
    }
    var label=btn.getAttribute('data-transcript-label')||'Transcrição do áudio original';
    box.innerHTML='<span>'+esc(label)+'</span><b>'+esc(transcript)+'</b>';
    box.hidden=false;
  }
  document.addEventListener('click',function(e){
    var sp=e.target.closest && e.target.closest('[data-speak]');
    if(sp){
      var text=sp.getAttribute('data-speak')||'';
      if(!text) return;
      if(sp.textContent==='Pausar'){ if('speechSynthesis' in window) window.speechSynthesis.cancel(); sp.textContent=sp.dataset.oldText||'Ouvir'; return; }
      speak(text, sp.getAttribute('data-lang')||'pt-BR', sp);
      return;
    }
    var del=e.target.closest && e.target.closest('[data-fav-del]');
    if(del){
      var dref=del.getAttribute('data-fav-del')||'';
      var dfavs=loadFavs();
      if(dref && dfavs[dref]){ delete dfavs[dref]; saveFavs(dfavs); updateFavButtons(); renderFavHome(); renderFavFull(); }
      return;
    }
    var fav=e.target.closest && e.target.closest('[data-fav]');
    if(fav){
      var ref=fav.getAttribute('data-ref')||'', url=fav.getAttribute('data-url')||location.pathname;
      if(!ref) return;
      var favs=loadFavs();
      if(favs[ref]) delete favs[ref]; else favs[ref]={url:url, savedAt:new Date().toISOString()};
      saveFavs(favs);
      updateFavButtons();
      renderFavHome();
      renderFavFull();
    }
  });
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',function(){updateFavButtons();renderFavHome();renderFavFull();});
  else { updateFavButtons(); renderFavHome(); renderFavFull(); }
  document.addEventListener('bec:study-sync', function(){ updateFavButtons(); renderFavHome(); renderFavFull(); });
  if(window.MutationObserver){
    var favMoTimer=null;
    new MutationObserver(function(){
      if(favMoTimer) return;
      favMoTimer=setTimeout(function(){ favMoTimer=null; updateFavButtons(); },150);
    }).observe(document.documentElement,{childList:true,subtree:true});
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

// Criar Plano: primeira versão local, preparada para sincronização futura
(function(){
  var form=document.querySelector('[data-plan-form]');
  var list=document.querySelector('[data-plan-list]');
  if(!form||!list) return;
  function load(){try{return JSON.parse(localStorage.getItem('bec.studyPlans')||'[]');}catch(e){return[];}}
  function save(plans){try{localStorage.setItem('bec.studyPlans',JSON.stringify(plans));}catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty();}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function render(){
    var plans=load();
    if(!plans.length){list.innerHTML='<p class="muted-line">Nenhum plano salvo neste navegador.</p>';return;}
    list.innerHTML='<h3>Planos salvos</h3>'+plans.map(function(p){
      return '<article class="saved-plan"><b>'+esc(p.conteudo)+'</b><span>'+esc(p.tipo)+' · '+esc(p.duracao)+' · '+esc(p.ritmo)+' · '+esc(p.visibilidade)+'</span></article>';
    }).join('');
  }
  form.addEventListener('submit',function(e){
    e.preventDefault();
    var data=new FormData(form);
    var plan={
      tipo:data.get('tipo')||'Livro',
      conteudo:(data.get('conteudo')||'').toString().trim(),
      duracao:data.get('duracao')||'7 dias',
      ritmo:data.get('ritmo')||'Leve',
      visibilidade:data.get('visibilidade')||'Privado',
      createdAt:new Date().toISOString()
    };
    if(!plan.conteudo) return;
    var plans=load();
    plans.unshift(plan);
    save(plans.slice(0,12));
    form.reset();
    render();
  });
  render();
})();

// Planos de leitura: progresso por dia (bec.planProgress), com sincronização
(function(){
  var boxes=document.querySelectorAll('input[data-plan]');
  if(!boxes.length) return;
  var KEY='bec.planProgress';
  function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')||{};}catch(e){return {};}}
  function save(all){try{localStorage.setItem(KEY,JSON.stringify(all));}catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty();}
  function paint(){
    var all=load();
    var done={};
    boxes.forEach(function(b){
      var slug=b.getAttribute('data-plan'), day=+b.getAttribute('data-day');
      var days=all[slug]||[];
      b.checked=days.indexOf(day)>-1;
      var row=b.closest('.plan-day'); if(row) row.classList.toggle('done', b.checked);
      done[slug]=(done[slug]||0)+(b.checked?1:0);
    });
    document.querySelectorAll('[data-plan-progress]').forEach(function(el){
      var slug=el.getAttribute('data-plan-slug');
      var total=document.querySelectorAll('input[data-plan="'+slug+'"]').length;
      el.textContent=(done[slug]||0)+' de '+total+' dias';
    });
  }
  document.addEventListener('change',function(e){
    var b=e.target.closest && e.target.closest('input[data-plan]');
    if(!b) return;
    var slug=b.getAttribute('data-plan'), day=+b.getAttribute('data-day');
    var all=load(), days=all[slug]||[];
    var pos=days.indexOf(day);
    if(b.checked && pos<0) days.push(day);
    if(!b.checked && pos>-1) days.splice(pos,1);
    if(days.length) all[slug]=days; else delete all[slug];
    save(all);
    paint();
  });
  document.addEventListener('click',function(e){
    var btn=e.target.closest && e.target.closest('[data-plan-reset]');
    if(!btn) return;
    var slug=btn.getAttribute('data-plan-reset');
    var all=load();
    if(!all[slug]) return;
    delete all[slug];
    save(all);
    paint();
  });
  document.addEventListener('bec:study-sync', paint);
  paint();
})();

// Histórico de leitura no Workspace
(function(){
  var box=document.querySelector('[data-history-list]');
  if(!box) return;
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function render(){
    var list=[];
    try{list=JSON.parse(localStorage.getItem('bec.history')||'[]')||[];}catch(e){}
    if(!list.length){ box.innerHTML='<p class="muted-line">Nenhuma leitura recente neste navegador. Abra um capítulo na Bíblia para começar.</p>'; return; }
    box.innerHTML=list.map(function(h){
      var when='';
      try{ when=new Date(h.at).toLocaleDateString('pt-BR'); }catch(e){}
      return '<a class="history-row" href="'+esc(h.url)+'"><b>'+esc(h.label)+'</b><span>'+esc(when)+'</span></a>';
    }).join('');
  }
  document.addEventListener('bec:study-sync', render);
  render();
})();

// Destaca a seção atual na navegação (desktop e barra inferior mobile)
(function(){
  var path=location.pathname;
  document.querySelectorAll('.nav-links a, .mobile-primary-nav a').forEach(function(a){
    var href=a.getAttribute('href')||'';
    var clean=href.replace(/index\.html$/,'');
    var section=clean.replace(/^(\.\.\/)+|^\.\//g,'');
    var on=false;
    if(section==='' ){ on=/^\/(index\.html)?$/.test(path)||/\/bibliaonline\/(index\.html)?$/.test(path); }
    else { on=path.indexOf('/'+section)>-1; }
    if(section==='ler/') on=on||path.indexOf('/versiculos/')>-1;
    if(on){ a.classList.add('active'); a.setAttribute('aria-current','page'); }
  });
})();

// Progresso por trecho estudado no capítulo (bec.readingRanges), com sincronização.
// Marca do versículo X ao Y sem exigir o capítulo inteiro.
(function(){
  var panel=document.querySelector('[data-study-frac]');
  if(!panel) return;
  var KEY='bec.readingRanges';
  var chapterRef=panel.getAttribute('data-chapter-ref')||'';
  var total=parseInt(panel.getAttribute('data-total'),10)||0;
  var startSel=panel.querySelector('[data-sf-start]');
  var endSel=panel.querySelector('[data-sf-end]');
  var saveBtn=panel.querySelector('[data-sf-save]');
  var bar=panel.querySelector('[data-sf-bar]');
  var pctEl=panel.querySelector('[data-sf-pct]');
  var listEl=panel.querySelector('[data-sf-list]');
  var rangeEl=panel.querySelector('[data-sf-range]');
  var markHint=panel.querySelector('[data-sf-mark-hint]');
  var markBtns=Array.prototype.slice.call(panel.querySelectorAll('[data-sf-mark]'));
  var chapterBox=document.querySelector('.chapter');
  if(!startSel||!endSel||!saveBtn||!bar||!listEl||!total) return;

  var markMode=null; // 'start' | 'end' | null

  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function curStart(){var n=parseInt(startSel.value,10);return isNaN(n)?null:n;}
  function curEnd(){var n=parseInt(endSel.value,10);return isNaN(n)?null:n;}
  function updateRangeLabel(){
    if(!rangeEl) return;
    var s=curStart(), e=curEnd();
    rangeEl.textContent='Início: '+(s!=null?s:'—')+' · Fim: '+(e!=null?e:'—');
  }
  function clearPreview(){
    if(!chapterBox) return;
    chapterBox.querySelectorAll('.sf-preview,.sf-mark-start,.sf-mark-end').forEach(function(v){
      v.classList.remove('sf-preview','sf-mark-start','sf-mark-end');
    });
  }
  function preview(){
    clearPreview();
    if(!chapterBox) return;
    var s=curStart(), e=curEnd();
    if(s==null||e==null) return;
    var lo=Math.min(s,e), hi=Math.max(s,e);
    for(var i=lo;i<=hi;i++){ var v=document.getElementById('v'+i); if(v) v.classList.add('sf-preview'); }
    var vs=document.getElementById('v'+s); if(vs) vs.classList.add('sf-mark-start');
    var ve=document.getElementById('v'+e); if(ve) ve.classList.add('sf-mark-end');
  }
  function setMarkMode(mode){
    markMode=mode;
    markBtns.forEach(function(b){
      var on=b.getAttribute('data-sf-mark')===mode;
      b.classList.toggle('on',on); b.setAttribute('aria-pressed',on?'true':'false');
    });
    if(markHint){
      if(mode){ markHint.hidden=false; markHint.textContent = mode==='start' ? 'Toque no versículo onde começou a leitura.' : 'Toque no versículo onde parou a leitura.'; }
      else markHint.hidden=true;
    }
    document.body.classList.toggle('sf-marking', !!mode);
  }
  function loadAll(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')||{};}catch(e){return {};}}
  function saveAll(all){try{localStorage.setItem(KEY,JSON.stringify(all));}catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty();}
  function getRanges(){var r=loadAll()[chapterRef];return Array.isArray(r)?r:[];}
  function setRanges(r){var all=loadAll(); if(r.length) all[chapterRef]=r; else delete all[chapterRef]; saveAll(all);}

  // ordena e funde trechos que se tocam ou se sobrepõem
  function normalize(r){
    var arr=(r||[]).map(function(x){
      var a=parseInt(x.s,10), b=parseInt(x.e,10);
      return {s:Math.min(a,b), e:Math.max(a,b)};
    }).filter(function(x){return !isNaN(x.s)&&!isNaN(x.e);})
      .sort(function(a,b){return a.s-b.s;});
    var out=[];
    arr.forEach(function(x){
      var last=out[out.length-1];
      if(last && x.s<=last.e+1) last.e=Math.max(last.e,x.e);
      else out.push({s:x.s,e:x.e});
    });
    return out;
  }
  function coverage(r){
    var n=0; r.forEach(function(x){ n+=(x.e-x.s+1); });
    return total ? Math.min(100, Math.round((n/total)*100)) : 0;
  }
  function paint(){
    var r=normalize(getRanges());
    bar.innerHTML='';
    r.forEach(function(x){
      var seg=document.createElement('span');
      seg.className='sf-segment';
      seg.style.left=(((x.s-1)/total)*100)+'%';
      seg.style.width=Math.max(((x.e-x.s+1)/total)*100, 2)+'%';
      bar.appendChild(seg);
    });
    if(pctEl) pctEl.textContent=coverage(r)+'%';
    document.querySelectorAll('.ch-verse.studied').forEach(function(v){v.classList.remove('studied');});
    r.forEach(function(x){
      for(var i=x.s;i<=x.e;i++){ var v=document.getElementById('v'+i); if(v) v.classList.add('studied'); }
    });
    if(!r.length){
      listEl.innerHTML='<li class="sf-empty">Nenhum trecho salvo ainda. Marque o início e o fim da leitura e toque em “Salvar trecho”.</li>';
    } else {
      listEl.innerHTML=r.map(function(x,idx){
        var label=x.s===x.e ? ('versículo '+x.s) : ('versículos '+x.s+'–'+x.e);
        return '<li class="sf-item"><span>'+esc(chapterRef)+' · '+label+'</span>'+
          '<button type="button" class="btn tiny ghost" data-sf-del="'+idx+'" aria-label="Remover trecho">Remover</button></li>';
      }).join('');
    }
    updateRangeLabel();
  }

  // botões "Marcar início" / "Marcar fim": armam o modo de toque no versículo
  markBtns.forEach(function(b){
    b.addEventListener('click',function(){
      var m=b.getAttribute('data-sf-mark');
      setMarkMode(markMode===m ? null : m);
    });
  });

  // no modo marcação, tocar num versículo define início/fim (sem navegar)
  if(chapterBox){
    chapterBox.addEventListener('click',function(ev){
      if(!markMode) return;
      if(ev.target.closest && ev.target.closest('.verse-tools')) return; // ferramentas continuam funcionando
      var v=ev.target.closest && ev.target.closest('.ch-verse'); if(!v) return;
      var n=parseInt((v.id||'').replace(/^v/,''),10); if(isNaN(n)) return;
      ev.preventDefault();
      var wasStart=(markMode==='start');
      if(wasStart) startSel.value=String(n); else endSel.value=String(n);
      updateRangeLabel(); preview();
      // após marcar o início, pede o fim automaticamente (fluxo de dois toques)
      if(wasStart) setMarkMode('end'); else setMarkMode(null);
    });
  }

  startSel.addEventListener('change',function(){ updateRangeLabel(); preview(); });
  endSel.addEventListener('change',function(){ updateRangeLabel(); preview(); });

  saveBtn.addEventListener('click',function(){
    var s=curStart(), e=curEnd();
    if(s==null||e==null) return;
    var r=getRanges(); r.push({s:s,e:e});
    setRanges(normalize(r));
    setMarkMode(null); clearPreview();
    paint();
    // Evento real de leitura: marcar um trecho credita a missão de leitura,
    // uma vez por capítulo por dia (abrir o capítulo, por si só, não conta).
    try{
      var mark=new Date().toISOString().slice(0,10)+'|'+chapterRef;
      if(localStorage.getItem('bec.game.readMark')!==mark){
        localStorage.setItem('bec.game.readMark',mark);
        gameRecord('read_chapters');
      }
    }catch(err){}
    var old=saveBtn.textContent;
    saveBtn.textContent='Salvo ✓';
    setTimeout(function(){ saveBtn.textContent=old; }, 1400);
  });

  listEl.addEventListener('click',function(ev){
    var del=ev.target.closest && ev.target.closest('[data-sf-del]');
    if(!del) return;
    var idx=parseInt(del.getAttribute('data-sf-del'),10);
    var r=normalize(getRanges());
    if(idx>=0 && idx<r.length){ r.splice(idx,1); setRanges(r); paint(); }
  });

  if(endSel.options.length) endSel.selectedIndex=endSel.options.length-1;
  document.addEventListener('bec:study-sync', paint);
  paint();
})();

// FAB de ferramentas de leitura (celular): abre um painel com fonte, original,
// tema, marcar início/fim/salvar e reportar. Fonte/original/tema/reportar
// reaproveitam os gatilhos delegados (data-rt, data-report-open); marcar e
// salvar acionam os botões reais do painel de progresso.
(function(){
  var fab=document.querySelector('[data-reader-fab]'); if(!fab) return;
  var toggle=fab.querySelector('[data-reader-fab-toggle]');
  var panel=fab.querySelector('[data-reader-fab-panel]');
  var configBtn=fab.querySelector('[data-reader-fab-config]');
  var configPanel=fab.querySelector('[data-reader-fab-config-panel]');
  if(!toggle||!panel) return;

  var TOOLS_KEY='bec.readerTools', POS_KEY='bec.fabPos';
  var LABELS={'font-dec':'Diminuir fonte','font-inc':'Aumentar fonte','orig':'Idioma original',
    'theme':'Tema','mark-start':'Marcar início','mark-end':'Marcar fim','save':'Salvar trecho','report':'Reportar'};

  function toolButtons(){return Array.prototype.slice.call(panel.querySelectorAll('.rfb[data-tool]'));}
  function allTools(){return toolButtons().map(function(b){return b.getAttribute('data-tool');});}
  function loadEnabled(){
    try{var v=JSON.parse(localStorage.getItem(TOOLS_KEY)||'null'); if(Array.isArray(v)) return v;}catch(e){}
    return allTools(); // padrão: todas as ferramentas visíveis
  }
  function saveEnabled(list){
    try{localStorage.setItem(TOOLS_KEY, JSON.stringify(list));}catch(e){}
    if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
  }
  function applyEnabled(){
    var en=loadEnabled();
    toolButtons().forEach(function(b){ b.hidden = en.indexOf(b.getAttribute('data-tool'))<0; });
  }

  function setOpen(open){
    panel.hidden=!open;
    toggle.setAttribute('aria-expanded', open?'true':'false');
    toggle.textContent=open?'✕':'⚙';
    if(!open && configPanel){ configPanel.hidden=true; if(configBtn) configBtn.setAttribute('aria-expanded','false'); }
  }

  // --- Personalizar quais ferramentas aparecem -----------------------------
  function buildConfig(){
    if(!configPanel) return;
    var en=loadEnabled();
    configPanel.innerHTML=allTools().map(function(t){
      var on=en.indexOf(t)>=0;
      return '<label class="fab-cfg-row"><input type="checkbox" data-tool-cfg="'+t+'"'+(on?' checked':'')+'>'+
        '<span>'+(LABELS[t]||t)+'</span></label>';
    }).join('');
  }
  if(configBtn && configPanel){
    configBtn.addEventListener('click',function(){
      var open=configPanel.hidden;
      if(open) buildConfig();
      configPanel.hidden=!open;
      configBtn.setAttribute('aria-expanded', open?'true':'false');
    });
    configPanel.addEventListener('change',function(ev){
      var cb=ev.target.closest && ev.target.closest('[data-tool-cfg]'); if(!cb) return;
      var en=loadEnabled(), t=cb.getAttribute('data-tool-cfg'), i=en.indexOf(t);
      if(cb.checked && i<0) en.push(t);
      else if(!cb.checked && i>=0) en.splice(i,1);
      saveEnabled(en); applyEnabled();
    });
  }

  // --- Acões das ferramentas de progresso (marcar/salvar) ------------------
  panel.addEventListener('click',function(ev){
    var mk=ev.target.closest && ev.target.closest('[data-fab-mark]');
    if(mk){ var b=document.querySelector('[data-study-frac] [data-sf-mark="'+mk.getAttribute('data-fab-mark')+'"]'); if(b) b.click(); setOpen(false); return; }
    var sv=ev.target.closest && ev.target.closest('[data-fab-save]');
    if(sv){ var s=document.querySelector('[data-study-frac] [data-sf-save]'); if(s) s.click(); setOpen(false); return; }
    // reportar fecha o painel (o modal assume); fonte/original/tema mantêm aberto
    if(ev.target.closest && ev.target.closest('[data-report-open]')) setOpen(false);
  });
  document.addEventListener('click',function(ev){
    if(panel.hidden) return;
    if(ev.target.closest && ev.target.closest('[data-reader-fab]')) return;
    setOpen(false);
  });

  // --- Posição arrastável do FAB (salva por usuário) -----------------------
  function applyPos(){
    try{var p=JSON.parse(localStorage.getItem(POS_KEY)||'null');
      if(p&&isFinite(p.right)&&isFinite(p.bottom)){ fab.style.right=p.right+'px'; fab.style.bottom=p.bottom+'px'; }
    }catch(e){}
  }
  applyPos();

  var drag=null, suppressClick=false;
  toggle.addEventListener('pointerdown',function(ev){
    var r=fab.getBoundingClientRect();
    drag={x:ev.clientX,y:ev.clientY,moved:false,
      right:window.innerWidth-r.right, bottom:window.innerHeight-r.bottom, curR:null, curB:null};
    try{toggle.setPointerCapture(ev.pointerId);}catch(e){}
  });
  toggle.addEventListener('pointermove',function(ev){
    if(!drag) return;
    var dx=ev.clientX-drag.x, dy=ev.clientY-drag.y;
    if(!drag.moved && Math.abs(dx)+Math.abs(dy)>6) drag.moved=true;
    if(drag.moved){
      var right=Math.max(6, Math.min(window.innerWidth-58, drag.right-dx));
      var bottom=Math.max(6, Math.min(window.innerHeight-58, drag.bottom-dy));
      fab.style.right=right+'px'; fab.style.bottom=bottom+'px';
      drag.curR=right; drag.curB=bottom;
    }
  });
  toggle.addEventListener('pointerup',function(){
    if(!drag) return;
    if(drag.moved && drag.curR!=null){
      suppressClick=true; // não abrir/fechar logo após arrastar
      try{localStorage.setItem(POS_KEY, JSON.stringify({right:Math.round(drag.curR),bottom:Math.round(drag.curB)}));}catch(e){}
      if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
    }
    drag=null;
  });
  toggle.addEventListener('click',function(){
    if(suppressClick){ suppressClick=false; return; } // clique fantasma após arrastar
    setOpen(panel.hidden);
  });

  applyEnabled();
  document.addEventListener('bec:study-sync', function(){ applyEnabled(); applyPos(); });
})();
