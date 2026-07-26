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
      {key:'ler_capitulo', title:'Leia um capitulo',    description:'Marque um trecho de leitura como lido hoje.',   icon:'📖', goal:1, metric:'read_chapters', points:10, sort:1},
      {key:'meditar',      title:'Medite no versiculo',  description:'Abra o versiculo para meditar hoje.',           icon:'🕊️', goal:1, metric:'meditate',      points:10, sort:2},
      {key:'anotar',       title:'Faca uma anotacao',    description:'Registre um aprendizado em uma anotacao.',      icon:'✍️', goal:1, metric:'notes',         points:10, sort:3},
      {key:'favoritar',    title:'Guarde um versiculo',  description:'Marque um versiculo como favorito.',            icon:'⭐', goal:1, metric:'favorites',     points:10, sort:4}
    ],
    weekly: [
      {key:'semana_leitura',   title:'Ritmo de leitura',       description:'Marque trechos de leitura em 4 dias desta semana.', icon:'📖', goal:4, metric:'read_chapters', points:40, sort:1},
      {key:'semana_anotacoes', title:'Semana de anotacoes',    description:'Faca 3 anotacoes nesta semana.',                    icon:'✍️', goal:3, metric:'notes',         points:40, sort:2},
      {key:'semana_favoritos', title:'Colecionador da semana', description:'Guarde 5 versiculos favoritos nesta semana.',       icon:'⭐', goal:5, metric:'favorites',     points:40, sort:3}
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
      {key:'missoes_7',        title:'Peregrino',      description:'Completou 7 missoes diarias.',        icon:'🎯', tier:'prata',  points:40, sort:10}
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
  // Semana ISO 'YYYY-Www' (segunda a domingo), usada como chave das missoes semanais.
  function weekKey(dt){
    var d=new Date(dt||Date.now());
    d=new Date(Date.UTC(d.getFullYear(),d.getMonth(),d.getDate()));
    var day=d.getUTCDay()||7; d.setUTCDate(d.getUTCDate()+4-day);
    var yearStart=new Date(Date.UTC(d.getUTCFullYear(),0,1));
    var wk=Math.ceil((((d-yearStart)/86400000)+1)/7);
    return d.getUTCFullYear()+'-W'+(wk<10?'0'+wk:wk);
  }
  function countKeys(k){try{var o=JSON.parse(localStorage.getItem(k)||'{}');return o&&typeof o==='object'?Object.keys(o).length:0;}catch(e){return 0;}}
  function counts(){
    return {
      notes: countKeys('bec.notes'),
      favorites: countKeys('bec.favs'),
      highlights: countKeys('bec.vhl') + countKeys('bec.whl')
    };
  }
  var LEVEL_XP=100; // XP por nivel (mantido igual ao servidor: level = 1 + xp/100)
  function levelFromXp(xp){return 1 + Math.floor((xp||0)/LEVEL_XP);}
  function xpIntoLevel(xp){return (xp||0)%LEVEL_XP;}          // XP acumulado dentro do nivel atual
  function xpToNext(xp){return LEVEL_XP - xpIntoLevel(xp);}    // XP que falta para o proximo nivel
  function levelPct(xp){return Math.round(100*xpIntoLevel(xp)/LEVEL_XP);}
  // Nome da faixa por nivel, ecoando a familia de medalhas (Semente..Devoto).
  function tierFromLevel(level){
    if(level>=17) return 'Devoto';
    if(level>=12) return 'Peregrino';
    if(level>=8)  return 'Escriba';
    if(level>=5)  return 'Estudioso';
    if(level>=3)  return 'Leitor';
    return 'Semente';
  }

  // ---- Estado local -------------------------------------------------------
  var STATE_KEY='bec.game';
  function loadState(){
    var s=null;
    try{s=JSON.parse(localStorage.getItem(STATE_KEY)||'null');}catch(e){}
    if(!s||typeof s!=='object') s={};
    s.streak=s.streak||0; s.longest=s.longest||0; s.xp=s.xp||0;
    s.missions=s.missions||{}; s.badges=s.badges||{};
    s.weekly=s.weekly||{};   // progresso das missoes semanais (reinicia por semana ISO)
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
    // Semana ISO: missoes semanais reiniciam a cada semana, com baseline proprio.
    var wk=weekKey();
    if(s.week!==wk){ s.week=wk; s.weekBase=counts(); s.weekly={}; }
    if(!s.weekBase) s.weekBase=counts();
    return s;
  }

  function missionByMetric(metric){return catalog.missions.filter(function(m){return m.metric===metric;});}
  function weeklyByMetric(metric){return (catalog.weekly||[]).filter(function(m){return m.metric===metric;});}

  // Aplica progresso a uma missao num mapa ('missions' diario ou 'weekly').
  // countTotal so vale para as diarias (medalha 'missoes_7' conta missoes diarias).
  function applyMission(s, mapKey, mission, value, countTotal){
    var map=s[mapKey]||(s[mapKey]={});
    var cur=map[mission.key]||{p:0,done:false};
    var p=Math.max(cur.p||0, Math.min(value, mission.goal));
    var justDone=(!cur.done && p>=mission.goal);
    map[mission.key]={p:p, done:cur.done||p>=mission.goal};
    if(justDone){
      s.xp=(s.xp||0)+(mission.points||10);
      if(countTotal) s.missionsDoneTotal=(s.missionsDoneTotal||0)+1;
    }
  }
  function setMissionProgress(s, mission, value){ applyMission(s,'missions',mission,value,true); }
  function setWeeklyProgress(s, mission, value){ applyMission(s,'weekly',mission,value,false); }

  // Credita missoes de contagem (notes/favorites/highlights) comparando com o
  // baseline: do dia para as diarias, da semana para as semanais.
  function creditFromSnapshot(s){
    var c=counts(), base=s.base||{}, wbase=s.weekBase||{};
    ['notes','favorites','highlights'].forEach(function(metric){
      var delta=(c[metric]||0)-(base[metric]||0);
      if(delta>0) missionByMetric(metric).forEach(function(m){setMissionProgress(s,m,delta);});
      var wdelta=(c[metric]||0)-(wbase[metric]||0);
      if(wdelta>0) weeklyByMetric(metric).forEach(function(m){setWeeklyProgress(s,m,wdelta);});
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
  }

  // ---- Sincronizacao best-effort com Supabase -----------------------------
  function account(){return window.BEC_ACCOUNT||null;}
  function sbClient(){var a=account();return a&&a.client?a.client:null;}
  function sbUser(){var a=account();return a&&a.user?a.user:null;}

  // Assinatura do estado sincronizavel: so envia ao banco quando muda de fato.
  function pushSig(s){
    var weekly=Object.keys(s.weekly||{}).map(function(k){var m=s.weekly[k];return k+':'+(m.p||0);}).sort();
    return JSON.stringify([s.xp||0, s.streak||0, s.longest||0, Object.keys(s.badges||{}).sort(), weekly]);
  }
  // Baseline do que o servidor ja tem; enquanto igual a isto, nao ha o que enviar.
  var lastPushSig=null;

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
      // Progresso semanal da semana corrente: servidor mantem o maior valor.
      var wk=weekKey();
      var w=await sb.from('user_weekly_mission_progress').select('mission_key,progress,completed').eq('user_id',u.id).eq('week',wk);
      if(w&&w.data) w.data.forEach(function(row){
        var cur=s.weekly[row.mission_key]||{p:0,done:false};
        s.weekly[row.mission_key]={p:Math.max(cur.p||0,row.progress||0), done:cur.done||!!row.completed};
      });
      // Registra o que o servidor ja possui: push so ocorre se surgir algo novo.
      lastPushSig=pushSig(s);
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
      var wrows=Object.keys(s.weekly||{}).map(function(k){
        var m=s.weekly[k];
        return {user_id:u.id, mission_key:k, week:s.week||weekKey(), progress:m.p||0, completed:!!m.done, updated_at:new Date().toISOString()};
      });
      if(wrows.length) await sb.from('user_weekly_mission_progress').upsert(wrows,{onConflict:'user_id,mission_key,week'});
      var badges=Object.keys(s.badges||{}).map(function(k){return {user_id:u.id, badge_key:k};});
      if(badges.length) await sb.from('user_badges').upsert(badges,{onConflict:'user_id,badge_key',ignoreDuplicates:true});
    }catch(e){/* ignora falhas de rede */}
  }

  // ---- Escrita autoritativa (dual-write) ----------------------------------
  // O XP/missoes/medalhas passam a ser DERIVADOS no servidor a partir de eventos
  // validados (RPC record_event). O motor local segue calculando para a UI
  // instantanea e para visitante/offline; quando logado, emitimos o evento real
  // e adotamos os valores autoritativos que a RPC devolve. Best-effort: qualquer
  // falha de rede cai no caminho local sem quebrar nada.
  async function recordEvent(metric, dedupKey, payload){
    var sb=sbClient(), u=sbUser(); if(!sb||!u) return;
    try{
      var r=await sb.rpc('record_event', {p_metric:metric, p_dedup_key:dedupKey||null, p_payload:payload||{}});
      var d=r&&r.data; if(!d) return;
      var s=loadState();                 // adota o autoritativo sem regredir
      if(typeof d.xp==='number') s.xp=Math.max(s.xp||0, d.xp);
      if(typeof d.streak==='number') s.streak=Math.max(s.streak||0, d.streak);
      if(typeof d.longest_streak==='number') s.longest=Math.max(s.longest||0, d.longest_streak);
      saveState(s); renderPanel(s);
    }catch(e){/* offline/erro: segue local */}
  }
  // Emite um evento por item novo de nota/favorito/grifo (dedup pela chave do
  // item), para o servidor derivar missoes de contagem sem confiar no total.
  var COUNT_SOURCES={notes:['bec.notes'], favorites:['bec.favs'], highlights:['bec.vhl','bec.whl']};
  function emitCountEvents(s){
    if(!sbClient()||!sbUser()) return;
    s.emitted=s.emitted||{};
    Object.keys(COUNT_SOURCES).forEach(function(metric){
      var keys=[]; COUNT_SOURCES[metric].forEach(function(lk){
        try{var o=JSON.parse(localStorage.getItem(lk)||'{}'); if(o&&typeof o==='object') Object.keys(o).forEach(function(k){keys.push(lk+':'+k);});}catch(e){}
      });
      var seen=s.emitted[metric]||{};
      keys.forEach(function(k){ if(!seen[k]){ seen[k]=1; recordEvent(metric, metric+'|'+k, {}); } });
      s.emitted[metric]=seen;
    });
    saveState(s);
  }

  // ---- Catalogo real (quando ha cliente) ----------------------------------
  var catalogLoaded=false;
  async function loadCatalog(){
    if(catalogLoaded) return false;       // catalogo e imutavel na sessao: busca 1x
    var sb=sbClient();
    if(!sb) return false;
    try{
      var m=await sb.from('daily_missions').select('*').eq('active',true).order('sort');
      var b=await sb.from('badges').select('*').order('sort');
      var w=await sb.from('weekly_missions').select('*').eq('active',true).order('sort');
      var changed=false;
      // Grifar por versículo virou uma ferramenta real (folha de ferramentas
      // do leitor), então missões com metric "highlights" voltam a valer.
      if(m&&m.data&&m.data.length){ catalog.missions=m.data; changed=true; }
      if(b&&b.data&&b.data.length){ catalog.badges=b.data; changed=true; }
      if(w&&w.data&&w.data.length){ catalog.weekly=w.data; changed=true; }
      catalogLoaded=true;
      return changed;
    }catch(e){/* mantem fallback: offline-first, o site segue sem conta/rede */}
    return false;
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

  // Pinta uma lista de missoes (diarias ou semanais) com barra de progresso.
  function renderMissions(el, list, progressMap){
    if(!el) return;
    list=list||[]; progressMap=progressMap||{};
    el.innerHTML=list.map(function(m){
      var mp=progressMap[m.key]||{p:0,done:false};
      var pct=Math.min(100, Math.round(100*(mp.p||0)/(m.goal||1)));
      return '<article class="mission'+(mp.done?' done':'')+'">'+
        '<span class="mission-ic">'+esc(m.icon||'📖')+'</span>'+
        '<div class="mission-body"><b>'+esc(m.title)+'</b><span>'+esc(m.description)+'</span>'+
        '<div class="mbar"><i style="width:'+pct+'%"></i></div></div>'+
        '<span class="mission-flag">'+(mp.done?'✓ +'+(m.points||10)+' XP':(mp.p||0)+'/'+m.goal)+'</span>'+
      '</article>';
    }).join('');
  }

  // Resumo compacto de gamificacao (usado na Inicio). Le o mesmo estado local.
  function renderHomeSummary(s){
    var block=qs('[data-home-progress]');
    if(!block) return;
    var set=function(sel,val){qsa(sel).forEach(function(el){el.textContent=val;});};
    var level=levelFromXp(s.xp);
    var missions=catalog.missions||[];
    var done=missions.filter(function(m){var mp=s.missions[m.key]; return mp&&mp.done;}).length;
    set('[data-home-streak]', s.streak||0);
    set('[data-home-level]', level);
    set('[data-home-tier]', tierFromLevel(level));
    set('[data-home-missions]', done+'/'+missions.length);
    var bar=qs('[data-home-xp-bar]'); if(bar) bar.style.width=levelPct(s.xp)+'%';
  }

  function renderPanel(s){
    var panel=qs('[data-progress-panel]');
    var acc=account(), logged=!!(acc&&acc.user);
    var c=counts();

    // Perfil (existe mesmo sem o painel de progresso). Atualiza todos os hooks
    // com o mesmo seletor (ex.: nivel aparece no cartao e na estatistica).
    var set=function(sel,val){qsa(sel).forEach(function(el){el.textContent=val;});};
    set('[data-profile-name]', (acc&&acc.profile&&acc.profile.name)||(logged?(acc.user.email||'Membro'):'Visitante'));
    set('[data-profile-status]', logged?'Conta ativa · sincronizado':'Visitante (estudo salvo neste navegador)');
    set('[data-profile-streak]', s.streak||0);
    set('[data-profile-notes]', c.notes);
    set('[data-profile-favs]', c.favorites);
    set('[data-profile-highlights]', c.highlights);

    renderHomeSummary(s);

    if(!panel) return;
    // Placar zerado não é boas-vindas: para quem nunca leu nada, "Nível 1,
    // 0 capítulos, 0/4 missões" é a primeira impressão da plataforma. O painel
    // só aparece quando existe atividade de verdade — capítulo estudado, nota,
    // grifo, favorito ou sequência iniciada.
    // Só conta o que a pessoa de fato fez com o texto. Sequência, XP e a
    // medalha "primeiro passo" são concedidos por abrir a página — na primeira
    // visita o estado já vem streak:1, xp:10, chaptersReadTotal:0. Usar
    // qualquer um deles como sinal traria o painel vazio de volta.
    var ativo = countKeys('bec.readingRanges') > 0 || c.notes > 0 ||
                c.highlights > 0 || c.favorites > 0 ||
                (s.chaptersReadTotal||0) > 0;
    // o índice do Workspace não pode oferecer um atalho para uma seção que
    // não está na página
    var atalho=qs('.ws-sections a[href="#progresso"]');
    if(atalho) atalho.hidden=!ativo;
    if(!ativo){ panel.hidden=true; return; }
    panel.hidden=false;
    var level=levelFromXp(s.xp);
    set('[data-progress-streak]', s.streak||0);
    set('[data-progress-level]', level);
    set('[data-progress-xp]', s.xp||0);
    set('[data-progress-medals]', Object.keys(s.badges||{}).length);
    var note=qs('[data-progress-note]');
    if(note) note.textContent=logged?'Sincronizado com sua conta':'Entre na conta para salvar entre aparelhos';

    // Cartao de nivel: faixa + barra de XP ate o proximo nivel
    set('[data-progress-tier]', tierFromLevel(level));
    set('[data-progress-xpinto]', xpIntoLevel(s.xp));
    set('[data-progress-xpneed]', LEVEL_XP);
    set('[data-progress-xptonext]', xpToNext(s.xp));
    var xpbar=qs('[data-xp-bar]'); if(xpbar) xpbar.style.width=levelPct(s.xp)+'%';

    renderMissions(qs('[data-mission-list]'), catalog.missions, s.missions);
    renderMissions(qs('[data-weekly-list]'), catalog.weekly, s.weekly);
    // Contadores dos blocos retráteis (missões/medalhas ficam recolhidas).
    var doneOf=function(list,map){list=list||[];map=map||{};return list.filter(function(m){var mp=map[m.key];return mp&&mp.done;}).length;};
    set('[data-mission-count]', doneOf(catalog.missions, s.missions)+'/'+(catalog.missions||[]).length);
    set('[data-weekly-count]', doneOf(catalog.weekly, s.weekly)+'/'+(catalog.weekly||[]).length);
    set('[data-medal-count]', Object.keys(s.badges||{}).length+'/'+(catalog.badges||[]).length);
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
  var busy=false, pushTimer=null;
  // Envia ao banco apenas quando ha progresso novo (assinatura mudou), com
  // debounce, para nao inundar o Supabase a cada evento de pagina/sync.
  function schedulePush(){
    if(!sbClient()||!sbUser()) return;          // sem conta: nada a enviar
    var s=loadState();
    if(lastPushSig!==null && pushSig(s)===lastPushSig) return; // igual ao servidor
    clearTimeout(pushTimer);
    pushTimer=setTimeout(function(){
      if(busy){ schedulePush(); return; }
      var st=loadState(), sig=pushSig(st);
      if(lastPushSig!==null && sig===lastPushSig) return;
      busy=true; lastPushSig=sig;
      Promise.resolve().then(function(){return push(st);})
        .catch(function(){ lastPushSig=null; })  // falhou: permite reenviar depois
        .then(function(){ busy=false; });
    }, 1500);
  }
  // Recalcula e repinta LOCALMENTE (sem tocar no banco). O envio fica a cargo
  // de schedulePush, chamado so em acoes reais do usuario.
  function refresh(){
    var s=loadState();
    rollover(s);
    creditFromSnapshot(s);
    evaluateBadges(s);
    saveState(s);
    emitCountEvents(s);   // dual-write: emite notas/favoritos/grifos novos
    renderBetaChrome();
    renderPanel(s);
  }

  // Chave de deduplicacao por acao real (idempotente no servidor).
  function eventDedup(metric){
    if(metric==='read_chapters'){ try{return localStorage.getItem('bec.game.readMark')||today();}catch(e){return today();} }
    if(metric==='meditate') return 'meditate|'+today();
    return null;
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
      weeklyByMetric(metric).forEach(function(m){
        var cur=(s.weekly[m.key]&&s.weekly[m.key].p)||0;
        setWeeklyProgress(s,m,cur+n);
      });
      evaluateBadges(s);
      saveState(s);
      renderPanel(s);
      schedulePush();
      recordEvent(metric, eventDedup(metric), {});  // dual-write autoritativo
    },
    // Concede uma medalha especifica a partir de um evento externo ao motor.
    grant:function(key){
      var s=loadState(); rollover(s);
      if(award(s,key)){ saveState(s); renderPanel(s); schedulePush(); }
    },
    // Nivel atual (UI de recursos travados por nivel, ex.: criar salas).
    // A trava real fica no servidor (create_group exige nivel 3).
    level:function(){try{return levelFromXp(loadState().xp);}catch(e){return 1;}},
    xpToNext:function(){try{return xpToNext(loadState().xp);}catch(e){return LEVEL_XP;}},
    refresh:refresh
  };

  // Quando a conta muda (login/logout), puxa do servidor e re-renderiza.
  // O push so acontece depois do pull e apenas se houver progresso local novo.
  document.addEventListener('bec:account', function(){
    loadCatalog().then(function(){
      var s=loadState(); rollover(s);
      pullOnce(s).then(function(){ evaluateBadges(s); saveState(s); refresh(); schedulePush(); });
    });
  });
  // Sincronizacao de estudo (favoritos/notas) mudou -> recredita missoes
  // localmente; o envio ao banco fica com schedulePush (so se algo mudou).
  document.addEventListener('bec:study-sync', function(){ refresh(); schedulePush(); });
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
  // Pinta ja com o catalogo local; repinta apenas se o catalogo real chegou.
  function start(){ drainQueue(); refresh(); loadCatalog().then(function(changed){ if(changed) refresh(); }); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})();
