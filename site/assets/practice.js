var BEC_BASE="https://alusionbr.github.io/bibliaonline";
// Memorização com repetição espaçada (SM-2 simplificado) e quiz por capítulo
// gerado no cliente a partir do texto já na página. Tudo local (bec.memory,
// bec.quiz), sincroniza quando há conta. Nenhuma pergunta é curada: é
// derivada do próprio texto Almeida 1911 já presente no DOM.
(function(){
  var core = window.BEC && window.BEC.core;
  function esc(s){ return core ? core.esc(s) : (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function qs(s, root){ return (root||document).querySelector(s); }
  function qsa(s, root){ return Array.prototype.slice.call((root||document).querySelectorAll(s)); }
  function today(){ return new Date().toISOString().slice(0,10); }

  function load(k, fb){ try{ var v=JSON.parse(localStorage.getItem('bec.'+k)||'null'); return v==null?fb:v; }catch(e){ return fb; } }
  function save(k, v){ try{ localStorage.setItem('bec.'+k, JSON.stringify(v)); }catch(e){} if(window.BEC_SYNC) window.BEC_SYNC.markDirty(); }
  function notifyChange(){ document.dispatchEvent(new CustomEvent('bec:practice-changed')); }

  function refToSlug(ref){
    var m=(ref||'').match(/^(.*?)\s+(\d+):(\d+)$/); if(!m) return '';
    var b=core ? core.bookSlugFromRef(ref) : '';
    return b ? b+'-'+m[2]+'-'+m[3] : '';
  }
  function refToUrl(ref){ var s=refToSlug(ref); return s ? (typeof BEC_BASE!=='undefined'?BEC_BASE:'')+'/versiculos/'+s+'/' : '#'; }

  // ---------- utilidades de texto (sem regex unicode, compatível com o resto do site) ----------
  function isLetter(ch){ return /[A-Za-zÀ-ÖØ-öø-ÿ]/.test(ch); }
  function cleanWord(w){ return (w||'').replace(/[^A-Za-zÀ-ÖØ-öø-ÿ]/g,''); }
  var STOP={};
  ('de e o a os as que do da em um uma para com não se por seu sua seus suas dos das ao aos à às '+
   'mas ou como quando onde já mais muito também foi era são está tem ter este esta isto esse essa '+
   'isso aquele aquela eu tu ele ela nós vós eles elas me te lhe nos vos lhes meu minha teu tua nosso '+
   'nossa pelo pela num numa entre sobre sob até desde então pois porque quem qual quais no na nos nas '+
   'lhe será serão foram haver havia').split(/\s+/).forEach(function(w){ STOP[w]=1; });
  function isContentWord(w){
    var c=cleanWord(w).toLowerCase();
    return c.length>=4 && !STOP[c];
  }

  function hashStr(s){
    var h=2166136261;
    for(var i=0;i<s.length;i++){ h^=s.charCodeAt(i); h=(h*16777619)>>>0; }
    return h>>>0;
  }
  function mulberry32(seed){
    var t=seed>>>0;
    return function(){
      t=(t+0x6D2B79F5)|0;
      var r=Math.imul(t^(t>>>15),1|t);
      r=(r+Math.imul(r^(r>>>7),61|r))^r;
      return ((r^(r>>>14))>>>0)/4294967296;
    };
  }
  function shuffle(arr, rng){
    for(var i=arr.length-1;i>0;i--){ var j=Math.floor(rng()*(i+1)); var tmp=arr[i]; arr[i]=arr[j]; arr[j]=tmp; }
    return arr;
  }
  function uniqueCI(list){
    var seen={}, out=[];
    list.forEach(function(w){ var k=w.toLowerCase(); if(!seen[k]){ seen[k]=1; out.push(w); } });
    return out;
  }

  // ==================================================================
  // Memorização (SM-2 simplificado)
  // ==================================================================
  function loadMem(){ var m=load('memory',null); if(!m||typeof m!=='object') m={}; m.items=m.items||{}; m.log=m.log||{}; return m; }
  function saveMem(m){ save('memory', m); }

  // Avalia uma revisão (grade 0=Errei, 1=Difícil, 2=Bom, 3=Fácil) e recalcula
  // fator de facilidade, intervalo (dias) e próxima data de vencimento.
  function schedule(item, grade){
    item.ef = Math.max(1.3, Math.min(2.8, item.ef || 2.5));
    item.reps = item.reps || 0;
    item.ivl = item.ivl || 0;
    if(grade===0){
      item.lapses = (item.lapses||0)+1;
      item.reps = 0; item.ivl = 0;
      item.ef = Math.max(1.3, item.ef-0.20);
    } else if(grade===1){
      item.reps++;
      item.ivl = Math.max(1, Math.round(item.ivl*1.2));
      item.ef = Math.max(1.3, item.ef-0.15);
    } else if(grade===2){
      item.reps++;
      item.ivl = item.reps===1 ? 1 : (item.reps===2 ? 3 : Math.round(item.ivl*item.ef));
    } else {
      item.reps++;
      item.ivl = item.reps===1 ? 2 : (item.reps===2 ? 5 : Math.round(item.ivl*item.ef*1.3));
      item.ef = Math.min(2.8, item.ef+0.10);
    }
    item.ivl = Math.max(0, Math.min(365, item.ivl));
    var d=new Date(); d.setDate(d.getDate()+item.ivl);
    item.due = d.toISOString().slice(0,10);
    item.last = new Date().toISOString();
    return item;
  }

  // refs com revisão vencida (due <= hoje), mais antigas primeiro.
  function dueRefs(m){
    m = m || loadMem();
    var t = today();
    return Object.keys(m.items)
      .filter(function(ref){ var it=m.items[ref]; return it && it.due && it.due<=t; })
      .sort(function(a,b){ return (m.items[a].due||'').localeCompare(m.items[b].due||''); });
  }

  function isMemorized(ref){ var m=loadMem(); return !!m.items[ref]; }
  // liga/desliga um versículo na lista de memorização (mesmo padrão de BEC.favs.toggle)
  function toggleMemorize(ref, t, url){
    var m=loadMem();
    if(m.items[ref]){
      delete m.items[ref];
    } else {
      m.items[ref] = {t:t||'', url:url||refToUrl(ref), ef:2.5, ivl:0, due:today(), reps:0, lapses:0, addedAt:new Date().toISOString()};
    }
    saveMem(m);
    renderMemoryApp();
    notifyChange();
    return !!m.items[ref];
  }
  function removeMemorize(ref){
    var m=loadMem();
    if(m.items[ref]){ delete m.items[ref]; saveMem(m); renderMemoryApp(); notifyChange(); }
  }

  // Busca o texto do versículo quando o item foi adicionado sem ele (ex.: a
  // partir da lista de favoritos, que só guarda referência + url). Lê a
  // própria página do versículo — nunca carrega o dataset inteiro (38 MB).
  function ensureText(ref, item){
    if(item.t) return Promise.resolve(item.t);
    if(!item.url || typeof fetch!=='function' || typeof DOMParser==='undefined') return Promise.resolve('');
    return fetch(item.url).then(function(r){ return r.text(); }).then(function(html){
      var doc=new DOMParser().parseFromString(html, 'text/html');
      var el=doc.querySelector('.pt');
      var t=el ? el.textContent.trim() : '';
      if(t){ var m=loadMem(); if(m.items[ref]){ m.items[ref].t=t; saveMem(m); } }
      return t;
    }).catch(function(){ return ''; });
  }

  // ---------- exercícios progressivos (dificuldade cresce com o número de revisões) ----------
  function maskedWords(text, ref){
    var rng=mulberry32(hashStr(ref+today()));
    var parts=text.split(/(\s+)/);
    var html=parts.map(function(w){
      if(/^\s+$/.test(w) || !w) return esc(w);
      if(!isContentWord(w) || rng()>=0.4) return esc(w);
      var clean=cleanWord(w);
      return '<button type="button" class="mem-chip" data-mem-word="'+esc(w)+'">'+
        Array(Math.min(clean.length,6)+1).join('▢')+'</button>';
    }).join('');
    return '<p class="mem-text mem-masked">'+html+'</p>';
  }
  function firstLetters(text){
    var parts=text.split(/(\s+)/);
    var html=parts.map(function(w){
      if(/^\s+$/.test(w) || !w) return esc(w);
      var i=0; while(i<w.length && !isLetter(w[i])) i++;
      if(i>=w.length) return esc(w);
      var lead=w.slice(0,i), first=w[i], rest=w.slice(i+1);
      var masked=rest.replace(/[A-Za-zÀ-ÖØ-öø-ÿ]/g,'_');
      return esc(lead)+esc(first)+esc(masked);
    }).join('');
    return '<p class="mem-text mem-letters">'+html+'</p>';
  }
  function exercisePromptHtml(ref, item){
    var reps=item.reps||0;
    if(reps>=6) return '<p class="mem-text mem-hidden">Recite de memória, depois confira.</p>';
    if(reps>=4) return firstLetters(item.t);
    if(reps>=2) return maskedWords(item.t, ref);
    return '<p class="mem-text">'+esc(item.t)+'</p>';
  }

  // ---------- overlay de revisão ----------
  var reviewEl=null, queue=[], qIdx=0, sessionDone=0;
  function getReviewOverlay(){
    if(reviewEl) return reviewEl;
    reviewEl=document.createElement('div'); reviewEl.className='verse-sheet mem-review'; reviewEl.hidden=true;
    reviewEl.innerHTML='<div class="verse-sheet-backdrop" data-mem-close></div><div class="verse-sheet-box mem-review-box" role="dialog" aria-modal="true"></div>';
    document.body.appendChild(reviewEl);
    reviewEl.addEventListener('click', function(e){
      if(e.target.closest && e.target.closest('[data-mem-close]')) closeReview();
      var chip=e.target.closest && e.target.closest('[data-mem-word]');
      if(chip){ var span=document.createElement('span'); span.className='mem-chip-revealed'; span.textContent=chip.getAttribute('data-mem-word'); chip.replaceWith(span); return; }
      var reveal=e.target.closest && e.target.closest('[data-mem-reveal]');
      if(reveal) revealAnswer();
      var grade=e.target.closest && e.target.closest('[data-mem-grade]');
      if(grade) gradeCurrent(parseInt(grade.getAttribute('data-mem-grade'),10));
    });
    return reviewEl;
  }
  function closeReview(){ if(reviewEl) reviewEl.hidden=true; document.body.classList.remove('sheet-open'); renderMemoryApp(); }

  function openReview(){
    queue=dueRefs().slice(0,20); // sessão razoável por vez
    qIdx=0; sessionDone=0;
    var el=getReviewOverlay(); el.hidden=false; document.body.classList.add('sheet-open');
    renderReviewStep();
  }
  function revealAnswer(){
    var box=reviewEl.querySelector('.mem-review-box');
    var m=loadMem(), ref=queue[qIdx], item=m.items[ref]; if(!item) return;
    var answer=box.querySelector('[data-mem-answer]');
    if(answer) answer.innerHTML='<p class="mem-text">'+esc(item.t)+'</p>'+
      '<div class="mem-grade-row">'+
        '<button type="button" class="btn mem-grade g0" data-mem-grade="0">Errei</button>'+
        '<button type="button" class="btn mem-grade g1" data-mem-grade="1">Difícil</button>'+
        '<button type="button" class="btn mem-grade g2" data-mem-grade="2">Bom</button>'+
        '<button type="button" class="btn mem-grade g3" data-mem-grade="3">Fácil</button>'+
      '</div>';
    var revealBtn=box.querySelector('[data-mem-reveal]'); if(revealBtn) revealBtn.hidden=true;
  }
  function gradeCurrent(grade){
    var m=loadMem(), ref=queue[qIdx], item=m.items[ref]; if(!item) return;
    schedule(item, grade);
    m.log[today()]=(m.log[today()]||0)+1;
    saveMem(m);
    sessionDone++;
    if(window.BEC_GAME && window.BEC_GAME.record) window.BEC_GAME.record('memorize');
    notifyChange();
    qIdx++;
    renderReviewStep();
  }
  function renderReviewStep(){
    if(!reviewEl) return;
    var box=reviewEl.querySelector('.mem-review-box');
    if(qIdx>=queue.length){
      box.innerHTML='<div class="verse-sheet-head"><b>Revisão concluída</b><button type="button" class="vs-x" data-mem-close aria-label="Fechar">×</button></div>'+
        '<p class="mem-summary">Você revisou '+sessionDone+' versículo'+(sessionDone===1?'':'s')+'. '+
        (sessionDone ? 'Os intervalos foram ajustados — volte quando vencerem.' : 'Nada vencido agora.')+'</p>'+
        '<button type="button" class="btn primary" data-mem-close>Concluir</button>';
      return;
    }
    var m=loadMem(), ref=queue[qIdx], item=m.items[ref];
    if(!item){ qIdx++; renderReviewStep(); return; }
    ensureText(ref, item).then(function(t){
      item.t=t||item.t;
      var prompt = item.t ? exercisePromptHtml(ref, item) : '<p class="mem-text mem-hidden">Não foi possível carregar o texto agora.</p>';
      var showGradeNow = !item.t || (item.reps||0)===0; // texto já visível: nada a "revelar"
      box.innerHTML='<div class="verse-sheet-head"><b>'+esc(ref)+'</b><span class="mem-progress">'+(qIdx+1)+'/'+queue.length+'</span><button type="button" class="vs-x" data-mem-close aria-label="Fechar">×</button></div>'+
        prompt+
        '<div data-mem-answer>'+
          (showGradeNow ?
            '<div class="mem-grade-row">'+
              '<button type="button" class="btn mem-grade g0" data-mem-grade="0">Errei</button>'+
              '<button type="button" class="btn mem-grade g1" data-mem-grade="1">Difícil</button>'+
              '<button type="button" class="btn mem-grade g2" data-mem-grade="2">Bom</button>'+
              '<button type="button" class="btn mem-grade g3" data-mem-grade="3">Fácil</button>'+
            '</div>'
            : '<button type="button" class="btn quiet" data-mem-reveal>Mostrar resposta</button>')+
        '</div>';
    });
  }

  // ---------- painel do Workspace (#decorar) ----------
  function renderMemoryApp(){
    var box=qs('[data-memory-app]'); if(!box) return;
    var m=loadMem();
    var due=dueRefs(m);
    var keys=Object.keys(m.items).sort(function(a,b){ return (m.items[a].due||'').localeCompare(m.items[b].due||''); });
    var html='<div class="memory-head"><div class="pstat"><b>'+due.length+'</b><span>para revisar hoje</span></div><div class="pstat"><b>'+keys.length+'</b><span>no total</span></div></div>';
    if(due.length){
      html+='<button type="button" class="btn primary" data-mem-review-open>Revisar agora ('+due.length+')</button>';
    } else if(keys.length){
      html+='<p class="muted-line">Nenhuma revisão pendente hoje. Volte quando vencer, ou toque em "🧠 Decorar" em outro versículo.</p>';
    } else {
      html+='<p class="muted-line">Toque em "🧠 Decorar" em qualquer versículo (ou nos favoritos) para começar. Os intervalos crescem conforme você acerta, no seu ritmo.</p>';
    }
    if(keys.length){
      html+='<div class="library-rows memory-list">'+keys.map(function(ref){
        var it=m.items[ref];
        var late = it.due<=today();
        var dueTxt = late ? 'hoje' : new Date(it.due+'T00:00:00').toLocaleDateString('pt-BR');
        return '<div class="fav-row"><a href="'+esc(it.url||'#')+'">'+esc(ref)+'</a>'+
          '<span class="muted-line mem-due'+(late?' late':'')+'">próx.: '+esc(dueTxt)+'</span>'+
          '<button type="button" class="btn tiny ghost" data-mem-remove="'+esc(ref)+'">Remover</button></div>';
      }).join('')+'</div>';
    }
    box.innerHTML=html;
    var tabBtn=qs('[data-ws-tab="decorar"]');
    if(tabBtn) tabBtn.textContent = due.length ? 'Decorar ('+due.length+')' : 'Decorar';
    var fabBtn=qs('[data-mem-review-fab]');
    if(fabBtn){ var span=fabBtn.querySelector('span'); if(span) span.textContent = due.length ? 'Revisar ('+due.length+')' : 'Revisar'; }
  }

  document.addEventListener('click', function(e){
    var toggleBtn=e.target.closest && e.target.closest('[data-mem-toggle]');
    if(toggleBtn){
      var ref=toggleBtn.getAttribute('data-mem-toggle')||'';
      var url=toggleBtn.getAttribute('data-mem-url')||'';
      if(!ref) return;
      var on=toggleMemorize(ref, '', url);
      toggleBtn.textContent = on ? '✓ Na fila' : '🧠 Decorar';
      toggleBtn.setAttribute('aria-pressed', on?'true':'false');
      return;
    }
    var rm=e.target.closest && e.target.closest('[data-mem-remove]');
    if(rm){ removeMemorize(rm.getAttribute('data-mem-remove')||''); return; }
    if(e.target.closest && e.target.closest('[data-mem-review-open],[data-mem-review-fab]')) openReview();
  });

  window.BEC_MEMORY = {
    toggle: toggleMemorize,
    remove: removeMemorize,
    isMemorized: isMemorized,
    dueCount: function(){ return dueRefs().length; },
    openReview: openReview
  };

  // ==================================================================
  // Quiz por capítulo (sem curadoria — gerado do texto já na página)
  // ==================================================================
  function eligibleVerses(){
    return qsa('.chapter .ch-verse[data-ref]').map(function(el){
      var ptEl=el.querySelector('.pt');
      if(!ptEl || ptEl.querySelector('.pt-missing')) return null;
      var text=ptEl.textContent.trim();
      var words=text.split(/\s+/).filter(Boolean);
      if(words.length<6) return null;
      var vnum=parseInt((el.id||'').replace(/^v/,''),10);
      if(isNaN(vnum)) return null;
      return {ref:el.getAttribute('data-ref'), text:text, words:words, vnum:vnum};
    }).filter(Boolean);
  }

  function buildFillBlank(verses, rng){
    var pool=shuffle(verses.slice(), rng);
    for(var i=0;i<pool.length;i++){
      var v=pool[i];
      var candidates=[];
      v.words.forEach(function(w, idx){ if(isContentWord(w)) candidates.push({idx:idx, clean:cleanWord(w)}); });
      if(!candidates.length) continue;
      var pick=candidates[Math.floor(rng()*candidates.length)];
      var distractors=[];
      verses.forEach(function(ov){
        if(ov.ref===v.ref) return;
        ov.words.forEach(function(w){
          var c=cleanWord(w);
          if(c.length>=4 && Math.abs(c.length-pick.clean.length)<=2 && c.toLowerCase()!==pick.clean.toLowerCase()) distractors.push(c);
        });
      });
      distractors=uniqueCI(distractors);
      if(distractors.length<3) continue;
      shuffle(distractors, rng);
      var opts=distractors.slice(0,3).concat([pick.clean]);
      shuffle(opts, rng);
      var blanked=v.words.map(function(w, idx){ return idx===pick.idx ? '____' : w; }).join(' ');
      return {type:'fill', prompt:'Complete a palavra que falta:', ref:v.ref, text:blanked, answer:pick.clean, options:opts};
    }
    return null;
  }

  function buildVerseNumber(verses, rng){
    if(verses.length<4) return null;
    var pool=shuffle(verses.slice(), rng);
    for(var i=0;i<pool.length;i++){
      var v=pool[i];
      var others=uniqueCI(verses.filter(function(o){ return o.vnum!==v.vnum; }).map(function(o){ return String(o.vnum); }));
      if(others.length<3) continue;
      shuffle(others, rng);
      var opts=others.slice(0,3).concat([String(v.vnum)]);
      shuffle(opts, rng);
      return {type:'vnum', prompt:'Qual é o número deste versículo?', ref:v.ref, text:v.text, answer:String(v.vnum), options:opts};
    }
    return null;
  }

  function buildOrder(verses, rng){
    var pool=shuffle(verses.slice(), rng);
    for(var i=0;i<pool.length;i++){
      var v=pool[i];
      if(v.words.length<8 || v.words.length>18) continue;
      var w=v.words.slice(), blocks=[];
      while(w.length){ var n=Math.min(w.length, 2+Math.floor(rng()*3)); blocks.push(w.splice(0,n).join(' ')); }
      if(blocks.length<3 || blocks.length>6) continue;
      var texts=blocks.map(function(b){ return b.toLowerCase(); });
      var hasDup=texts.some(function(t, idx){ return texts.indexOf(t)!==idx; });
      if(hasDup) continue;
      var shuffled=blocks.map(function(b, idx){ return {t:b, i:idx}; });
      shuffle(shuffled, rng);
      var same=shuffled.every(function(b, idx){ return b.i===idx; });
      if(same && shuffled.length>1) shuffled.reverse();
      return {type:'order', prompt:'Toque os trechos na ordem correta:', ref:v.ref, blocks:blocks, shuffled:shuffled};
    }
    return null;
  }

  function chapterKey(){
    var el=qs('.chapter[data-chapter-ref]');
    return el ? el.getAttribute('data-chapter-ref') : (document.title||'quiz');
  }
  function buildQuiz(){
    var verses=eligibleVerses();
    if(verses.length<3) return [];
    var rng=mulberry32(hashStr(chapterKey()+today()));
    var builders=shuffle([buildFillBlank, buildVerseNumber, buildOrder, buildFillBlank, buildVerseNumber], rng);
    var qsList=[];
    builders.forEach(function(builder){
      if(qsList.length>=5) return;
      var q=builder(verses, rng);
      if(q) qsList.push(q);
    });
    return qsList;
  }

  function loadQuiz(){ var q=load('quiz',null); if(!q||typeof q!=='object') q={}; q.chapters=q.chapters||{}; q.log=q.log||{}; return q; }
  function saveQuizResult(key, score, total){
    var q=loadQuiz();
    var cur=q.chapters[key]||{best:0, total:total, last:null};
    q.chapters[key]={best:Math.max(cur.best||0, score), total:total, last:new Date().toISOString()};
    q.log[today()]=(q.log[today()]||0)+1;
    save('quiz', q);
    notifyChange();
  }

  var quizEl=null, quizQs=[], quizIdx=0, quizScore=0, quizOrderPicked=[];
  function getQuizModal(){
    if(quizEl) return quizEl;
    quizEl=document.createElement('div'); quizEl.className='verse-sheet quiz-modal'; quizEl.hidden=true;
    quizEl.innerHTML='<div class="verse-sheet-backdrop" data-quiz-close></div><div class="verse-sheet-box quiz-box" role="dialog" aria-modal="true"></div>';
    document.body.appendChild(quizEl);
    quizEl.addEventListener('click', function(e){
      if(e.target.closest && e.target.closest('[data-quiz-close]')){ closeQuiz(); return; }
      var opt=e.target.closest && e.target.closest('[data-quiz-answer]');
      if(opt){ answerQuiz(opt); return; }
      var block=e.target.closest && e.target.closest('[data-quiz-block]');
      if(block){ pickOrderBlock(block); return; }
      var check=e.target.closest && e.target.closest('[data-quiz-order-check]');
      if(check){ checkOrder(); return; }
    });
    return quizEl;
  }
  function closeQuiz(){ if(quizEl) quizEl.hidden=true; document.body.classList.remove('sheet-open'); }
  function openQuiz(){
    quizQs=buildQuiz();
    if(!quizQs.length) return;
    quizIdx=0; quizScore=0;
    var el=getQuizModal(); el.hidden=false; document.body.classList.add('sheet-open');
    renderQuizStep();
  }
  function nextQuizStep(){ quizIdx++; setTimeout(renderQuizStep, 900); }
  function answerQuiz(btn){
    if(btn.disabled) return;
    var q=quizQs[quizIdx];
    var val=btn.getAttribute('data-quiz-answer');
    var ok=val===q.answer;
    qsa('[data-quiz-answer]', quizEl).forEach(function(b){
      b.disabled=true;
      if(b.getAttribute('data-quiz-answer')===q.answer) b.classList.add('correct');
      else if(b===btn) b.classList.add('wrong');
    });
    if(ok) quizScore++;
    nextQuizStep();
  }
  function pickOrderBlock(btn){
    var pos=parseInt(btn.getAttribute('data-quiz-block'),10);
    if(quizOrderPicked.indexOf(pos)>-1) return;
    quizOrderPicked.push(pos);
    btn.disabled=true; btn.classList.add('picked');
    var picked=qs('[data-quiz-order-picked]', quizEl);
    var q=quizQs[quizIdx];
    if(picked) picked.innerHTML=quizOrderPicked.map(function(p){ return '<span class="quiz-block-picked">'+esc(q.shuffled[p].t)+'</span>'; }).join(' ');
    var checkBtn=qs('[data-quiz-order-check]', quizEl);
    if(checkBtn) checkBtn.hidden = quizOrderPicked.length<q.shuffled.length;
  }
  function checkOrder(){
    var q=quizQs[quizIdx];
    var ok=quizOrderPicked.every(function(pos, idx){ return q.shuffled[pos].i===idx; });
    if(ok) quizScore++;
    var picked=qs('[data-quiz-order-picked]', quizEl);
    if(picked) picked.classList.add(ok?'ok':'bad');
    qsa('[data-quiz-block]', quizEl).forEach(function(b){ b.disabled=true; });
    var checkBtn=qs('[data-quiz-order-check]', quizEl); if(checkBtn) checkBtn.hidden=true;
    nextQuizStep();
  }
  function renderQuizStep(){
    if(!quizEl) return;
    var box=quizEl.querySelector('.quiz-box');
    if(quizIdx>=quizQs.length){
      saveQuizResult(chapterKey(), quizScore, quizQs.length);
      if(window.BEC_GAME && window.BEC_GAME.record) window.BEC_GAME.record('quiz');
      box.innerHTML='<div class="verse-sheet-head"><b>Resultado</b><button type="button" class="vs-x" data-quiz-close aria-label="Fechar">×</button></div>'+
        '<p class="mem-summary">Você acertou '+quizScore+' de '+quizQs.length+'.</p>'+
        '<button type="button" class="btn primary" data-quiz-close>Fechar</button>';
      return;
    }
    var q=quizQs[quizIdx];
    var head='<div class="verse-sheet-head"><b>Pergunta '+(quizIdx+1)+'/'+quizQs.length+'</b><button type="button" class="vs-x" data-quiz-close aria-label="Fechar">×</button></div>';
    var body;
    if(q.type==='order'){
      quizOrderPicked=[];
      body='<p class="quiz-prompt">'+esc(q.prompt)+'</p>'+
        '<div class="quiz-order-picked" data-quiz-order-picked></div>'+
        '<div class="quiz-order-pool">'+q.shuffled.map(function(b, pos){ return '<button type="button" class="btn quiet quiz-block" data-quiz-block="'+pos+'">'+esc(b.t)+'</button>'; }).join('')+'</div>'+
        '<button type="button" class="btn primary" data-quiz-order-check hidden>Conferir</button>';
    } else {
      body='<p class="quiz-prompt">'+esc(q.prompt)+'</p><p class="mem-text">'+esc(q.text)+'</p>'+
        '<div class="quiz-opts">'+q.options.map(function(o){ return '<button type="button" class="btn quiet quiz-opt" data-quiz-answer="'+esc(o)+'">'+esc(o)+'</button>'; }).join('')+'</div>';
    }
    box.innerHTML=head+body;
  }

  document.addEventListener('click', function(e){
    if(e.target.closest && e.target.closest('[data-quiz-open]')) openQuiz();
  });

  // ---------- inicialização ----------
  function initChapterQuizButton(){
    var btn=qs('[data-quiz-open]'); if(!btn) return;
    if(eligibleVerses().length<3) btn.hidden=true;
  }

  function wire(){
    renderMemoryApp();
    initChapterQuizButton();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', wire); else wire();
  document.addEventListener('bec:study-sync', renderMemoryApp);
})();
