// Gamificacao: missoes diarias, medalhas, streak e XP.
//
// Desenho para facilitar ajustes por humanos:
//  - O catalogo (missoes/medalhas) vem do banco (tabelas `daily_missions` e
//    `badges`). Se o banco nao estiver disponivel, usa o FALLBACK abaixo, que
//    espelha o seed em docs/supabase-gamification.sql. Para mudar textos,
//    icones ou metas, edite o banco (fonte da verdade) e este fallback.
//  - Todo o estado local fica em localStorage 'bec.game' e nunca lanca erro:
//    o site continua funcionando offline e sem login.
//  - A conta (cliente Supabase, usuario e profile) e exposta por auth.js em
//    window.BEC_ACCOUNT e no evento 'bec:account'. Aqui so lemos isso.
(function(){
  'use strict';

  // ---- Catalogo de reserva (espelha o seed do banco) ----------------------
  var FALLBACK = {
    missions: [
      {key:'ler_capitulo', title:'Leia um capitulo',    description:'Abra e leia ao menos um capitulo hoje.',        icon:'📖', goal:1, metric:'read_chapters', points:10, sort:1},
      {key:'meditar',      title:'Medite no versiculo',  description:'Abra o versiculo para meditar hoje.',           icon:'🕊️', goal:1, metric:'meditate',      points:10, sort:2},
      {key:'anotar',       title:'Faca uma anotacao',    description:'Registre um aprendizado em uma anotacao.',      icon:'✍️', goal:1, metric:'notes',         points:10, sort:3},
      {key:'favoritar',    title:'Guarde um versiculo',  description:'Marque um versiculo como favorito.',            icon:'⭐', goal:1, metric:'favorites',     points:10, sort:4},
      {key:'grifar',       title:'Grife uma passagem',   description:'Destaque uma passagem com o marca-texto.',      icon:'🖍️', goal:1, metric:'highlights',    points:10, sort:5}
    ],
    badges: [
      {key:'primeiro_passo',   title:'Primeiro Passo', description:'Comecou a jornada de estudo.',        icon:'🌱', tier:'bronze', points:10, sort:1},
      {key:'primeira_nota',    title:'Escriba',        description:'Escreveu a primeira anotacao.',       icon:'✍️', tier:'bronze', points:15, sort:2},
      {key:'primeiro_favorito',title:'Tesouro',        description:'Guardou o primeiro favorito.',        icon:'⭐', tier:'bronze', points:15, sort:3},
      {key:'primeiro_grifo',   title:'Iluminador',     description:'Grifou a primeira passagem.',         icon:'🖍️', tier:'bronze', points:15, sort:4},
      {key:'leitor_10',        title:'Leitor',         description:'Leu 10 capitulos.',                   icon:'📖', tier:'bronze', points:20, sort:5},
      {key:'leitor_50',        title:'Estudioso',      description:'Leu 50 capitulos.',                   icon:'📚', tier:'prata',  points:40, sort:6},
      {key:'streak_3',         title:'Constante',      description:'Estudou 3 dias seguidos.',            icon:'🔥', tier:'bronze', points:20, sort:7},
      {key:'streak_7',         title:'Semana Fiel',    description:'Estudou 7 dias seguidos.',            icon:'🔥', tier:'prata',  points:40, sort:8},
      {key:'streak_30',        title:'Devoto',         description:'Estudou 30 dias seguidos.',           icon:'🔥', tier:'ouro',   points:100,sort:9},
      {key:'missoes_7',        title:'Peregrino',      description:'Completou 7 missoes diarias.',        icon:'🎯', tier:'prata',  points:40, sort:10},
      {key:'comunidade',       title:'Companheiro',    description:'Entrou numa sala da comunidade.',     icon:'🤝', tier:'bronze', points:20, sort:11}
    ]
  };

  // ---- Utilitarios --------------------------------------------------------
  function qs(s){return document.querySelector(s);}
  function qsa(s){return Array.prototype.slice.call(document.querySelectorAll(s));}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function today(){return new Date().toISOString().slice(0,10);}
  function daysBetween(a,b){ // b - a em dias inteiros (datas YYYY-MM-DD)
    try{return Math.round((Date.parse(b)-Date.parse(a))/86400000);}catch(e){return 99;}
  }
  function countKeys(k){try{var o=JSON.parse(localStorage.getItem(k)||'{}');return o&&typeof o==='object'?Object.keys(o).length:0;}catch(e){return 0;}}
  function counts(){
    return {
      notes: countKeys('bec.notes'),
      favorites: countKeys('bec.favs'),
      highlights: countKeys('bec.vhl') + countKeys('bec.whl')
    };
  }
  function levelFromXp(xp){return 1 + Math.floor((xp||0)/100);} // 100 XP por nivel

  // ---- Estado local -------------------------------------------------------
  var STATE_KEY='bec.game';
  function loadState(){
    var s=null;
    try{s=JSON.parse(localStorage.getItem(STATE_KEY)||'null');}catch(e){}
    if(!s||typeof s!=='object') s={};
    s.streak=s.streak||0; s.longest=s.longest||0; s.xp=s.xp||0;
    s.missions=s.missions||{}; s.badges=s.badges||{};
    s.missionsDoneTotal=s.missionsDoneTotal||0; s.chaptersReadTotal=s.chaptersReadTotal||0;
    return s;
  }
  function saveState(s){try{localStorage.setItem(STATE_KEY,JSON.stringify(s));}catch(e){}}

  var catalog=FALLBACK; // trocado por dados reais do banco quando disponivel

  // ---- Regra do dia (rollover + streak + missoes por snapshot) ------------
  function rollover(s){
    var t=today();
    if(s.day!==t){
      // streak: ativo hoje conta como um dia de estudo
      if(s.lastActive){
        var d=daysBetween(s.lastActive,t);
        if(d===1) s.streak=(s.streak||0)+1;
        else if(d>1) s.streak=1;
        // d===0 nao deveria acontecer aqui (day!==t)
      }else{
        s.streak=1;
      }
      s.lastActive=t;
      s.longest=Math.max(s.longest||0, s.streak||0);
      s.day=t;
      s.base=counts();      // baseline: so conta atividade NOVA de hoje
      s.missions={};        // missoes reiniciam a cada dia
    }
    if(!s.base) s.base=counts();
    return s;
  }

  function missionByMetric(metric){return catalog.missions.filter(function(m){return m.metric===metric;});}

  function setMissionProgress(s, mission, value){
    var cur=s.missions[mission.key]||{p:0,done:false};
    var p=Math.max(cur.p||0, Math.min(value, mission.goal));
    var justDone=(!cur.done && p>=mission.goal);
    s.missions[mission.key]={p:p, done:cur.done||p>=mission.goal};
    if(justDone){
      s.xp=(s.xp||0)+(mission.points||10);
      s.missionsDoneTotal=(s.missionsDoneTotal||0)+1;
    }
  }

  // Credita missoes de notes/favorites/highlights comparando com o baseline do dia
  function creditFromSnapshot(s){
    var c=counts(), base=s.base||{};
    ['notes','favorites','highlights'].forEach(function(metric){
      var delta=(c[metric]||0)-(base[metric]||0);
      if(delta>0) missionByMetric(metric).forEach(function(m){setMissionProgress(s,m,delta);});
    });
  }

  // ---- Medalhas -----------------------------------------------------------
  function award(s, key){
    if(s.badges[key]) return false;
    var def=catalog.badges.filter(function(b){return b.key===key;})[0];
    s.badges[key]=true;
    s.xp=(s.xp||0)+((def&&def.points)||10);
    return true;
  }
  function evaluateBadges(s){
    var c=counts();
    award(s,'primeiro_passo');
    if(c.notes>=1) award(s,'primeira_nota');
    if(c.favorites>=1) award(s,'primeiro_favorito');
    if(c.highlights>=1) award(s,'primeiro_grifo');
    if((s.chaptersReadTotal||0)>=10) award(s,'leitor_10');
    if((s.chaptersReadTotal||0)>=50) award(s,'leitor_50');
    if((s.streak||0)>=3) award(s,'streak_3');
    if((s.streak||0)>=7) award(s,'streak_7');
    if((s.streak||0)>=30) award(s,'streak_30');
    if((s.missionsDoneTotal||0)>=7) award(s,'missoes_7');
    // 'comunidade' e concedida ao entrar numa sala (fase da comunidade).
  }

  // ---- Sincronizacao best-effort com Supabase -----------------------------
  function account(){return window.BEC_ACCOUNT||null;}
  function sbClient(){var a=account();return a&&a.client?a.client:null;}
  function sbUser(){var a=account();return a&&a.user?a.user:null;}

  async function pullOnce(s){
    var sb=sbClient(), u=sbUser();
    if(!sb||!u) return;
    try{
      var r=await sb.from('user_gamification').select('xp,streak,longest_streak,last_active').eq('user_id',u.id).maybeSingle();
      if(r&&r.data){
        // servidor manda no que for maior (nao perde progresso entre aparelhos)
        s.xp=Math.max(s.xp||0, r.data.xp||0);
        s.streak=Math.max(s.streak||0, r.data.streak||0);
        s.longest=Math.max(s.longest||0, r.data.longest_streak||0);
      }
      var b=await sb.from('user_badges').select('badge_key').eq('user_id',u.id);
      if(b&&b.data) b.data.forEach(function(row){s.badges[row.badge_key]=true;});
    }catch(e){/* offline/desconfigurado: segue local */}
  }

  async function push(s){
    var sb=sbClient(), u=sbUser();
    if(!sb||!u) return;
    try{
      await sb.from('user_gamification').upsert({
        user_id:u.id, xp:s.xp||0, level:levelFromXp(s.xp),
        streak:s.streak||0, longest_streak:s.longest||0,
        last_active:s.lastActive||today(), updated_at:new Date().toISOString()
      },{onConflict:'user_id'});
      var rows=Object.keys(s.missions||{}).map(function(k){
        var m=s.missions[k];
        return {user_id:u.id, mission_key:k, day:s.day||today(), progress:m.p||0, completed:!!m.done, updated_at:new Date().toISOString()};
      });
      if(rows.length) await sb.from('user_mission_progress').upsert(rows,{onConflict:'user_id,mission_key,day'});
      var badges=Object.keys(s.badges||{}).map(function(k){return {user_id:u.id, badge_key:k};});
      if(badges.length) await sb.from('user_badges').upsert(badges,{onConflict:'user_id,badge_key',ignoreDuplicates:true});
    }catch(e){/* ignora falhas de rede */}
  }

  // ---- Catalogo real (quando ha cliente) ----------------------------------
  async function loadCatalog(){
    var sb=sbClient();
    if(!sb) return;
    try{
      var m=await sb.from('daily_missions').select('*').eq('active',true).order('sort');
      var b=await sb.from('badges').select('*').order('sort');
      if(m&&m.data&&m.data.length) catalog.missions=m.data;
      if(b&&b.data&&b.data.length) catalog.badges=b.data;
    }catch(e){/* mantem fallback */}
  }

  // ---- Renderizacao -------------------------------------------------------
  function renderBetaChrome(){
    var acc=account();
    var profile=acc&&acc.profile;
    // Selo da conta (nav): mostra papel/estado quando logado.
    var badge=qs('[data-account-badge]');
    if(badge){
      var label='';
      if(acc&&acc.user){
        if(profile&&profile.platform_role==='admin') label='Admin';
        else if(profile&&profile.platform_role==='moderator') label='Mod';
        else if(!profile||profile.is_beta!==false) label='Beta';
      }
      if(label){badge.textContent=label; badge.className='account-badge role-'+label.toLowerCase(); badge.hidden=false;}
      else{badge.hidden=true;}
    }
    // Banner beta global (plataforma em testes), dispensavel.
    var banner=qs('[data-beta-banner]');
    if(banner){
      var dismissed=false; try{dismissed=localStorage.getItem('bec.betaDismiss')==='1';}catch(e){}
      banner.hidden=dismissed;
    }
  }

  function renderPanel(s){
    var panel=qs('[data-progress-panel]');
    var acc=account(), logged=!!(acc&&acc.user);
    var c=counts();

    // Perfil (existe mesmo sem o painel de progresso)
    var set=function(sel,val){var el=qs(sel); if(el) el.textContent=val;};
    set('[data-profile-name]', (acc&&acc.profile&&acc.profile.name)||(logged?(acc.user.email||'Membro'):'Visitante'));
    set('[data-profile-status]', logged?'Conta ativa · sincronizado':'Visitante (estudo salvo neste navegador)');
    set('[data-profile-streak]', s.streak||0);
    set('[data-profile-notes]', c.notes);
    set('[data-profile-favs]', c.favorites);
    set('[data-profile-highlights]', c.highlights);

    if(!panel) return;
    panel.hidden=false;
    set('[data-progress-streak]', s.streak||0);
    set('[data-progress-level]', levelFromXp(s.xp));
    set('[data-progress-xp]', s.xp||0);
    set('[data-progress-medals]', Object.keys(s.badges||{}).length);
    var note=qs('[data-progress-note]');
    if(note) note.textContent=logged?'Sincronizado com sua conta':'Entre na conta para salvar entre aparelhos';

    var mlist=qs('[data-mission-list]');
    if(mlist){
      mlist.innerHTML=catalog.missions.map(function(m){
        var mp=s.missions[m.key]||{p:0,done:false};
        var pct=Math.min(100, Math.round(100*(mp.p||0)/(m.goal||1)));
        return '<article class="mission'+(mp.done?' done':'')+'">'+
          '<span class="mission-ic">'+esc(m.icon||'📖')+'</span>'+
          '<div class="mission-body"><b>'+esc(m.title)+'</b><span>'+esc(m.description)+'</span>'+
          '<div class="mbar"><i style="width:'+pct+'%"></i></div></div>'+
          '<span class="mission-flag">'+(mp.done?'✓ +'+(m.points||10)+' XP':'')+'</span>'+
        '</article>';
      }).join('');
    }
    var grid=qs('[data-medal-grid]');
    if(grid){
      grid.innerHTML=catalog.badges.map(function(b){
        var got=!!s.badges[b.key];
        return '<div class="medal '+(got?'got tier-'+(b.tier||'bronze'):'locked')+'" title="'+esc(b.title+' — '+b.description)+'">'+
          '<span class="medal-ic">'+esc(b.icon||'🏅')+'</span>'+
          '<b>'+esc(b.title)+'</b>'+
          '<span class="medal-desc">'+esc(got?b.description:'Bloqueada')+'</span>'+
        '</div>';
      }).join('');
    }
  }

  // ---- Ciclo principal ----------------------------------------------------
  var busy=false;
  function refresh(){
    var s=loadState();
    rollover(s);
    creditFromSnapshot(s);
    evaluateBadges(s);
    saveState(s);
    renderBetaChrome();
    renderPanel(s);
    if(!busy){busy=true; Promise.resolve().then(function(){return push(s);}).catch(function(){}).then(function(){busy=false;});}
  }

  // API publica: outros scripts chamam BEC_GAME.record('read_chapters')
  window.BEC_GAME={
    record:function(metric, n){
      n=n||1;
      var s=loadState(); rollover(s);
      if(metric==='read_chapters') s.chaptersReadTotal=(s.chaptersReadTotal||0)+n;
      missionByMetric(metric).forEach(function(m){
        var cur=(s.missions[m.key]&&s.missions[m.key].p)||0;
        setMissionProgress(s,m,cur+n);
      });
      evaluateBadges(s);
      saveState(s);
      renderPanel(s);
      if(!busy){busy=true; Promise.resolve().then(function(){return push(s);}).catch(function(){}).then(function(){busy=false;});}
    },
    refresh:refresh
  };

  // Quando a conta muda (login/logout), puxa do servidor e re-renderiza.
  document.addEventListener('bec:account', function(){
    loadCatalog().then(function(){
      var s=loadState(); rollover(s);
      pullOnce(s).then(function(){ evaluateBadges(s); saveState(s); refresh(); });
    });
  });
  // Sincronizacao de estudo (favoritos/notas) mudou -> recredita missoes.
  document.addEventListener('bec:study-sync', refresh);
  // Aviso beta: fechar.
  document.addEventListener('click', function(e){
    if(e.target.closest && e.target.closest('[data-beta-dismiss]')){
      try{localStorage.setItem('bec.betaDismiss','1');}catch(err){}
      var b=qs('[data-beta-banner]'); if(b) b.hidden=true;
    }
  });

  function drainQueue(){
    var q=window.BEC_ACT||[]; window.BEC_ACT=[];
    q.forEach(function(m){try{window.BEC_GAME.record(m);}catch(e){}});
  }
  function start(){ drainQueue(); loadCatalog().then(refresh); refresh(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})();
