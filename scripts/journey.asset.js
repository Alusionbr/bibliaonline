// A jornada usa o catálogo e o progresso existentes, sem copiar dados de estudo.
(function () {
  'use strict';
  var core = window.BEC && window.BEC.core;
  var pd = window.BEC && window.BEC.planData;
  if (!core || !pd) return;
  var prefix = core.prefix;
  var selected = pd.loadJSON('journeyPlan', '');
  var plans = [];
  var box = document.querySelector('[data-journey-content]');
  var names = {'joao/1':'O Verbo se fez carne','joao/2':'O primeiro sinal',
    'joao/3':'Jesus e Nicodemos','joao/4':'A água da vida'};
  function esc(value) { return core.esc(String(value == null ? '' : value)); }
  function destination(ref) {
    var key = pd.urlChapterKey(ref.url);
    if (key) return prefix + 'ler/' + key + '/';
    // Only accept known verse routes from saved plans, never arbitrary URLs.
    var verse = String(ref.url || '').match(/(?:^|\/)versiculos\/([a-z0-9-]+)\/?$/);
    return verse ? prefix + 'versiculos/' + verse[1] + '/' : null;
  }
  function render() {
    if (!box || !plans.length) return;
    var plan = plans.find(function(p){return p.slug === selected;}) || plans[0];
    selected = plan.slug;
    var done = pd.progressFor(plan.slug).filter(function(n){
      return Number.isInteger(n) && n >= 0 && n < plan.dias.length;
    }).filter(function(n,i,a){return a.indexOf(n) === i;});
    var next = plan.dias.findIndex(function(_,i){return done.indexOf(i) < 0;});
    var previousCount = window.matchMedia('(max-width: 800px)').matches ? 0 : 1;
    var start = Math.max(0, (next < 0 ? plan.dias.length - 1 : next) - previousCount);
    var end = Math.min(plan.dias.length, start + 4);
    var pct = Math.round(done.length / plan.dias.length * 100);
    var rows = plan.dias.slice(start,end).map(function(refs, offset){
      var i = start + offset, complete = done.indexOf(i) >= 0, current = i === next;
      var title = refs.map(function(r){return names[pd.urlChapterKey(r.url)] || r.label;}).join(' · ');
      var links = refs.map(function(ref){
        var url = destination(ref);
        return url ? '<a class="btn '+(current?'primary':'quiet')+'" href="'+esc(url)+'">'+
          (refs.length === 1 ? (complete ? 'Reler ' : 'Ler ') : '')+esc(ref.label)+'</a>' : '<span>'+esc(ref.label)+'</span>';
      }).join('');
      return '<li class="journey-step '+(complete?'is-complete ':'')+(current?'is-current':'')+'">'+
        '<span class="journey-dot" aria-label="'+(complete?'Concluído':current?'Próxima leitura':'Pendente')+'">'+(i+1)+'</span>'+
        '<details '+(current?'open':'')+'><summary><span class="step-day">Dia '+(i+1)+(complete?' · Concluído':'')+'</span>'+
        '<h3>'+esc(title)+'</h3></summary><div class="step-content"><p>Leia com calma. Registre uma descoberta ao terminar.</p>'+
        '<div class="step-links">'+links+'</div></div></details></li>';
    }).join('');
    box.innerHTML = '<div class="journey-grid"><div class="journey-route">'+
      '<label class="journey-picker">Sua jornada<select data-journey-select>'+plans.map(function(p){
        return '<option value="'+esc(p.slug)+'" '+(p.slug===plan.slug?'selected':'')+'>'+esc(p.titulo)+'</option>';
      }).join('')+'</select></label>'+
      '<ol class="journey-steps" start="'+(start+1)+'">'+rows+'</ol>'+
      '<a class="journey-all" href="'+prefix+(plan.tipo==='curado'?'planos/'+esc(plan.slug)+'/':'workspace/#criar-plano')+'">Ver todos os '+plan.dias.length+' dias</a></div>'+
      '<aside class="journey-rhythm"><p class="eyebrow">No seu ritmo</p><div class="journey-count"><b>'+done.length+'</b><span>/ '+plan.dias.length+' dias</span></div>'+
      '<progress max="'+plan.dias.length+'" value="'+done.length+'" aria-label="Progresso do plano">'+pct+'%</progress>'+
      '<h3>'+(next<0?'Uma jornada concluída.':done.length?'Você já começou.':'Seu primeiro passo começa aqui.')+'</h3>'+
      '<p>'+(next<0?'Reserve um momento para rever o que aprendeu. Quando quiser, escolha uma nova leitura.':'A leitura de hoje já faz diferença. Se precisar de uma pausa, seu progresso continua aqui.')+'</p>'+
      '<div class="journey-milestone"><span class="eyebrow">'+(next<0?'Conquista':'Próximo marco')+'</span><strong>'+
      (next<0?'Plano completo':done.length<3?'Completar 3 dias de leitura':'Concluir este plano')+'</strong><small>Aprender também é uma forma de avançar.</small></div>'+
      '<a href="'+prefix+'workspace/#progresso">Ver minhas conquistas</a></aside></div>';
  }
  function loadPlans() {
    if (!box) return;
    pd.allPlans().then(function(items){
      plans = items.filter(function(p){return p && p.slug && Array.isArray(p.dias) && p.dias.length && p.dias.every(Array.isArray);});
      render();
    });
  }
  if (box) box.addEventListener('change',function(e){
    if (!e.target.matches('[data-journey-select]')) return;
    selected = e.target.value;
    try { localStorage.setItem('bec.journeyPlan',JSON.stringify(selected)); } catch (_) {}
    render();
    var picker=box.querySelector('[data-journey-select]'); if(picker) picker.focus();
  });
  document.addEventListener('bec:study-sync', loadPlans);
  window.addEventListener('storage',loadPlans);
  loadPlans();

  var companion = document.querySelector('.reader-companion');
  if (companion && window.matchMedia('(max-width: 800px)').matches) companion.open = false;
  var finish = document.querySelector('[data-complete-chapter]');
  var fraction = document.querySelector('[data-study-frac]');
  var feedback = document.querySelector('[data-reading-feedback]');
  function paintFinish() {
    if (!finish || !fraction) return;
    var pct = fraction.querySelector('[data-sf-pct]');
    var complete = pct && pct.textContent === '100%';
    finish.disabled = complete;
    finish.textContent = complete ? 'Leitura concluída' : 'Concluir leitura';
    feedback.textContent = complete ? 'Mais um passo na sua jornada. Sua leitura foi registrada.' : 'Cada leitura conta. Continue no seu tempo.';
  }
  if (finish && fraction) {
    finish.addEventListener('click',function(){
      var a = fraction.querySelector('[data-sf-start]');
      var b = fraction.querySelector('[data-sf-end]');
      a.selectedIndex = 0; b.selectedIndex = b.options.length - 1;
      fraction.querySelector('[data-sf-save]').click();
      paintFinish();
    });
    new MutationObserver(paintFinish).observe(fraction.querySelector('[data-sf-pct]'),{childList:true,characterData:true,subtree:true});
    paintFinish();
  }
})();
