// home: menu + busca local (índice embutido em window.__INDEX__)
document.addEventListener('click',function(e){
  if(e.target.closest('[data-menu]')){document.querySelector('[data-links]').classList.toggle('open');}
});
(function(){
  var q=document.getElementById('q'), out=document.getElementById('results');
  if(!q||!out||!window.__INDEX__) return;
  // busca sem acento: "genesis" encontra "Gênesis", "joao" encontra "João".
  function fold(s){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
  window.__INDEX__.forEach(function(i){i.kf=fold(i.k);});  // chave sem acento (1x)
  function render(term){
    out.innerHTML='';
    term=fold((term||'').trim().toLowerCase());
    if(!term) return;
    // casa por tokens: cada palavra digitada precisa aparecer na chave.
    // assim "salmo 23", "salmos 23" e "23:1" encontram o versículo direto
    // (e não só os artigos relacionados).
    var terms=term.split(/\s+/).filter(Boolean);
    var res=window.__INDEX__.filter(function(i){
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
  q.addEventListener('input',function(e){render(e.target.value);});
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
