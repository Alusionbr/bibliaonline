// cloud.js — camada colaborativa (Supabase). Gerado por build.py. Não editar à mão.
(function(){
  if(!window.supabase || !window.supabase.createClient){ return; }
  var sb = window.supabase.createClient('https://pxqhpntifbtjaoqtirao.supabase.co', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB4cWhwbnRpZmJ0amFvcXRpcmFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI1OTY3ODYsImV4cCI6MjA5ODE3Mjc4Nn0.s8ZJUMzQI7ACsb48I4lkcqj0Y2lQXoD-zIfojRCaRug', {
    auth: { persistSession:true, autoRefreshToken:true, detectSessionInUrl:true }
  });

  // ---------- util ----------
  function siteRoot(){
    try { var s=document.querySelector('script[src*="assets/cloud.js"]'); if(s) return new URL('../', s.src).href; } catch(e){}
    return location.origin + '/';
  }
  var ROOT = siteRoot();
  function url(p){ return ROOT + p; }
  function qsParam(n){ try { return new URLSearchParams(location.search).get(n); } catch(e){ return null; } }
  function h(tag, attrs, kids){
    var e=document.createElement(tag); attrs=attrs||{};
    for(var k in attrs){
      if(k==='text'){ e.textContent=attrs[k]; }
      else if(k==='class'){ e.className=attrs[k]; }
      else if(k==='on'){ for(var ev in attrs.on){ e.addEventListener(ev, attrs.on[ev]); } }
      else if(attrs[k]!=null){ e.setAttribute(k, attrs[k]); }
    }
    (kids||[]).forEach(function(c){ if(c==null||c===false) return; e.appendChild(typeof c==='string'?document.createTextNode(c):c); });
    return e;
  }
  function clear(el){ while(el && el.firstChild) el.removeChild(el.firstChild); }
  function nameHint(){ try { return localStorage.getItem('bec.cloud.name')||''; } catch(e){ return ''; } }
  function setNameHint(v){ try { localStorage.setItem('bec.cloud.name', v); } catch(e){} }
  function fmtDate(s){ try { return new Date(s).toLocaleString('pt-BR', {dateStyle:'short', timeStyle:'short'}); } catch(e){ return ''; } }
  var toastBox=null;
  function toast(msg, kind){
    if(!toastBox){ toastBox=h('div',{id:'cloud-toast'}); document.body.appendChild(toastBox); }
    var t=h('div',{class:'cloud-toast'+(kind?(' '+kind):''), text:msg});
    toastBox.appendChild(t);
    setTimeout(function(){ t.classList.add('out'); setTimeout(function(){ if(t.parentNode) t.parentNode.removeChild(t); }, 350); }, 3200);
  }

  // ---------- estado ----------
  var state = { user:null, profile:null, memberships:[], isStaff:false };
  window.BEC_CLOUD = { sb: sb, state: state };
  function uid(){ return state.user ? state.user.id : null; }
  function activeGroups(){ return state.memberships.filter(function(m){ return m.status==='active'; }); }
  function membershipByCode(code){ return state.memberships.filter(function(m){ return m.groups && m.groups.invite_code===code; })[0]; }
  function roleIn(gid){ var m=state.memberships.filter(function(x){ return x.group_id===gid && x.status==='active'; })[0]; return m?m.role:null; }
  function canModerate(gid){ var r=roleIn(gid); return r==='admin'||r==='moderator'||state.isStaff; }
  function profileComplete(){ var p=state.profile; return !!(p && p.age && p.gender && p.account_type); }

  // ---------- badges (papéis visíveis) ----------
  function badge(cls, txt){ return h('span',{class:'badge '+cls, text:txt}); }
  function renderBadges(o){
    o=o||{}; var w=h('span',{class:'badges'});
    if(o.role==='admin') w.appendChild(badge('role-admin','Admin'));
    else if(o.role==='moderator') w.appendChild(badge('role-mod','Moderador'));
    if(o.staff) w.appendChild(badge('staff','Equipe'));
    if(o.type==='pastor') w.appendChild(badge('pastor','Pastor'));
    else if(o.type==='aluno') w.appendChild(badge('aluno','Aluno'));
    if(o.beta) w.appendChild(badge('beta','beta'));
    return w;
  }
  async function loadStaffFlag(){
    state.isStaff=false; if(!uid()) return;
    try { var r= await sb.from('staff').select('user_id').eq('user_id', uid()).maybeSingle(); state.isStaff=!!(r && r.data); } catch(e){}
  }
  async function staffSet(ids){
    var s={}; ids=(ids||[]).filter(Boolean); if(!ids.length) return s;
    try { var r= await sb.from('staff').select('user_id').in('user_id', ids); if(!r.error) r.data.forEach(function(x){ s[x.user_id]=1; }); } catch(e){}
    return s;
  }
  // exige cadastro completo antes de ações de grupo; injeta aviso e retorna false
  function requireComplete(container){
    if(profileComplete()) return true;
    container.appendChild(h('div',{class:'cloud-card'},[
      h('h2',{text:'Complete seu cadastro'}),
      h('p',{class:'read', text:'Para participar dos grupos de estudo, complete seu cadastro (nome, idade, gênero e se é Pastor ou Aluno).'}),
      h('a',{class:'btn primary', href:url('conta/'), text:'Completar cadastro'})
    ]));
    return false;
  }

  async function loadProfile(){
    if(!uid()){ state.profile=null; return; }
    try {
      var r = await sb.from('profiles').select('id,name,age,gender,account_type,is_beta').eq('id', uid()).maybeSingle();
      state.profile = r.data || null;
    } catch(e){ state.profile=null; }
  }
  async function loadMemberships(){
    state.memberships = [];
    if(!uid()) return;
    try {
      var r = await sb.from('group_members')
        .select('id,role,status,group_id,groups(id,name,invite_code,description)')
        .eq('user_id', uid());
      if(!r.error && r.data) state.memberships = r.data;
    } catch(e){}
  }

  // ---------- navegação ----------
  function updateNav(){
    var a=document.getElementById('nav-conta');
    if(a){ a.textContent = state.user ? (state.profile && state.profile.name ? state.profile.name : 'Minha conta') : 'Conta'; }
    var g=document.getElementById('nav-grupos');
    if(g){
      var pending = state.memberships.some(function(m){ return m.status==='pending'; });
      g.textContent = 'Grupos';
      if(state.user && activeGroups().length){ g.setAttribute('data-count', String(activeGroups().length)); } else { g.removeAttribute('data-count'); }
      g.classList.toggle('has-pending', !!pending);
    }
    var eq=document.getElementById('nav-equipe');
    if(eq){ if(state.isStaff) eq.removeAttribute('hidden'); else eq.setAttribute('hidden','hidden'); }
  }

  // ---------- ROTEAMENTO ----------
  async function route(){
    updateNav();
    if(document.getElementById('conta-app')) await renderAccount();
    if(document.getElementById('grupos-app')) await renderGroupsIndex();
    if(document.getElementById('form-create-group')) initCreateGroup();
    if(document.getElementById('grupo-detail')) await renderGroupDetail();
    if(document.getElementById('equipe-app')) await renderTeam();
    var vc = document.querySelector('.verse-cont[data-slug]');
    if(vc){ await renderVerseNotes(vc); injectSuggest(vc); }
  }

  // ---------- CONTA ----------
  async function renderAccount(){
    var app=document.getElementById('conta-app'); if(!app) return; clear(app);
    if(!state.user){
      function authErrMsg(e){
        var m=(e&&e.message)||'';
        if(/invalid.login/i.test(m)||/invalid.credentials/i.test(m)||/invalid password/i.test(m)) return 'E-mail ou senha incorretos.';
        if(/email.not.confirmed/i.test(m)) return 'Confirme seu e-mail antes de entrar.';
        if(/user.already.registered/i.test(m)||/already.registered/i.test(m)) return 'E-mail já cadastrado. Tente entrar com sua senha.';
        if(/password.*characters/i.test(m)||/should be at least/i.test(m)) return 'Senha deve ter pelo menos 6 caracteres.';
        if(/rate.limit/i.test(m)) return 'Muitas tentativas. Aguarde alguns minutos.';
        return m||'Erro inesperado. Tente novamente.';
      }
      var nameI = h('input',{type:'text', id:'login-name', placeholder:'Seu nome (novo cadastro)', autocomplete:'name', value:nameHint()});
      var emailI = h('input',{type:'email', id:'login-email', placeholder:'voce@email.com', autocomplete:'email'});
      var passI = h('input',{type:'password', id:'login-pass', placeholder:'Senha (mín. 6 caracteres)', autocomplete:'current-password'});
      var btnEnter = h('button',{class:'btn primary', type:'button', text:'Entrar', on:{click:async function(){
        var v=(emailI.value||'').trim(), pw=(passI.value||'');
        if(!v||v.indexOf('@')<0){ toast('Digite um e-mail válido.','err'); return; }
        if(!pw){ toast('Digite sua senha.','err'); return; }
        btnEnter.disabled=true; btnEnter.textContent='Entrando…';
        try {
          var r= await sb.auth.signInWithPassword({ email:v, password:pw });
          if(r.error) throw r.error;
        } catch(e){ toast(authErrMsg(e),'err'); btnEnter.disabled=false; btnEnter.textContent='Entrar'; }
      }}});
      var btnSign = h('button',{class:'btn ghost', type:'button', text:'Criar conta', on:{click:async function(){
        var v=(emailI.value||'').trim(), pw=(passI.value||''), nm=(nameI.value||'').trim();
        if(!v||v.indexOf('@')<0){ toast('Digite um e-mail válido.','err'); return; }
        if(pw.length<6){ toast('Senha deve ter pelo menos 6 caracteres.','err'); return; }
        if(nm.length<2){ toast('Informe seu nome (campo acima).','err'); return; }
        btnSign.disabled=true; btnSign.textContent='Criando…';
        if(nm) setNameHint(nm);
        try {
          var r= await sb.auth.signUp({ email:v, password:pw, options:{ emailRedirectTo: url('conta/'), data:{ name:nm } } });
          if(r.error) throw r.error;
          if(r.data && r.data.session){
            // auto-confirm ativo: sessão aberta, onAuthStateChange dispara refresh
          } else {
            clear(app); app.appendChild(h('div',{class:'cloud-card'},[
              h('h2',{text:'Verifique seu e-mail'}),
              h('p',{class:'read', text:'Enviamos um link de confirmação para '+v+'. Abra-o para ativar sua conta e entrar.'})
            ]));
          }
        } catch(e){ toast(authErrMsg(e),'err'); btnSign.disabled=false; btnSign.textContent='Criar conta'; }
      }}});
      var btnGoogle = h('button',{class:'btn oauth google', type:'button', text:'Entrar com Google', on:{click:async function(){
        var r= await sb.auth.signInWithOAuth({ provider:'google', options:{ redirectTo: url('conta/') } });
        if(r.error) toast('Google: '+(r.error.message||'erro'),'err');
      }}});
      var btnApple = h('button',{class:'btn oauth apple', type:'button', text:'Entrar com Apple', on:{click:async function(){
        var r= await sb.auth.signInWithOAuth({ provider:'apple', options:{ redirectTo: url('conta/') } });
        if(r.error) toast('Apple: '+(r.error.message||'erro'),'err');
      }}});
      // magic link como opção secundária (discreta)
      var magicSec = h('div',{class:'magic-link-sec'});
      magicSec.style.display='none';
      var magicEmail = h('input',{type:'email', id:'login-email-magic', placeholder:'voce@email.com', autocomplete:'email'});
      var btnMagic = h('button',{class:'btn ghost', type:'button', text:'Enviar link', on:{click:async function(){
        var v=(magicEmail.value||'').trim();
        if(!v||v.indexOf('@')<0){ toast('Digite um e-mail válido.','err'); return; }
        btnMagic.disabled=true; btnMagic.textContent='Enviando…';
        try {
          var r= await sb.auth.signInWithOtp({ email:v, options:{ emailRedirectTo: url('conta/') } });
          if(r.error) throw r.error;
          clear(magicSec); magicSec.appendChild(h('p',{class:'read', text:'Link enviado para '+v+'. Abra no mesmo aparelho.'}));
        } catch(e){ toast('Não foi possível enviar: '+(e.message||e),'err'); btnMagic.disabled=false; btnMagic.textContent='Enviar link'; }
      }}});
      magicSec.appendChild(h('label',{class:'cloud-label', for:'login-email-magic', text:'E-mail para link mágico'}));
      magicSec.appendChild(magicEmail);
      magicSec.appendChild(btnMagic);
      var toggleMagic = h('button',{class:'btn link', type:'button', text:'Entrar com link por e-mail (sem senha)', on:{click:function(){
        magicSec.style.display = magicSec.style.display==='none' ? 'grid' : 'none';
      }}});
      app.appendChild(h('div',{class:'cloud-card'},[
        h('h2',{text:'Entrar ou criar conta'}),
        h('p',{class:'read', text:'A leitura da Bíblia continua livre, sem conta. A conta serve só para os grupos de estudo.'}),
        h('label',{class:'cloud-label', for:'login-name', text:'Nome (para novo cadastro)'}), nameI,
        h('label',{class:'cloud-label', for:'login-email', text:'E-mail'}), emailI,
        h('label',{class:'cloud-label', for:'login-pass', text:'Senha'}), passI,
        h('div',{class:'cloud-row'},[btnEnter, btnSign]),
        h('div',{class:'cloud-divider', text:'ou continue com'}),
        h('div',{class:'oauth-row'},[btnGoogle, btnApple]),
        h('div',{class:'cloud-divider'}),
        toggleMagic, magicSec
      ]));
      return;
    }
    // logado — cadastro (obrigatório p/ grupos) + perfil
    var p=state.profile||{};
    var nameInput = h('input',{type:'text', id:'profile-name', value:p.name||nameHint()||'', placeholder:'Seu nome', maxlength:'60'});
    var ageInput = h('input',{type:'number', id:'profile-age', value:p.age||'', placeholder:'Idade', min:'13', max:'120'});
    var genderSel = h('select',{id:'profile-gender'},[
      h('option',{value:'', text:'Gênero…'}),
      h('option',{value:'m', text:'Masculino'}),
      h('option',{value:'f', text:'Feminino'}),
      h('option',{value:'prefiro_nao_dizer', text:'Prefiro não dizer'})
    ]);
    if(p.gender) genderSel.value=p.gender;
    var typeSel = h('select',{id:'profile-type'},[
      h('option',{value:'', text:'Você é…'}),
      h('option',{value:'pastor', text:'Pastor(a)'}),
      h('option',{value:'aluno', text:'Aluno(a)'})
    ]);
    if(p.account_type) typeSel.value=p.account_type;
    var saveBtn = h('button',{class:'btn primary', type:'button', text:'Salvar cadastro', on:{click:async function(){
      var nm=(nameInput.value||'').trim(), age=parseInt(ageInput.value,10), gen=genderSel.value, tp=typeSel.value;
      if(nm.length<2){ toast('Informe seu nome.','err'); return; }
      if(!age || age<13){ toast('Idade mínima 13 anos.','err'); return; }
      if(!gen){ toast('Selecione o gênero.','err'); return; }
      if(!tp){ toast('Selecione Pastor ou Aluno.','err'); return; }
      saveBtn.disabled=true;
      var r= await sb.rpc('save_profile', { p_name:nm, p_age:age, p_gender:gen, p_type:tp });
      saveBtn.disabled=false;
      if(r.error){ toast(rpcMsg(r.error,'Erro ao salvar.'),'err'); }
      else { state.profile=Object.assign({}, p, {name:nm, age:age, gender:gen, account_type:tp}); setNameHint(nm); updateNav(); toast('Cadastro salvo.'); renderAccount(); }
    }}});
    var out = h('button',{class:'btn ghost', type:'button', text:'Sair', on:{click:async function(){ await sb.auth.signOut(); location.reload(); }}});
    var card=h('div',{class:'cloud-card'},[
      h('h2',{text: profileComplete()?'Minha conta':'Complete seu cadastro'}),
      h('p',{class:'read', text:state.user.email||''}),
      renderBadges({ staff:state.isStaff, type:p.account_type, beta:p.is_beta!==false }),
      h('label',{class:'cloud-label', for:'profile-name', text:'Nome'}), nameInput,
      h('div',{class:'cloud-grid2'},[
        h('div',{},[h('label',{class:'cloud-label', for:'profile-age', text:'Idade'}), ageInput]),
        h('div',{},[h('label',{class:'cloud-label', for:'profile-gender', text:'Gênero'}), genderSel])
      ]),
      h('label',{class:'cloud-label', for:'profile-type', text:'Perfil'}), typeSel,
      h('div',{class:'cloud-row'},[saveBtn, out])
    ]);
    app.appendChild(card);
    app.appendChild(h('div',{class:'cloud-card'},[
      h('h2',{text:'Meus grupos'}),
      h('p',{class:'read', text:'Veja, crie e entre em grupos de estudo na página de grupos.'}),
      h('a',{class:'btn primary', href:url('grupos/'), text:'Ir para Grupos'})
    ]));
    if(state.isStaff){
      app.appendChild(h('div',{class:'cloud-card'},[
        h('h2',{text:'Equipe'}),
        h('p',{class:'read', text:'Você faz parte da equipe do site. Acesse o painel para revisar sugestões da comunidade.'}),
        h('a',{class:'btn ghost', href:url('equipe/'), text:'Abrir painel da Equipe'})
      ]));
    }
  }

  // ---------- GRUPOS (índice) ----------
  async function renderGroupsIndex(){
    var app=document.getElementById('grupos-app'); if(!app) return; clear(app);
    if(!state.user){
      app.appendChild(h('div',{class:'cloud-card'},[
        h('h2',{text:'Grupos de estudo'}),
        h('p',{class:'read', text:'Entre na sua conta para criar ou participar de grupos de estudo, compartilhar notas e seguir planos juntos.'}),
        h('a',{class:'btn primary', href:url('conta/'), text:'Entrar / Criar conta'})
      ]));
      return;
    }
    if(!requireComplete(app)) return;
    // quota: só o criador vira admin, logo nº de grupos onde sou admin = grupos criados
    var owned=state.memberships.filter(function(m){ return m.status==='active' && m.role==='admin'; }).length;
    var atLimit = !state.isStaff && owned>=3;
    // ações
    var codeInput=h('input',{type:'text', placeholder:'código do convite', maxlength:'12'});
    var joinBtn=h('button',{class:'btn ghost', type:'button', text:'Entrar com código', on:{click:async function(){
      var c=(codeInput.value||'').trim().toLowerCase();
      if(!c){ toast('Digite o código do convite.','err'); return; }
      joinBtn.disabled=true;
      try {
        var r= await sb.rpc('join_group', { p_code:c });
        if(r.error) throw r.error;
        await loadMemberships();
        toast('Pedido enviado. Aguardando aprovação do administrador.');
        location.href=url('grupos/grupo/?c='+encodeURIComponent(c));
      } catch(e){ toast(rpcMsg(e,'Código inválido ou grupo não encontrado.'),'err'); joinBtn.disabled=false; }
    }}});
    var createBtn = atLimit
      ? h('span',{class:'btn primary disabled', title:'Limite de 3 grupos', text:'+ Criar grupo'})
      : h('a',{class:'btn primary', href:url('grupos/novo/'), text:'+ Criar grupo'});
    app.appendChild(h('div',{class:'cloud-actions'},[
      createBtn,
      h('span',{class:'quota', text:(state.isStaff?'Equipe':('Você criou '+owned+' de 3 grupos'))}),
      h('span',{class:'cloud-join'},[codeInput, joinBtn])
    ]));
    var actives=activeGroups(), pend=state.memberships.filter(function(m){ return m.status==='pending'; });
    if(!actives.length && !pend.length){
      app.appendChild(h('p',{class:'read', text:'Você ainda não participa de nenhum grupo. Crie um e convide pessoas pelo código, ou entre num grupo existente.'}));
    }
    if(actives.length){
      var list=h('div',{class:'group-list'});
      actives.forEach(function(m){
        var g=m.groups||{};
        list.appendChild(h('a',{class:'group-item', href:url('grupos/grupo/?c='+encodeURIComponent(g.invite_code))},[
          h('strong',{text:g.name||'Grupo'}),
          m.role==='admin'?h('span',{class:'tag', text:'admin'}):null,
          g.description?h('span',{class:'group-desc', text:g.description}):null
        ]));
      });
      app.appendChild(h('section',{},[h('h2',{text:'Meus grupos'}), list]));
    }
    if(pend.length){
      var pl=h('div',{class:'group-list'});
      pend.forEach(function(m){ var g=m.groups||{}; pl.appendChild(h('div',{class:'group-item pending'},[h('strong',{text:g.name||'Grupo'}), h('span',{class:'tag', text:'aguardando aprovação'})])); });
      app.appendChild(h('section',{},[h('h2',{text:'Pedidos pendentes'}), pl]));
    }
  }

  function initCreateGroup(){
    var form=document.getElementById('form-create-group'); if(!form || form.dataset.bound) return; form.dataset.bound='1';
    if(!state.user){ location.href=url('conta/'); return; }
    if(!profileComplete()){ location.href=url('conta/'); return; }
    form.addEventListener('submit', async function(e){
      e.preventDefault();
      var name=(form.querySelector('[name=name]').value||'').trim();
      var desc=(form.querySelector('[name=description]').value||'').trim();
      if(!name){ toast('Dê um nome ao grupo.','err'); return; }
      var btn=form.querySelector('button[type=submit]'); btn.disabled=true;
      try {
        // criação atômica + limite de 3 validados no servidor (RPC security definer)
        var r= await sb.rpc('create_group', { p_name:name, p_description:desc });
        if(r.error) throw r.error;
        var code = (r.data && r.data[0] && r.data[0].invite_code) || '';
        await loadMemberships();
        location.href = code ? url('grupos/grupo/?c='+code) : url('grupos/');
      } catch(e2){ toast(rpcMsg(e2,'Erro ao criar grupo.'),'err'); btn.disabled=false; }
    });
  }

  // ---------- GRUPO (detalhe) ----------
  var detailChan=null;
  async function renderGroupDetail(){
    var root=document.getElementById('grupo-detail'); if(!root) return; clear(root);
    if(!state.user){ root.appendChild(h('div',{class:'cloud-card'},[h('p',{class:'read', text:'Entre na sua conta para ver este grupo.'}), h('a',{class:'btn primary', href:url('conta/'), text:'Entrar'})])); return; }
    var code=qsParam('c');
    if(!code){ root.appendChild(h('p',{class:'read', text:'Grupo não especificado.'})); return; }
    var mem=membershipByCode(code);
    // não-membro ou pendente: mostra cartão de entrada/aguardo
    if(!mem || mem.status!=='active'){
      var brief=null;
      try { var b= await sb.rpc('group_brief', { p_code:code }); if(!b.error && b.data && b.data.length) brief=b.data[0]; } catch(e){}
      var card=h('div',{class:'cloud-card'});
      card.appendChild(h('h1',{text: brief?brief.name:'Grupo de estudo'}));
      if(brief && brief.description) card.appendChild(h('p',{class:'read', text:brief.description}));
      if(mem && mem.status==='pending'){
        card.appendChild(h('p',{class:'read', text:'Seu pedido foi enviado. Aguardando o administrador aprovar.'}));
      } else {
        card.appendChild(h('p',{class:'read', text:'Você ainda não faz parte deste grupo.'}));
        card.appendChild(h('button',{class:'btn primary', type:'button', text:'Pedir para entrar', on:{click:async function(){
          try { var r= await sb.rpc('join_group',{p_code:code}); if(r.error) throw r.error; await loadMemberships(); renderGroupDetail(); toast('Pedido enviado.'); }
          catch(e){ toast(rpcMsg(e,'Não foi possível entrar.'),'err'); }
        }}}));
      }
      root.appendChild(card); return;
    }
    var g=mem.groups, gid=g.id;
    var ctx={ role: mem.role, admin: mem.role==='admin'||state.isStaff, mod: canModerate(gid), staff: state.isStaff };
    root.appendChild(h('header',{class:'group-head'},[
      h('h1',{text:g.name}),
      renderBadges({ role: mem.role, staff: state.isStaff }),
      g.description?h('p',{class:'read', text:g.description}):null,
      h('p',{class:'group-code'},['Código do convite: ', h('code',{text:g.invite_code}),
        h('button',{class:'btn-mini', type:'button', text:'copiar', on:{click:function(){ try{ navigator.clipboard.writeText(g.invite_code); toast('Código copiado.'); }catch(e){} }}})])
    ]));
    var tabs=h('div',{class:'tabs', role:'tablist'});
    var panel=h('div',{class:'tab-panel'});
    var defs=[['feed','Feed'],['discussoes','Discussões'],['membros','Membros'],['planos','Planos']];
    defs.forEach(function(d){
      tabs.appendChild(h('button',{class:'tab', type:'button', 'data-tab':d[0], text:d[1], on:{click:function(){
        Array.prototype.forEach.call(tabs.children,function(b){ b.classList.toggle('on', b.getAttribute('data-tab')===d[0]); });
        showTab(d[0], gid, g, ctx, panel);
      }}}));
    });
    root.appendChild(tabs); root.appendChild(panel);
    tabs.children[0].classList.add('on');
    showTab('feed', gid, g, ctx, panel);
    // realtime do grupo (feed)
    if(detailChan){ try{ sb.removeChannel(detailChan); }catch(e){} }
    detailChan = sb.channel('grp-'+gid)
      .on('postgres_changes',{event:'*',schema:'public',table:'activity_feed',filter:'group_id=eq.'+gid}, function(){
        var on=tabs.querySelector('.tab.on'); if(on && on.getAttribute('data-tab')==='feed') showTab('feed',gid,g,ctx,panel);
      })
      .subscribe();
  }

  async function showTab(name, gid, g, ctx, panel){
    clear(panel);
    if(name==='feed') return renderFeed(gid, panel);
    if(name==='discussoes') return renderDiscussions(gid, ctx, panel);
    if(name==='membros') return renderMembers(gid, ctx, panel);
    if(name==='planos') return renderPlans(gid, ctx, panel);
  }

  async function renderFeed(gid, panel){
    panel.appendChild(h('p',{class:'read muted', text:'Atividade recente do grupo.'}));
    var r= await sb.from('activity_feed').select('id,event_type,payload,created_at,profiles(name)').eq('group_id',gid).order('created_at',{ascending:false}).limit(60);
    if(r.error){ panel.appendChild(h('p',{class:'read', text:'Não foi possível carregar o feed.'})); return; }
    if(!r.data.length){ panel.appendChild(h('p',{class:'read', text:'Sem atividade ainda. Adicione uma nota num versículo para começar.'})); return; }
    var list=h('ul',{class:'feed'});
    r.data.forEach(function(ev){
      var who=(ev.profiles&&ev.profiles.name)||'Alguém';
      var txt=who+' '+feedText(ev);
      list.appendChild(h('li',{class:'feed-item'},[ h('span',{class:'feed-txt', text:txt}), h('time',{text:fmtDate(ev.created_at)}) ]));
    });
    panel.appendChild(list);
  }
  function feedText(ev){
    var p=ev.payload||{};
    if(ev.event_type==='note_added') return 'comentou em '+ (p.verse_ref?refLabel(p.verse_ref):'um versículo')+'.';
    if(ev.event_type==='topic_added') return 'abriu a discussão "'+(p.title||'')+'".';
    if(ev.event_type==='joined_group') return 'entrou no grupo.';
    return ev.event_type;
  }
  function refLabel(slug){ return slug; }

  async function renderMembers(gid, ctx, panel){
    var admin=ctx.admin;
    var r= await sb.from('group_members').select('id,role,status,user_id,profiles(name,account_type,is_beta)').eq('group_id',gid).order('status',{ascending:true});
    if(r.error){ panel.appendChild(h('p',{class:'read', text:'Não foi possível carregar os membros.'})); return; }
    var ids=r.data.map(function(m){ return m.user_id; });
    var staff=await staffSet(ids);
    var pend=r.data.filter(function(m){ return m.status==='pending'; });
    var act=r.data.filter(function(m){ return m.status==='active'; });
    function nameOf(m){ return (m.profiles&&m.profiles.name)||'(sem nome)'; }
    function badgesOf(m){ var p=m.profiles||{}; return renderBadges({ role:m.role, staff:!!staff[m.user_id], type:p.account_type, beta:p.is_beta!==false }); }
    if(admin && pend.length){
      var pl=h('ul',{class:'member-list'});
      pend.forEach(function(m){
        pl.appendChild(h('li',{class:'member pending'},[
          h('span',{class:'member-name', text:nameOf(m)}),
          h('span',{class:'member-actions'},[
            h('button',{class:'btn-mini ok', type:'button', text:'Aprovar', on:{click:async function(){
              var u= await sb.rpc('decide_member',{p_member_id:m.id, p_approve:true});
              if(u.error){ toast(rpcMsg(u.error,'Erro ao aprovar.'),'err'); } else { toast('Membro aprovado.'); renderMembers(gid,ctx,panel); }
            }}}),
            h('button',{class:'btn-mini', type:'button', text:'Recusar', on:{click:async function(){
              var u= await sb.rpc('decide_member',{p_member_id:m.id, p_approve:false});
              if(u.error){ toast('Erro.','err'); } else { renderMembers(gid,ctx,panel); }
            }}})
          ])
        ]));
      });
      panel.appendChild(h('section',{},[h('h3',{text:'Pedidos pendentes'}), pl]));
    }
    var al=h('ul',{class:'member-list'});
    act.forEach(function(m){
      var actions=h('span',{class:'member-actions'});
      if(admin && m.role!=='admin'){
        if(m.role==='moderator'){
          actions.appendChild(h('button',{class:'btn-mini', type:'button', text:'Rebaixar', on:{click:async function(){
            var u= await sb.rpc('set_member_role',{p_member_id:m.id, p_role:'member'});
            if(u.error){ toast(rpcMsg(u.error,'Erro.'),'err'); } else { renderMembers(gid,ctx,panel); }
          }}}));
        } else {
          actions.appendChild(h('button',{class:'btn-mini', type:'button', text:'Tornar moderador', on:{click:async function(){
            var u= await sb.rpc('set_member_role',{p_member_id:m.id, p_role:'moderator'});
            if(u.error){ toast(rpcMsg(u.error,'Erro.'),'err'); } else { toast('Agora é moderador.'); renderMembers(gid,ctx,panel); }
          }}}));
        }
        actions.appendChild(h('button',{class:'btn-mini', type:'button', text:'Remover', on:{click:async function(){
          if(!confirm('Remover este membro?')) return;
          var u= await sb.rpc('remove_member',{p_member_id:m.id});
          if(u.error){ toast(rpcMsg(u.error,'Erro.'),'err'); } else { renderMembers(gid,ctx,panel); }
        }}}));
      }
      al.appendChild(h('li',{class:'member'},[ h('span',{class:'member-name', text:nameOf(m)}), badgesOf(m), actions ]));
    });
    panel.appendChild(h('section',{},[h('h3',{text:'Membros ('+act.length+')'}), al]));
  }

  // ---------- PLANOS do grupo ----------
  async function renderPlans(gid, ctx, panel){
    var admin=ctx.admin;
    if(admin){
      var nm=h('input',{type:'text', placeholder:'Nome do plano (ex.: João em 21 dias)'});
      var ta=h('textarea',{rows:'5', placeholder:'Um dia por linha. Capítulos separados por vírgula.\nEx.:\nJoão 1\nJoão 2, João 3'});
      var add=h('button',{class:'btn primary', type:'button', text:'Criar plano', on:{click:async function(){
        var name=(nm.value||'').trim(); if(!name){ toast('Dê um nome ao plano.','err'); return; }
        var dias=(ta.value||'').split('\n').map(function(l){ return l.split(',').map(function(s){ return s.trim(); }).filter(Boolean); }).filter(function(a){ return a.length; });
        if(!dias.length){ toast('Adicione ao menos um dia.','err'); return; }
        var r= await sb.from('group_plans').insert({ group_id:gid, name:name, chapters:dias, duration:dias.length, created_by:uid() });
        if(r.error){ toast('Erro ao criar plano: '+(r.error.message||''),'err'); } else { nm.value=''; ta.value=''; toast('Plano criado.'); renderPlans(gid,admin,panel); }
      }}});
      panel.appendChild(h('details',{class:'plan-new'},[ h('summary',{text:'+ Novo plano do grupo'}), h('div',{class:'cloud-card'},[nm, ta, add]) ]));
    }
    var r= await sb.from('group_plans').select('id,name,chapters,duration,created_at').eq('group_id',gid).order('created_at',{ascending:false});
    if(r.error){ panel.appendChild(h('p',{class:'read', text:'Não foi possível carregar os planos.'})); return; }
    if(!r.data.length){ panel.appendChild(h('p',{class:'read', text:'Nenhum plano ainda.'})); return; }
    for(var i=0;i<r.data.length;i++){ await renderOnePlan(r.data[i], gid, panel); }
  }

  async function renderOnePlan(plan, gid, panel){
    var wrap=h('section',{class:'group-plan'});
    wrap.appendChild(h('h3',{text:plan.name}));
    var prog= await sb.from('group_plan_progress').select('user_id,day_index').eq('plan_id',plan.id);
    var mine={}, counts={};
    if(!prog.error){ prog.data.forEach(function(p){ counts[p.day_index]=(counts[p.day_index]||0)+1; if(p.user_id===uid()) mine[p.day_index]=1; }); }
    var dias=plan.chapters||[];
    var ul=h('ul',{class:'plan-days'});
    dias.forEach(function(caps, idx){
      var cb=h('input',{type:'checkbox'}); if(mine[idx]) cb.checked=true;
      cb.addEventListener('change', async function(){
        if(cb.checked){
          var ins= await sb.from('group_plan_progress').insert({ plan_id:plan.id, user_id:uid(), day_index:idx });
          if(ins.error){ cb.checked=false; toast('Erro ao marcar.','err'); return; }
        } else {
          await sb.from('group_plan_progress').delete().eq('plan_id',plan.id).eq('user_id',uid()).eq('day_index',idx);
        }
        counts[idx]=(counts[idx]||0)+(cb.checked?1:-1); cnt.textContent=collLabel(counts[idx]);
      });
      var cnt=h('span',{class:'plan-count', text:collLabel(counts[idx]||0)});
      var label=caps.map(function(c){ return capLink(c); });
      var li=h('li',{class:'plan-day'},[ h('label',{},[cb, h('span',{class:'plan-day-n', text:'Dia '+(idx+1)+': '})].concat(interleave(label))), cnt ]);
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
    panel.appendChild(wrap);
  }
  function collLabel(n){ n=n||0; return n===0?'ninguém ainda':(n+(n===1?' leu':' leram')); }
  function interleave(nodes){ var out=[]; nodes.forEach(function(n,i){ if(i) out.push(' · '); out.push(n); }); return out; }
  function capLink(cap){
    // "João 1" -> link para o capítulo, se possível; senão texto
    var m=String(cap).match(/^(.*)\s+(\d+)$/);
    if(!m) return h('span',{text:cap});
    var slug=bookSlug(m[1]);
    return h('a',{href:url('ler/'+slug+'/'+m[2]+'/'), text:cap});
  }
  function bookSlug(name){
    return String(name).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'');
  }

  // ---------- DISCUSSÕES do grupo (fórum) ----------
  var discChan=null, topicChan=null;
  async function renderDiscussions(gid, ctx, panel){
    if(discChan){ try{ sb.removeChannel(discChan); }catch(e){} discChan=null; }
    if(topicChan){ try{ sb.removeChannel(topicChan); }catch(e){} topicChan=null; }
    // novo tópico
    var tt=h('input',{type:'text', placeholder:'Título do tópico', maxlength:'140'});
    var tb=h('textarea',{rows:'3', placeholder:'Escreva o primeiro comentário (opcional)'});
    var addT=h('button',{class:'btn primary', type:'button', text:'Abrir discussão', on:{click:async function(){
      var title=(tt.value||'').trim(); if(title.length<2){ toast('Dê um título ao tópico.','err'); return; }
      addT.disabled=true;
      var r= await sb.rpc('create_topic',{ p_group_id:gid, p_title:title, p_body:(tb.value||'').trim() });
      addT.disabled=false;
      if(r.error){ toast(rpcMsg(r.error,'Erro ao criar tópico.'),'err'); } else { tt.value=''; tb.value=''; toast('Discussão criada.'); renderDiscussions(gid,ctx,panel); }
    }}});
    panel.appendChild(h('details',{class:'plan-new'},[ h('summary',{text:'+ Nova discussão'}), h('div',{class:'cloud-card'},[tt, tb, addT]) ]));
    var listWrap=h('div',{}); panel.appendChild(listWrap);
    await loadTopics(gid, ctx, listWrap);
    discChan = sb.channel('disc-'+gid)
      .on('postgres_changes',{event:'*',schema:'public',table:'group_topics',filter:'group_id=eq.'+gid}, function(){ loadTopics(gid, ctx, listWrap); })
      .subscribe();
  }
  async function loadTopics(gid, ctx, listWrap){
    var r= await sb.from('group_topics').select('id,title,pinned,locked,created_at,updated_at,user_id,profiles(name)')
      .eq('group_id',gid).order('pinned',{ascending:false}).order('updated_at',{ascending:false}).limit(80);
    clear(listWrap);
    if(r.error){ listWrap.appendChild(h('p',{class:'read', text:'Não foi possível carregar as discussões.'})); return; }
    if(!r.data.length){ listWrap.appendChild(h('p',{class:'read', text:'Nenhuma discussão ainda. Abra a primeira.'})); return; }
    var ul=h('ul',{class:'topic-list'});
    r.data.forEach(function(t){
      ul.appendChild(h('li',{class:'topic'+(t.pinned?' pinned':'')},[
        h('button',{class:'topic-open', type:'button', on:{click:function(){ openTopic(t, gid, ctx, listWrap); }}},[
          t.pinned?h('span',{class:'topic-flag', text:'📌'}):null,
          t.locked?h('span',{class:'topic-flag', text:'🔒'}):null,
          h('span',{class:'topic-title', text:t.title})
        ]),
        h('span',{class:'topic-meta', text:'por '+((t.profiles&&t.profiles.name)||'Membro')+' · '+fmtDate(t.updated_at)})
      ]));
    });
    listWrap.appendChild(ul);
  }
  async function openTopic(t, gid, ctx, listWrap){
    clear(listWrap);
    listWrap.appendChild(h('button',{class:'btn-mini', type:'button', text:'← voltar', on:{click:function(){ if(topicChan){ try{ sb.removeChannel(topicChan); }catch(e){} topicChan=null; } loadTopics(gid, ctx, listWrap); }}}));
    var head=h('div',{class:'topic-head'},[ h('h3',{text:t.title}) ]);
    if(ctx.mod){
      head.appendChild(h('span',{class:'topic-mod'},[
        h('button',{class:'btn-mini', type:'button', text:t.pinned?'Desafixar':'Fixar', on:{click:async function(){ var r=await sb.rpc('moderate_topic',{p_topic_id:t.id,p_pin:!t.pinned,p_lock:null,p_delete:false}); if(!r.error){ t.pinned=!t.pinned; toast('Atualizado.'); } }}}),
        h('button',{class:'btn-mini', type:'button', text:t.locked?'Destrancar':'Trancar', on:{click:async function(){ var r=await sb.rpc('moderate_topic',{p_topic_id:t.id,p_pin:null,p_lock:!t.locked,p_delete:false}); if(!r.error){ t.locked=!t.locked; toast('Atualizado.'); } }}}),
        h('button',{class:'btn-mini', type:'button', text:'Apagar', on:{click:async function(){ if(!confirm('Apagar esta discussão?')) return; var r=await sb.rpc('moderate_topic',{p_topic_id:t.id,p_pin:null,p_lock:null,p_delete:true}); if(!r.error){ toast('Apagada.'); if(topicChan){ try{ sb.removeChannel(topicChan); }catch(e){} } loadTopics(gid,ctx,listWrap); } }}})
      ]));
    }
    listWrap.appendChild(head);
    var postsEl=h('div',{class:'post-list'}); listWrap.appendChild(postsEl);
    await loadPosts(t, gid, ctx, postsEl);
    // responder
    var rb=h('textarea',{rows:'2', placeholder: t.locked&&!ctx.mod?'Tópico trancado':'Responder…'});
    if(t.locked&&!ctx.mod) rb.disabled=true;
    var send=h('button',{class:'btn primary', type:'button', text:'Responder', on:{click:async function(){
      var body=(rb.value||'').trim(); if(!body){ return; }
      var r= await sb.rpc('add_post',{ p_topic_id:t.id, p_body:body });
      if(r.error){ toast(rpcMsg(r.error,'Erro ao responder.'),'err'); } else { rb.value=''; loadPosts(t, gid, ctx, postsEl); }
    }}});
    listWrap.appendChild(h('div',{class:'gn-form'},[ rb, h('div',{class:'cloud-row'},[send]) ]));
    if(topicChan){ try{ sb.removeChannel(topicChan); }catch(e){} }
    topicChan = sb.channel('topic-'+t.id)
      .on('postgres_changes',{event:'*',schema:'public',table:'topic_posts',filter:'topic_id=eq.'+t.id}, function(){ loadPosts(t, gid, ctx, postsEl); })
      .subscribe();
  }
  async function loadPosts(t, gid, ctx, postsEl){
    var r= await sb.from('topic_posts').select('id,body,created_at,user_id,profiles(name,account_type,is_beta)').eq('topic_id',t.id).order('created_at',{ascending:true});
    clear(postsEl);
    if(r.error){ postsEl.appendChild(h('p',{class:'read muted', text:'Não foi possível carregar as respostas.'})); return; }
    var ids=r.data.map(function(p){ return p.user_id; });
    var staff=await staffSet(ids);
    if(!r.data.length){ postsEl.appendChild(h('p',{class:'gn-empty', text:'Sem respostas ainda.'})); return; }
    r.data.forEach(function(p){
      var pr=p.profiles||{};
      var post=h('article',{class:'post'},[
        h('div',{class:'gn-meta'},[ h('strong',{text:pr.name||'Membro'}), renderBadges({ staff:!!staff[p.user_id], type:pr.account_type, beta:pr.is_beta!==false }), h('time',{text:fmtDate(p.created_at)}) ]),
        h('p',{class:'gn-body', text:p.body})
      ]);
      if(p.user_id===uid() || ctx.mod){
        post.appendChild(h('button',{class:'btn-mini', type:'button', text:'apagar', on:{click:async function(){ if(!confirm('Apagar resposta?')) return; var d=await sb.rpc('delete_post',{p_post_id:p.id}); if(!d.error){ loadPosts(t,gid,ctx,postsEl); } else { toast(rpcMsg(d.error,'Erro.'),'err'); } }}}));
      }
      postsEl.appendChild(post);
    });
  }

  // ---------- NOTAS do grupo no versículo ----------
  var verseChan=null;
  async function renderVerseNotes(vc){
    var slug=vc.getAttribute('data-slug'); if(!slug) return;
    var existing=document.getElementById('group-notes-block'); if(existing) existing.parentNode.removeChild(existing);
    if(!state.user) return;                 // deslogado: nada de nuvem (experiência atual intacta)
    var groups=activeGroups(); if(!groups.length) return;  // sem grupo: nada a mostrar
    var sec=h('section',{id:'group-notes-block', class:'group-notes-block', 'aria-label':'Notas do grupo'});
    sec.appendChild(h('h3',{class:'gn-title', text:'Notas do grupo'}));
    var listEl=h('div',{id:'gn-list'}); sec.appendChild(listEl);
    // form de nova nota
    var groupSel=null;
    if(groups.length>1){
      groupSel=h('select',{class:'gn-group'});
      groups.forEach(function(m){ groupSel.appendChild(h('option',{value:m.group_id, text:(m.groups&&m.groups.name)||'Grupo'})); });
    }
    var body=h('textarea',{rows:'3', placeholder:'Sua nota sobre este versículo (visível ao grupo)…'});
    var pub=h('button',{class:'btn primary', type:'button', text:'Publicar', on:{click:async function(){
      var txt=(body.value||'').trim(); if(!txt){ return; }
      var gid=groupSel?groupSel.value:groups[0].group_id;
      var r= await sb.from('group_notes').insert({ group_id:gid, user_id:uid(), verse_ref:slug, body:txt });
      if(r.error){ toast('Erro ao publicar: '+(r.error.message||''),'err'); } else { body.value=''; toast('Nota publicada.'); loadVerseNotes(slug, listEl, groups); }
    }}});
    var form=h('div',{class:'gn-form'},[ groupSel, body, h('div',{class:'cloud-row'},[pub]) ]);
    sec.appendChild(form);
    // injeta após a área de leitura do versículo
    var anchor=vc.querySelector('.verse-hero') || vc;
    anchor.parentNode.insertBefore(sec, anchor.nextSibling);
    await loadVerseNotes(slug, listEl, groups);
    // realtime
    if(verseChan){ try{ sb.removeChannel(verseChan); }catch(e){} }
    verseChan = sb.channel('vn-'+slug)
      .on('postgres_changes',{event:'*',schema:'public',table:'group_notes',filter:'verse_ref=eq.'+slug}, function(){ loadVerseNotes(slug, listEl, groups); })
      .subscribe();
  }

  async function loadVerseNotes(slug, listEl, groups){
    var gids=groups.map(function(m){ return m.group_id; });
    var r= await sb.from('group_notes')
      .select('id,body,created_at,user_id,group_id,profiles(name,account_type,is_beta),groups(name)')
      .eq('verse_ref',slug).in('group_id',gids).order('created_at',{ascending:true});
    clear(listEl);
    if(r.error){ listEl.appendChild(h('p',{class:'read muted', text:'Não foi possível carregar as notas do grupo.'})); return; }
    if(!r.data.length){ listEl.appendChild(h('p',{class:'gn-empty', text:'Nenhuma nota do grupo neste versículo ainda. Seja o primeiro.'})); return; }
    var staff=await staffSet(r.data.map(function(n){ return n.user_id; }));
    r.data.forEach(function(n){
      var pr=n.profiles||{};
      var who=pr.name||'Membro';
      var gname=(n.groups&&n.groups.name)||'';
      var card=h('article',{class:'gn-note'});
      card.appendChild(h('div',{class:'gn-meta'},[ h('strong',{text:who}),
        renderBadges({ staff:!!staff[n.user_id], type:pr.account_type, beta:pr.is_beta!==false }),
        gname?h('span',{class:'gn-group-tag', text:gname}):null, h('time',{text:fmtDate(n.created_at)}) ]));
      card.appendChild(h('p',{class:'gn-body', text:n.body}));
      if(n.user_id===uid() || canModerate(n.group_id)){
        card.appendChild(h('button',{class:'btn-mini', type:'button', text:'apagar', on:{click:async function(){
          if(!confirm('Apagar esta nota?')) return;
          var d= await sb.from('group_notes').delete().eq('id',n.id);
          if(!d.error){ loadVerseNotes(slug, listEl, groups); } else { toast('Erro ao apagar.','err'); }
        }}}));
      }
      // comentários
      var thread=h('div',{class:'gn-thread', hidden:'hidden'});
      var toggle=h('button',{class:'btn-mini gn-comment-toggle', type:'button', text:'comentários', on:{click:function(){
        if(thread.hasAttribute('hidden')){ thread.removeAttribute('hidden'); loadComments(n.id, thread); } else { thread.setAttribute('hidden','hidden'); }
      }}});
      card.appendChild(toggle); card.appendChild(thread);
      listEl.appendChild(card);
    });
  }

  async function loadComments(noteId, thread){
    clear(thread);
    var r= await sb.from('note_comments').select('id,body,created_at,user_id,profiles(name)').eq('note_id',noteId).order('created_at',{ascending:true});
    if(!r.error){
      r.data.forEach(function(c){
        var who=(c.profiles&&c.profiles.name)||'Membro';
        thread.appendChild(h('div',{class:'gn-comment'},[ h('strong',{text:who+': '}), h('span',{text:c.body}),
          c.user_id===uid()?h('button',{class:'btn-mini', type:'button', text:'×', title:'apagar', on:{click:async function(){ await sb.from('note_comments').delete().eq('id',c.id); loadComments(noteId,thread); }}}):null ]));
      });
    }
    var inp=h('input',{type:'text', placeholder:'Comentar…', class:'gn-comment-input'});
    inp.addEventListener('keydown', async function(e){
      if(e.key==='Enter'){ var t=(inp.value||'').trim(); if(!t) return; var ins= await sb.from('note_comments').insert({ note_id:noteId, user_id:uid(), body:t }); if(!ins.error){ inp.value=''; loadComments(noteId,thread); } else { toast('Erro ao comentar.','err'); } }
    });
    thread.appendChild(inp);
  }

  function rpcMsg(e, fallback){ var m=(e&&(e.message||e.error_description||e.hint))||''; if(/function .* does not exist|404|not found/i.test(m)) return 'Recurso ainda não disponível no servidor.'; return m||fallback; }

  // ---------- COLABORAÇÃO BETA: sugerir correção ----------
  function injectSuggest(vc){
    if(!state.user || document.getElementById('suggest-btn')) return;
    var slug=vc.getAttribute('data-slug')||'';
    var btn=h('button',{id:'suggest-btn', class:'btn-mini suggest-btn', type:'button', text:'Sugerir correção', on:{click:function(){ openSuggest(slug); }}});
    var anchor=vc.querySelector('.verse-hero')||vc;
    anchor.appendChild(btn);
  }
  function openSuggest(slug){
    var ta=h('textarea',{rows:'4', placeholder:'Descreva o erro ou a sugestão para este versículo…'});
    var back=h('div',{class:'modal-back'});
    function close(){ if(back.parentNode) back.parentNode.removeChild(back); }
    var send=h('button',{class:'btn primary', type:'button', text:'Enviar', on:{click:async function(){
      var body=(ta.value||'').trim(); if(body.length<3){ toast('Escreva sua sugestão.','err'); return; }
      send.disabled=true;
      var r= await sb.rpc('submit_suggestion',{ p_kind:'correcao', p_verse_ref:slug, p_page_url:location.pathname, p_body:body });
      send.disabled=false;
      if(r.error){ toast(rpcMsg(r.error,'Erro ao enviar.'),'err'); } else { toast('Obrigado! Sua sugestão foi enviada para revisão.'); close(); }
    }}});
    back.appendChild(h('div',{class:'suggest-modal'},[
      h('h3',{text:'Sugerir correção'}),
      h('p',{class:'read', text:'Sua contribuição (beta) vai para a fila de revisão da equipe. Obrigado por ajudar a melhorar o site.'}),
      ta, h('div',{class:'cloud-row'},[ send, h('button',{class:'btn ghost', type:'button', text:'Cancelar', on:{click:close}}) ])
    ]));
    back.addEventListener('click', function(e){ if(e.target===back) close(); });
    document.body.appendChild(back);
  }

  // ---------- EQUIPE (staff): fila de sugestões ----------
  async function renderTeam(){
    var app=document.getElementById('equipe-app'); if(!app) return; clear(app);
    if(!state.user){ app.appendChild(h('div',{class:'cloud-card'},[h('p',{class:'read', text:'Entre na sua conta.'}), h('a',{class:'btn primary', href:url('conta/'), text:'Entrar'})])); return; }
    if(!state.isStaff){ app.appendChild(h('div',{class:'cloud-card'},[h('h2',{text:'Acesso restrito'}), h('p',{class:'read', text:'Esta área é da equipe do site.'})])); return; }
    app.appendChild(h('p',{class:'read muted', text:'Fila de sugestões e correções enviadas pela comunidade (beta).'}));
    var listEl=h('div',{class:'team-queue'}); app.appendChild(listEl);
    await loadTeamQueue(listEl);
  }
  async function loadTeamQueue(listEl){
    var r= await sb.from('suggestions').select('id,kind,verse_ref,page_url,body,status,created_at,profiles(name)').order('created_at',{ascending:false}).limit(100);
    clear(listEl);
    if(r.error){ listEl.appendChild(h('p',{class:'read', text:'Não foi possível carregar a fila.'})); return; }
    if(!r.data.length){ listEl.appendChild(h('p',{class:'read', text:'Nenhuma sugestão por enquanto.'})); return; }
    r.data.forEach(function(s){
      var who=(s.profiles&&s.profiles.name)||'Usuário';
      var card=h('article',{class:'team-item status-'+(s.status||'pendente')},[
        h('div',{class:'gn-meta'},[ h('strong',{text:who}), h('span',{class:'tag', text:s.kind==='correcao'?'correção':'sugestão'}),
          s.verse_ref?h('a',{class:'gn-group-tag', href:url('versiculos/'+s.verse_ref+'/'), text:s.verse_ref}):null,
          h('span',{class:'tag', text:s.status||'pendente'}), h('time',{text:fmtDate(s.created_at)}) ]),
        h('p',{class:'gn-body', text:s.body})
      ]);
      if(s.status==='pendente'){
        card.appendChild(h('div',{class:'cloud-row'},[
          h('button',{class:'btn-mini ok', type:'button', text:'Aprovar', on:{click:async function(){ var u=await sb.rpc('review_suggestion',{p_id:s.id,p_status:'aprovada'}); if(!u.error){ loadTeamQueue(listEl); } }}}),
          h('button',{class:'btn-mini', type:'button', text:'Descartar', on:{click:async function(){ var u=await sb.rpc('review_suggestion',{p_id:s.id,p_status:'descartada'}); if(!u.error){ loadTeamQueue(listEl); } }}})
        ]));
      }
      listEl.appendChild(card);
    });
  }

  // ---------- BOOT ----------
  async function refresh(){
    await loadProfile();
    await loadStaffFlag();
    await loadMemberships();
    await route();
  }
  sb.auth.onAuthStateChange(function(evt, session){
    state.user = session ? session.user : null;
    refresh();
  });
  // dispara render inicial mesmo sem evento (sessão já resolvida)
  sb.auth.getSession().then(function(res){
    state.user = res && res.data && res.data.session ? res.data.session.user : null;
    refresh();
  });
})();
