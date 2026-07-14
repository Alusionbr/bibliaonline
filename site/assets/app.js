var BEC_BOOKS=[{"nome": "Gênesis", "slug": "genesis", "cap": 50}, {"nome": "Êxodo", "slug": "exodo", "cap": 40}, {"nome": "Levítico", "slug": "levitico", "cap": 27}, {"nome": "Números", "slug": "numeros", "cap": 36}, {"nome": "Deuteronômio", "slug": "deuteronomio", "cap": 34}, {"nome": "Josué", "slug": "josue", "cap": 24}, {"nome": "Juízes", "slug": "juizes", "cap": 21}, {"nome": "Rute", "slug": "rute", "cap": 4}, {"nome": "1 Samuel", "slug": "1-samuel", "cap": 31}, {"nome": "2 Samuel", "slug": "2-samuel", "cap": 24}, {"nome": "1 Reis", "slug": "1-reis", "cap": 22}, {"nome": "2 Reis", "slug": "2-reis", "cap": 25}, {"nome": "1 Crônicas", "slug": "1-cronicas", "cap": 29}, {"nome": "2 Crônicas", "slug": "2-cronicas", "cap": 36}, {"nome": "Esdras", "slug": "esdras", "cap": 10}, {"nome": "Neemias", "slug": "neemias", "cap": 13}, {"nome": "Ester", "slug": "ester", "cap": 10}, {"nome": "Jó", "slug": "jo", "cap": 42}, {"nome": "Salmos", "slug": "salmos", "cap": 150}, {"nome": "Provérbios", "slug": "proverbios", "cap": 31}, {"nome": "Eclesiastes", "slug": "eclesiastes", "cap": 12}, {"nome": "Cânticos", "slug": "canticos", "cap": 8}, {"nome": "Isaías", "slug": "isaias", "cap": 66}, {"nome": "Jeremias", "slug": "jeremias", "cap": 52}, {"nome": "Lamentações", "slug": "lamentacoes", "cap": 5}, {"nome": "Ezequiel", "slug": "ezequiel", "cap": 48}, {"nome": "Daniel", "slug": "daniel", "cap": 12}, {"nome": "Oseias", "slug": "oseias", "cap": 14}, {"nome": "Joel", "slug": "joel", "cap": 4}, {"nome": "Amós", "slug": "amos", "cap": 9}, {"nome": "Obadias", "slug": "obadias", "cap": 1}, {"nome": "Jonas", "slug": "jonas", "cap": 4}, {"nome": "Miquéias", "slug": "miqueias", "cap": 7}, {"nome": "Naum", "slug": "naum", "cap": 3}, {"nome": "Habacuque", "slug": "habacuque", "cap": 3}, {"nome": "Sofonias", "slug": "sofonias", "cap": 3}, {"nome": "Ageu", "slug": "ageu", "cap": 2}, {"nome": "Zacarias", "slug": "zacarias", "cap": 14}, {"nome": "Malaquias", "slug": "malaquias", "cap": 3}, {"nome": "Mateus", "slug": "mateus", "cap": 28}, {"nome": "Marcos", "slug": "marcos", "cap": 16}, {"nome": "Lucas", "slug": "lucas", "cap": 24}, {"nome": "João", "slug": "joao", "cap": 21}, {"nome": "Atos", "slug": "atos", "cap": 28}, {"nome": "Romanos", "slug": "romanos", "cap": 16}, {"nome": "1 Coríntios", "slug": "1-corintios", "cap": 16}, {"nome": "2 Coríntios", "slug": "2-corintios", "cap": 13}, {"nome": "Gálatas", "slug": "galatas", "cap": 6}, {"nome": "Efésios", "slug": "efesios", "cap": 6}, {"nome": "Filipenses", "slug": "filipenses", "cap": 4}, {"nome": "Colossenses", "slug": "colossenses", "cap": 4}, {"nome": "1 Tessalonicenses", "slug": "1-tessalonicenses", "cap": 5}, {"nome": "2 Tessalonicenses", "slug": "2-tessalonicenses", "cap": 3}, {"nome": "1 Timóteo", "slug": "1-timoteo", "cap": 6}, {"nome": "2 Timóteo", "slug": "2-timoteo", "cap": 4}, {"nome": "Tito", "slug": "tito", "cap": 3}, {"nome": "Filemom", "slug": "filemom", "cap": 1}, {"nome": "Hebreus", "slug": "hebreus", "cap": 13}, {"nome": "Tiago", "slug": "tiago", "cap": 5}, {"nome": "1 Pedro", "slug": "1-pedro", "cap": 5}, {"nome": "2 Pedro", "slug": "2-pedro", "cap": 3}, {"nome": "1 João", "slug": "1-joao", "cap": 5}, {"nome": "2 João", "slug": "2-joao", "cap": 1}, {"nome": "3 João", "slug": "3-joao", "cap": 1}, {"nome": "Judas", "slug": "judas", "cap": 1}, {"nome": "Apocalipse", "slug": "apocalipse", "cap": 22}];
﻿// Sinaliza atividade para a gamificação (game.js). Se o game.js ainda não
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
// busca: indice local carregado sob demanda; a mesma logica atende tanto a
// busca da home quanto o overlay global (nav), disponivel em toda pagina.
(function(){
  window.BEC = window.BEC || {};
  var core=window.BEC.core;
  var PREFIX=core?core.prefix:'';
  // busca sem acento: "genesis" encontra "Gênesis", "joao" encontra "João".
  function fold(s){return (s||'').normalize('NFD').replace(/[̀-ͯ]/g,'');}
  // índice carregado sob demanda (arquivo externo, não embutido na página)
  var idxPromise=null;
  function getIndex(){
    if(!idxPromise){
      var p=core ? core.fetchData('data/search-index.json') : fetch('data/search-index.json').then(function(r){return r.json();});
      idxPromise=p.then(function(data){
        data.forEach(function(i){ i.kf=fold((i.titulo+' '+i.desc+' '+(i.k||'')).toLowerCase()); });
        return data;
      });
    }
    return idxPromise;
  }
  function renderInto(out, IDX, term){
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
      var a=document.createElement('a');a.className='result';a.href=PREFIX+i.url;
      a.innerHTML='<span class="kind">'+i.t+'</span><h4>'+i.titulo+'</h4><p>'+i.desc+'</p>';
      out.appendChild(a);
    });
  }
  function wireSearch(input, out){
    if(!input||!out) return;
    input.addEventListener('input',function(e){
      var val=e.target.value;
      getIndex().then(function(IDX){
        if(input.value!==val) return;  // ignora respostas obsoletas
        renderInto(out, IDX, val);
      }).catch(function(){ out.innerHTML='<p class="empty">Não foi possível carregar a busca. Recarregue a página.</p>'; });
    });
  }
  window.BEC.search = {wire: wireSearch};
  wireSearch(document.getElementById('q'), document.getElementById('results'));
})();
// overlay de busca global — o gatilho [data-search-open] existe no nav e,
// nas páginas de capítulo (celular), também no painel único de leitura;
// por isso a abertura é delegada, não presa a um único botão.
(function(){
  var overlay=document.querySelector('[data-search-overlay]');
  if(!overlay) return;
  var input=overlay.querySelector('[data-search-input]');
  var out=overlay.querySelector('[data-search-results]');
  if(window.BEC && window.BEC.search) window.BEC.search.wire(input, out);
  function openOverlay(){ overlay.hidden=false; document.body.classList.add('search-open'); setTimeout(function(){ if(input) input.focus(); },30); }
  function closeOverlay(){ overlay.hidden=true; document.body.classList.remove('search-open'); }
  document.addEventListener('click', function(e){
    if(e.target.closest && e.target.closest('[data-search-open]')) openOverlay();
  });
  overlay.addEventListener('click', function(e){
    if(e.target===overlay || (e.target.closest && e.target.closest('[data-search-close]'))) closeOverlay();
  });
  document.addEventListener('keydown', function(e){ if(e.key==='Escape' && !overlay.hidden) closeOverlay(); });
})();
// reveal
if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
  var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.style.animationDelay='0s';en.target.classList.add('reveal');io.unobserve(en.target);}});});
  document.querySelectorAll('.card,.era').forEach(function(c){io.observe(c);});
}
// leitor: cada versículo cresce sutilmente ao entrar na tela (ver .verse-reveal
// em styles.css); desligado via Configurações (html.no-reveal) ou reduced-motion.
if(!document.documentElement.classList.contains('no-reveal') && !window.matchMedia('(prefers-reduced-motion: reduce)').matches){
  var verses=document.querySelectorAll('.verse-reveal');
  if(verses.length){
    var vio=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('on'); vio.unobserve(en.target);}});},{rootMargin:'0px 0px -8% 0px'});
    verses.forEach(function(v){vio.observe(v);});
  }
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
  var THEME_COLOR={dark:'#07111f',sepia:'#d6c09b',light:'#efe4d0'};
  function applyTheme(t){
    d.classList.remove('sepia','dark');
    if(t==='dark') d.classList.add('dark'); else if(t==='sepia') d.classList.add('sepia');
    try{localStorage.setItem('bec.theme',t);}catch(e){}
    if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
    var tc=document.querySelector('meta[name="theme-color"]');
    if(tc) tc.setAttribute('content', THEME_COLOR[t]||THEME_COLOR.light);
  }
  window.BEC = window.BEC || {};
  window.BEC.setTheme = applyTheme;
  window.BEC.applyOrig = applyOrig;
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

  function escH(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

  // "Ver outro versículo": sorteio aleatório (mantém o comportamento antigo)
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

  // Versículo do dia: estável (o mesmo o dia inteiro, muda à meia-noite),
  // compartilhável, e conta como "meditar" uma vez por dia (reforço de hábito).
  var dailyBox=document.querySelector('[data-daily-verse]');
  if(dailyBox){
    var dvBody=dailyBox.querySelector('[data-daily-verse-body]');
    var dvShare=dailyBox.querySelector('[data-daily-share]');
    var dvStreak=dailyBox.querySelector('[data-daily-streak]');
    var todayKey=new Date().toISOString().slice(0,10);
    fetch('data/daily.json').then(function(r){return r.json();}).then(function(list){
      if(!list || !list.length) return;
      var item=list[Math.floor(Date.now()/86400000)%list.length];
      var vurl=new URL('versiculos/'+item.slug+'/', location.href).href;
      if(dvBody){
        dvBody.innerHTML='<h3 class="daily-verse-ref">'+escH(item.ref)+'</h3>'+
          '<p class="daily-verse-text">'+escH(item.pt)+'</p>'+
          '<a class="daily-verse-open" href="versiculos/'+escH(item.slug)+'/">Abrir contexto →</a>';
      }
      if(dvShare){
        dvShare.hidden=false;
        dvShare.addEventListener('click',function(){
          if(window.BEC && window.BEC.shareCard) window.BEC.shareCard(item.ref, item.pt, vurl, dvShare);
        });
      }
      try{
        if(localStorage.getItem('bec.dailySeen')!==todayKey){
          localStorage.setItem('bec.dailySeen', todayKey);
          gameRecord('meditate');
        }
      }catch(e){}
      if(dvStreak){
        try{ var g=JSON.parse(localStorage.getItem('bec.game')||'{}'); var st=g.streak||0;
          if(st>0){ dvStreak.textContent='🔥 '+st+(st===1?' dia seguido':' dias seguidos')+' — volte amanhã'; dvStreak.hidden=false; }
        }catch(e){}
      }
    }).catch(function(){});
  }
})();

