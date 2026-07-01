var BEC_BASE="https://alusionbr.github.io/bibliaonline";
// Ferramentas de estudo (offline): grifar palavra/versículo, anotar, exportar.
// Tudo salvo no localStorage deste navegador. Nada vai para servidor.
(function(){
  function load(k){try{return JSON.parse(localStorage.getItem('bec.'+k)||'{}');}catch(e){return{};}}
  function save(k,v){try{localStorage.setItem('bec.'+k,JSON.stringify(v));}catch(e){} if(k==='notes'||k==='vhl'||k==='whl'||k==='favorites') scheduleCloudSync();}
  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  // referência "Livro c:v" → slug e URL absoluta do versículo (BEC_BASE injetado no build)
  function refToSlug(ref){
    var m=(ref||'').match(/^(.*?)\s+(\d+):(\d+)$/); if(!m) return '';
    var b=m[1].normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
    return b+'-'+m[2]+'-'+m[3];
  }
  function refToUrl(ref){ var s=refToSlug(ref); return s? BEC_BASE+'/versiculos/'+s+'/' : BEC_BASE; }
  function downloadBlob(name, blob){
    var u=URL.createObjectURL(blob); var a=document.createElement('a'); a.href=u; a.download=name;
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(u);
  }

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
    cont.classList.add('study-target');
    cont.setAttribute('tabindex','0');
    var nb=document.createElement('div'); nb.className='note-box'; nb.hidden=true;
    nb.innerHTML='<textarea placeholder="Sua anotação para '+esc(ref)+'..."></textarea>'+
      '<div class="note-actions"><button type="button" data-act="copy-note">⧉ Copiar versículo + nota</button></div>';
    anchor.appendChild(nb);
    cont.dataset.studyReady='1';
    apply(cont, ref);
  }

  function flash(btn, txt){
    var o=btn.textContent;
    if(btn.closest && btn.closest('.study-context')) btn.textContent = txt==='Falhou' ? '!' : '✓';
    else btn.textContent=txt;
    setTimeout(function(){btn.textContent=o;},1400);
  }
  function copyText(str, btn){
    (navigator.clipboard?navigator.clipboard.writeText(str):Promise.reject())
      .then(function(){ if(btn) flash(btn,'Copiado!'); })
      .catch(function(){ try{ var t=document.createElement('textarea'); t.value=str; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove(); if(btn) flash(btn,'Copiado!'); }catch(e){ if(btn) flash(btn,'Falhou'); } });
  }
  function verseText(cont, ref){
    var pt=cont.querySelector('.pt'); var t=pt?pt.textContent.trim():'';
    var note=load('notes')[ref];
    return ref + (t? '\n'+t : '') + (note? '\n\nAnotação: '+note : '');
  }
  function shareText(str, btn){
    if(navigator.share){ navigator.share({title:'Bíblia em Contexto', text:str}).catch(function(){}); }
    else copyText(str, btn);
  }
  // contador de palavras grifadas → cartão de doação a cada N (protótipo, sem backend)
  var DONATE_EVERY=500, DONATE_URL='https://www.buymeacoffee.com/';
  function bumpMark(){
    var n=(parseInt(localStorage.getItem('bec.markCount'),10)||0)+1;
    try{ localStorage.setItem('bec.markCount', n); }catch(e){}
    var milestone=Math.floor(n/DONATE_EVERY);
    var shown=parseInt(localStorage.getItem('bec.donateMilestone'),10)||0;
    if(milestone>shown) showDonate(milestone);
  }
  function showDonate(milestone){
    try{ localStorage.setItem('bec.donateMilestone', milestone); }catch(e){}
    if(document.querySelector('.donate')) return;
    var d=document.createElement('div'); d.className='donate';
    d.innerHTML='<button type="button" class="x" aria-label="Fechar">×</button>'+
      '<a href="'+DONATE_URL+'" target="_blank" rel="noopener">☕ Gostou? Apoie este projeto</a>';
    d.querySelector('.x').onclick=function(){ d.remove(); };
    document.body.appendChild(d);
  }

  // ---------- compartilhar cartão-imagem do versículo (+ link) ----------
  function wrapCanvas(ctx, text, maxW){
    var words=(text||'').split(/\s+/), lines=[], cur='';
    words.forEach(function(w){
      var t=cur?cur+' '+w:w;
      if(ctx.measureText(t).width>maxW && cur){ lines.push(cur); cur=w; } else cur=t;
    });
    if(cur) lines.push(cur);
    return lines;
  }
  function makeVerseCard(ref, pt){
    return new Promise(function(resolve, reject){
      try{
        var W=1080, H=1080, cv=document.createElement('canvas'); cv.width=W; cv.height=H;
        var ctx=cv.getContext && cv.getContext('2d'); if(!ctx){ reject(); return; }
        ctx.fillStyle='#f4eee2'; ctx.fillRect(0,0,W,H);
        ctx.fillStyle='#e7d6ab'; ctx.fillRect(0,0,W,14); ctx.fillRect(0,H-14,W,14);
        ctx.textBaseline='top';
        ctx.fillStyle='#8a6726'; ctx.font='600 54px Georgia, serif'; ctx.fillText(ref, 90, 110);
        ctx.fillStyle='#16120c';
        var size=66, maxW=W-180, lines=wrapCanvas(ctx, pt, maxW);
        ctx.font=size+'px Georgia, serif'; lines=wrapCanvas(ctx, pt, maxW);
        while(lines.length*size*1.35 > H-440 && size>30){ size-=4; ctx.font=size+'px Georgia, serif'; lines=wrapCanvas(ctx, pt, maxW); }
        var y=250, lh=size*1.35;
        lines.forEach(function(ln){ ctx.fillText(ln, 90, y); y+=lh; });
        ctx.fillStyle='#6f6453'; ctx.font='500 36px Georgia, serif'; ctx.fillText('Bíblia em Contexto', 90, H-150);
        ctx.fillStyle='#8a6726'; ctx.font='30px Georgia, serif'; ctx.fillText(BEC_BASE.replace(/^https?:\/\//,''), 90, H-100);
        if(cv.toBlob) cv.toBlob(function(b){ b?resolve(b):reject(); }, 'image/png'); else reject();
      }catch(e){ reject(); }
    });
  }
  function shareVerse(cont, ref, btn){
    var pt=cont.querySelector('.pt'); var t=pt?pt.textContent.trim():'';
    var url=refToUrl(ref), text=ref+(t?'\n'+t:'')+'\n'+url;
    makeVerseCard(ref, t).then(function(blob){
      var file; try{ file=new File([blob],'versiculo.png',{type:'image/png'}); }catch(e){ file=null; }
      if(file && navigator.canShare && navigator.canShare({files:[file]})){
        navigator.share({files:[file], text:ref+'\n'+url, title:'Bíblia em Contexto'}).catch(function(){});
      } else if(navigator.share){
        navigator.share({title:'Bíblia em Contexto', text:text}).catch(function(){});
      } else { copyText(text, btn); downloadBlob('versiculo.png', blob); }
    }).catch(function(){
      if(navigator.share){ navigator.share({title:'Bíblia em Contexto', text:text}).catch(function(){}); }
      else copyText(text, btn);
    });
  }

  // ---------- modal de confirmação (evita apagar por toque acidental) ----------
  function confirmModal(msg, onYes){
    var ov=document.createElement('div'); ov.className='bec-modal';
    ov.innerHTML='<div class="bec-modal-box"><p>'+esc(msg)+'</p>'+
      '<div class="bec-modal-actions"><button type="button" class="btn ghost" data-no>Cancelar</button>'+
      '<button type="button" class="btn danger" data-yes>Apagar tudo</button></div></div>';
    ov.addEventListener('click', function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-no]'))) ov.remove();
      else if(e.target.closest && e.target.closest('[data-yes]')){ ov.remove(); onYes(); }
    });
    document.body.appendChild(ov);
  }

  // ---------- seta de ferramentas ocultas (salvar/compartilhar, anotações, apagar) ----------
  // ---------- conta e sincronizacao Supabase ----------
  var cloudSession=null, cloudTimer=null, cloudBusy=false;
  var SESSION_KEY='bec.supabase.session';
  function cfg(){ return window.BEC_SUPABASE_CONFIG || null; }
  function cloudReady(){ var c=cfg(); return !!(c && c.url && c.publishableKey && window.fetch); }
  function readSession(){ try{return JSON.parse(localStorage.getItem(SESSION_KEY)||'null');}catch(e){return null;} }
  function writeSession(s){ cloudSession=s||null; try{ if(s) localStorage.setItem(SESSION_KEY, JSON.stringify(s)); else localStorage.removeItem(SESSION_KEY); }catch(e){} updateAccountButton(); }
  function authHeaders(token){
    var c=cfg();
    return {'apikey':c.publishableKey,'Authorization':'Bearer '+(token||c.publishableKey),'Content-Type':'application/json'};
  }
  function cloudFetch(path, opts){
    opts=opts||{}; opts.headers=Object.assign(authHeaders(opts.token), opts.headers||{});
    delete opts.token;
    return fetch(cfg().url+path, opts).then(function(r){
      if(!r.ok) return r.text().then(function(t){ throw new Error(t||r.statusText); });
      if(r.status===204) return null;
      return r.json();
    });
  }
  function ensureFreshSession(){
    var s=cloudSession||readSession();
    if(!s || !s.access_token) return Promise.resolve(null);
    cloudSession=s;
    var now=Math.floor(Date.now()/1000);
    if(s.expires_at && s.expires_at-now>60) return Promise.resolve(s);
    if(!s.refresh_token) return Promise.resolve(s);
    return cloudFetch('/auth/v1/token?grant_type=refresh_token', {
      method:'POST',
      body:JSON.stringify({refresh_token:s.refresh_token})
    }).then(function(n){
      var ns={access_token:n.access_token,refresh_token:n.refresh_token||s.refresh_token,expires_at:n.expires_at,user:n.user||s.user};
      writeSession(ns); return ns;
    }).catch(function(){ writeSession(null); return null; });
  }
  function loadPrefs(){ try{return JSON.parse(localStorage.getItem('bec.preferences')||'{}');}catch(e){return{};} }
  function savePrefs(p){ try{localStorage.setItem('bec.preferences',JSON.stringify(p||{}));}catch(e){} scheduleCloudSync(); }
  function accountPrefs(){
    var p=loadPrefs();
    p.profile=p.profile||{};
    p.customStudies=Array.isArray(p.customStudies)?p.customStudies:[];
    p.groups=Array.isArray(p.groups)?p.groups:[];
    return p;
  }
  function statePayload(){
    var prefs=loadPrefs();
    prefs.theme=localStorage.getItem('bec.theme')||'';
    prefs.fontscale=localStorage.getItem('bec.fontscale')||'';
    prefs.context=localStorage.getItem('bec.context')||'';
    prefs.bookorder=localStorage.getItem('bec.bookorder')||'';
    prefs.lastRead=(function(){try{return JSON.parse(localStorage.getItem('bec.lastRead')||'null');}catch(e){return null;}})();
    return {
      user_id:cloudSession && cloudSession.user && cloudSession.user.id,
      notes:load('notes'),
      verse_highlights:load('vhl'),
      word_highlights:load('whl'),
      favorites:load('favorites'),
      preferences:prefs,
      updated_at:new Date().toISOString()
    };
  }
  function mergeObj(a,b){ var out={}, k; a=a||{}; b=b||{}; for(k in a) out[k]=a[k]; for(k in b) out[k]=b[k]; return out; }
  function applyRemote(row){
    if(!row) return false;
    function put(k,v){ try{localStorage.setItem('bec.'+k,JSON.stringify(v||{}));}catch(e){} }
    put('notes', mergeObj(row.notes, load('notes')));
    put('vhl', mergeObj(row.verse_highlights, load('vhl')));
    put('whl', mergeObj(row.word_highlights, load('whl')));
    put('favorites', mergeObj(row.favorites, load('favorites')));
    try{localStorage.setItem('bec.preferences',JSON.stringify(mergeObj(row.preferences, loadPrefs())));}catch(e){}
    return true;
  }
  function pullCloud(){
    return ensureFreshSession().then(function(s){
      if(!s) return null;
      var id=encodeURIComponent(s.user.id);
      return cloudFetch('/rest/v1/user_study_state?select=notes,verse_highlights,word_highlights,favorites,preferences&user_id=eq.'+id+'&limit=1', {token:s.access_token})
        .then(function(rows){ return rows && rows[0] ? rows[0] : null; });
    });
  }
  function pushCloud(){
    return ensureFreshSession().then(function(s){
      if(!s || !cloudSession.user) return null;
      return cloudFetch('/rest/v1/user_study_state?on_conflict=user_id', {
        method:'POST',
        token:s.access_token,
        headers:{'Prefer':'resolution=merge-duplicates,return=minimal'},
        body:JSON.stringify([statePayload()])
      });
    });
  }
  function scheduleCloudSync(){
    if(!cloudReady() || !cloudSession || cloudBusy) return;
    clearTimeout(cloudTimer);
    cloudTimer=setTimeout(function(){
      cloudBusy=true;
      pushCloud().catch(function(){}).then(function(){ cloudBusy=false; updateAccountButton(); });
    }, 700);
  }
  function updateAccountButton(){
    var b=document.querySelector('[data-account]');
    if(!b) return;
    var s=cloudSession||readSession();
    b.textContent=s && s.user && s.user.email ? 'Conta' : 'Entrar';
    b.title=s && s.user && s.user.email ? s.user.email : 'Entrar ou criar conta';
  }
  function normalizeAuth(res){
    if(!res) return null;
    if(res.session) return {
      access_token:res.session.access_token,
      refresh_token:res.session.refresh_token,
      expires_at:res.session.expires_at,
      user:res.user || res.session.user
    };
    return {
      access_token:res.access_token,
      refresh_token:res.refresh_token,
      expires_at:res.expires_at,
      user:res.user
    };
  }
  function showAccount(msg){
    var s=cloudSession||readSession(), logged=!!(s&&s.user);
    var ov=document.createElement('div'); ov.className='bec-modal';
    ov.innerHTML='<div class="bec-modal-box auth-box">'+
      '<p><b>'+(logged?'Sua conta':'Entrar ou criar conta')+'</b></p>'+
      (msg?'<p class="empty">'+esc(msg)+'</p>':'')+
      (logged?'<p>'+esc(s.user.email||'')+'</p><div class="bec-modal-actions"><button type="button" class="btn ghost" data-close>Fechar</button><button type="button" class="btn danger" data-logout>Sair</button></div>':
      '<p class="auth-help">Se ainda não tem conta, digite seu email e uma senha e toque em Criar conta.</p>'+
      '<label>Email<br><input type="email" data-email autocomplete="email"></label><br>'+
      '<label>Senha<br><input type="password" data-pass autocomplete="current-password"></label>'+
      '<div class="bec-modal-actions"><button type="button" class="btn ghost" data-close>Cancelar</button><button type="button" class="btn ghost" data-login>Entrar</button><button type="button" class="btn primary" data-signup>Criar conta</button></div>')+
      '</div>';
    ov.addEventListener('click', function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-close]'))) ov.remove();
      if(e.target.closest && e.target.closest('[data-logout]')){ cloudFetch('/auth/v1/logout',{method:'POST',token:s.access_token}).catch(function(){}); writeSession(null); ov.remove(); }
      if(e.target.closest && (e.target.closest('[data-login]')||e.target.closest('[data-signup]'))){
        e.preventDefault();
        var email=ov.querySelector('[data-email]').value.trim(), pass=ov.querySelector('[data-pass]').value;
        var signup=!!e.target.closest('[data-signup]');
        if(!email || pass.length<8){ ov.remove(); showAccount('Informe email e senha com pelo menos 8 caracteres.'); return; }
        var clicked=e.target.closest('[data-login]')||e.target.closest('[data-signup]');
        clicked.disabled=true; clicked.textContent=signup?'Criando...':'Entrando...';
        var path=signup?'/auth/v1/signup':'/auth/v1/token?grant_type=password';
        cloudFetch(path,{method:'POST',body:JSON.stringify({email:email,password:pass})}).then(function(res){
          var auth=normalizeAuth(res);
          if(signup && (!auth || !auth.access_token)) return cloudFetch('/auth/v1/token?grant_type=password',{method:'POST',body:JSON.stringify({email:email,password:pass})}).then(normalizeAuth);
          return auth;
        }).then(function(res){
          if(signup && res && res.user && !res.access_token){
            ov.remove();
            showAccount('Conta criada. Confira seu email para confirmar a conta e depois entre.', 'login', {email:email});
            return false;
          }
          if(!res || !res.access_token || !res.user) throw new Error('auth');
          writeSession({access_token:res.access_token,refresh_token:res.refresh_token,expires_at:res.expires_at,user:res.user});
          return pullCloud().then(function(row){ applyRemote(row); return pushCloud(); }).catch(function(){ return null; }).then(function(){ return true; });
        }).then(function(ok){ if(ok){ ov.remove(); location.reload(); } }).catch(function(err){ ov.remove(); showAccount(signup?'Nao foi possivel criar a conta. Tente outro email ou confira a senha.':'Nao foi possivel entrar. Confira email e senha.'); });
      }
    });
    document.body.appendChild(ov);
    var emailInput=ov.querySelector('[data-email]'); if(emailInput) emailInput.focus();
  }
  function escAttr(s){ return esc(s).replace(/"/g,'&quot;'); }
  function prefId(prefix){ return prefix+'-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7); }
  function accountItemHtml(kind, item){
    var meta=[];
    if(item.pace) meta.push(item.pace);
    if(item.visibility) meta.push(item.visibility);
    if(item.topic) meta.push(item.topic);
    return '<div class="account-item">'+
      '<div><b>'+esc(item.title||item.name||'Sem titulo')+'</b>'+
      (meta.length?'<span>'+esc(meta.join(' · '))+'</span>':'')+
      (item.focus?'<p>'+esc(item.focus)+'</p>':'')+
      (item.refs?'<p>'+esc(item.refs)+'</p>':'')+
      (item.description?'<p>'+esc(item.description)+'</p>':'')+
      '</div><button type="button" class="btn ghost mini" data-del-'+kind+'="'+escAttr(item.id||'')+'">Remover</button></div>';
  }
  function accountPanelHtml(s, msg){
    var p=accountPrefs(), profile=p.profile||{};
    var studies=p.customStudies||[], groups=p.groups||[];
    return '<div class="bec-modal-box auth-box account-box">'+
      '<div class="account-head"><div><p><b>Sua conta</b></p><span>'+esc(s.user.email||'')+'</span></div><button type="button" class="btn ghost mini" data-close>Fechar</button></div>'+
      (msg?'<p class="empty">'+esc(msg)+'</p>':'')+
      '<section class="account-section"><h3>Perfil</h3>'+
      '<label>Nome<br><input type="text" data-profile-name autocomplete="name" value="'+escAttr(profile.name||'')+'"></label>'+
      '<label>Sobre voce<br><textarea data-profile-bio rows="3">'+esc(profile.bio||'')+'</textarea></label>'+
      '<div class="bec-modal-actions"><button type="button" class="btn primary" data-save-profile>Salvar perfil</button></div></section>'+
      '<section class="account-section"><h3>Estudos personalizados</h3>'+
      '<div class="account-list">'+(studies.length?studies.map(function(x){return accountItemHtml('study',x);}).join(''):'<p class="empty small">Nenhum estudo criado.</p>')+'</div>'+
      '<label>Titulo do estudo<br><input type="text" data-study-title value=""></label>'+
      '<label>Objetivo<br><input type="text" data-study-focus value=""></label>'+
      '<div class="account-grid"><label>Ritmo<br><select data-study-pace><option>Diario</option><option>Semanal</option><option>Livre</option></select></label>'+
      '<label>Passagens<br><input type="text" data-study-refs value=""></label></div>'+
      '<div class="bec-modal-actions"><button type="button" class="btn primary" data-add-study>Criar estudo</button></div></section>'+
      '<section class="account-section"><h3>Grupos</h3>'+
      '<div class="account-list">'+(groups.length?groups.map(function(x){return accountItemHtml('group',x);}).join(''):'<p class="empty small">Nenhum grupo criado.</p>')+'</div>'+
      '<label>Nome do grupo<br><input type="text" data-group-name value=""></label>'+
      '<label>Descricao<br><input type="text" data-group-description value=""></label>'+
      '<div class="account-grid"><label>Tema<br><input type="text" data-group-topic value=""></label>'+
      '<label>Privacidade<br><select data-group-visibility><option>Privado</option><option>Convite</option><option>Publico</option></select></label></div>'+
      '<div class="bec-modal-actions"><button type="button" class="btn primary" data-add-group>Criar grupo</button></div></section>'+
      '<div class="bec-modal-actions account-bottom"><button type="button" class="btn danger" data-logout>Sair</button></div>'+
      '</div>';
  }
  function persistAccountPrefs(p, ov, msg){
    savePrefs(p);
    pushCloud().catch(function(){}).then(function(){ ov.remove(); showAccount(msg); });
  }
  function showAccount(msg, mode, vals){
    var s=cloudSession||readSession(), logged=!!(s&&s.user);
    mode=mode||'signup'; vals=vals||{};
    var signupMode=mode!=='login';
    var ov=document.createElement('div'); ov.className='bec-modal';
    if(logged) ov.innerHTML=accountPanelHtml(s, msg);
    else ov.innerHTML='<div class="bec-modal-box auth-box">'+
      '<p><b>'+(logged?'Sua conta':(signupMode?'Criar conta':'Entrar na conta'))+'</b></p>'+
      (msg?'<p class="empty">'+esc(msg)+'</p>':'')+
      '<p class="auth-help">'+(signupMode?'Digite seu email e crie uma senha com pelo menos 8 caracteres.':'Entre com o email e a senha que voce cadastrou.')+'</p>'+
      '<label>Email<br><input type="email" data-email autocomplete="email" value="'+esc(vals.email||'')+'"></label><br>'+
      '<label>Senha<br><input type="password" data-pass autocomplete="'+(signupMode?'new-password':'current-password')+'" value="'+esc(vals.pass||'')+'"></label>'+
      '<div class="bec-modal-actions"><button type="button" class="btn ghost" data-close>Cancelar</button><button type="button" class="btn ghost" data-switch="'+(signupMode?'login':'signup')+'">'+(signupMode?'Ja tenho conta':'Criar conta')+'</button><button type="button" class="btn primary" data-auth="'+(signupMode?'signup':'login')+'">'+(signupMode?'Criar conta':'Entrar')+'</button></div>'+
      '</div>';
    ov.addEventListener('click', function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-close]'))) ov.remove();
      if(e.target.closest && e.target.closest('[data-logout]')){ cloudFetch('/auth/v1/logout',{method:'POST',token:s.access_token}).catch(function(){}); writeSession(null); ov.remove(); }
      if(logged && e.target.closest){
        if(e.target.closest('[data-save-profile]')){
          e.preventDefault();
          var p=accountPrefs();
          p.profile={name:(ov.querySelector('[data-profile-name]').value||'').trim(), bio:(ov.querySelector('[data-profile-bio]').value||'').trim()};
          persistAccountPrefs(p, ov, 'Perfil salvo.');
          return;
        }
        if(e.target.closest('[data-add-study]')){
          e.preventDefault();
          var title=(ov.querySelector('[data-study-title]').value||'').trim();
          if(!title){ ov.remove(); showAccount('Informe o titulo do estudo.'); return; }
          var ps=accountPrefs();
          ps.customStudies.push({id:prefId('study'), title:title, focus:(ov.querySelector('[data-study-focus]').value||'').trim(), pace:ov.querySelector('[data-study-pace]').value, refs:(ov.querySelector('[data-study-refs]').value||'').trim(), createdAt:new Date().toISOString()});
          persistAccountPrefs(ps, ov, 'Estudo criado.');
          return;
        }
        if(e.target.closest('[data-add-group]')){
          e.preventDefault();
          var name=(ov.querySelector('[data-group-name]').value||'').trim();
          if(!name){ ov.remove(); showAccount('Informe o nome do grupo.'); return; }
          var pg=accountPrefs();
          pg.groups.push({id:prefId('group'), name:name, description:(ov.querySelector('[data-group-description]').value||'').trim(), topic:(ov.querySelector('[data-group-topic]').value||'').trim(), visibility:ov.querySelector('[data-group-visibility]').value, createdAt:new Date().toISOString()});
          persistAccountPrefs(pg, ov, 'Grupo criado.');
          return;
        }
        var ds=e.target.closest('[data-del-study]');
        if(ds){
          e.preventDefault();
          var pds=accountPrefs(), id=ds.getAttribute('data-del-study');
          pds.customStudies=pds.customStudies.filter(function(x){return x.id!==id;});
          persistAccountPrefs(pds, ov, 'Estudo removido.');
          return;
        }
        var dg=e.target.closest('[data-del-group]');
        if(dg){
          e.preventDefault();
          var pdg=accountPrefs(), gid=dg.getAttribute('data-del-group');
          pdg.groups=pdg.groups.filter(function(x){return x.id!==gid;});
          persistAccountPrefs(pdg, ov, 'Grupo removido.');
          return;
        }
      }
      var sw=e.target.closest && e.target.closest('[data-switch]');
      if(sw){
        e.preventDefault();
        var curEmail=ov.querySelector('[data-email]').value.trim(), curPass=ov.querySelector('[data-pass]').value;
        ov.remove(); showAccount('', sw.getAttribute('data-switch'), {email:curEmail, pass:curPass});
        return;
      }
      var authBtn=e.target.closest && e.target.closest('[data-auth]');
      if(authBtn){
        e.preventDefault();
        var email=ov.querySelector('[data-email]').value.trim(), pass=ov.querySelector('[data-pass]').value;
        var signup=authBtn.getAttribute('data-auth')==='signup';
        if(!email || pass.length<8){ ov.remove(); showAccount('Informe email e senha com pelo menos 8 caracteres.', signup?'signup':'login', {email:email, pass:pass}); return; }
        authBtn.disabled=true; authBtn.textContent=signup?'Criando...':'Entrando...';
        var path=signup?'/auth/v1/signup':'/auth/v1/token?grant_type=password';
        cloudFetch(path,{method:'POST',body:JSON.stringify({email:email,password:pass})}).then(function(res){
          var auth=normalizeAuth(res);
          if(signup && (!auth || !auth.access_token)) return cloudFetch('/auth/v1/token?grant_type=password',{method:'POST',body:JSON.stringify({email:email,password:pass})}).then(normalizeAuth);
          return auth;
        }).then(function(res){
          if(signup && res && res.user && !res.access_token){
            ov.remove();
            showAccount('Conta criada. Confira seu email para confirmar a conta e depois entre.', 'login', {email:email});
            return false;
          }
          if(!res || !res.access_token || !res.user) throw new Error('auth');
          writeSession({access_token:res.access_token,refresh_token:res.refresh_token,expires_at:res.expires_at,user:res.user});
          return pullCloud().then(function(row){ applyRemote(row); return pushCloud(); }).catch(function(){ return null; }).then(function(){ return true; });
        }).then(function(ok){ if(ok){ ov.remove(); location.reload(); } }).catch(function(){ ov.remove(); showAccount(signup?'Nao foi possivel criar a conta. Tente outro email ou confira a senha.':'Nao foi possivel entrar. Confira email e senha.', signup?'signup':'login', {email:email}); });
      }
    });
    document.body.appendChild(ov);
    var emailInput=ov.querySelector('[data-email]'); if(emailInput) emailInput.focus();
  }
  function makeAccountButton(){
    if(!cloudReady() || document.querySelector('[data-account]')) return;
    var tools=document.querySelector('.reader-tools') || document.body;
    var b=document.createElement('button'); b.type='button'; b.className='rt'; b.setAttribute('data-account',''); b.title='Entrar ou criar conta'; b.textContent='Entrar';
    b.onclick=function(){ showAccount(); };
    tools.appendChild(b);
    ensureFreshSession().then(function(s){ if(s){ writeSession(s); pullCloud().then(function(row){ if(applyRemote(row)) scheduleCloudSync(); }); } else updateAccountButton(); });
  }
  function clearAll(){ ['notes','vhl','whl','favorites'].forEach(function(k){ localStorage.removeItem('bec.'+k); }); render(); scheduleCloudSync(); }
  function studyText(){ var n=load('notes'),v=load('vhl'),w=load('whl'),f=load('favorites'); return exportText(allRefs(n,v,w,f),n,v,w,f); }
  function makeToolsMenu(){
    if(document.querySelector('.tools-fab')) return;
    var fab=document.createElement('button'); fab.type='button'; fab.className='tools-fab';
    fab.setAttribute('aria-expanded','false'); fab.title='Ferramentas de estudo'; fab.textContent='↥';
    var panel=document.createElement('div'); panel.className='tools-panel'; panel.hidden=true;
    panel.innerHTML='<button type="button" data-t="share">📝 Salvar nas Notas / Compartilhar</button>'+
      '<button type="button" data-t="txt">📄 Baixar .txt</button>'+
      '<a href="'+BEC_BASE+'/anotacoes/" data-t="notes">🗒 Minhas anotações</a>'+
      '<button type="button" data-t="clear">🗑 Apagar tudo</button>';
    fab.onclick=function(){ var open=panel.hidden; panel.hidden=!open; fab.setAttribute('aria-expanded', open?'true':'false'); fab.textContent=open?'✕':'↥'; };
    panel.addEventListener('click', function(e){
      var b=e.target.closest && e.target.closest('[data-t]'); if(!b) return;
      var t=b.getAttribute('data-t');
      if(t==='share') shareText(studyText(), b);                       // iOS: folha de compartilhamento → Notas
      else if(t==='txt') download('meu-estudo.txt', studyText(), 'text/plain');
      else if(t==='clear') confirmModal('Apagar TODAS as marcações e anotações deste navegador? Esta ação não pode ser desfeita.', clearAll);
    });
    document.body.appendChild(fab); document.body.appendChild(panel);
  }

  var activeStudy=null;
  function getStudyBar(){
    var bar=document.querySelector('.study-context');
    if(bar) return bar;
    bar=document.createElement('div'); bar.className='study-context'; bar.hidden=true;
    bar.setAttribute('aria-label','Ferramentas do versículo selecionado');
    bar.innerHTML='<button type="button" data-act="vhl" aria-label="Grifar versículo" title="Grifar versículo">🖍</button>'+
      '<button type="button" data-act="note" aria-label="Anotar" title="Anotar">🗒</button>'+
      '<button type="button" data-act="copy" aria-label="Copiar versículo" title="Copiar versículo">⧉</button>'+
      '<button type="button" data-act="share" aria-label="Compartilhar" title="Compartilhar">↗</button>';
    bar.innerHTML='<button type="button" data-act="fav" aria-label="Favoritar" title="Favoritar">★</button>'+bar.innerHTML;
    document.body.appendChild(bar);
    return bar;
  }
  function refreshStudyBar(){
    var bar=getStudyBar();
    if(!activeStudy){ bar.hidden=true; return; }
    var ref=activeStudy.getAttribute('data-ref'), vhl=load('vhl');
    bar.hidden=false;
    bar.setAttribute('data-ref', ref||'');
    var h=bar.querySelector('[data-act="vhl"]');
    if(h) h.classList.toggle('on', !!vhl[ref]);
    var f=bar.querySelector('[data-act="fav"]');
    if(f) f.classList.toggle('on', !!load('favorites')[ref]);
    var n=bar.querySelector('[data-act="note"]');
    if(n){
      var noteIsOpen=!!(activeStudy.querySelector('.note-box') && !activeStudy.querySelector('.note-box').hidden);
      n.classList.toggle('on', noteIsOpen);
      n.setAttribute('aria-expanded', noteIsOpen?'true':'false');
    }
  }
  function findStudyByRef(ref){
    if(!ref) return null;
    var items=document.querySelectorAll('.verse-cont[data-ref], .ch-verse[data-ref]');
    for(var i=0;i<items.length;i++){ if(items[i].getAttribute('data-ref')===ref) return items[i]; }
    return null;
  }
  function activateStudy(cont){
    if(!cont || !cont.getAttribute('data-ref')) return;
    if(activeStudy && activeStudy!==cont) activeStudy.classList.remove('study-active');
    activeStudy=cont;
    activeStudy.classList.add('study-active');
    refreshStudyBar();
  }
  function closeStudyBar(){
    if(activeStudy) activeStudy.classList.remove('study-active');
    activeStudy=null;
    refreshStudyBar();
  }
  function noteOpen(){
    return !!(activeStudy && activeStudy.querySelector('.note-box') && !activeStudy.querySelector('.note-box').hidden);
  }
  function setNoteOpen(cont, open){
    if(!cont) return;
    activateStudy(cont);
    var nb=cont.querySelector('.note-box');
    if(!nb) return;
    nb.hidden=!open;
    cont.classList.toggle('note-open', !!open);
    refreshStudyBar();
    if(open){
      var ta=nb.querySelector('textarea');
      setTimeout(function(){
        try{ nb.scrollIntoView({block:'nearest', behavior:'smooth'}); }catch(e){ nb.scrollIntoView(); }
        if(ta) ta.focus();
      }, 0);
    }
  }

  function apply(cont, ref){
    if(load('vhl')[ref]) cont.classList.add('v-hl');
    if(load('favorites')[ref]) cont.classList.add('fav');
    var notes=load('notes');
    if(notes[ref]){
      var ta=cont.querySelector('.note-box textarea');
      if(ta) ta.value=notes[ref];
      cont.classList.add('has-note');
    }
    var rec=load('whl')[ref]||{};
    Object.keys(rec).forEach(function(f){
      rec[f].forEach(function(o){
        var w=cont.querySelector('.w[data-f="'+f+'"][data-i="'+o.i+'"]');
        if(w){ w.classList.add('w-hl'); w.setAttribute('data-c', o.c||'y'); }
      });
    });
  }

  function toggleWord(w){
    var cont=w.closest('[data-ref]'); if(!cont) return;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var all=load('whl'), recd=all[ref]||{}, arr=recd[f]||[];
    var pos=-1; for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ pos=n; break; } }
    if(pos>-1){ arr.splice(pos,1); w.classList.remove('w-hl'); w.removeAttribute('data-c'); }
    else { arr.push({i:i,t:w.textContent,c:'y'}); w.classList.add('w-hl'); w.setAttribute('data-c','y'); }
    if(arr.length) recd[f]=arr; else delete recd[f];
    if(Object.keys(recd).length) all[ref]=recd; else delete all[ref];
    save('whl', all);
    bumpMark();
  }

  function toggleVerse(cont, ref, btn){
    var all=load('vhl');
    if(all[ref]){ delete all[ref]; cont.classList.remove('v-hl'); if(btn) btn.classList.remove('on'); }
    else { all[ref]=1; cont.classList.add('v-hl'); if(btn) btn.classList.add('on'); }
    save('vhl', all);
    refreshStudyBar();
  }

  function toggleFavorite(cont, ref, btn){
    var all=load('favorites');
    if(all[ref]){ delete all[ref]; cont.classList.remove('fav'); if(btn) btn.classList.remove('on'); }
    else { all[ref]=1; cont.classList.add('fav'); if(btn) btn.classList.add('on'); }
    save('favorites', all);
    refreshStudyBar();
  }

  document.addEventListener('click', function(e){
    var action=e.target.closest && e.target.closest('.study-context button, .note-actions button');
    if(action){
      var bar=action.closest && action.closest('.study-context');
      var cont=bar ? findStudyByRef(bar.getAttribute('data-ref')) : action.closest('[data-ref]');
      if(!cont && activeStudy && !(activeStudy.classList && activeStudy.classList.contains('study-context'))) cont=activeStudy;
      if(!cont) return;
      var ref=cont.getAttribute('data-ref'), act=action.dataset.act;
      activateStudy(cont);
      if(act==='fav') toggleFavorite(cont, ref, action);
      else if(act==='vhl') toggleVerse(cont, ref, action);
      else if(act==='note'){ var nb=cont.querySelector('.note-box'); setNoteOpen(cont, !(nb && !nb.hidden)); }
      else if(act==='copy' || act==='copy-note') copyText(verseText(cont, ref), action);
      else if(act==='share') shareVerse(cont, ref, action);
      return;
    }
    if(e.target.closest && e.target.closest('.tools-fab,.tools-panel,.pen-toggle,.pen-colors,.sel-bar,.note-box,.translit-toggle,.original-toggle,.study-open,.study-dialog,a,button,select,input,textarea')) return;
    var w=e.target.closest && e.target.closest('.w');
    if(w && w.closest('[data-ref]')){ if(penOn) return; activateStudy(w.closest('[data-ref]')); return; }
    var cont=e.target.closest && e.target.closest('.verse-cont[data-ref], .ch-verse[data-ref]');
    if(cont) activateStudy(cont);
    else if(!noteOpen()) closeStudyBar();
  });
  document.addEventListener('keydown', function(e){
    if(e.key!=='Enter' && e.key!==' ') return;
    var cont=e.target.closest && e.target.closest('.verse-cont[data-ref], .ch-verse[data-ref]');
    if(!cont || e.target.closest('button,a,select,input,textarea')) return;
    e.preventDefault();
    activateStudy(cont);
  });

  // ---------- caneta marca-texto: arrastar pinta as palavras (com cores) ----------
  var penOn=false, penColor='y', painting=false, activePointerId=null, pendingWhl=null, lastPenTap=null;
  var COLORS=['x','y','g','b','p'], CNAMES={x:'Desmarcar',y:'Amarelo',g:'Verde',b:'Azul',p:'Rosa'};
  function setPen(on){
    penOn=on; document.body.classList.toggle('hl-mode', on);
    var b=document.querySelector('.pen-toggle');
    if(b){ b.classList.toggle('on', on); b.setAttribute('aria-pressed', on?'true':'false'); }
    save('penmode', {on:on});
  }
  function setColor(c){
    penColor=c;
    var sw=document.querySelectorAll('.pen-colors button');
    for(var i=0;i<sw.length;i++){ sw[i].classList.toggle('on', sw[i].getAttribute('data-c')===c); }
    save('pencolor', {c:c});
  }
  function wordAtPoint(x,y){ var el=document.elementFromPoint(x,y); return el && el.closest ? el.closest('.w') : null; }
  function wordKey(w){
    var cont=w && w.closest('[data-ref]'); if(!cont) return '';
    return cont.getAttribute('data-ref')+'|'+w.dataset.f+'|'+w.dataset.i;
  }
  function removeWordMark(w, all){
    var cont=w && w.closest('[data-ref]'); if(!cont || !all) return false;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var recd=all[ref], arr=recd && recd[f], pos=-1;
    if(arr){ for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ pos=n; break; } } }
    if(pos<0) return false;
    arr.splice(pos,1); w.classList.remove('w-hl'); w.removeAttribute('data-c');
    if(!arr.length) delete recd[f];
    if(!Object.keys(recd).length) delete all[ref];
    return true;
  }
  function isRepeatTap(w){
    var now=Date.now(), key=wordKey(w);
    return !!(lastPenTap && lastPenTap.key===key && now-lastPenTap.t<520);
  }
  function paintWord(w){
    if(!w) return; var cont=w.closest('[data-ref]'); if(!cont) return;
    var ref=cont.getAttribute('data-ref'), f=w.dataset.f, i=+w.dataset.i;
    var recd=pendingWhl[ref]||(pendingWhl[ref]={}); var arr=recd[f]||(recd[f]=[]);
    var found=null, pos=-1; for(var n=0;n<arr.length;n++){ if(arr[n].i===i){ found=arr[n]; pos=n; break; } }
    if(penColor==='x'){
      if(found) removeWordMark(w, pendingWhl);
      return;
    }
    if(found){ if(found.c!==penColor){ found.c=penColor; w.setAttribute('data-c', penColor); } }
    else { arr.push({i:i,t:w.textContent,c:penColor}); w.classList.add('w-hl'); w.setAttribute('data-c', penColor); bumpMark(); }
  }
  function startPaint(e){
    if(!penOn) return;
    var w=(e.target.closest && e.target.closest('.w')); if(!w || !w.closest('[data-ref]')) return;
    e.preventDefault(); pendingWhl=load('whl');
    if(isRepeatTap(w) && removeWordMark(w, pendingWhl)){
      save('whl', pendingWhl); lastPenTap=null; painting=false; activePointerId=null; return;
    }
    painting=true; activePointerId=e.pointerId; paintWord(w);
    lastPenTap={key:wordKey(w), t:Date.now()};
  }
  function movePaint(e){ if(!painting || e.pointerId!==activePointerId) return; e.preventDefault(); var w=wordAtPoint(e.clientX, e.clientY); if(w && wordKey(w)!==(lastPenTap && lastPenTap.key)) lastPenTap=null; paintWord(w); }
  function endPaint(){ if(!painting) return; painting=false; activePointerId=null; save('whl', pendingWhl); }
  document.addEventListener('pointerdown', startPaint);
  document.addEventListener('pointermove', movePaint);
  document.addEventListener('pointerup', endPaint);
  document.addEventListener('pointercancel', endPaint);
  function makePenTools(){
    if(!document.querySelector('.verse-cont[data-ref], .ch-verse[data-ref]')) return;
    if(document.querySelector('.pen-toggle')) return;
    var btn=document.createElement('button'); btn.type='button'; btn.className='pen-toggle';
    btn.setAttribute('aria-pressed','false'); btn.title='Marca-texto (caneta)'; btn.textContent='🖍';
    btn.onclick=function(){ setPen(!penOn); };
    document.body.appendChild(btn);
    var pal=document.createElement('div'); pal.className='pen-colors';
    pal.innerHTML=COLORS.map(function(c){
      return '<button type="button" data-c="'+c+'" aria-label="'+CNAMES[c]+'" title="'+CNAMES[c]+'">'+(c==='x'?'x':'')+'</button>';
    }).join('');
    pal.addEventListener('click', function(e){ var b=e.target.closest('button'); if(b) setColor(b.getAttribute('data-c')); });
    document.body.appendChild(pal);
    setColor((load('pencolor').c)||'y');
    if(load('penmode').on) setPen(true);
  }

  // ---------- marca-texto por seleção: barra flutuante (Grifar / Copiar) ----------
  var selBar=null, selT=null;
  function getSelBar(){
    if(selBar) return selBar;
    selBar=document.createElement('div'); selBar.className='sel-bar'; selBar.hidden=true;
    selBar.innerHTML='<button type="button" data-sel="copy">⧉ Copiar seleção</button>';
    document.body.appendChild(selBar);
    selBar.addEventListener('mousedown', function(e){ e.preventDefault(); });  // preserva a seleção
    selBar.addEventListener('click', function(e){
      var b=e.target.closest('button'); if(b) copySelection(b);
    });
    return selBar;
  }
  function hideSelBar(){ if(selBar) selBar.hidden=true; }
  function selInfo(){
    var sel=window.getSelection();
    if(!sel || sel.isCollapsed || !sel.rangeCount) return null;
    var r=sel.getRangeAt(0), node=r.commonAncestorContainer;
    var el=node.nodeType===1?node:node.parentNode;
    var cont=el && el.closest ? el.closest('[data-ref]') : null;
    if(!cont) return null;
    var text=sel.toString().trim(); if(!text) return null;
    return {sel:sel, range:r, cont:cont, text:text};
  }
  function showSelBar(){
    var info=selInfo(); if(!info){ hideSelBar(); return; }
    var bar=getSelBar(); bar.hidden=false;
    try{
      var rect=info.range.getBoundingClientRect();
      var top=window.scrollY + rect.top - bar.offsetHeight - 8;
      if(top < window.scrollY+4) top = window.scrollY + rect.bottom + 8;
      var left=window.scrollX + rect.left + rect.width/2 - bar.offsetWidth/2;
      bar.style.top=Math.max(4,top)+'px';
      bar.style.left=Math.max(4,left)+'px';
    }catch(e){}
  }
  function copySelection(btn){ var info=selInfo(); if(info) copyText(info.text, btn); }
  function scheduleSelBar(){ clearTimeout(selT); selT=setTimeout(showSelBar, 10); }
  document.addEventListener('mouseup', scheduleSelBar);
  document.addEventListener('touchend', scheduleSelBar);
  document.addEventListener('selectionchange', function(){
    var s=window.getSelection(); if(!s || s.isCollapsed) hideSelBar();
  });
  document.addEventListener('mousedown', function(e){
    if(selBar && !selBar.hidden && !(e.target.closest && e.target.closest('.sel-bar'))) hideSelBar();
  });
  window.addEventListener('scroll', hideSelBar, {passive:true});
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
  makeAccountButton();
  makePenTools();
  makeToolsMenu();
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
  function allRefs(notes, vhl, whl, fav){
    var s={}; [notes,vhl,whl,fav].forEach(function(o){ Object.keys(o||{}).forEach(function(r){ s[r]=1; }); });
    return Object.keys(s).sort();
  }
  function exportText(keys, notes, vhl, whl, fav){
    var out='Minhas anotações — Bíblia em Contexto\n\n';
    keys.forEach(function(ref){
      out+=ref+'\n';
      if(fav && fav[ref]) out+='  [favorito]\n';
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
  function importData(obj){
    var n=load('notes'), v=load('vhl'), w=load('whl'), f=load('favorites');
    if(obj.notes) Object.keys(obj.notes).forEach(function(r){ n[r]=obj.notes[r]; });
    if(obj.favorites) Object.keys(obj.favorites).forEach(function(r){ f[r]=obj.favorites[r]; });
    if(obj.vhl) Object.keys(obj.vhl).forEach(function(r){ v[r]=obj.vhl[r]; });
    if(obj.whl) Object.keys(obj.whl).forEach(function(r){
      var rec=obj.whl[r]; w[r]=w[r]||{};
      Object.keys(rec).forEach(function(f){
        var ex=w[r][f]||[], have={}; ex.forEach(function(o){ have[o.i]=1; });
        rec[f].forEach(function(o){ if(!have[o.i]) ex.push(o); }); w[r][f]=ex;
      });
    });
    save('notes',n); save('vhl',v); save('whl',w); save('favorites',f);
  }
  function render(){
    var box=document.getElementById('anotacoes'); if(!box) return;
    var notes=load('notes'), vhl=load('vhl'), whl=load('whl'), fav=load('favorites'), keys=allRefs(notes,vhl,whl,fav);
    if(!keys.length){ box.innerHTML='<p class="empty">Você ainda não grifou nem anotou nada. Abra um versículo (ou um capítulo) e use “Grifar” ou “Anotar”.</p>'; return; }
    box.innerHTML=keys.map(function(ref){
      var h='<div class="anot"><h3><a href="'+slugFromRef(ref)+'">'+esc(ref)+'</a></h3>';
      if(fav[ref]) h+='<p class="anot-tag">★ favorito</p>';
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
    function data(){ var n=load('notes'),v=load('vhl'),w=load('whl'),f=load('favorites'); return {keys:allRefs(n,v,w,f),notes:n,vhl:v,whl:w,favorites:f}; }
    if(c) c.onclick=function(){ var d=data(); var txt=exportText(d.keys,d.notes,d.vhl,d.whl,d.favorites);
      (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){ c.textContent='Copiado!'; setTimeout(function(){c.textContent='Copiar tudo';},1500); })
      .catch(function(){ download('anotacoes.txt',txt,'text/plain'); }); };
    if(t) t.onclick=function(){ var d=data(); download('anotacoes.txt', exportText(d.keys,d.notes,d.vhl,d.whl,d.favorites), 'text/plain'); };
    if(j) j.onclick=function(){ download('anotacoes.json', JSON.stringify({notes:load('notes'),vhl:load('vhl'),whl:load('whl'),favorites:load('favorites')}, null, 2), 'application/json'); };
    if(x) x.onclick=function(){ confirmModal('Apagar TODAS as marcações e anotações deste navegador? Esta ação não pode ser desfeita.', function(){ ['notes','vhl','whl','favorites'].forEach(function(k){localStorage.removeItem('bec.'+k);}); render(); scheduleCloudSync(); }); };
    var sh=document.getElementById('anot-share');
    if(sh) sh.onclick=function(){ var d=data(); var txt=exportText(d.keys,d.notes,d.vhl,d.whl,d.favorites);
      if(navigator.share){ navigator.share({title:'Minhas anotações — Bíblia em Contexto', text:txt}).catch(function(){}); }
      else (navigator.clipboard?navigator.clipboard.writeText(txt):Promise.reject()).then(function(){ sh.textContent='Copiado!'; setTimeout(function(){sh.textContent='Compartilhar';},1500); }).catch(function(){ download('anotacoes.txt',txt,'text/plain'); }); };
    var imp=document.getElementById('anot-import'), impf=document.getElementById('anot-import-file');
    if(imp && impf){
      imp.onclick=function(){ impf.click(); };
      impf.onchange=function(){
        var f=impf.files[0]; if(!f) return;
        var rd=new FileReader();
        rd.onload=function(){ try{ importData(JSON.parse(rd.result)); render(); imp.textContent='Importado!'; }catch(e){ imp.textContent='Arquivo inválido'; } setTimeout(function(){imp.textContent='Importar backup';},1800); };
        rd.readAsText(f); impf.value='';
      };
    }
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', wire); else wire();
})();
