// Comunidade: Salas de Estudo reais (tabela `groups` + RPCs do Supabase).
//
// Roda apenas na pagina /comunidade/salas/ (procura [data-community-app]).
// Usa o cliente/usuario expostos por auth.js em window.BEC_ACCOUNT. Sem login
// ou sem Supabase, mostra um convite para entrar — nunca quebra a pagina.
//
// Permissoes (espelham as RPCs no banco, ver docs/gamification.md e o schema):
//  - criar sala: qualquer usuario logado (limite de 3 por conta, exceto staff)
//  - entrar: por codigo de convite (fica "pendente" ate aprovacao do admin)
//  - criar topico / responder: qualquer membro ativo
//  - aprovar/recusar, definir papel, remover: admin da sala (ou staff)
(function(){
  'use strict';
  var root=document.querySelector('[data-community-app]');
  if(!root) return;

  // ---- Bridge de conta ----------------------------------------------------
  function acc(){return window.BEC_ACCOUNT||null;}
  function sb(){var a=acc();return a&&a.client?a.client:null;}
  function uid(){var a=acc();return a&&a.user?a.user.id:null;}
  function loggedIn(){return !!(sb()&&uid());}

  // ---- Utilitarios --------------------------------------------------------
  function esc(s){return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function when(ts){try{return new Date(ts).toLocaleDateString('pt-BR');}catch(e){return '';}}
  function roleLabel(r){return r==='admin'?'Admin':r==='moderator'?'Moderador':'Membro';}

  var state={view:'list', room:null, rooms:[], members:[], topics:[], topic:null, posts:[], busy:false, loading:false, msg:'', err:''};
  var lastLoad=null; // ultima carga de leitura, para o botao "Tentar de novo"

  function flash(msg, isErr){state.msg=isErr?'':msg; state.err=isErr?msg:''; render();}
  // Leituras nao podem falhar em silencio: sem isto, um erro de rede vira
  // um falso "voce nao tem salas".
  function need(r){
    if(r&&r.error) throw r.error;
    return (r&&r.data)||[];
  }
  function loadFailed(){
    state.loading=false;
    state.err='Não foi possível carregar agora. Verifique a conexão e tente de novo.';
    render();
  }
  function copyCode(code, el){
    (navigator.clipboard?navigator.clipboard.writeText(code):Promise.reject())
      .then(function(){ if(el) el.textContent='Copiado!'; setTimeout(function(){ if(el) el.textContent='Copiar código'; },1400); })
      .catch(function(){
        try{
          var t=document.createElement('textarea'); t.value=code; document.body.appendChild(t);
          t.select(); document.execCommand('copy'); t.remove();
          if(el) el.textContent='Copiado!'; setTimeout(function(){ if(el) el.textContent='Copiar código'; },1400);
        }catch(e){}
      });
  }

  // ---- Camada de dados (leituras diretas com RLS) -------------------------
  function myRooms(){
    return sb().from('group_members')
      .select('id,role,status,group_id,groups(name,description,invite_code,created_by)')
      .eq('user_id', uid());
  }
  function roomMembers(gid){
    return sb().from('group_members')
      .select('id,user_id,role,status,profiles(name)')
      .eq('group_id', gid).order('status').order('role');
  }
  function roomTopics(gid){
    return sb().from('group_topics')
      .select('id,title,body,pinned,locked,created_at,user_id,profiles(name)')
      .eq('group_id', gid)
      .order('pinned',{ascending:false}).order('created_at',{ascending:false});
  }
  function topicPosts(tid){
    return sb().from('topic_posts')
      .select('id,body,created_at,user_id,profiles(name)')
      .eq('topic_id', tid).order('created_at',{ascending:true});
  }

  // ---- RPCs ---------------------------------------------------------------
  function rpc(name, args){return sb().rpc(name, args);}

  // ---- Navegacao ----------------------------------------------------------
  async function goList(){
    lastLoad=goList;
    state.view='list'; state.room=null; state.topic=null; state.err='';
    if(loggedIn()){
      state.loading=true;
      render();
      try{
        state.rooms=need(await myRooms());
      }catch(e){ loadFailed(); return; }
      state.loading=false;
    }
    render();
  }
  async function openRoom(membership){
    lastLoad=function(){ openRoom(membership); };
    state.view='room'; state.room=membership; state.topic=null; state.err='';
    state.loading=true;
    render(); // mostra esqueleto enquanto carrega
    var gid=membership.group_id;
    try{
      state.members=need(await roomMembers(gid));
      state.topics=need(await roomTopics(gid));
    }catch(e){ loadFailed(); return; }
    state.loading=false;
    render();
  }
  async function openTopic(topic){
    lastLoad=function(){ openTopic(topic); };
    state.view='topic'; state.topic=topic; state.err='';
    state.loading=true;
    render();
    try{
      state.posts=need(await topicPosts(topic.id));
    }catch(e){ loadFailed(); return; }
    state.loading=false;
    render();
  }

  function myRole(){return state.room?state.room.role:null;}
  function isAdmin(){return myRole()==='admin';}

  // ---- Acoes --------------------------------------------------------------
  async function withBusy(fn){
    if(state.busy) return; state.busy=true; render();
    try{ await fn(); }catch(e){ state.err=(e&&e.message)||'Algo deu errado.'; }
    state.busy=false; render();
  }
  function award(key){try{if(window.BEC_GAME&&window.BEC_GAME.grant) window.BEC_GAME.grant(key);}catch(e){}}

  async function actCreateRoom(name, desc){
    await withBusy(async function(){
      var r=await rpc('create_group',{p_name:name, p_description:desc});
      if(r.error) throw r.error;
      award('comunidade');
      await goList();
      flash('Sala criada. Compartilhe o codigo de convite com o grupo.');
    });
  }
  async function actJoin(code){
    await withBusy(async function(){
      var r=await rpc('join_group',{p_code:code});
      if(r.error) throw r.error;
      award('comunidade');
      await goList();
      var st=(r.data&&r.data[0]&&r.data[0].status)||'pending';
      flash(st==='active'?'Voce entrou na sala.':'Pedido enviado. Aguarde a aprovacao do admin.');
    });
  }
  async function actCreateTopic(title, body){
    await withBusy(async function(){
      var r=await rpc('create_topic',{p_group_id:state.room.group_id, p_title:title, p_body:body});
      if(r.error) throw r.error;
      var t=await roomTopics(state.room.group_id); state.topics=(t&&t.data)||[];
      flash('Discussao criada.');
    });
  }
  async function actPost(body){
    await withBusy(async function(){
      var r=await rpc('add_post',{p_topic_id:state.topic.id, p_body:body});
      if(r.error) throw r.error;
      var p=await topicPosts(state.topic.id); state.posts=(p&&p.data)||[];
    });
  }
  async function actDecide(memberId, approve){
    await withBusy(async function(){
      var r=await rpc('decide_member',{p_member_id:memberId, p_approve:approve});
      if(r.error) throw r.error;
      var m=await roomMembers(state.room.group_id); state.members=(m&&m.data)||[];
    });
  }
  async function actSetRole(memberId, role){
    await withBusy(async function(){
      var r=await rpc('set_member_role',{p_member_id:memberId, p_role:role});
      if(r.error) throw r.error;
      var m=await roomMembers(state.room.group_id); state.members=(m&&m.data)||[];
    });
  }
  async function actRemove(memberId){
    await withBusy(async function(){
      var r=await rpc('remove_member',{p_member_id:memberId});
      if(r.error) throw r.error;
      var m=await roomMembers(state.room.group_id); state.members=(m&&m.data)||[];
    });
  }

  // ---- Renderizacao -------------------------------------------------------
  function banner(){
    var out='';
    if(state.err){
      out+='<p class="community-alert err">'+esc(state.err)+
        (lastLoad?' <button type="button" class="btn tiny" data-act="retry">Tentar de novo</button>':'')+'</p>';
    }
    if(state.msg) out+='<p class="community-alert ok">'+esc(state.msg)+'</p>';
    return out;
  }
  function loadingLine(msg){return '<p class="muted-line">'+esc(msg)+'</p>';}

  function viewSignedOut(){
    return '<div class="community-empty">'+
      '<h2>Salas de Estudo</h2>'+
      '<p>Entre na sua conta para criar salas, convidar pessoas pelo codigo e conduzir discussoes ligadas ao texto biblico.</p>'+
      '<button type="button" class="btn primary" data-auth-open>Entrar para participar</button>'+
    '</div>';
  }

  function roomCard(mb){
    var g=mb.groups||{};
    var pending=mb.status!=='active';
    var name=g.name || (pending?'Sala (aguardando aprovacao)':'Sala');
    return '<article class="room-card'+(pending?' pending':'')+'" '+(pending?'':'data-act="open" data-mid="'+esc(mb.id)+'"')+'>'+
      '<div class="room-card-top"><b>'+esc(name)+'</b><span class="role-pill role-'+esc(mb.role)+'">'+roleLabel(mb.role)+'</span></div>'+
      (g.description?'<p>'+esc(g.description)+'</p>':'')+
      '<span class="room-card-foot">'+(pending?'Pendente de aprovacao':'Abrir sala →')+'</span>'+
    '</article>';
  }

  function viewList(){
    var rooms=state.rooms||[];
    var cards=state.loading
      ? loadingLine('Carregando suas salas…')
      : rooms.length
        ? '<div class="room-grid">'+rooms.map(roomCard).join('')+'</div>'
        : '<p class="muted-line">Voce ainda nao participa de nenhuma sala. Crie a primeira ou entre por um codigo.</p>';
    return banner()+
      '<section class="community-block"><h2>Minhas salas</h2>'+cards+'</section>'+
      '<div class="community-forms">'+
        '<form class="community-form" data-form="create">'+
          '<h3>Criar uma sala</h3>'+
          '<label>Nome da sala<input name="name" maxlength="80" required placeholder="Ex.: Evangelho de Joao"></label>'+
          '<label>Descricao (opcional)<textarea name="desc" maxlength="500" rows="2" placeholder="Tema, plano ou objetivo do grupo"></textarea></label>'+
          '<button type="submit" class="btn primary"'+(state.busy?' disabled':'')+'>Criar sala</button>'+
        '</form>'+
        '<form class="community-form" data-form="join">'+
          '<h3>Entrar por codigo</h3>'+
          '<label>Codigo de convite<input name="code" maxlength="12" required placeholder="Ex.: a1b2c3d4"></label>'+
          '<button type="submit" class="btn ghost"'+(state.busy?' disabled':'')+'>Entrar</button>'+
          '<p class="muted-line">Peca o codigo a quem criou a sala. Voce entra como pendente ate um admin aprovar.</p>'+
        '</form>'+
      '</div>';
  }

  function memberRow(m){
    var name=(m.profiles&&m.profiles.name)||'Membro';
    var me=m.user_id===uid();
    var pending=m.status!=='active';
    var admin=isAdmin();
    var ctrls='';
    if(admin && pending){
      ctrls='<button type="button" class="btn tiny" data-act="approve" data-mid="'+esc(m.id)+'">Aprovar</button>'+
            '<button type="button" class="btn tiny ghost" data-act="reject" data-mid="'+esc(m.id)+'">Recusar</button>';
    }else if(admin && !me && m.role!=='admin'){
      ctrls=(m.role==='moderator'
              ? '<button type="button" class="btn tiny ghost" data-act="role" data-mid="'+esc(m.id)+'" data-role="member">Tirar mod</button>'
              : '<button type="button" class="btn tiny ghost" data-act="role" data-mid="'+esc(m.id)+'" data-role="moderator">Tornar mod</button>')+
            '<button type="button" class="btn tiny ghost" data-act="remove" data-mid="'+esc(m.id)+'">Remover</button>';
    }
    return '<li class="member-row'+(pending?' pending':'')+'">'+
      '<span class="member-name">'+esc(name)+(me?' (voce)':'')+'</span>'+
      '<span class="role-pill role-'+esc(m.role)+'">'+roleLabel(m.role)+(pending?' · pendente':'')+'</span>'+
      (ctrls?'<span class="member-ctrls">'+ctrls+'</span>':'')+
    '</li>';
  }

  function topicItem(t){
    var name=(t.profiles&&t.profiles.name)||'Membro';
    return '<li class="topic-item" data-act="topic" data-tid="'+esc(t.id)+'">'+
      (t.pinned?'<span class="topic-flag">📌</span>':'')+
      (t.locked?'<span class="topic-flag">🔒</span>':'')+
      '<b>'+esc(t.title)+'</b>'+
      '<span class="topic-meta">'+esc(name)+' · '+when(t.created_at)+'</span>'+
    '</li>';
  }

  function viewRoom(){
    var g=state.room.groups||{};
    var admin=isAdmin();
    var pendings=(state.members||[]).filter(function(m){return m.status!=='active';});
    var head='<div class="community-head">'+
      '<button type="button" class="btn tiny ghost" data-act="back">← Minhas salas</button>'+
      '<h2>'+esc(g.name||'Sala')+'</h2>'+
      (g.description?'<p class="room-desc">'+esc(g.description)+'</p>':'')+
      (g.invite_code&&state.room.status==='active'
        ? '<p class="invite">Codigo de convite: <code>'+esc(g.invite_code)+'</code> '+
          '<button type="button" class="btn tiny ghost" data-act="copy-code" data-code="'+esc(g.invite_code)+'">Copiar código</button> '+
          '<span>novos membros entram como pendentes ate um admin aprovar</span></p>'
        : '')+
    '</div>';

    if(state.loading) return banner()+head+loadingLine('Carregando participantes e discussoes…');

    var membersHtml='<section class="community-block"><h3>Participantes'+
      (admin&&pendings.length?' <span class="pending-count">'+pendings.length+' pendente(s)</span>':'')+
      '</h3><ul class="member-list">'+
      (state.members||[]).map(memberRow).join('')+'</ul></section>';

    var topicsHtml='<section class="community-block"><h3>Discussoes</h3>'+
      ((state.topics&&state.topics.length)
        ? '<ul class="topic-list">'+state.topics.map(topicItem).join('')+'</ul>'
        : '<p class="muted-line">Ainda nao ha discussoes. Comece a primeira abaixo.</p>')+
      '<form class="community-form" data-form="topic">'+
        '<label>Nova discussao<input name="title" maxlength="140" required placeholder="Titulo (ex.: Contexto de Joao 1)"></label>'+
        '<textarea name="body" maxlength="5000" rows="2" placeholder="Abra a conversa (opcional)"></textarea>'+
        '<button type="submit" class="btn primary"'+(state.busy?' disabled':'')+'>Criar discussao</button>'+
      '</form></section>';

    return banner()+head+membersHtml+topicsHtml;
  }

  function postItem(p){
    var name=(p.profiles&&p.profiles.name)||'Membro';
    return '<li class="post-item"><div class="post-meta">'+esc(name)+' · '+when(p.created_at)+'</div>'+
      '<div class="post-body">'+esc(p.body).replace(/\n/g,'<br>')+'</div></li>';
  }

  function viewTopic(){
    var t=state.topic;
    var locked=t.locked && !(isAdmin()||myRole()==='moderator');
    var head='<div class="community-head">'+
      '<button type="button" class="btn tiny ghost" data-act="back-room">← '+esc((state.room.groups&&state.room.groups.name)||'Sala')+'</button>'+
      '<h2>'+esc(t.title)+(t.locked?' 🔒':'')+'</h2>'+
      (t.body?'<p class="topic-body">'+esc(t.body).replace(/\n/g,'<br>')+'</p>':'')+
    '</div>';
    var posts=state.loading
      ? loadingLine('Carregando respostas…')
      : (state.posts&&state.posts.length)
        ? '<ul class="post-list">'+state.posts.map(postItem).join('')+'</ul>'
        : '<p class="muted-line">Seja o primeiro a responder.</p>';
    var form=locked
      ? '<p class="muted-line">Discussao trancada por um moderador.</p>'
      : '<form class="community-form" data-form="post">'+
          '<textarea name="body" maxlength="5000" rows="3" required placeholder="Escreva sua resposta"></textarea>'+
          '<button type="submit" class="btn primary"'+(state.busy?' disabled':'')+'>Responder</button>'+
        '</form>';
    return banner()+head+'<section class="community-block">'+posts+form+'</section>';
  }

  function render(){
    if(!loggedIn()){ root.innerHTML=viewSignedOut(); return; }
    if(state.view==='room' && state.room) root.innerHTML=viewRoom();
    else if(state.view==='topic' && state.topic) root.innerHTML=viewTopic();
    else root.innerHTML=viewList();
  }

  // ---- Eventos ------------------------------------------------------------
  root.addEventListener('click', function(e){
    var el=e.target.closest('[data-act]'); if(!el) return;
    var act=el.getAttribute('data-act');
    if(act==='open'){
      var mb=(state.rooms||[]).filter(function(r){return r.id===el.getAttribute('data-mid');})[0];
      if(mb) openRoom(mb);
    }else if(act==='topic'){
      var t=(state.topics||[]).filter(function(x){return x.id===el.getAttribute('data-tid');})[0];
      if(t) openTopic(t);
    }else if(act==='back'){ goList(); }
    else if(act==='retry'){ if(lastLoad) lastLoad(); }
    else if(act==='copy-code'){ copyCode(el.getAttribute('data-code')||'', el); }
    else if(act==='back-room'){ state.view='room'; state.topic=null; render(); }
    else if(act==='approve'){ actDecide(el.getAttribute('data-mid'), true); }
    else if(act==='reject'){ actDecide(el.getAttribute('data-mid'), false); }
    else if(act==='role'){ actSetRole(el.getAttribute('data-mid'), el.getAttribute('data-role')); }
    else if(act==='remove'){ actRemove(el.getAttribute('data-mid')); }
  });

  root.addEventListener('submit', function(e){
    var form=e.target.closest('[data-form]'); if(!form) return;
    e.preventDefault();
    var kind=form.getAttribute('data-form');
    var d=new FormData(form);
    if(kind==='create'){ actCreateRoom((d.get('name')||'').trim(), (d.get('desc')||'').trim()); }
    else if(kind==='join'){ actJoin((d.get('code')||'').trim().toLowerCase()); }
    else if(kind==='topic'){ actCreateTopic((d.get('title')||'').trim(), (d.get('body')||'').trim()); }
    else if(kind==='post'){ var b=(d.get('body')||'').trim(); if(b) actPost(b); }
  });

  // Reage a login/logout.
  document.addEventListener('bec:account', function(){ goList(); });

  // Estado inicial.
  goList();
})();
