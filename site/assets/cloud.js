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
  var state = { user:null, profile:null, memberships:[] };
  window.BEC_CLOUD = { sb: sb, state: state };
  function uid(){ return state.user ? state.user.id : null; }
  function activeGroups(){ return state.memberships.filter(function(m){ return m.status==='active'; }); }
  function isAdminOf(gid){ return state.memberships.some(function(m){ return m.group_id===gid && m.status==='active' && m.role==='admin'; }); }
  function membershipByCode(code){ return state.memberships.filter(function(m){ return m.groups && m.groups.invite_code===code; })[0]; }

  async function loadProfile(){
    if(!uid()){ state.profile=null; return; }
    try {
      var r = await sb.from('profiles').select('id,name,avatar_url').eq('id', uid()).maybeSingle();
      state.profile = r.data || null;
      // 1º acesso: se o trigger não preencheu o nome (ex.: e-mail já existia antes),
      // aplica o lembrete local digitado no cadastro.
      if(state.profile && !((state.profile.name||'').trim())){
        var hint=nameHint();
        if(hint){ var u= await sb.from('profiles').update({name:hint}).eq('id', uid()); if(!u.error) state.profile.name=hint; }
      }
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
  }

  // ---------- ROTEAMENTO ----------
  async function route(){
    updateNav();
    if(document.getElementById('conta-app')) await renderAccount();
    if(document.getElementById('grupos-app')) await renderGroupsIndex();
    if(document.getElementById('form-create-group')) initCreateGroup();
    if(document.getElementById('grupo-detail')) await renderGroupDetail();
    var vc = document.querySelector('.verse-cont[data-slug]');
    if(vc) await renderVerseNotes(vc);
  }

  // ---------- CONTA ----------
  async function renderAccount(){
    var app=document.getElementById('conta-app'); if(!app) return; clear(app);
    if(!state.user){
      var nameI = h('input',{type:'text', id:'login-name', placeholder:'Como quer ser chamado(a)', autocomplete:'name', value:nameHint()});
      var email = h('input',{type:'email', id:'login-email', placeholder:'voce@email.com', autocomplete:'email'});
      var btn = h('button',{class:'btn primary', type:'button', text:'Enviar link de acesso', on:{click:async function(){
        var v=(email.value||'').trim();
        var nm=(nameI.value||'').trim();
        if(!v || v.indexOf('@')<0){ toast('Digite um e-mail válido.','err'); return; }
        btn.disabled=true; btn.textContent='Enviando…';
        try {
          // nome vai como metadado do usuário; o trigger handle_new_user o copia
          // para profiles.name no 1º acesso. Guardamos também um lembrete local
          // (fallback) caso o e-mail já existisse antes.
          if(nm) setNameHint(nm);
          var r= await sb.auth.signInWithOtp({ email:v, options:{ emailRedirectTo: url('conta/'), data: nm?{ name:nm }:undefined } });
          if(r.error) throw r.error;
          clear(app); app.appendChild(h('div',{class:'cloud-card'},[
            h('h2',{text:'Verifique seu e-mail'}),
            h('p',{class:'read', text:'Enviamos um link de acesso para '+v+'. Abra no mesmo aparelho para entrar — sem senha.'})
          ]));
        } catch(e){ toast('Não foi possível enviar: '+(e.message||e),'err'); btn.disabled=false; btn.textContent='Enviar link de acesso'; }
      }}});
      app.appendChild(h('div',{class:'cloud-card'},[
        h('h2',{text:'Entrar ou criar conta'}),
        h('p',{class:'read', text:'A leitura da Bíblia continua livre, sem conta. A conta serve só para os grupos de estudo: você recebe um link mágico no e-mail (sem senha) e pronto.'}),
        h('label',{class:'cloud-label', for:'login-name', text:'Seu nome'}),
        nameI,
        h('label',{class:'cloud-label', for:'login-email', text:'E-mail'}),
        email, btn
      ]));
      return;
    }
    // logado
    var nameInput = h('input',{type:'text', id:'profile-name', value:(state.profile&&state.profile.name)||'', placeholder:'Seu nome'});
    var saveBtn = h('button',{class:'btn ghost', type:'button', text:'Salvar nome', on:{click:async function(){
      var nm=(nameInput.value||'').trim();
      var r= await sb.from('profiles').update({name:nm}).eq('id', uid());
      if(r.error){ toast('Erro ao salvar.','err'); } else { state.profile=state.profile||{}; state.profile.name=nm; updateNav(); toast('Nome salvo.'); }
    }}});
    var out = h('button',{class:'btn', type:'button', text:'Sair', on:{click:async function(){ await sb.auth.signOut(); location.reload(); }}});
    app.appendChild(h('div',{class:'cloud-card'},[
      h('h2',{text:'Minha conta'}),
      h('p',{class:'read', text:state.user.email||''}),
      h('label',{class:'cloud-label', for:'profile-name', text:'Nome de exibição'}),
      nameInput, h('div',{class:'cloud-row'},[saveBtn, out])
    ]));
    app.appendChild(h('div',{class:'cloud-card'},[
      h('h2',{text:'Meus grupos'}),
      h('p',{class:'read', text:'Veja, crie e entre em grupos de estudo na página de grupos.'}),
      h('a',{class:'btn primary', href:url('grupos/'), text:'Ir para Grupos'})
    ]));
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
    app.appendChild(h('div',{class:'cloud-actions'},[
      h('a',{class:'btn primary', href:url('grupos/novo/'), text:'+ Criar grupo'}),
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
    form.addEventListener('submit', async function(e){
      e.preventDefault();
      var name=(form.querySelector('[name=name]').value||'').trim();
      var desc=(form.querySelector('[name=description]').value||'').trim();
      if(!name){ toast('Dê um nome ao grupo.','err'); return; }
      var btn=form.querySelector('button[type=submit]'); btn.disabled=true;
      // id + código gerados no cliente => evita ler de volta (RLS) logo após criar
      var gid = (window.crypto&&crypto.randomUUID)?crypto.randomUUID():('g'+Date.now()+Math.random().toString(16).slice(2));
      var code = gid.replace(/-/g,'').slice(0,8);
      try {
        var r1= await sb.from('groups').insert({ id:gid, name:name, description:desc, invite_code:code, created_by:uid() });
        if(r1.error) throw r1.error;
        var r2= await sb.from('group_members').insert({ group_id:gid, user_id:uid(), role:'admin', status:'active' });
        if(r2.error) throw r2.error;
        await loadMemberships();
        location.href=url('grupos/grupo/?c='+code);
      } catch(e2){ toast('Erro ao criar grupo: '+(e2.message||e2),'err'); btn.disabled=false; }
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
    var g=mem.groups, gid=g.id, admin=isAdminOf(gid);
    root.appendChild(h('header',{class:'group-head'},[
      h('h1',{text:g.name}),
      g.description?h('p',{class:'read', text:g.description}):null,
      h('p',{class:'group-code'},['Código do convite: ', h('code',{text:g.invite_code}),
        h('button',{class:'btn-mini', type:'button', text:'copiar', on:{click:function(){ try{ navigator.clipboard.writeText(g.invite_code); toast('Código copiado.'); }catch(e){} }}})])
    ]));
    var tabs=h('div',{class:'tabs', role:'tablist'});
    var panel=h('div',{class:'tab-panel'});
    var defs=[['feed','Feed'],['membros','Membros'],['planos','Planos']];
    defs.forEach(function(d){
      tabs.appendChild(h('button',{class:'tab', type:'button', 'data-tab':d[0], text:d[1], on:{click:function(){
        Array.prototype.forEach.call(tabs.children,function(b){ b.classList.toggle('on', b.getAttribute('data-tab')===d[0]); });
        showTab(d[0], gid, g, admin, panel);
      }}}));
    });
    root.appendChild(tabs); root.appendChild(panel);
    tabs.children[0].classList.add('on');
    showTab('feed', gid, g, admin, panel);
    // realtime do grupo (feed)
    if(detailChan){ try{ sb.removeChannel(detailChan); }catch(e){} }
    detailChan = sb.channel('grp-'+gid)
      .on('postgres_changes',{event:'*',schema:'public',table:'activity_feed',filter:'group_id=eq.'+gid}, function(){
        var on=tabs.querySelector('.tab.on'); if(on && on.getAttribute('data-tab')==='feed') showTab('feed',gid,g,admin,panel);
      })
      .subscribe();
  }

  async function showTab(name, gid, g, admin, panel){
    clear(panel);
    if(name==='feed') return renderFeed(gid, panel);
    if(name==='membros') return renderMembers(gid, admin, panel);
    if(name==='planos') return renderPlans(gid, admin, panel);
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
    if(ev.event_type==='joined_group') return 'entrou no grupo.';
    return ev.event_type;
  }
  function refLabel(slug){ return slug; }

  async function renderMembers(gid, admin, panel){
    var r= await sb.from('group_members').select('id,role,status,user_id,profiles(name)').eq('group_id',gid).order('status',{ascending:true});
    if(r.error){ panel.appendChild(h('p',{class:'read', text:'Não foi possível carregar os membros.'})); return; }
    var pend=r.data.filter(function(m){ return m.status==='pending'; });
    var act=r.data.filter(function(m){ return m.status==='active'; });
    if(admin && pend.length){
      var pl=h('ul',{class:'member-list'});
      pend.forEach(function(m){
        pl.appendChild(h('li',{class:'member pending'},[
          h('span',{text:(m.profiles&&m.profiles.name)||'(sem nome)'}),
          h('span',{class:'member-actions'},[
            h('button',{class:'btn-mini ok', type:'button', text:'Aprovar', on:{click:async function(){
              var u= await sb.from('group_members').update({status:'active'}).eq('id',m.id);
              if(u.error){ toast('Erro ao aprovar.','err'); } else { toast('Membro aprovado.'); renderMembers(gid,admin,panel); }
            }}}),
            h('button',{class:'btn-mini', type:'button', text:'Recusar', on:{click:async function(){
              var u= await sb.from('group_members').delete().eq('id',m.id);
              if(u.error){ toast('Erro.','err'); } else { renderMembers(gid,admin,panel); }
            }}})
          ])
        ]));
      });
      panel.appendChild(h('section',{},[h('h3',{text:'Pedidos pendentes'}), pl]));
    }
    var al=h('ul',{class:'member-list'});
    act.forEach(function(m){
      al.appendChild(h('li',{class:'member'},[
        h('span',{text:(m.profiles&&m.profiles.name)||'(sem nome)'}),
        m.role==='admin'?h('span',{class:'tag', text:'admin'}):null,
        (admin && m.user_id!==uid())?h('button',{class:'btn-mini', type:'button', text:'remover', on:{click:async function(){
          if(!confirm('Remover este membro?')) return;
          var u= await sb.from('group_members').delete().eq('id',m.id);
          if(!u.error){ renderMembers(gid,admin,panel); }
        }}}):null
      ]));
    });
    panel.appendChild(h('section',{},[h('h3',{text:'Membros ('+act.length+')'}), al]));
  }

  // ---------- PLANOS do grupo ----------
  async function renderPlans(gid, admin, panel){
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
      .select('id,body,created_at,user_id,group_id,profiles(name),groups(name)')
      .eq('verse_ref',slug).in('group_id',gids).order('created_at',{ascending:true});
    clear(listEl);
    if(r.error){ listEl.appendChild(h('p',{class:'read muted', text:'Não foi possível carregar as notas do grupo.'})); return; }
    if(!r.data.length){ listEl.appendChild(h('p',{class:'gn-empty', text:'Nenhuma nota do grupo neste versículo ainda. Seja o primeiro.'})); return; }
    r.data.forEach(function(n){
      var who=(n.profiles&&n.profiles.name)||'Membro';
      var gname=(n.groups&&n.groups.name)||'';
      var card=h('article',{class:'gn-note'});
      card.appendChild(h('div',{class:'gn-meta'},[ h('strong',{text:who}), gname?h('span',{class:'gn-group-tag', text:gname}):null, h('time',{text:fmtDate(n.created_at)}) ]));
      card.appendChild(h('p',{class:'gn-body', text:n.body}));
      if(n.user_id===uid()){
        card.appendChild(h('button',{class:'btn-mini', type:'button', text:'apagar', on:{click:async function(){
          if(!confirm('Apagar sua nota?')) return;
          var d= await sb.from('group_notes').delete().eq('id',n.id);
          if(!d.error){ loadVerseNotes(slug, listEl, groups); }
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

  // ---------- BOOT ----------
  async function refresh(){
    await loadProfile();
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
