// Léxico hebraico interativo: toca numa palavra do texto original para ver
// número de Strong, glosa e morfologia. Dados 100% locais e curados (sem IA):
// BEC_LEXICON (glossário) injetado no build + data/tokens/<livro>.json
// (tokenização palavra-a-palavra do Westminster Leningrad Codex), carregado
// sob demanda por livro. Se a contagem de palavras não bater com a de tokens
// para um versículo, a palavra simplesmente não vira interativa.
(function(){
  if(!window.BEC || !window.BEC.core) return;
  var core = window.BEC.core;
  var LEX = window.BEC_LEXICON || {};
  var shardCache = {};
  var PREFIXES = {b:'prefixo: em / com / por', c:'prefixo: e', d:'prefixo: o / a (artigo)',
    k:'prefixo: como', l:'prefixo: para / a', m:'prefixo: de / desde', s:'prefixo relativo: que'};
  var POS = {A:'adjetivo', C:'conjunção', D:'advérbio', N:'substantivo', P:'pronome',
    R:'preposição', S:'sufixo', T:'partícula', V:'verbo'};
  var GENDER = {m:'masculino', f:'feminino', b:'ambos os gêneros', c:'comum'};
  var NUMBER = {s:'singular', p:'plural', d:'dual'};
  var STATE = {a:'absoluto', c:'construto', d:'determinado'};

  function bookShard(slug){
    if(!shardCache[slug]) shardCache[slug]=core.fetchData('data/tokens/'+slug+'.json').catch(function(){return null;});
    return shardCache[slug];
  }

  function wrapOriginal(p){
    if(p.dataset.lexWrapped) return;
    var parts=p.textContent.split(/(\s+)/), i=0;
    p.textContent='';
    parts.forEach(function(part){
      if(part===''||/^\s+$/.test(part)){ p.appendChild(document.createTextNode(part)); return; }
      var s=document.createElement('span'); s.className='lex-w-pending'; s.dataset.i=i; s.textContent=part;
      p.appendChild(s); i++;
    });
    p.dataset.lexWrapped='1';
  }

  function annotate(cont){
    var p=cont.querySelector('.orig.scr-hebrew[data-lang="he-IL"]');
    if(!p || p.dataset.lexWrapped) return;
    var ref=cont.getAttribute('data-ref'); if(!ref) return;
    var m=ref.match(/^(.*?)\s+(\d+):(\d+)$/); if(!m) return;
    var slug=core.bookSlugFromRef(ref); if(!slug) return;
    wrapOriginal(p);
    bookShard(slug).then(function(map){
      if(!map) return;
      var toks=map[m[2]+':'+m[3]]; if(!toks) return;
      var words=p.querySelectorAll('.lex-w-pending');
      if(words.length!==toks.length) return; // alinhamento não bateu: degrada em silêncio
      words.forEach(function(w, idx){
        w.className='lex-w'; w.tabIndex=0; w.setAttribute('role','button');
        w.setAttribute('aria-label','Ver no léxico');
        w.dataset.strong=toks[idx][0]; w.dataset.morph=toks[idx][1]||'';
      });
    });
  }

  function annotateAll(root){
    (root||document).querySelectorAll('.ch-verse[data-ref], .verse-cont[data-ref]').forEach(annotate);
  }

  function decodeMorph(code){
    if(!code) return '';
    var segs=code.replace(/^[HA]/,'').split('/');
    var last=segs[segs.length-1];
    var pos=POS[last.charAt(0)];
    if(!pos) return '';
    var out=pos;
    if(last.charAt(0)==='N' && last.length>=4){
      var extra=[GENDER[last.charAt(1)], NUMBER[last.charAt(2)], STATE[last.charAt(3)]].filter(Boolean);
      if(extra.length) out+=', '+extra.join(', ');
    }
    return out;
  }

  function lookupPart(part){
    if(/^[a-z]$/.test(part)) return {prefix:PREFIXES[part]||''};
    var num=part.split(' ')[0];
    var entry=LEX[num];
    return entry ? {he:entry.he, tr:entry.tr, pt:entry.pt} : null;
  }

  var pop=null;
  function getPop(){
    if(pop) return pop;
    pop=document.createElement('div'); pop.className='lex-pop'; pop.hidden=true;
    document.body.appendChild(pop);
    return pop;
  }
  function hidePop(){ if(pop) pop.hidden=true; }
  function showPop(w){
    var parts=(w.dataset.strong||'').split('/');
    var rows=parts.map(lookupPart).filter(Boolean);
    var box=getPop();
    var morphLine=decodeMorph(w.dataset.morph);
    var body=rows.map(function(r){
      if(r.prefix) return '<p class="lex-pop-prefix">'+core.esc(r.prefix)+'</p>';
      return '<p class="lex-pop-entry"><b>'+core.esc(r.tr||'')+'</b> — '+core.esc(r.pt||'')+'</p>';
    }).join('');
    if(!body) body='<p class="lex-pop-empty">Sem verbete no glossário para esta palavra ainda.</p>';
    box.innerHTML='<div class="lex-pop-word">'+core.esc(w.textContent)+'</div>'+
      (morphLine?'<p class="lex-pop-morph">'+core.esc(morphLine)+'</p>':'')+body+
      '<button type="button" class="lex-pop-close" aria-label="Fechar">×</button>';
    box.hidden=false;
    try{
      var r=w.getBoundingClientRect();
      var top=window.scrollY+r.bottom+8;
      var left=window.scrollX+Math.max(8,Math.min(r.left, document.documentElement.clientWidth-260));
      box.style.top=top+'px'; box.style.left=left+'px';
    }catch(e){}
  }

  document.addEventListener('click', function(e){
    if(e.target.closest && e.target.closest('.lex-pop-close')){ hidePop(); return; }
    var w=e.target.closest && e.target.closest('.lex-w');
    if(w){ e.stopPropagation(); showPop(w); return; }
    if(pop && !pop.hidden && !(e.target.closest && e.target.closest('.lex-pop'))) hidePop();
  });
  document.addEventListener('keydown', function(e){
    if(e.key==='Escape'){ hidePop(); return; }
    if(e.key==='Enter' || e.key===' '){
      var w=e.target.closest && e.target.closest('.lex-w');
      if(w){ e.preventDefault(); showPop(w); }
    }
  });

  annotateAll();
  document.addEventListener('bec:content-added', function(e){ annotateAll(e.detail && e.detail.root); });
})();
