// Ferramentas de estudo (offline): grifar palavra/versículo, anotar, exportar.
// Tudo salvo no localStorage deste navegador. Nada vai para servidor.
(function(){
  function load(k){try{return JSON.parse(localStorage.getItem('bec.'+k)||'{}');}catch(e){return{};}}
  function save(k,v){try{localStorage.setItem('bec.'+k,JSON.stringify(v));}catch(e){}}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

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
    var hint=cont.matches('.verse-cont') ? '<span class="study-hint">toque numa palavra para grifar</span>' : '';
    bar.innerHTML='<button type="button" data-act="vhl">🖍 Grifar versículo</button>'+
      '<button type="button" data-act="note">🗒 Anotar</button>'+
      '<button type="button" data-act="copy">⧉ Copiar versículo</button>'+hint;
    anchor.appendChild(bar);
    var nb=document.createElement('div'); nb.className='note-box'; nb.hidden=true;
    nb.innerHTML='<textarea placeholder="Sua anotação para '+esc(ref)+'..."></textarea>'+
      '<div class="note-actions"><button type="button" data-act="copy-note">⧉ Copiar nota</button></div>';
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
    return ref + (t? ' — ' + t : '');
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
        if(w) w.classList.add('w-hl');
      });
    });
  }

  function toggleWord(w){
    var cont=w.closest('[data-ref]'); if(!cont) return;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var all=load('whl'), recd=all[ref]||{}, arr=recd[f]||[];
    var pos=-1; for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ pos=n; break; } }
    if(pos>-1){ arr.splice(pos,1); w.classList.remove('w-hl'); }
    else { arr.push({i:i,t:w.textContent}); w.classList.add('w-hl'); }
    if(arr.length) recd[f]=arr; else delete recd[f];
    if(Object.keys(recd).length) all[ref]=recd; else delete all[ref];
    save('whl', all);
  }

  function toggleVerse(cont, ref, btn){
    var all=load('vhl');
    if(all[ref]){ delete all[ref]; cont.classList.remove('v-hl'); if(btn) btn.classList.remove('on'); }
    else { all[ref]=1; cont.classList.add('v-hl'); if(btn) btn.classList.add('on'); }
    save('vhl', all);
  }

  document.addEventListener('click', function(e){
    var w=e.target.closest && e.target.closest('.w');
    if(w && w.closest('[data-ref]')){ toggleWord(w); return; }
    var btn=e.target.closest && e.target.closest('.study button, .note-actions button');
    if(btn){
      var cont=btn.closest('[data-ref]'), ref=cont.getAttribute('data-ref'), act=btn.dataset.act;
      if(act==='vhl') toggleVerse(cont, ref, btn);
      else if(act==='note'){ var nb=cont.querySelector('.note-box'); nb.hidden=!nb.hidden; if(!nb.hidden) nb.querySelector('textarea').focus(); }
      else if(act==='copy') copyText(verseText(cont, ref), btn);
      else if(act==='copy-note'){ var ta=cont.querySelector('.note-box textarea'); copyText(ref+'\n'+(ta?ta.value:''), btn); }
    }
  });
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
    if(x) x.onclick=function(){ if(confirm('Apagar TODAS as marcações e anotações deste navegador?')){ ['notes','vhl','whl'].forEach(function(k){localStorage.removeItem('bec.'+k);}); render(); } };
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', wire); else wire();
})();
