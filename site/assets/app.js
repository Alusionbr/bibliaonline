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
    try{
      localStorage.setItem('bec.lastRead', JSON.stringify({url:location.pathname, label:h1.textContent.trim()}));
      becTouchHistory(location.pathname, h1.textContent.trim());
    }catch(e){}
    // missão "ler um capítulo": credita uma vez por dia por página
    try{
      var mark=new Date().toISOString().slice(0,10)+'|'+location.pathname;
      if(localStorage.getItem('bec.game.readMark')!==mark){
        localStorage.setItem('bec.game.readMark',mark);
        gameRecord('read_chapters');
      }
    }catch(e){}
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
