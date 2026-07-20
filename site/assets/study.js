var BEC_BASE="https://alusionbr.github.io/bibliaonline";
// Ferramentas de estudo por versículo: uma única folha de ferramentas (toque
// no texto) reúne favoritar, grifar (com cor), anotar, ouvir, compartilhar,
// salvar em coleção e ver referências cruzadas. Tudo salvo no localStorage
// deste navegador; sincroniza quando há conta. Nada é enviado a servidor.
(function(){
  var core = window.BEC && window.BEC.core;
  function esc(s){ return core ? core.esc(s) : (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function confirmModal(msg, onYes){ return core ? core.confirmModal(msg, onYes) : (onYes && onYes()); }
  function download(name, text, type){ return core ? core.download(name, text, type) : null; }
  function copyText(str, btn, label){ return core ? core.copyText(str, btn, label) : null; }
  function flash(btn, txt){ return core ? core.flash(btn, txt) : null; }

  function load(k){try{return JSON.parse(localStorage.getItem('bec.'+k)||'{}');}catch(e){return{};}}
  function save(k,v){try{localStorage.setItem('bec.'+k,JSON.stringify(v));}catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty();}

  // referência "Livro c:v" → slug e URL absoluta do versículo (BEC_BASE injetado no build)
  function refToSlug(ref){
    var m=(ref||'').match(/^(.*?)\s+(\d+):(\d+)$/); if(!m) return '';
    var b=m[1].normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
    return b+'-'+m[2]+'-'+m[3];
  }
  function refToUrl(ref){ var s=refToSlug(ref); return s? BEC_BASE+'/versiculos/'+s+'/' : BEC_BASE; }

  // ---------- grifo por versículo (4 cores) ----------
  var COLORS=['y','g','b','p'], CNAMES={y:'Amarelo',g:'Verde',b:'Azul',p:'Rosa'};
  function hlColor(ref){
    var v=load('vhl')[ref];
    if(!v) return null;
    return typeof v==='object' ? (v.c||'y') : 'y'; // formato antigo: 1 = amarelo
  }
  function setHlColor(ref, color){
    var all=load('vhl');
    if(hlColor(ref)===color) delete all[ref]; else all[ref]={c:color};
    save('vhl', all);
    paintState(ref);
  }

  function paintState(ref){
    document.querySelectorAll('[data-ref]').forEach(function(cont){
      if(cont.getAttribute('data-ref')!==ref) return;
      var color=hlColor(ref);
      cont.classList.toggle('v-hl', !!color);
      if(color) cont.setAttribute('data-c', color); else cont.removeAttribute('data-c');
      cont.classList.toggle('has-note', !!load('notes')[ref]);
    });
  }
  function paintAll(root){
    (root||document).querySelectorAll('[data-ref]').forEach(function(cont){
      paintState(cont.getAttribute('data-ref'));
    });
  }

  // ---------- referências cruzadas: dataset curado (poucos KB, sempre
  // carregado) + TSK ampliado por livro (site/data/xref/<livro>.json, sob
  // demanda — só existe depois de scripts/import_tsk.py + build_xref_shards;
  // enquanto não existir, o fetch falha e a fonte curada segue sozinha) ----
  var xrefPromise=null;
  function xrefData(){
    if(!core) return Promise.resolve({});
    if(!xrefPromise) xrefPromise=core.fetchData('data/cross-references.json').catch(function(){return {};});
    return xrefPromise;
  }
  var xrefBookCache={};
  function xrefBookData(ref){
    var slug=core?core.bookSlugFromRef(ref):'';
    if(!slug) return Promise.resolve({});
    if(!xrefBookCache[slug]) xrefBookCache[slug]=core.fetchData('data/xref/'+slug+'.json').catch(function(){return {};});
    return xrefBookCache[slug];
  }
  function chVsKey(ref){ var m=(ref||'').match(/(\d+):(\d+)$/); return m ? m[1]+':'+m[2] : ''; }
  function allXrefs(ref){
    return Promise.all([xrefData(), xrefBookData(ref)]).then(function(res){
      var curated=res[0][ref]||[];
      var extra=(res[1][chVsKey(ref)]||[]).filter(function(r){ return r!==ref && curated.indexOf(r)<0; });
      return {curated:curated, extra:extra};
    });
  }
  var XREF_INITIAL_LIMIT=10;
  function xrefChip(r, curated){
    return '<a class="xref-chip'+(curated?' curated':'')+'" href="'+refToUrl(r)+'" data-xref-nav="'+esc(r)+'">'+esc(r)+'</a>';
  }
  function renderXrefInto(list, data, expanded){
    if(!list) return;
    var curatedSet={}; data.curated.forEach(function(r){ curatedSet[r]=1; });
    var all=data.curated.concat(data.extra);
    var limit=expanded ? all.length : XREF_INITIAL_LIMIT;
    var shown=all.slice(0, limit);
    var html=shown.map(function(r){ return xrefChip(r, !!curatedSet[r]); }).join('');
    if(!expanded && all.length>limit) html+='<button type="button" class="xref-more" data-xref-expand>mostrar todas ('+all.length+')</button>';
    list.innerHTML=html;
  }
  function fillXrefBlocks(root){
    (root||document).querySelectorAll('[data-xref]').forEach(function(sec){
      if(sec.dataset.xrefDone) return;
      var ref=sec.getAttribute('data-xref-ref');
      allXrefs(ref).then(function(data){
        sec.dataset.xrefDone='1';
        if(!data.curated.length && !data.extra.length) return;
        sec._xrefData=data;
        renderXrefInto(sec.querySelector('[data-xref-list]'), data, false);
        sec.hidden=false;
      });
    });
  }
  document.addEventListener('click', function(e){
    var expandBtn=e.target.closest && e.target.closest('[data-xref-expand]');
    if(!expandBtn) return;
    var container=expandBtn.closest('[data-xref],[data-vs-xref]');
    if(container && container._xrefData){
      var list=container.querySelector('[data-xref-list],[data-vs-xref-list]');
      renderXrefInto(list, container._xrefData, true);
    }
  });

  // ---------- cadeia de leitura: segue de referência em referência mostrando
  // a trilha percorrida (sensação de descoberta, sem estado no servidor) ----
  var CHAIN_KEY='bec.xchain', CHAIN_MAX=12;
  function loadChain(){ try{ return JSON.parse(sessionStorage.getItem(CHAIN_KEY)||'[]'); }catch(e){ return []; } }
  function saveChain(list){ try{ sessionStorage.setItem(CHAIN_KEY, JSON.stringify(list.slice(-CHAIN_MAX))); }catch(e){} }
  function extendChain(fromRef, fromUrl, toRef, toUrl){
    var chain=loadChain();
    if(!chain.length || chain[chain.length-1].ref!==fromRef) chain.push({ref:fromRef, url:fromUrl});
    chain.push({ref:toRef, url:toUrl});
    saveChain(chain);
  }
  function renderChainBar(){
    var cont=document.querySelector('.verse-cont[data-ref]');
    var main=document.getElementById('main');
    if(!cont || !main) return;
    var ref=cont.getAttribute('data-ref');
    var chain=loadChain();
    if(!chain.length || chain[chain.length-1].ref!==ref) return;
    var bar=document.createElement('div'); bar.className='xchain-bar';
    bar.innerHTML='🔗 Trilha: '+chain.map(function(step, i){
      return i===chain.length-1 ? '<b>'+esc(step.ref)+'</b>' : '<a href="'+esc(step.url)+'">'+esc(step.ref)+'</a>';
    }).join(' → ')+' <button type="button" data-xchain-end>Encerrar</button>';
    main.insertBefore(bar, main.firstChild);
  }
  document.addEventListener('click', function(e){
    if(e.target.closest && e.target.closest('[data-xchain-end]')){
      try{ sessionStorage.removeItem(CHAIN_KEY); }catch(err){}
      var bar=e.target.closest('.xchain-bar'); if(bar) bar.remove();
      return;
    }
    var navChip=e.target.closest && e.target.closest('[data-xref-nav]');
    if(!navChip) return;
    var toRef=navChip.getAttribute('data-xref-nav'), toUrl=navChip.getAttribute('href');
    var fromRef=sheetRef;
    if(!fromRef){ var sec=navChip.closest('[data-xref-ref]'); fromRef=sec?sec.getAttribute('data-xref-ref'):null; }
    if(fromRef) extendChain(fromRef, refToUrl(fromRef), toRef, toUrl);
  });
  renderChainBar();

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
  function verseText(ref){
    var cont=findCont(ref); var pt=cont&&cont.querySelector('.pt'); var t=pt?pt.textContent.trim():'';
    var note=load('notes')[ref];
    return ref + (t? '\n'+t : '') + (note? '\n\nAnotação: '+note : '');
  }
  // compartilha um versículo a partir do texto já em mãos (não depende do DOM):
  // gera o cartão-imagem e usa Web Share API, com cópia como último recurso.
  function shareCard(ref, t, url, btn){
    url=url||refToUrl(ref);
    var text=ref+(t?'\n'+t:'')+'\n'+url;
    makeVerseCard(ref, t).then(function(blob){
      var file; try{ file=new File([blob],'versiculo.png',{type:'image/png'}); }catch(e){ file=null; }
      if(file && navigator.canShare && navigator.canShare({files:[file]})){
        navigator.share({files:[file], text:ref+'\n'+url, title:'Bíblia em Contexto'}).catch(function(){});
      } else if(navigator.share){
        navigator.share({title:'Bíblia em Contexto', text:text}).catch(function(){});
      } else { copyText(text, btn, 'Copiado!'); download('versiculo.png', blob, 'image/png'); }
    }).catch(function(){
      if(navigator.share){ navigator.share({title:'Bíblia em Contexto', text:text}).catch(function(){}); }
      else copyText(text, btn, 'Copiado!');
    });
  }
  function shareVerse(ref, btn){
    var cont=findCont(ref); var pt=cont&&cont.querySelector('.pt'); var t=pt?pt.textContent.trim():'';
    shareCard(ref, t, refToUrl(ref), btn);
  }
  window.BEC=window.BEC||{}; window.BEC.shareCard=shareCard;

  // ---------- ferramentas de áudio (Web Speech), delegadas a BEC.speak ----------
  function speak(text, lang, btn){
    if(window.BEC && window.BEC.speak) return window.BEC.speak(text, lang, btn);
    if(!('speechSynthesis' in window)){ if(btn) btn.textContent='Sem voz neste navegador'; return; }
    window.speechSynthesis.cancel();
    var u=new SpeechSynthesisUtterance(text); u.lang=lang||'pt-BR';
    u.rate=(lang==='he-IL'||lang==='el-GR')?0.82:0.92;
    u.onend=function(){ if(btn && btn.dataset.oldText){btn.textContent=btn.dataset.oldText; delete btn.dataset.oldText;} };
    u.onerror=u.onend;
    if(btn){ btn.dataset.oldText=btn.textContent; btn.textContent='Pausar…'; }
    window.speechSynthesis.speak(u);
  }

  // ---------- coleções (mesmo formato de bec.collections usado pela Biblioteca) ----------
  function collections(){ return load('collections'); }
  function addToCollection(id, ref, url){
    var all=collections(), c=all[id]; if(!c) return;
    c.items=c.items||[];
    if(c.items.some(function(it){return it.ref===ref;})) return;
    c.items.push({ref:ref, url:url, addedAt:new Date().toISOString()});
    save('collections', all);
  }
  function createCollection(name){
    var all=collections(); var id=Date.now().toString(36)+Math.random().toString(36).slice(2,7);
    all[id]={name:name, desc:'', items:[], createdAt:new Date().toISOString()};
    save('collections', all);
    return id;
  }

  // ---------- localizar o container do versículo em qualquer página aberta ----------
  function findCont(ref){
    var els=document.querySelectorAll('[data-ref]');
    for(var i=0;i<els.length;i++){ if(els[i].getAttribute('data-ref')===ref) return els[i]; }
    return null;
  }

  // ---------- folha de ferramentas (única, criada sob demanda) ----------
  var sheet=null, sheetRef=null;
  function getSheet(){
    if(sheet) return sheet;
    sheet=document.createElement('div'); sheet.className='verse-sheet'; sheet.hidden=true;
    sheet.innerHTML='<div class="verse-sheet-backdrop" data-sheet-close></div><div class="verse-sheet-box" role="dialog" aria-modal="true"></div>';
    document.body.appendChild(sheet);
    sheet.addEventListener('click', function(e){
      if(e.target.closest && e.target.closest('[data-sheet-close]')) closeSheet();
    });
    // arrastar a folha para baixo (no mobile ela nasce colada embaixo) dispensa
    var box=sheet.querySelector('.verse-sheet-box'), dragY0=null, dragDist=0;
    box.addEventListener('touchstart', function(e){
      // só inicia o arrasto pelo topo/cabeçalho, não em áreas roláveis/campos
      if(e.target.closest('textarea,input,.vs-xref-list,.vs-col-list')) { dragY0=null; return; }
      dragY0=e.touches[0].clientY; dragDist=0;
    }, {passive:true});
    box.addEventListener('touchmove', function(e){
      if(dragY0==null) return;
      dragDist=e.touches[0].clientY-dragY0;
      if(dragDist>0){ box.style.transform='translateX(-50%) translateY('+dragDist+'px)'; box.style.transition='none'; }
    }, {passive:true});
    box.addEventListener('touchend', function(){
      if(dragY0==null) return;
      box.style.transform=''; box.style.transition='';
      if(dragDist>90) closeSheet();
      dragY0=null; dragDist=0;
    });
    return sheet;
  }
  function closeSheet(){ if(sheet){ sheet.hidden=true; } sheetRef=null; document.body.classList.remove('sheet-open'); }
  document.addEventListener('keydown', function(e){ if(e.key==='Escape') closeSheet(); });

  function favState(ref){ return window.BEC && window.BEC.favs ? window.BEC.favs.isFav(ref) : !!load('favs')[ref]; }
  function toggleFav(ref, url){
    if(window.BEC && window.BEC.favs) return window.BEC.favs.toggle(ref, url);
    var favs=load('favs');
    if(favs[ref]) delete favs[ref]; else favs[ref]={url:url, savedAt:new Date().toISOString()};
    save('favs', favs);
    return !!favs[ref];
  }

  function renderSheetBody(ref, cont){
    var box=sheet.querySelector('.verse-sheet-box');
    var origP=cont.querySelector('.orig'), ptP=cont.querySelector('.pt');
    var origText=origP?origP.textContent.trim():'', origLang=origP?origP.getAttribute('data-lang'):'pt-BR';
    var ptText=ptP?ptP.textContent.trim():'';
    var color=hlColor(ref), fav=favState(ref), note=load('notes')[ref]||'';
    var colorBtns=COLORS.map(function(c){
      return '<button type="button" class="vs-color" data-vs-color="'+c+'" data-c="'+c+'" aria-pressed="'+(color===c?'true':'false')+'" aria-label="Grifar em '+CNAMES[c]+' (toque de novo para remover)"></button>';
    }).join('');
    box.innerHTML=
      '<div class="verse-sheet-head"><b>'+esc(ref)+'</b><button type="button" class="vs-x" data-sheet-close aria-label="Fechar">×</button></div>'+
      '<div class="verse-sheet-actions">'+
        (origText?'<button type="button" class="vs-act" data-vs-act="speak-orig">🔊<span>Ouvir original</span></button>':'')+
        (ptText?'<button type="button" class="vs-act" data-vs-act="speak-pt">🔊<span>Ouvir em português</span></button>':'')+
        '<button type="button" class="vs-act" data-vs-act="fav" aria-pressed="'+(fav?'true':'false')+'">'+(fav?'★':'☆')+'<span>'+(fav?'Favorito':'Favoritar')+'</span></button>'+
        (window.BEC_MEMORY ? '<button type="button" class="vs-act" data-vs-act="memorize" aria-pressed="'+(window.BEC_MEMORY.isMemorized(ref)?'true':'false')+'">'+(window.BEC_MEMORY.isMemorized(ref)?'✓':'🧠')+'<span>'+(window.BEC_MEMORY.isMemorized(ref)?'Na fila de decorar':'Decorar')+'</span></button>' : '')+
        '<button type="button" class="vs-act" data-vs-act="copy">⧉<span>Copiar</span></button>'+
        '<button type="button" class="vs-act" data-vs-act="share">↗<span>Compartilhar</span></button>'+
        '<button type="button" class="vs-act" data-vs-act="collection">🗂<span>Salvar em coleção</span></button>'+
      '</div>'+
      '<div class="verse-sheet-row vs-colors-row"><span>Grifar</span><div class="vs-colors">'+colorBtns+'</div></div>'+
      '<div class="verse-sheet-row vs-note-row">'+
        '<label for="vs-note-ta">Nota</label>'+
        '<textarea id="vs-note-ta" class="vs-note" placeholder="Escreva sua anotação para '+esc(ref)+'…">'+esc(note)+'</textarea>'+
      '</div>'+
      '<div class="verse-sheet-row vs-xref-row" data-vs-xref hidden>'+
        '<span>Referências cruzadas</span><div class="vs-xref-list" data-vs-xref-list></div>'+
      '</div>'+
      '<div class="verse-sheet-row vs-collection-row" data-vs-collection hidden></div>';
    box.dataset.origText=origText; box.dataset.origLang=origLang; box.dataset.ptText=ptText;

    allXrefs(ref).then(function(data){
      if(sheetRef!==ref) return;
      if(!data.curated.length && !data.extra.length) return;
      var row=box.querySelector('[data-vs-xref]');
      row._xrefData=data;
      renderXrefInto(box.querySelector('[data-vs-xref-list]'), data, false);
      row.hidden=false;
    });
  }

  function openSheet(cont){
    var ref=cont.getAttribute('data-ref'); if(!ref) return;
    sheetRef=ref;
    var s=getSheet();
    renderSheetBody(ref, cont);
    s.hidden=false;
    document.body.classList.add('sheet-open');
  }

  function renderCollectionPicker(){
    var box=sheet.querySelector('.verse-sheet-box'), row=box.querySelector('[data-vs-collection]');
    var all=collections(), ids=Object.keys(all).sort(function(a,b){return (all[b].createdAt||'').localeCompare(all[a].createdAt||'');});
    var items=ids.map(function(id){ return '<button type="button" class="btn tiny" data-vs-col-add="'+id+'">'+esc(all[id].name)+'</button>'; }).join('');
    row.innerHTML=(items?'<div class="vs-col-list">'+items+'</div>':'<p class="muted-line">Nenhuma coleção ainda.</p>')+
      '<form class="vs-col-new" data-vs-col-new><input type="text" name="name" maxlength="80" placeholder="Nova coleção…"><button type="submit" class="btn tiny primary">Criar</button></form>';
    row.hidden=false;
  }

  document.addEventListener('submit', function(e){
    var f=e.target.closest && e.target.closest('[data-vs-col-new]');
    if(!f || !sheetRef) return;
    e.preventDefault();
    var name=(f.name.value||'').trim(); if(!name) return;
    var id=createCollection(name);
    addToCollection(id, sheetRef, refToUrl(sheetRef));
    var box=sheet.querySelector('.verse-sheet-box');
    box.querySelector('[data-vs-collection]').innerHTML='<p class="vs-done">Adicionado a "'+esc(name)+'" ✓</p>';
  });

  document.addEventListener('click', function(e){
    // colar (colar dentro do sheet)
    var colAdd=e.target.closest && e.target.closest('[data-vs-col-add]');
    if(colAdd && sheetRef){
      var id=colAdd.getAttribute('data-vs-col-add');
      addToCollection(id, sheetRef, refToUrl(sheetRef));
      flash(colAdd, '✓ Adicionado');
      return;
    }
    var color=e.target.closest && e.target.closest('[data-vs-color]');
    if(color && sheetRef){
      setHlColor(sheetRef, color.getAttribute('data-vs-color'));
      renderSheetBody(sheetRef, findCont(sheetRef) || document.createElement('div'));
      return;
    }
    var act=e.target.closest && e.target.closest('[data-vs-act]');
    if(act && sheetRef){
      var box=sheet.querySelector('.verse-sheet-box'), kind=act.getAttribute('data-vs-act');
      if(kind==='speak-orig'){ if(window.BEC && window.BEC.stopListenChapter) window.BEC.stopListenChapter(); speak(box.dataset.origText, box.dataset.origLang, act.querySelector('span')||act); }
      else if(kind==='speak-pt'){ if(window.BEC && window.BEC.stopListenChapter) window.BEC.stopListenChapter(); speak(box.dataset.ptText, 'pt-BR', act.querySelector('span')||act); }
      else if(kind==='fav'){
        var cont=findCont(sheetRef);
        var on=toggleFav(sheetRef, refToUrl(sheetRef));
        act.setAttribute('aria-pressed', on?'true':'false');
        act.innerHTML=(on?'★':'☆')+'<span>'+(on?'Favorito':'Favoritar')+'</span>';
      }
      else if(kind==='memorize' && window.BEC_MEMORY){
        var on=window.BEC_MEMORY.toggle(sheetRef, box.dataset.ptText, refToUrl(sheetRef));
        act.setAttribute('aria-pressed', on?'true':'false');
        act.innerHTML=(on?'✓':'🧠')+'<span>'+(on?'Na fila de decorar':'Decorar')+'</span>';
      }
      else if(kind==='copy') copyText(verseText(sheetRef), act, 'Copiado!');
      else if(kind==='share') shareVerse(sheetRef, act);
      else if(kind==='collection') renderCollectionPicker();
      return;
    }
  });

  document.addEventListener('input', function(e){
    if(e.target.matches && e.target.matches('.vs-note') && sheetRef){
      var ref=sheetRef, val=e.target.value.trim();
      var notes=load('notes');
      if(val) notes[ref]=val; else delete notes[ref];
      save('notes', notes);
      // marca a data da edição (só local — a home usa pra mostrar as mais
      // recentes primeiro; não faz parte do que sincroniza com a conta).
      var meta=load('notesMeta');
      if(val){ meta[ref]=new Date().toISOString(); } else { delete meta[ref]; }
      try{ localStorage.setItem('bec.notesMeta', JSON.stringify(meta)); }catch(err){}
      paintState(ref);
    }
  });

  // toca no texto do versículo (fora de links/botões/seleção) abre a folha
  document.addEventListener('click', function(e){
    var tap=e.target.closest && e.target.closest('.verse-tap');
    if(!tap) return;
    if(e.target.closest && e.target.closest('a,button,select,textarea,input,.lex-w,.audio-transcript')) return;
    var sel=window.getSelection();
    if(sel && !sel.isCollapsed && sel.toString().trim()) return; // deixa a seleção de texto funcionar
    var cont=tap.closest('[data-ref]'); if(!cont) return;
    openSheet(cont);
  });

  // ---------- marca-texto por seleção: barra flutuante (Copiar seleção) ----------
  var selBar=null, selT=null;
  function getSelBar(){
    if(selBar) return selBar;
    selBar=document.createElement('div'); selBar.className='sel-bar'; selBar.hidden=true;
    selBar.innerHTML='<button type="button" data-sel="copy">⧉ Copiar seleção</button>';
    document.body.appendChild(selBar);
    selBar.addEventListener('mousedown', function(e){ e.preventDefault(); });
    selBar.addEventListener('click', function(e){ var b=e.target.closest('button'); if(b) copySelection(b); });
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
  function copySelection(btn){ var info=selInfo(); if(info) copyText(info.text, btn, 'Copiado!'); }
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

  // ---------- ferramentas ocultas do painel de leitura (exportar/apagar) ----------
  function studyText(){
    var n=load('notes'), v=load('vhl'), keys=allRefs(n,v,{});
    return exportText(keys, n, v, {});
  }
  function shareStudyText(text, btn){
    // pela folha nativa de compartilhar (iOS/Android permitem "Salvar em Notas")
    if(navigator.share){ navigator.share({title:'Bíblia em Contexto', text:text}).catch(function(){}); }
    else copyText(text, btn, 'Copiado!');
  }
  document.addEventListener('click', function(e){
    if(e.target.closest && e.target.closest('[data-study-export]')) download('meu-estudo.txt', studyText(), 'text/plain');
    if(e.target.closest && e.target.closest('[data-study-share]')) shareStudyText(studyText(), e.target.closest('[data-study-share]'));
    if(e.target.closest && e.target.closest('[data-study-clear]')){
      confirmModal('Apagar TODAS as marcações e anotações deste navegador? Esta ação não pode ser desfeita.', function(){
        ['notes','vhl','whl'].forEach(function(k){ localStorage.removeItem('bec.'+k); });
        if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
        paintAll(); render();
      });
    }
  });

  // ---------- página de Anotações: listar, copiar, baixar, limpar ----------
  function slugFromRef(ref){ var s=refToSlug(ref); return s? '../versiculos/'+s+'/' : '#'; }
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
    if(!keys.length){ box.innerHTML='<p class="empty">Você ainda não grifou nem anotou nada. Abra um versículo (ou um capítulo) e toque no texto para “Grifar” ou “Nota”.</p>'; return; }
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
    if(x) x.onclick=function(){ confirmModal('Apagar TODAS as marcações e anotações deste navegador? Esta ação não pode ser desfeita.', function(){ ['notes','vhl','whl'].forEach(function(k){localStorage.removeItem('bec.'+k);}); if(window.BEC_SYNC) window.BEC_SYNC.markDirty(); render(); }); };
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

  paintAll();
  fillXrefBlocks();
  document.addEventListener('bec:content-added', function(e){
    var root=e.detail && e.detail.root;
    paintAll(root); fillXrefBlocks(root);
  });
  document.addEventListener('bec:study-sync', function(){ paintAll(); render(); });
})();
