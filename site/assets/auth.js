// Supabase Auth + sincronizacao privada de estudo.
(function(){
  var TABLE='user_study_state';
  var KEYS={
    notes:'bec.notes',
    vhl:'bec.vhl',
    whl:'bec.whl',
    favs:'bec.favs'
  };
  var PREF_KEYS=['bec.theme','bec.fontscale','bec.bookorder','bec.pencolor','bec.penmode'];
  var client=null, currentUser=null, syncing=false, dirty=false, syncTimer=null;

  function qs(s,root){return (root||document).querySelector(s);}
  function qsa(s,root){return Array.prototype.slice.call((root||document).querySelectorAll(s));}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function parse(k, fallback){try{return JSON.parse(localStorage.getItem(k)||'null')||fallback;}catch(e){return fallback;}}
  function store(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
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
    if(!p) return;
    Object.keys(p).forEach(function(k){
      try{localStorage.setItem('bec.'+k, p[k]);}catch(e){}
    });
  }
  function localPayload(userId){
    return {
      user_id:userId,
      notes:parse(KEYS.notes,{}),
      verse_highlights:parse(KEYS.vhl,{}),
      word_highlights:parse(KEYS.whl,{}),
      favorites:parse(KEYS.favs,{}),
      preferences:prefs(),
      updated_at:new Date().toISOString()
    };
  }
  function applyPayload(row){
    if(!row) return;
    store(KEYS.notes,row.notes||{});
    store(KEYS.vhl,row.verse_highlights||{});
    store(KEYS.whl,row.word_highlights||{});
    store(KEYS.favs,row.favorites||{});
    applyPrefs(row.preferences||{});
    document.dispatchEvent(new CustomEvent('bec:study-sync'));
  }
  function mergedPayload(userId,row){
    var local=localPayload(userId);
    if(!row) return local;
    return {
      user_id:userId,
      notes:shallowMerge(row.notes, local.notes),
      verse_highlights:shallowMerge(row.verse_highlights, local.verse_highlights),
      word_highlights:shallowMerge(row.word_highlights, local.word_highlights),
      favorites:shallowMerge(row.favorites, local.favorites),
      preferences:shallowMerge(row.preferences, local.preferences),
      updated_at:new Date().toISOString()
    };
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
  async function syncNow(){
    var sb=ensureClient();
    if(!sb || !currentUser || syncing) return;
    syncing=true; dirty=false;
    try{
      setStatus('Sincronizando...', 'muted');
      var res=await sb.from(TABLE).select('notes,verse_highlights,word_highlights,favorites,preferences,updated_at').eq('user_id', currentUser.id).maybeSingle();
      if(res.error && res.error.code!=='PGRST116') throw res.error;
      var payload=mergedPayload(currentUser.id, res.data);
      var up=await sb.from(TABLE).upsert(payload,{onConflict:'user_id'});
      if(up.error) throw up.error;
      applyPayload(payload);
      setStatus('Sincronizado.', 'ok');
    }catch(e){
      dirty=true;
      setStatus((e&&e.message)||'Nao foi possivel sincronizar agora.', 'err');
    }finally{
      syncing=false;
    }
  }
  function markDirty(){
    dirty=true;
    clearTimeout(syncTimer);
    syncTimer=setTimeout(syncNow,900);
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
      user.innerHTML=logged?'Conectado como <b>'+esc(currentUser.email||'usuario')+'</b>':'';
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
        currentUser=si.data.user;
        updateUi();
        await syncNow();
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
    currentUser=null;
    updateUi();
  }
  function wire(){
    buildModal();
    document.addEventListener('click',function(e){
      if(e.target.closest && e.target.closest('[data-auth-open]')) openModal();
      if(e.target.closest && e.target.closest('[data-auth-mode]')) setMode(e.target.closest('[data-auth-mode]').getAttribute('data-auth-mode'));
      if(e.target.closest && e.target.closest('[data-auth-sync]')) syncNow();
      if(e.target.closest && e.target.closest('[data-auth-signout]')) signOut();
    });
    var f=qs('[data-auth-form]');
    if(f) f.addEventListener('submit',handleSubmit);
    setMode('login');
    var sb=ensureClient();
    if(sb){
      sb.auth.getUser().then(function(r){
        currentUser=r.data&&r.data.user;
        updateUi();
        if(currentUser) syncNow();
      });
      sb.auth.onAuthStateChange(function(_event,session){
        currentUser=session&&session.user;
        updateUi();
        if(currentUser) syncNow();
      });
    }
    updateUi();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',wire); else wire();
})();