// audio de leitura + favoritos (sem arquivos de audio hospedados)
(function(){
  window.BEC = window.BEC || {};
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
  // pausa/retoma de verdade (Web Speech API), não cancela+reinicia: clicar de
  // novo no mesmo botão enquanto fala alterna Pausar/Continuar; falar em outro
  // botão cancela a fala anterior e reseta o rótulo dela.
  var activeSpeakBtn=null;
  function resetSpeakBtn(btn){
    if(btn && btn.dataset.oldText!=null){ btn.textContent=btn.dataset.oldText; delete btn.dataset.oldText; }
    if(activeSpeakBtn===btn) activeSpeakBtn=null;
  }
  function speak(text, lang, btn, onDone){
    if(!('speechSynthesis' in window)){ if(btn){btn.textContent='Sem voz neste navegador';} return; }
    if(btn && btn===activeSpeakBtn && window.speechSynthesis.speaking){
      if(window.speechSynthesis.paused){ window.speechSynthesis.resume(); btn.textContent='Pausar'; }
      else { window.speechSynthesis.pause(); btn.textContent='Continuar'; }
      return;
    }
    window.speechSynthesis.cancel();
    if(activeSpeakBtn) resetSpeakBtn(activeSpeakBtn);
    var u=new SpeechSynthesisUtterance(text);
    u.lang=lang||'pt-BR';
    u.rate=(lang==='he-IL'||lang==='el-GR')?0.82:0.92;
    u.onend=function(){ resetSpeakBtn(btn); if(onDone) onDone(true); };
    u.onerror=function(){ resetSpeakBtn(btn); if(onDone) onDone(false); };
    if(btn){ btn.dataset.oldText=btn.textContent; btn.textContent='Pausar'; activeSpeakBtn=btn; }
    window.speechSynthesis.speak(u);
  }
  function stopSpeak(){
    if('speechSynthesis' in window) window.speechSynthesis.cancel();
    if(activeSpeakBtn) resetSpeakBtn(activeSpeakBtn);
  }
  // ponte usada pela folha de ferramentas do versículo (study.js): favoritar
  // e ouvir sem duplicar a lógica de persistência/estado dos botões.
  window.BEC.speak = speak;
  window.BEC.stopSpeak = stopSpeak;
  window.BEC.favs = {
    isFav: function(ref){ return !!loadFavs()[ref]; },
    toggle: function(ref, url){
      var favs=loadFavs();
      if(favs[ref]) delete favs[ref]; else favs[ref]={url:url||location.pathname, savedAt:new Date().toISOString()};
      saveFavs(favs);
      updateFavButtons(); renderFavHome(); renderFavFull();
      return !!favs[ref];
    }
  };
  document.addEventListener('click',function(e){
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

// Ouvir capítulo: lê os versículos em português em sequência (leitura
// acompanhada), destacando o versículo atual, em vez de só ouvir um por vez.
(function(){
  var btn=document.querySelector('[data-listen-chapter]');
  var chapterBox=document.querySelector('.chapter');
  if(!btn || !chapterBox || !window.BEC) return;
  var label=btn.querySelector('span');
  var verses=Array.prototype.slice.call(chapterBox.querySelectorAll('.ch-verse[id]'));
  if(!verses.length){ btn.hidden=true; return; }
  var playing=false, idx=-1, curEl=null;

  function clearHighlight(){ if(curEl){ curEl.classList.remove('listen-current'); curEl=null; } }
  function stop(){
    var was=playing;
    playing=false; idx=-1; clearHighlight();
    if(was && window.BEC.stopSpeak) window.BEC.stopSpeak();
    btn.classList.remove('on');
    if(label) label.textContent='Ouvir capítulo';
  }
  window.BEC.stopListenChapter=stop;
  function playNext(){
    idx++;
    if(!playing || idx>=verses.length){ stop(); return; }
    var v=verses[idx];
    var pt=v.querySelector('.pt');
    var text=pt && !pt.querySelector('.pt-missing') ? pt.textContent.trim() : '';
    clearHighlight();
    curEl=v; v.classList.add('listen-current');
    if(v.scrollIntoView) v.scrollIntoView({block:'center', behavior:'smooth'});
    if(!text){ playNext(); return; }
    window.BEC.speak(text, 'pt-BR', null, function(){ if(playing) playNext(); });
  }
  btn.addEventListener('click', function(){
    if(playing){ stop(); return; }
    playing=true; btn.classList.add('on'); if(label) label.textContent='Parar leitura';
    idx=-1; playNext();
  });
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

// Criar Plano: gera um cronograma real dia a dia (por livro ou por tema) e
// alimenta o mesmo sistema de progresso (bec.planProgress) dos planos prontos.
(function(){
  var form=document.querySelector('[data-plan-form]');
  var list=document.querySelector('[data-plan-list]');
  if(!form||!list) return;
  window.BEC = window.BEC || {};
  var core=window.BEC.core;
  var PREFIX=core?core.prefix:'';
  var BOOKS=window.BEC_BOOKS||[];
  function esc(s){ return core?core.esc(s):(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

  function load(){try{return JSON.parse(localStorage.getItem('bec.studyPlans')||'[]');}catch(e){return[];}}
  function save(plans){try{localStorage.setItem('bec.studyPlans',JSON.stringify(plans));}catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty();}

  function distribute(total, days){
    days=Math.max(1, Math.min(days, total||1));
    var base=Math.floor(total/days), extra=total%days, out=[], n=1;
    for(var d=0; d<days; d++){
      var count=base+(d<extra?1:0), refs=[];
      for(var i=0;i<count;i++){ refs.push(n); n++; }
      out.push(refs);
    }
    return out;
  }

  function bookPlan(bookName, days){
    var book=BOOKS.filter(function(b){return b.nome===bookName;})[0];
    if(!book) return null;
    var dias=distribute(book.cap, days).map(function(chs){
      return chs.map(function(c){ return {label:bookName+' '+c, href:PREFIX+'ler/'+book.slug+'/'+c+'/'}; });
    });
    return {titulo:bookName, descricao:'Leitura de '+bookName+' em '+dias.length+' dias.', dias:dias};
  }

  function topicPlan(term, days){
    if(!core) return Promise.resolve(null);
    return core.fetchData('data/search-index.json').then(function(idx){
      function fold(s){ return (s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase(); }
      var t=fold(term);
      var matches=idx.filter(function(i){ return i.t==='Versículo' && fold(i.titulo+' '+i.desc+' '+(i.k||'')).indexOf(t)>-1; });
      if(!matches.length) return null;
      var perDay=Math.max(1, Math.ceil(matches.length/days)), dias=[];
      for(var d=0; d<days && d*perDay<matches.length; d++){
        dias.push(matches.slice(d*perDay,(d+1)*perDay).map(function(m){ return {label:m.titulo, href:PREFIX+m.url}; }));
      }
      return {titulo:'Tema: '+term, descricao:'Versículos sobre "'+term+'" em '+dias.length+' dias.', dias:dias};
    });
  }

  function render(){
    var plans=load();
    list.innerHTML = plans.length ? plans.map(function(p){
      var daysHtml=p.dias.map(function(refs, i){
        return '<li class="plan-day"><label class="plan-check"><input type="checkbox" data-plan="'+esc(p.id)+'" data-day="'+i+'"><span>Dia '+(i+1)+'</span></label>'+
          '<span class="plan-chapters">'+refs.map(function(r){ return '<a href="'+esc(r.href)+'">'+esc(r.label)+'</a>'; }).join(' · ')+'</span></li>';
      }).join('');
      return '<article class="saved-plan">'+
        '<div class="section-title"><h3>'+esc(p.titulo)+'</h3><span class="plan-progress" data-plan-progress data-plan-slug="'+esc(p.id)+'">0 de '+p.dias.length+' dias</span></div>'+
        '<p class="muted-line">'+esc(p.descricao)+'</p>'+
        '<ol class="plan-days">'+daysHtml+'</ol>'+
        '<p class="map-actions"><button type="button" class="btn ghost" data-plan-remove="'+esc(p.id)+'">Remover plano</button></p>'+
      '</article>';
    }).join('') : '<p class="muted-line">Nenhum plano criado ainda.</p>';
    if(window.BEC.plans) window.BEC.plans.repaint();
  }

  form.addEventListener('submit', function(e){
    e.preventDefault();
    var data=new FormData(form);
    var tipo=data.get('tipo')||'livro';
    var duracao=parseInt(data.get('duracao'),10)||30;
    var submitBtn=form.querySelector('button[type="submit"]');
    var oldLabel=submitBtn?submitBtn.textContent:'';
    if(submitBtn){ submitBtn.disabled=true; submitBtn.textContent='Gerando…'; }
    function finish(base){
      if(submitBtn){ submitBtn.disabled=false; submitBtn.textContent=oldLabel; }
      if(!base || !base.dias || !base.dias.length){
        if(submitBtn){ submitBtn.textContent='Nada encontrado — tente outro tema'; setTimeout(function(){submitBtn.textContent=oldLabel;},2200); }
        return;
      }
      var plan={id:'p'+Date.now().toString(36), tipo:tipo, titulo:base.titulo, descricao:base.descricao,
        dias:base.dias, createdAt:new Date().toISOString()};
      var plans=load(); plans.unshift(plan); save(plans.slice(0,12));
      render();
    }
    if(tipo==='tema'){
      var term=(data.get('conteudo')||'').toString().trim();
      if(!term){ if(submitBtn){ submitBtn.disabled=false; submitBtn.textContent=oldLabel; } return; }
      topicPlan(term, duracao).then(finish).catch(function(){ finish(null); });
    } else {
      finish(bookPlan(data.get('livro')||'', duracao));
    }
  });

  document.addEventListener('click', function(e){
    var rm=e.target.closest && e.target.closest('[data-plan-remove]');
    if(!rm) return;
    var id=rm.getAttribute('data-plan-remove');
    save(load().filter(function(p){ return p.id!==id; }));
    try{
      var all=JSON.parse(localStorage.getItem('bec.planProgress')||'{}');
      delete all[id];
      localStorage.setItem('bec.planProgress', JSON.stringify(all));
    }catch(err){}
    render();
  });

  var bookSelect=form.querySelector('[data-plan-book-select]');
  if(bookSelect) bookSelect.innerHTML=BOOKS.map(function(b){ return '<option value="'+esc(b.nome)+'">'+esc(b.nome)+' ('+b.cap+' cap.)</option>'; }).join('');

  var tipoSelect=form.querySelector('[data-plan-tipo]');
  if(tipoSelect) tipoSelect.addEventListener('change', function(){
    form.querySelectorAll('[data-plan-field]').forEach(function(f){
      f.hidden = f.getAttribute('data-plan-field')!==tipoSelect.value;
    });
  });

  render();
})();

// Planos de leitura: progresso por dia (bec.planProgress), com sincronização.
// Sem guarda de "sem checkbox no carregamento": planos criados depois (Criar
// Plano) também precisam do listener delegado funcionando.
(function(){
  window.BEC = window.BEC || {};
  var KEY='bec.planProgress';
  function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')||{};}catch(e){return {};}}
  function save(all){try{localStorage.setItem(KEY,JSON.stringify(all));}catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty();}
  function paint(){
    var boxes=document.querySelectorAll('input[data-plan]');
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
  window.BEC.plans = {repaint: paint};
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

  // Evento real de leitura: credita a missão de leitura (uma vez por capítulo
  // por dia — abrir o capítulo, por si só, não conta) e avisa o módulo de
  // plano de leitura, que pode concluir o dia de um plano ativo.
  function creditRead(){
    try{
      var mark=new Date().toISOString().slice(0,10)+'|'+chapterRef;
      if(localStorage.getItem('bec.game.readMark')!==mark){
        localStorage.setItem('bec.game.readMark',mark);
        gameRecord('read_chapters');
      }
    }catch(err){}
    document.dispatchEvent(new CustomEvent('bec:chapter-read', {detail:{ref:chapterRef}}));
  }

  saveBtn.addEventListener('click',function(){
    var s=curStart(), e=curEnd();
    if(s==null||e==null) return;
    var r=getRanges(); r.push({s:s,e:e});
    setRanges(normalize(r));
    setMarkMode(null); clearPreview();
    paint();
    creditRead();
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

  // Marcador automático (opcional, ligado em Configurações): conforme o
  // versículo passa pela faixa de leitura da tela, estende o trecho lido
  // do 1 até ali — reaproveita getRanges/setRanges/normalize/paint/creditRead
  // acima, sem duplicar a lógica de mesclagem de trechos.
  if(chapterBox && localStorage.getItem('bec.autoread')==='1' && 'IntersectionObserver' in window){
    var autoMax=0, autoTimer=null;
    (getRanges()||[]).forEach(function(x){ if(x.e>autoMax) autoMax=x.e; });
    function commitAuto(){
      autoTimer=null;
      var r=normalize(getRanges().concat([{s:1,e:autoMax}]));
      setRanges(r);
      paint();
      creditRead();
    }
    var aio=new IntersectionObserver(function(es){
      es.forEach(function(en){
        if(!en.isIntersecting) return;
        var n=parseInt((en.target.id||'').replace(/^v/,''),10);
        if(isNaN(n) || n<=autoMax) return;
        autoMax=n;
        if(autoTimer) clearTimeout(autoTimer);
        autoTimer=setTimeout(commitAuto, 700);
      });
    },{rootMargin:'0px 0px -55% 0px'});
    chapterBox.querySelectorAll('.ch-verse[id]').forEach(function(v){aio.observe(v);});
  }
})();

// Dados de plano compartilhados (window.BEC.planData): planos criados no
// Workspace + planos curados (plan-index.json), unificados no mesmo formato
// {slug, tipo, titulo, dias:[[{label,url}]]}. Usado pelo banner do leitor,
// pelo card "Plano de hoje" da home e por qualquer outro módulo que precise
// saber em que dia de plano uma referência está.
(function(){
  window.BEC = window.BEC || {};
  var core=window.BEC.core;

  function loadJSON(k, fb){ try{ var v=JSON.parse(localStorage.getItem('bec.'+k)||'null'); return v==null?fb:v; }catch(e){ return fb; } }
  function urlChapterKey(url){
    var m=url && String(url).match(/ler\/([a-z0-9-]+)\/(\d+)\/?$/);
    return m ? (m[1]+'/'+m[2]) : null;
  }
  function customPlans(){
    // planos criados guardam o link do dia em "href" (ver módulo Criar Plano);
    // normaliza para "url" aqui pra bater com o formato de plan-index.json.
    return (loadJSON('studyPlans', [])||[]).map(function(p){
      var dias=(p.dias||[]).map(function(refs){
        return refs.map(function(r){ return {label:r.label, url:r.url||r.href||null}; });
      });
      return {slug:p.id, tipo:'criado', titulo:p.titulo, dias:dias};
    });
  }
  function curatedPlans(){
    if(!core) return Promise.resolve([]);
    return core.fetchData('data/plan-index.json').then(function(idx){
      return idx.map(function(p){ return {slug:p.slug, tipo:'curado', titulo:p.titulo, dias:p.dias}; });
    }).catch(function(){ return []; });
  }
  function allPlans(){ return curatedPlans().then(function(c){ return customPlans().concat(c); }); }
  function findDay(plan, chapterKey){
    for(var i=0;i<plan.dias.length;i++){
      for(var j=0;j<plan.dias[i].length;j++){
        if(urlChapterKey(plan.dias[i][j].url)===chapterKey) return i;
      }
    }
    return -1;
  }
  function progressFor(slug){
    var all=loadJSON('planProgress', {});
    return Array.isArray(all[slug]) ? all[slug] : [];
  }
  function nextOpenDay(plan){
    var done=progressFor(plan.slug);
    for(var i=0;i<plan.dias.length;i++){ if(done.indexOf(i)<0) return i; }
    return -1; // plano concluído
  }
  function markDay(slug, dayIdx){
    var all=loadJSON('planProgress', {});
    var days=all[slug]||[];
    if(days.indexOf(dayIdx)<0){
      days.push(dayIdx); all[slug]=days;
      try{ localStorage.setItem('bec.planProgress', JSON.stringify(all)); }catch(e){}
      if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
      if(window.BEC.plans) window.BEC.plans.repaint();
    }
  }
  function refCovered(entry, verseTotals, ranges){
    var k=urlChapterKey(entry.url);
    if(!k) return false; // ref de versículo avulso (plano por tema): fora do auto-mark
    var parts=k.split('/'), total=verseTotals && verseTotals[parts[0]] && verseTotals[parts[0]][parts[1]];
    if(!total) return false;
    var r=ranges[entry.label];
    if(!Array.isArray(r) || !r.length) return false;
    var covered=0;
    r.forEach(function(x){ covered += Math.max(0, Math.min(x.e,total)-Math.max(x.s,1)+1); });
    return covered>=total;
  }
  function showToast(msg){
    var t=document.createElement('div'); t.className='bec-toast'; t.textContent=msg;
    document.body.appendChild(t);
    requestAnimationFrame(function(){ t.classList.add('on'); });
    setTimeout(function(){ t.classList.remove('on'); setTimeout(function(){ t.remove(); }, 300); }, 2600);
  }

  window.BEC.planData = {
    allPlans: allPlans, findDay: findDay, progressFor: progressFor, nextOpenDay: nextOpenDay,
    markDay: markDay, refCovered: refCovered, showToast: showToast, urlChapterKey: urlChapterKey,
    loadJSON: loadJSON
  };
})();

// Leitor ↔ plano de leitura: mostra "Dia N de T · Plano" quando o capítulo
// aberto pertence a um plano ativo (criado no Workspace ou curado), com
// link para o plano e botão para marcar o dia. Quando o capítulo é lido por
// completo (evento bec:chapter-read do módulo de progresso por trecho, acima),
// marca o dia sozinho se TODOS os capítulos daquele dia já estiverem 100%
// cobertos — dias com referência de versículo avulso (planos por tema)
// ficam de fora do auto-marcar e exigem o botão manual.
(function(){
  var box=document.querySelector('[data-plan-context]');
  if(!box) return;
  window.BEC = window.BEC || {};
  var core=window.BEC.core, pd=window.BEC.planData;
  var PREFIX=core?core.prefix:'';

  function curChapterKey(){
    var m=location.pathname.match(/ler\/([a-z0-9-]+)\/(\d+)\/?$/);
    return m ? (m[1]+'/'+m[2]) : null;
  }

  function render(){
    var chapterKey=curChapterKey();
    if(!chapterKey || !core) return;
    pd.allPlans().then(function(candidates){
      for(var i=0;i<candidates.length;i++){
        var plan=candidates[i];
        var dayIdx=pd.findDay(plan, chapterKey);
        if(dayIdx<0) continue;
        var done=pd.progressFor(plan.slug);
        var isDone=done.indexOf(dayIdx)>-1;
        var planUrl=(plan.tipo==='curado') ? (PREFIX+'planos/'+plan.slug+'/') : (PREFIX+'workspace/#criar-plano');
        box.innerHTML=
          '<span class="plan-context-info">📖 <b>Dia '+(dayIdx+1)+' de '+plan.dias.length+'</b> · '+core.esc(plan.titulo)+
          '<span class="plan-context-count">'+done.length+' de '+plan.dias.length+' dias</span></span>'+
          '<span class="plan-context-actions">'+
            '<a class="btn tiny ghost" href="'+planUrl+'">Ver plano</a>'+
            (isDone
              ? '<span class="plan-context-done">✓ Dia concluído</span>'
              : '<button type="button" class="btn tiny primary" data-plan-context-mark="'+core.esc(plan.slug)+'" data-plan-context-day="'+dayIdx+'">Marcar dia como lido</button>')+
          '</span>';
        box.hidden=false;
        return;
      }
      box.hidden=true;
    });
  }

  box.addEventListener('click', function(e){
    var b=e.target.closest && e.target.closest('[data-plan-context-mark]');
    if(!b) return;
    pd.markDay(b.getAttribute('data-plan-context-mark'), parseInt(b.getAttribute('data-plan-context-day'),10));
    render();
  });

  document.addEventListener('bec:chapter-read', function(){
    if(!core) return;
    core.fetchData('data/chapter-verses.json').then(function(verseTotals){
      var ranges=pd.loadJSON('readingRanges', {});
      pd.allPlans().then(function(candidates){
        var chapterKey=curChapterKey();
        candidates.forEach(function(plan){
          var dayIdx=pd.findDay(plan, chapterKey);
          if(dayIdx<0) return;
          if(pd.progressFor(plan.slug).indexOf(dayIdx)>-1) return;
          var refs=plan.dias[dayIdx];
          var allCovered=refs.length && refs.every(function(entry){ return pd.refCovered(entry, verseTotals, ranges); });
          if(allCovered){
            pd.markDay(plan.slug, dayIdx);
            pd.showToast('Dia '+(dayIdx+1)+' concluído · '+plan.titulo+' ✓');
            render();
          }
        });
      });
    }).catch(function(){});
  });

  render();
  document.addEventListener('bec:study-sync', render);
})();

// Home viva: "Plano de hoje" (próximo dia não concluído do plano mais
// recente) e Workspace "Continuar leitura" (usa bec.lastRead de verdade).
(function(){
  window.BEC = window.BEC || {};
  var core=window.BEC.core, pd=window.BEC.planData;
  var PREFIX=core?core.prefix:'';

  var planBox=document.querySelector('[data-home-plan] [data-home-plan-body]');
  if(planBox && pd){
    pd.allPlans().then(function(plans){
      if(!plans.length) return;
      // prioriza planos criados (mais recentes primeiro, já vêm nessa ordem)
      // com dia em aberto; senão o primeiro plano curado com dia em aberto.
      for(var i=0;i<plans.length;i++){
        var plan=plans[i], dayIdx=pd.nextOpenDay(plan);
        if(dayIdx<0) continue;
        var firstRef=plan.dias[dayIdx][0];
        // reconstrói a URL a partir do slug/capítulo (não do href salvo, que
        // é relativo à página onde o plano foi criado e pode ter outra
        // profundidade da atual) — funciona a partir de qualquer página.
        var key=firstRef && pd.urlChapterKey(firstRef.url);
        var href=key ? (PREFIX+'ler/'+key+'/')
          : (plan.tipo==='curado' ? PREFIX+'planos/'+plan.slug+'/' : PREFIX+'workspace/#criar-plano');
        planBox.innerHTML=
          '<p><b>Dia '+(dayIdx+1)+' de '+plan.dias.length+'</b> · '+core.esc(plan.titulo)+'</p>'+
          '<a href="'+href+'">Continuar → '+core.esc(firstRef?firstRef.label:'')+'</a>';
        return;
      }
    });
  }

  var notesBox=document.querySelector('[data-home-notes] [data-home-notes-body]');
  if(notesBox){
    var notes={}, notesMeta={};
    try{ notes=JSON.parse(localStorage.getItem('bec.notes')||'{}')||{}; }catch(e){}
    try{ notesMeta=JSON.parse(localStorage.getItem('bec.notesMeta')||'{}')||{}; }catch(e){}
    var refs=Object.keys(notes);
    if(refs.length){
      refs.sort(function(a,b){
        var da=notesMeta[a], db=notesMeta[b];
        if(da && db) return db.localeCompare(da); // mais recente primeiro
        if(da) return -1; if(db) return 1;
        return a.localeCompare(b); // sem data (nota antiga): ordem estável
      });
      function refToUrl(ref){
        var m=(ref||'').match(/^(.*?)\s+(\d+):(\d+)$/); if(!m) return null;
        var slug=m[1].normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
        return PREFIX+'versiculos/'+slug+'-'+m[2]+'-'+m[3]+'/';
      }
      notesBox.innerHTML=refs.slice(0,3).map(function(ref){
        var url=refToUrl(ref); if(!url) return '';
        var preview=(notes[ref]||'').slice(0,64);
        return '<p class="home-note-row"><a href="'+url+'"><b>'+core.esc(ref)+'</b></a> — '+core.esc(preview)+(notes[ref].length>64?'…':'')+'</p>';
      }).join('') || notesBox.innerHTML;
    }
  }

  var wsContinue=document.querySelector('[data-ws-continue]');
  if(wsContinue){
    try{
      var lr=JSON.parse(localStorage.getItem('bec.lastRead')||'null');
      if(lr && lr.url){
        wsContinue.href=lr.url;
        wsContinue.querySelector('h3').textContent='Continuar: '+lr.label;
      }
    }catch(e){}
  }
})();

// Modo leitura (foco): esconde menus, módulos e ferramentas, deixando só o
// texto do capítulo em uma coluna confortável. Persistido para reaplicar ao
// abrir o próximo capítulo; nunca vaza para páginas sem texto corrido.
// Foco progressivo: o versículo na linha de leitura fica pleno e os demais
// esmaecem; um contador discreto mostra quantos versículos faltam e, no fim,
// oferece "Marcar capítulo como lido" (reusa o fluxo real que credita missão).
(function(){
  var KEY='bec.focusRead';
  function isChapter(){return !!document.querySelector('.chapter');}
  function verses(){return Array.prototype.slice.call(document.querySelectorAll('.chapter .ch-verse'));}
  var active=false, raf=null;

  function updateCurrent(){
    raf=null;
    if(!active) return;
    var vs=verses(); if(!vs.length) return;
    var focal=window.innerHeight*0.38, cur=vs[0], best=Infinity;
    vs.forEach(function(v){
      var r=v.getBoundingClientRect();
      var d=(r.top<=focal && r.bottom>=focal) ? 0 : Math.min(Math.abs(r.top-focal), Math.abs(r.bottom-focal));
      if(d<best){ best=d; cur=v; }
    });
    // Fim do capítulo: quando o último versículo já está todo visível, ele é o
    // atual mesmo sem cruzar a linha focal (senão o fim nunca chega em telas altas).
    var lastR=vs[vs.length-1].getBoundingClientRect();
    if(lastR.bottom<=window.innerHeight-4) cur=vs[vs.length-1];
    vs.forEach(function(v){ v.classList.toggle('fr-current', v===cur); });
    var left=vs.length-vs.indexOf(cur)-1;
    var lbl=document.querySelector('[data-focus-remaining]');
    if(lbl) lbl.textContent = left>0 ? ('Faltam '+left+' versículo'+(left>1?'s':'')) : 'Fim do capítulo';
    var mk=document.querySelector('[data-focus-mark]');
    if(mk && !mk.disabled) mk.hidden = left>0;
  }
  function onScroll(){ if(!raf) raf=requestAnimationFrame(updateCurrent); }

  function apply(on){
    active = !!on && isChapter();
    document.documentElement.classList.toggle('focus-read', active);
    if(active){ window.addEventListener('scroll', onScroll, {passive:true}); updateCurrent(); }
    else{
      window.removeEventListener('scroll', onScroll);
      verses().forEach(function(v){ v.classList.remove('fr-current'); });
    }
  }
  try{ if(localStorage.getItem(KEY)==='1') apply(true); }catch(e){}

  document.addEventListener('click', function(ev){
    var mk=ev.target.closest && ev.target.closest('[data-focus-mark]');
    if(mk){
      // Marca o capítulo inteiro pelo mesmo caminho do painel de progresso
      // (persiste o trecho e credita a leitura uma vez por capítulo/dia).
      var st=document.querySelector('[data-study-frac] [data-sf-start]');
      var en=document.querySelector('[data-study-frac] [data-sf-end]');
      var sv=document.querySelector('[data-study-frac] [data-sf-save]');
      if(st&&en&&sv&&st.options.length){
        st.value=st.options[0].value;
        en.value=en.options[en.options.length-1].value;
        sv.click();
        mk.textContent='✓ Capítulo lido';
        mk.disabled=true;
      }
      return;
    }
    var b=ev.target.closest && ev.target.closest('[data-focus-toggle]');
    if(!b || !isChapter()) return;
    var on=!document.documentElement.classList.contains('focus-read');
    apply(on);
    try{localStorage.setItem(KEY, on?'1':'0');}catch(e){}
  });
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
    'theme':'Tema','search':'Buscar','focus':'Modo leitura','mark-start':'Marcar início','mark-end':'Marcar fim','save':'Salvar trecho','report':'Reportar',
    'study-notes':'Minhas anotações','study-share':'Compartilhar estudo','study-export':'Baixar .txt','study-clear':'Apagar tudo'};

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
    // reportar, exportar e apagar fecham o painel (assumem modal/download próprios);
    // fonte/original/tema/foco mantêm o painel aberto para vários toques seguidos
    if(ev.target.closest && ev.target.closest('[data-report-open],[data-search-open],[data-study-export],[data-study-share],[data-study-clear]')) setOpen(false);
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

// Configurações do Workspace: tema, fonte, idioma original, ordem dos livros
// e gestão de dados locais (backup completo / apagar tudo).
(function(){
  var panel=document.querySelector('[data-settings-panel]');
  if(!panel) return;
  window.BEC = window.BEC || {};
  var core=window.BEC.core;
  var d=document.documentElement;
  var THEMES=['light','sepia','dark'];

  function markActive(sel, attr, current){
    panel.querySelectorAll(sel).forEach(function(b){ b.classList.toggle('on', b.getAttribute(attr)===current); });
  }
  function syncUI(){
    var theme=localStorage.getItem('bec.theme'); if(THEMES.indexOf(theme)<0) theme='light';
    markActive('[data-set-theme]','data-set-theme', theme);
    markActive('[data-set-font]','data-set-font', localStorage.getItem('bec.fontscale')||'1');
    markActive('[data-set-order]','data-set-order', localStorage.getItem('bec.bookorder')||'bib');
    var orig=panel.querySelector('[data-set-orig]');
    if(orig) orig.checked = localStorage.getItem('bec.origmode')==='1';
    var ar=panel.querySelector('[data-set-autoread]');
    if(ar) ar.checked = localStorage.getItem('bec.autoread')==='1';
    var rv=panel.querySelector('[data-set-reveal]');
    if(rv) rv.checked = localStorage.getItem('bec.reveal')!=='0';
  }

  panel.addEventListener('click', function(e){
    var t=e.target.closest && e.target.closest('[data-set-theme]');
    if(t){
      if(window.BEC.setTheme) window.BEC.setTheme(t.getAttribute('data-set-theme'));
      syncUI(); return;
    }
    var f=e.target.closest && e.target.closest('[data-set-font]');
    if(f){
      var scale=f.getAttribute('data-set-font');
      d.classList.remove('fs-0','fs-1','fs-2','fs-3'); d.classList.add('fs-'+scale);
      try{localStorage.setItem('bec.fontscale', scale);}catch(err){}
      if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
      syncUI(); return;
    }
    var o=e.target.closest && e.target.closest('[data-set-order]');
    if(o){
      try{localStorage.setItem('bec.bookorder', o.getAttribute('data-set-order'));}catch(err){}
      if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
      syncUI(); return;
    }
    var org=e.target.closest && e.target.closest('[data-set-orig]');
    if(org){ if(window.BEC.applyOrig) window.BEC.applyOrig(org.checked); return; }
    var ar=e.target.closest && e.target.closest('[data-set-autoread]');
    if(ar){
      try{localStorage.setItem('bec.autoread', ar.checked?'1':'0');}catch(err){}
      if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
      return;
    }
    var rv=e.target.closest && e.target.closest('[data-set-reveal]');
    if(rv){
      try{localStorage.setItem('bec.reveal', rv.checked?'1':'0');}catch(err){}
      document.documentElement.classList.toggle('no-reveal', !rv.checked);
      return;
    }
    var exp=e.target.closest && e.target.closest('[data-settings-export]');
    if(exp){
      var backup={};
      ['notes','vhl','whl','favs','collections','notebooks','studyPlans','planProgress','readingRanges'].forEach(function(k){
        try{ backup[k]=JSON.parse(localStorage.getItem('bec.'+k)||'null'); }catch(err){}
      });
      if(core) core.download('biblia-em-contexto-backup.json', JSON.stringify(backup,null,2), 'application/json');
      return;
    }
    var imp=e.target.closest && e.target.closest('[data-settings-import]');
    if(imp){ var file=panel.querySelector('[data-settings-import-file]'); if(file) file.click(); return; }
    var clr=e.target.closest && e.target.closest('[data-settings-clear]');
    if(clr && core){
      core.confirmModal('Apagar TODOS os dados salvos neste navegador (notas, grifos, favoritos, coleções, cadernos, planos e progresso)? Esta ação não pode ser desfeita.', function(){
        Object.keys(localStorage).filter(function(k){return k.indexOf('bec.')===0;}).forEach(function(k){ localStorage.removeItem(k); });
        if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
        var status=panel.querySelector('[data-settings-status]');
        if(status) status.textContent='Dados apagados. Recarregue a página.';
      }, 'Apagar tudo');
    }
  });

  var importFile=panel.querySelector('[data-settings-import-file]');
  if(importFile) importFile.addEventListener('change', function(){
    var f=importFile.files[0]; if(!f) return;
    var rd=new FileReader();
    rd.onload=function(){
      var status=panel.querySelector('[data-settings-status]');
      try{
        var obj=JSON.parse(rd.result);
        Object.keys(obj).forEach(function(k){ if(obj[k]!=null) localStorage.setItem('bec.'+k, JSON.stringify(obj[k])); });
        if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
        if(status) status.textContent='Backup importado ✓ Recarregue a página.';
      }catch(err){ if(status) status.textContent='Arquivo inválido.'; }
    };
    rd.readAsText(f); importFile.value='';
  });

  syncUI();
  document.addEventListener('bec:study-sync', syncUI);
})();

// Dashboard de estatísticas do Workspace: números derivados dos dados já
// salvos neste navegador (sem contagem no servidor).
(function(){
  var grid=document.querySelector('[data-stats-grid]');
  if(!grid) return;
  var BOOKS=window.BEC_BOOKS||[];
  function loadJSON(k, fb){ try{ return JSON.parse(localStorage.getItem('bec.'+k)||'null')||fb; }catch(e){ return fb; } }
  function setText(sel, val){ var el=grid.querySelector(sel); if(el) el.textContent=val; }

  function render(){
    var ranges=loadJSON('readingRanges',{});
    var notes=loadJSON('notes',{});
    var vhl=loadJSON('vhl',{});
    var favs=loadJSON('favs',{});
    var history=loadJSON('history',[]);

    var chapters=Object.keys(ranges).length;
    var totalChapters=BOOKS.reduce(function(s,b){return s+(b.cap||0);},0);
    var pct=totalChapters ? Math.min(100, Math.round((chapters/totalChapters)*100)) : 0;

    setText('[data-stat-chapters]', chapters);
    setText('[data-stat-bible-pct]', pct+'%');
    setText('[data-stat-notes]', Object.keys(notes).length);
    setText('[data-stat-highlights]', Object.keys(vhl).length);
    setText('[data-stat-favs]', Object.keys(favs).length);

    var hm=document.querySelector('[data-stats-heatmap]');
    if(hm){
      var days={};
      (history||[]).forEach(function(h){ if(h && h.at) days[h.at.slice(0,10)]=1; });
      var today=new Date(), cells='';
      for(var i=13;i>=0;i--){
        var dt=new Date(today); dt.setDate(dt.getDate()-i);
        var key=dt.toISOString().slice(0,10);
        cells+='<span class="hm-cell'+(days[key]?' on':'')+'" title="'+key+'"></span>';
      }
      hm.innerHTML=cells;
    }
  }
  render();
  document.addEventListener('bec:study-sync', render);
})();

// Abas do Workspace (#estudar): Atalhos/Anotações/Favoritos/Coleções/Cadernos
// embutidos como painéis — os apps (study.js, library.js, app.js) já se
// inicializam sozinhos a partir dos containers; aqui só troca o que é visível.
(function(){
  var tabs=document.querySelector('[data-ws-tabs]');
  if(!tabs) return;
  var buttons=Array.prototype.slice.call(tabs.querySelectorAll('[data-ws-tab]'));
  var panels=Array.prototype.slice.call(document.querySelectorAll('[data-ws-panel]'));
  function setTab(name){
    buttons.forEach(function(b){
      var on=b.getAttribute('data-ws-tab')===name;
      b.classList.toggle('on', on); b.setAttribute('aria-selected', on?'true':'false');
    });
    panels.forEach(function(p){ p.hidden = p.getAttribute('data-ws-panel')!==name; });
    try{ localStorage.setItem('bec.wsTab', name); }catch(e){}
  }
  tabs.addEventListener('click', function(e){
    var b=e.target.closest && e.target.closest('[data-ws-tab]');
    if(b) setTab(b.getAttribute('data-ws-tab'));
  });
  var saved='atalhos';
  try{ saved=localStorage.getItem('bec.wsTab')||'atalhos'; }catch(e){}
  if(!buttons.some(function(b){return b.getAttribute('data-ws-tab')===saved;})) saved='atalhos';
  var hashTab=(location.hash||'').replace('#','');
  if(buttons.some(function(b){return b.getAttribute('data-ws-tab')===hashTab;})) saved=hashTab;
  setTab(saved);
  if(hashTab===saved){
    var target=document.getElementById(hashTab);
    if(target) target.scrollIntoView();
  }
})();

// Gesto de deslizar (swipe) para folhear capítulos no leitor — deixa a leitura
// no telefone com cara de app. Deslizar para a esquerda vai ao próximo capítulo,
// para a direita ao anterior. Só age em gestos claramente horizontais e nunca
// atrapalha seleção de texto, a folha do versículo ou o modo de grifar.
(function(){
  var ch=document.querySelector('.chapter[data-prev-chapter], .chapter[data-next-chapter]');
  if(!ch) return;
  var prevUrl=ch.getAttribute('data-prev-chapter'), nextUrl=ch.getAttribute('data-next-chapter');
  var x0=0, y0=0, tracking=false;
  var reduce=window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function blocked(t){
    var b=document.body.classList;
    if(b.contains('sheet-open') || b.contains('hl-mode')) return true;
    try{ if(window.getSelection && String(window.getSelection())) return true; }catch(e){}
    if(t && t.closest && t.closest('a,button,input,textarea,select,[data-vs-act],[contenteditable]')) return true;
    return false;
  }
  ch.addEventListener('touchstart', function(e){
    if(e.touches.length!==1 || blocked(e.target)){ tracking=false; return; }
    x0=e.touches[0].clientX; y0=e.touches[0].clientY; tracking=true;
  }, {passive:true});
  ch.addEventListener('touchend', function(e){
    if(!tracking) return; tracking=false;
    var t=e.changedTouches[0], dx=t.clientX-x0, dy=t.clientY-y0;
    // precisa ser um gesto nítido e predominantemente horizontal
    if(Math.abs(dx)<60 || Math.abs(dx)<Math.abs(dy)*1.4) return;
    if(blocked(e.target)) return;
    var url=dx<0?nextUrl:prevUrl;
    if(!url) return;
    if(reduce){ location.href=url; return; }
    document.body.classList.add('swiping-'+(dx<0?'left':'right'));
    setTimeout(function(){ location.href=url; }, 160);
  }, {passive:true});
})();
