var BEC_BASE="https://alusionbr.github.io/bibliaonline";
// Ferramentas de estudo (offline): grifar palavra/versículo, anotar, exportar.
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
    var bar=document.createElement('div'); bar.className='study';
    var hint=cont.matches('.verse-cont') ? '<span class="study-hint">use a caneta 🖍 para grifar; selecione para copiar</span>' : '';
    bar.innerHTML='<button type="button" data-act="vhl">🖍 Grifar versículo</button>'+
      '<button type="button" data-act="note">🗒 Anotar</button>'+
      '<button type="button" data-act="copy">⧉ Copiar versículo</button>'+
      '<button type="button" data-act="share">↗ Compartilhar</button>'+hint;
    anchor.appendChild(bar);
    var nb=document.createElement('div'); nb.className='note-box'; nb.hidden=true;
    nb.innerHTML='<textarea placeholder="Sua anotação para '+esc(ref)+'..."></textarea>'+
      '<div class="note-actions"><button type="button" data-act="copy-note">⧉ Copiar versículo + nota</button></div>';
    anchor.appendChild(nb);
    cont.dataset.studyReady='1';
    apply(cont, ref);
  }

  function flash(btn, txt){ var o=btn.textContent; btn.textContent=txt; setTimeout(function(){btn.textContent=o;},1400); }
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

  function apply(cont, ref){
    if(load('vhl')[ref]){ cont.classList.add('v-hl'); var b=cont.querySelector('.study button[data-act="vhl"]'); if(b) b.classList.add('on'); }
    var notes=load('notes');
    if(notes[ref]){
      var ta=cont.querySelector('.note-box textarea');
      if(ta){ ta.value=notes[ref]; ta.closest('.note-box').hidden=false; }
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
  }

  document.addEventListener('click', function(e){
    var w=e.target.closest && e.target.closest('.w');
    if(w && w.closest('[data-ref]')){ if(penOn) return; toggleWord(w); return; }
    var btn=e.target.closest && e.target.closest('.study button, .note-actions button');
    if(btn){
      var cont=btn.closest('[data-ref]'), ref=cont.getAttribute('data-ref'), act=btn.dataset.act;
      if(act==='vhl') toggleVerse(cont, ref, btn);
      else if(act==='note'){ var nb=cont.querySelector('.note-box'); nb.hidden=!nb.hidden; if(!nb.hidden) nb.querySelector('textarea').focus(); }
      else if(act==='copy' || act==='copy-note') copyText(verseText(cont, ref), btn);
      else if(act==='share') shareVerse(cont, ref, btn);
    }
  });

  // ---------- caneta marca-texto: arrastar pinta as palavras (com cores) ----------
  var penOn=false, penColor='y', painting=false, activePointerId=null, pendingWhl=null;
  var COLORS=['y','g','b','p'], CNAMES={y:'Amarelo',g:'Verde',b:'Azul',p:'Rosa'};
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
  function paintWord(w){
    if(!w) return; var cont=w.closest('[data-ref]'); if(!cont) return;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var recd=pendingWhl[ref]||(pendingWhl[ref]={}); var arr=recd[f]||(recd[f]=[]);
    var found=null; for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ found=arr[n]; break; } }
    if(found){ if(found.c!==penColor){ found.c=penColor; w.setAttribute('data-c', penColor); } }
    else { arr.push({i:i,t:w.textContent,c:penColor}); w.classList.add('w-hl'); w.setAttribute('data-c', penColor); bumpMark(); }
  }
  function startPaint(e){
    if(!penOn) return;
    var w=(e.target.closest && e.target.closest('.w')); if(!w || !w.closest('[data-ref]')) return;
    e.preventDefault(); painting=true; activePointerId=e.pointerId; pendingWhl=load('whl'); paintWord(w);
  }
  function movePaint(e){ if(!painting || e.pointerId!==activePointerId) return; e.preventDefault(); paintWord(wordAtPoint(e.clientX, e.clientY)); }
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
    pal.innerHTML=COLORS.map(function(c){ return '<button type="button" data-c="'+c+'" aria-label="'+CNAMES[c]+'"></button>'; }).join('');
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
      var h='<div class="anot"><h3><a href="'+refToUrl(ref)+'">'+esc(ref)+'</a></h3>';
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
  // ---------- caixa "Minhas anotações" que abre por cima (reaproveita render()) ----------
  var notesDrawer=null;
  function openNotesDrawer(){
    if(!notesDrawer){
      notesDrawer=document.createElement('div');
      notesDrawer.className='anot-drawer';
      notesDrawer.innerHTML='<div class="anot-drawer-box" role="dialog" aria-modal="true" aria-label="Minhas anotações">'+
        '<div class="anot-drawer-head"><h2>Minhas anotações</h2>'+
        '<button type="button" class="anot-drawer-x" aria-label="Fechar">✕</button></div>'+
        '<div id="anotacoes" class="anot-list"></div>'+
        '<p class="anot-drawer-foot"><a href="'+BEC_BASE+'/anotacoes/">Gerenciar / exportar →</a></p>'+
        '</div>';
      document.body.appendChild(notesDrawer);
      function close(){ notesDrawer.classList.remove('open'); }
      notesDrawer.addEventListener('click', function(e){ if(e.target===notesDrawer || e.target.closest('.anot-drawer-x')) close(); });
      document.addEventListener('keydown', function(e){ if(e.key==='Escape' && notesDrawer.classList.contains('open')) close(); });
    }
    render();
    notesDrawer.classList.add('open');
  }
  // abrir a caixa ao tocar nos links de "Anotações" (menu, ferramentas) — exceto na própria página /anotacoes/
  if(!document.getElementById('anotacoes')){
    document.addEventListener('click', function(e){
      var a=e.target.closest && e.target.closest('a[href$="anotacoes/"]'); if(!a) return;
      if(a.closest('.anot-drawer')) return; // o link "Gerenciar →" navega normalmente
      e.preventDefault(); openNotesDrawer();
    });
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', wire); else wire();
})();
