// Utilitários compartilhados por todos os módulos de estudo (evita reimplementar
// esc/confirmModal/download em cada arquivo). Carregado antes dos demais.
window.BEC = window.BEC || {};
(function(){
  var PREFIX = (document.body && document.body.getAttribute('data-prefix')) || '';

  function esc(s){
    return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  function download(name, text, type){
    var b=new Blob([text], {type:type||'text/plain'}), u=URL.createObjectURL(b);
    var a=document.createElement('a'); a.href=u; a.download=name; document.body.appendChild(a);
    a.click(); a.remove(); URL.revokeObjectURL(u);
  }

  function confirmModal(msg, onYes, yesLabel){
    var ov=document.createElement('div'); ov.className='bec-modal';
    ov.innerHTML='<div class="bec-modal-box"><p>'+esc(msg)+'</p>'+
      '<div class="bec-modal-actions"><button type="button" class="btn ghost" data-no>Cancelar</button>'+
      '<button type="button" class="btn danger" data-yes>'+esc(yesLabel||'Apagar tudo')+'</button></div></div>';
    ov.addEventListener('click', function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-no]'))) ov.remove();
      else if(e.target.closest && e.target.closest('[data-yes]')){ ov.remove(); onYes(); }
    });
    document.body.appendChild(ov);
    return ov;
  }

  function copyText(str, btn, doneLabel){
    (navigator.clipboard?navigator.clipboard.writeText(str):Promise.reject())
      .then(function(){ if(btn) flash(btn, doneLabel||'Copiado!'); })
      .catch(function(){
        try{
          var t=document.createElement('textarea'); t.value=str; document.body.appendChild(t);
          t.select(); document.execCommand('copy'); t.remove();
          if(btn) flash(btn, doneLabel||'Copiado!');
        }catch(e){ if(btn) flash(btn,'Falhou'); }
      });
  }

  function flash(btn, txt, ms){
    var o=btn.textContent; btn.textContent=txt;
    setTimeout(function(){ btn.textContent=o; }, ms||1400);
  }

  // fetch relativo à raiz do site, funciona em qualquer profundidade de página
  function fetchData(path){ return fetch(PREFIX+path).then(function(r){ if(!r.ok) throw new Error('http '+r.status); return r.json(); }); }

  function bookSlugFromRef(ref){
    var m=(ref||'').match(/^(.*?)\s+\d+:\d+$/); if(!m) return '';
    return m[1].normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
  }

  window.BEC.core = {
    prefix: PREFIX, esc: esc, download: download, confirmModal: confirmModal,
    copyText: copyText, flash: flash, fetchData: fetchData, bookSlugFromRef: bookSlugFromRef
  };

  // registra o service worker (app-shell + offline). Escopo = raiz do site,
  // então funciona em qualquer subpasta/profundidade de página.
  if('serviceWorker' in navigator){
    window.addEventListener('load', function(){
      navigator.serviceWorker.register(PREFIX+'sw.js').catch(function(){});
    });
  }
})();
