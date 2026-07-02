// Supabase Auth + sincronizacao privada de estudo.
(function(){
  var TABLE='user_study_state';
  var KEYS={
    notes:'bec.notes',
    vhl:'bec.vhl',
    whl:'bec.whl',
    favs:'bec.favs',
    plans:'bec.studyPlans',
    collections:'bec.collections',
    notebooks:'bec.notebooks'
  };
  var PREF_KEYS=['bec.theme','bec.fontscale','bec.bookorder','bec.pencolor','bec.penmode','bec.lastRead','bec.history','bec.planProgress'];
  // Colunas do user_study_state. Se a migracao v2 (docs/supabase-user-study-state-v2.sql)
  // ainda nao foi aplicada, cai para o conjunto v1 sem derrubar a sincronizacao.
  var COLS_V1='notes,verse_highlights,word_highlights,favorites,preferences,updated_at';
  var COLS_V2='notes,verse_highlights,word_highlights,favorites,preferences,study_plans,collections,notebooks,updated_at';
  var V2_FIELDS=['study_plans','collections','notebooks'];
  var legacyColumns=false;
  var client=null, currentUser=null, currentProfile=null, syncing=false, dirty=false, syncTimer=null;

  // Ponte de conta para os demais scripts (ex.: game.js): cliente, usuario e
  // profile ficam em window.BEC_ACCOUNT e mudancas disparam 'bec:account'.
  function publishAccount(){
    window.BEC_ACCOUNT={client:client, user:currentUser, profile:currentProfile};
    document.dispatchEvent(new CustomEvent('bec:account'));
  }
  async function loadProfile(){
    if(!client || !currentUser){currentProfile=null; return;}
    try{
      var r=await client.from('profiles').select('id,name,is_beta,platform_role,account_type').eq('id',currentUser.id).maybeSingle();
      currentProfile=(r&&r.data)||null;
    }catch(e){currentProfile=null;}
  }
  async function setSession(user){
    var prev=currentUser?currentUser.id:null;
    var next=user?user.id:null;
    currentUser=user||null;
    // Mesmo usuario (ex.: TOKEN_REFRESHED, INITIAL_SESSION repetido): nada a refazer.
    if(next===prev) return;
    await loadProfile();
    updateUi();
    publishAccount();
    if(currentUser) syncNow();
  }

  function qs(s,root){return (root||document).querySelector(s);}
  function qsa(s,root){return Array.prototype.slice.call((root||document).querySelectorAll(s));}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function parse(k, fallback){try{return JSON.parse(localStorage.getItem(k)||'null')||fallback;}catch(e){return fallback;}}
  function shallowMerge(a,b){var out={}, k; a=a||{}; b=b||{}; for(k in a) out[k]=a[k]; for(k in b) out[k]=b[k]; return out;}
  function prefs(){
    var out={};
    PREF_KEYS.forEach(function(k){
      var val=localStorage.getItem(k);
      if(val!==null) out[k.replace(/^bec\./,'')]=val;
    });
    return out;
  }
  function applyPrefs(p){
    if(!p) return false;
    var changed=false;
    Object.keys(p).forEach(function(k){
      try{
        if(localStorage.getItem('bec.'+k)!==p[k]){ localStorage.setItem('bec.'+k, p[k]); changed=true; }
      }catch(e){}
    });
    return changed;
  }
  function localPayload(userId){
    var out={
      user_id:userId,
      notes:parse(KEYS.notes,{}),
      verse_highlights:parse(KEYS.vhl,{}),
      word_highlights:parse(KEYS.whl,{}),
      favorites:parse(KEYS.favs,{}),
      preferences:prefs(),
      updated_at:new Date().toISOString()
    };
    if(!legacyColumns){
      out.study_plans=parse(KEYS.plans,[]);
      out.collections=parse(KEYS.collections,{});
      out.notebooks=parse(KEYS.notebooks,{});
    }
    return out;
  }
  function storeChanged(k,v){
    var next=JSON.stringify(v);
    var prev=null;
    try{prev=localStorage.getItem(k);}catch(e){}
    if(prev===next) return false;
    try{localStorage.setItem(k,next);}catch(e){}
    return true;
  }
  function applyPayload(row){
    if(!row) return;
    // So avisa os outros scripts quando algo realmente mudou, para nao
    // repintar versiculos/favoritos a cada carga de pagina.
    var changed=false;
    changed=storeChanged(KEYS.notes,row.notes||{})||changed;
    changed=storeChanged(KEYS.vhl,row.verse_highlights||{})||changed;
    changed=storeChanged(KEYS.whl,row.word_highlights||{})||changed;
    changed=storeChanged(KEYS.favs,row.favorites||{})||changed;
    // Campos v2 so quando presentes: um payload legado nao pode zerar o local.
    if('study_plans' in row) changed=storeChanged(KEYS.plans,row.study_plans||[])||changed;
    if('collections' in row) changed=storeChanged(KEYS.collections,row.collections||{})||changed;
    if('notebooks' in row) changed=storeChanged(KEYS.notebooks,row.notebooks||{})||changed;
    changed=applyPrefs(row.preferences||{})||changed;
    if(changed) document.dispatchEvent(new CustomEvent('bec:study-sync'));
  }
  function mergePlans(remote, local){
    var seen={}, out=[];
    (local||[]).concat(remote||[]).forEach(function(p){
      var k=p&&p.createdAt;
      if(!k||seen[k]) return;
      seen[k]=1; out.push(p);
    });
    out.sort(function(a,b){return (b.createdAt||'').localeCompare(a.createdAt||'');});
    return out.slice(0,12);
  }
  function mergedPayload(userId,row){
    var local=localPayload(userId);
    if(!row) return local;
    var out={
      user_id:userId,
      notes:shallowMerge(row.notes, local.notes),
      verse_highlights:shallowMerge(row.verse_highlights, local.verse_highlights),
      word_highlights:shallowMerge(row.word_highlights, local.word_highlights),
      favorites:shallowMerge(row.favorites, local.favorites),
      preferences:shallowMerge(row.preferences, local.preferences),
      updated_at:new Date().toISOString()
    };
    if(!legacyColumns){
      out.study_plans=mergePlans(row.study_plans, local.study_plans);
      out.collections=shallowMerge(row.collections, local.collections);
      out.notebooks=shallowMerge(row.notebooks, local.notebooks);
    }
    return out;
  }
  function setStatus(msg,type){
    var el=qs('[data-auth-status]');
    if(!el) return;
    el.textContent=msg||'';
    el.className='auth-status '+(type||'');
  }
  function config(){
    var c=window.BEC_SUPABASE_CONFIG||{};
    if(!c.url || !c.publishableKey || /cole|your|placeholder/i.test(c.publishableKey)) return null;
    return c;
  }
  function ensureClient(){
    if(client) return client;
    var c=config();
    if(!c || !window.supabase || !window.supabase.createClient) return null;
    client=window.supabase.createClient(c.url, c.publishableKey);
    return client;
  }
  function isMissingColumn(e){
    if(!e) return false;
    if(e.code==='42703'||e.code==='PGRST204') return true;
    var msg=(e.message||'');
    return /column/i.test(msg) && V2_FIELDS.some(function(f){return msg.indexOf(f)>-1;});
  }
  async function syncNow(opts){
    var sb=ensureClient();
    if(!sb || !currentUser || syncing) return;
    // Carga de pagina e somente leitura; so grava no banco quando ha
    // alteracao local pendente (dirty), pedido explicito ou primeira linha.
    var push=!!(opts&&opts.push)||dirty;
    syncing=true; dirty=false;
    try{
      setStatus('Sincronizando...', 'muted');
      var res=await sb.from(TABLE).select(legacyColumns?COLS_V1:COLS_V2).eq('user_id', currentUser.id).maybeSingle();
      if(res.error && res.error.code!=='PGRST116') throw res.error;
      var payload=mergedPayload(currentUser.id, res.data);
      if(push || !res.data){
        var up=await sb.from(TABLE).upsert(payload,{onConflict:'user_id'});
        if(up.error) throw up.error;
      }
      applyPayload(payload);
      setStatus('Sincronizado.', 'ok');
    }catch(e){
      if(!legacyColumns && isMissingColumn(e)){
        // Banco ainda sem a migracao v2: refaz uma vez com as colunas v1.
        legacyColumns=true;
        syncing=false;
        if(push) dirty=true;
        return syncNow(opts);
      }
      if(push) dirty=true;
      setStatus((e&&e.message)||'Nao foi possivel sincronizar agora.', 'err');
    }finally{
      syncing=false;
    }
  }
  function markDirty(){
    dirty=true;
    clearTimeout(syncTimer);
    syncTimer=setTimeout(function(){syncNow({push:true});},900);
  }
  window.BEC_SYNC={markDirty:markDirty,syncNow:syncNow,isReady:function(){return !!currentUser;}};

  function buildModal(){
    if(qs('.auth-modal')) return;
    var ov=document.createElement('div');
    ov.className='auth-modal';
    ov.hidden=true;
    ov.innerHTML='<div class="auth-box" role="dialog" aria-modal="true" aria-labelledby="auth-title">'+
      '<button type="button" class="auth-close" data-auth-close aria-label="Fechar">×</button>'+
      '<h2 id="auth-title">Sua conta</h2>'+
      '<div class="auth-user" data-auth-user hidden></div>'+
      '<div class="auth-tabs" role="tablist">'+
        '<button type="button" class="on" data-auth-mode="login">Entrar</button>'+
        '<button type="button" data-auth-mode="signup">Criar conta</button>'+
      '</div>'+
      '<form class="auth-form" data-auth-form>'+
        '<label>Nome <input name="name" autocomplete="name"></label>'+
        '<label>Email <input name="email" type="email" autocomplete="email" required></label>'+
        '<label>Senha <input name="password" type="password" autocomplete="current-password" minlength="6" required></label>'+
        '<button type="submit" class="btn primary" data-auth-submit>Entrar</button>'+
      '</form>'+
      '<div class="auth-actions" data-auth-actions hidden>'+
        '<a class="btn ghost" href="'+rootPath()+'workspace/#perfil">Meu perfil</a>'+
        '<a class="btn ghost" href="'+rootPath()+'workspace/#configuracoes">Configurações</a>'+
        '<button type="button" class="btn ghost" data-auth-sync>Sincronização</button>'+
        '<a class="btn ghost" href="'+rootPath()+'privacidade/">Privacidade</a>'+
        '<button type="button" class="btn ghost" data-auth-signout>Sair</button>'+
      '</div>'+
      '<p class="auth-status" data-auth-status></p>'+
    '</div>';
    document.body.appendChild(ov);
    ov.addEventListener('click',function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-auth-close]'))) closeModal();
    });
  }
  function openModal(){
    buildModal();
    var m=qs('.auth-modal');
    if(m) m.hidden=false;
    updateUi();
    var email=qs('.auth-form input[name=email]');
    if(email && !currentUser) setTimeout(function(){email.focus();},30);
  }
  function closeModal(){var m=qs('.auth-modal'); if(m) m.hidden=true;}
  function rootPath(){
    var m=qs('link[rel="manifest"]');
    var href=m?m.getAttribute('href'):'';
    return href?href.replace(/manifest\.webmanifest.*$/,''):'./';
  }
  function setMode(mode){
    qsa('[data-auth-mode]').forEach(function(b){b.classList.toggle('on',b.getAttribute('data-auth-mode')===mode);});
    var name=qs('.auth-form [name=name]');
    var pass=qs('.auth-form [name=password]');
    var submit=qs('[data-auth-submit]');
    if(name) name.closest('label').hidden=(mode!=='signup');
    if(pass) pass.autocomplete=mode==='signup'?'new-password':'current-password';
    if(submit) submit.textContent=mode==='signup'?'Criar conta':'Entrar';
  }
  function updateUi(){
    var logged=!!currentUser;
    qsa('[data-auth-open]').forEach(function(b){
      b.textContent=logged?(currentUser.email||'Conta'):'Entrar';
      b.classList.toggle('on',logged);
    });
    var form=qs('[data-auth-form]'), actions=qs('[data-auth-actions]'), user=qs('[data-auth-user]');
    if(form) form.hidden=logged;
    if(actions) actions.hidden=!logged;
    if(user){
      user.hidden=!logged;
      var chip='';
      if(logged){
        var role=currentProfile&&currentProfile.platform_role;
        if(role==='admin') chip=' <span class="beta-chip role-admin">Admin</span>';
        else if(role==='moderator') chip=' <span class="beta-chip role-mod">Moderador</span>';
        else if(!currentProfile||currentProfile.is_beta!==false) chip=' <span class="beta-chip">Beta teste</span>';
      }
      user.innerHTML=logged?'Conectado como <b>'+esc(currentUser.email||'usuario')+'</b>'+chip:'';
    }
    if(!config()) setStatus('Configure site/assets/supabase-config.js com a URL e a publishable key para ativar login.', 'err');
    else if(logged) setStatus(dirty?'Alteracoes locais aguardando sincronizacao.':'');
    else setStatus('');
  }
  async function handleSubmit(e){
    e.preventDefault();
    var sb=ensureClient();
    if(!sb){setStatus('Supabase ainda nao configurado.', 'err'); return;}
    var form=e.currentTarget, mode=(qs('[data-auth-mode].on')||{}).getAttribute?qs('[data-auth-mode].on').getAttribute('data-auth-mode'):'login';
    var email=form.email.value.trim(), password=form.password.value, name=form.name.value.trim();
    var btn=qs('[data-auth-submit]');
    if(btn) btn.disabled=true;
    try{
      if(mode==='signup'){
        var su=await sb.auth.signUp({email:email,password:password,options:{data:{name:name},emailRedirectTo:location.href.split('#')[0]}});
        if(su.error) throw su.error;
        setStatus('Conta criada. Se a confirmacao por email estiver ativa, confirme o email antes de entrar.', 'ok');
      }else{
        var si=await sb.auth.signInWithPassword({email:email,password:password});
        if(si.error) throw si.error;
        await setSession(si.data.user);
        closeModal();
      }
    }catch(err){
      setStatus((err&&err.message)||'Falha na autenticacao.', 'err');
    }finally{
      if(btn) btn.disabled=false;
    }
  }
  async function signOut(){
    var sb=ensureClient(); if(!sb) return;
    await sb.auth.signOut();
    currentUser=null; currentProfile=null;
    updateUi();
    publishAccount();
  }
  function wire(){
    buildModal();
    document.addEventListener('click',function(e){
      if(e.target.closest && e.target.closest('[data-auth-open]')) openModal();
      if(e.target.closest && e.target.closest('[data-auth-mode]')) setMode(e.target.closest('[data-auth-mode]').getAttribute('data-auth-mode'));
      if(e.target.closest && e.target.closest('[data-auth-sync]')) syncNow({push:true});
      if(e.target.closest && e.target.closest('[data-auth-signout]')) signOut();
    });
    var f=qs('[data-auth-form]');
    if(f) f.addEventListener('submit',handleSubmit);
    setMode('login');
    var sb=ensureClient();
    if(sb){
      publishAccount();
      // O INITIAL_SESSION ja cobre a carga da pagina (dispensa getUser) e o
      // trabalho sai do callback via setTimeout: consultar o Supabase dentro
      // do callback de auth trava o lock interno do supabase-js (deadlock).
      sb.auth.onAuthStateChange(function(_event,session){
        var user=(session&&session.user)||null;
        setTimeout(function(){ setSession(user); },0);
      });
    }
    updateUi();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',wire); else wire();
})();
