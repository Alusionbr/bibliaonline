// Reportar erro / sugestao (usuarios logados). Reusa o RPC submit_suggestion
// (SECURITY DEFINER, exige login) e review_suggestion (staff) do Supabase.
//  - Deslogado: convida a entrar.
//  - Falha de rede: guarda em bec.pendingReports e reenvia numa proxima visita.
(function(){
  'use strict';

  function esc(s){return (s==null?'':String(s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function client(){var a=window.BEC_ACCOUNT; return a&&a.client?a.client:null;}
  function loggedIn(){var a=window.BEC_ACCOUNT; return !!(a&&a.client&&a.user);}
  function userId(){var a=window.BEC_ACCOUNT; return a&&a.user?a.user.id:null;}

  // Referencia biblica mais proxima (paginas de leitura), para dar contexto.
  function currentRef(){
    var el=document.querySelector('.verse-cont[data-ref], .ch-verse[data-ref]');
    return el?el.getAttribute('data-ref'):'';
  }

  function loadPending(){try{return JSON.parse(localStorage.getItem('bec.pendingReports')||'[]')||[];}catch(e){return [];}}
  function savePending(list){try{localStorage.setItem('bec.pendingReports',JSON.stringify(list.slice(-20)));}catch(e){}}

  function sendReport(row){
    var sb=client();
    if(!sb || !loggedIn()) return Promise.reject(new Error('sem sessao'));
    return sb.rpc('submit_suggestion', {
      p_kind:row.kind, p_verse_ref:row.verse_ref||'', p_page_url:row.page_url||'', p_body:row.body
    }).then(function(res){ if(res && res.error) throw res.error; return res; });
  }

  // Reenvia reportes guardados quando ha sessao.
  function flushPending(){
    var list=loadPending();
    if(!list.length || !loggedIn()) return;
    var next=list.shift();
    sendReport(next).then(function(){ savePending(list); flushPending(); })
      .catch(function(){ /* mantem na fila */ });
  }

  function buildModal(){
    if(document.querySelector('.report-modal')) return;
    var ov=document.createElement('div');
    ov.className='report-modal bec-modal';
    ov.hidden=true;
    ov.innerHTML='<div class="bec-modal-box report-box" role="dialog" aria-modal="true" aria-labelledby="report-title">'+
      '<button type="button" class="auth-close" data-report-close aria-label="Fechar">×</button>'+
      '<h2 id="report-title">Reportar um problema</h2>'+
      '<div data-report-signedout hidden>'+
        '<p class="muted-line">Entre na sua conta para enviar um reporte — assim conseguimos te dar retorno.</p>'+
        '<button type="button" class="btn primary" data-auth-open>Entrar para reportar</button>'+
      '</div>'+
      '<form data-report-form>'+
        '<label>Tipo'+
          '<select name="kind"><option value="correcao">Erro / correção (algo errado no site ou no texto)</option><option value="sugestao">Sugestão de melhoria</option></select>'+
        '</label>'+
        '<label>Mensagem'+
          '<textarea name="body" rows="4" maxlength="4000" required placeholder="Descreva o que aconteceu ou o que você gostaria de ver."></textarea>'+
        '</label>'+
        '<button type="submit" class="btn primary" data-report-submit>Enviar</button>'+
      '</form>'+
      '<p class="auth-status" data-report-status></p>'+
    '</div>';
    document.body.appendChild(ov);
    ov.addEventListener('click', function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-report-close]'))) close();
    });
    ov.querySelector('[data-report-form]').addEventListener('submit', submit);
  }

  function status(msg, type){
    var el=document.querySelector('[data-report-status]');
    if(el){ el.textContent=msg||''; el.className='auth-status '+(type||''); }
  }
  function syncMode(){
    var form=document.querySelector('[data-report-form]');
    var out=document.querySelector('[data-report-signedout]');
    var on=loggedIn();
    if(form) form.hidden=!on;
    if(out) out.hidden=on;
  }
  function open(){
    buildModal();
    var m=document.querySelector('.report-modal');
    if(m){ m.hidden=false; status(''); syncMode();
      if(loggedIn()){ var t=m.querySelector('textarea'); if(t) setTimeout(function(){t.focus();},30); } }
  }
  function close(){ var m=document.querySelector('.report-modal'); if(m) m.hidden=true; }

  function submit(e){
    e.preventDefault();
    if(!loggedIn()){ syncMode(); return; }
    var form=e.currentTarget;
    var body=(form.body.value||'').trim();
    if(body.length<3){ status('Escreva um pouco mais na mensagem.', 'err'); return; }
    var row={
      kind:form.kind.value==='sugestao'?'sugestao':'correcao',
      body:body.slice(0,4000),
      page_url:location.href.slice(0,300),
      verse_ref:(currentRef()||'').slice(0,120)
    };
    var btn=form.querySelector('[data-report-submit]');
    if(btn) btn.disabled=true;
    status('Enviando...', 'muted');
    sendReport(row).then(function(){
      status('Obrigado! Recebemos seu reporte.', 'ok');
      form.reset();
      setTimeout(close, 1200);
    }).catch(function(){
      var list=loadPending(); list.push(row); savePending(list);
      status('Sem conexão agora — seu reporte foi guardado e será enviado depois.', 'ok');
      form.reset();
      setTimeout(close, 1800);
    }).then(function(){ if(btn) btn.disabled=false; });
  }

  // O acionador vive no conjunto de ferramentas do topo (nav). So cria o botao
  // flutuante de fallback se, por algum motivo, a nav nao tiver o gatilho.
  function mountButton(){
    if(document.querySelector('[data-report-open]')) return;
    if(document.querySelector('.report-fab')) return;
    var b=document.createElement('button');
    b.type='button'; b.className='report-fab'; b.setAttribute('data-report-open','');
    b.title='Reportar um problema'; b.innerHTML='<span aria-hidden="true">🐞</span><span class="report-fab-txt">Reportar</span>';
    document.body.appendChild(b);
  }

  document.addEventListener('click', function(e){
    if(e.target.closest && e.target.closest('[data-report-open]')) open();
  });

  // ---- Leitura de reportes por administradores (staff) --------------------
  // O bloco so aparece para quem esta na tabela `staff` (mesmo criterio do RLS).
  var adminLoaded=false;
  function when(ts){try{return new Date(ts).toLocaleDateString('pt-BR');}catch(e){return '';}}
  function kindLabel(k){return k==='sugestao'?'💡 Sugestão':'🛠 Erro/correção';}
  function renderReports(rows){
    var box=document.querySelector('[data-admin-reports-list]');
    if(!box) return;
    if(!rows.length){ box.innerHTML='<p class="muted-line">Nenhum reporte por enquanto.</p>'; return; }
    box.innerHTML=rows.map(function(r){
      var done=r.status && r.status!=='pendente';
      return '<div class="report-row'+(done?' done':'')+'">'+
        '<div class="report-meta"><b>'+esc(kindLabel(r.kind))+'</b> · '+esc(when(r.created_at))+
          (r.verse_ref?' · '+esc(r.verse_ref):'')+' · <span class="report-status">'+esc(r.status||'pendente')+'</span></div>'+
        '<div class="report-body">'+esc(r.body).replace(/\n/g,'<br>')+'</div>'+
        (r.page_url?'<a class="report-link" href="'+esc(r.page_url)+'" target="_blank" rel="noopener">abrir página</a>':'')+
        (done?'':'<div class="report-actions">'+
          '<button type="button" class="btn tiny" data-report-review="'+esc(r.id)+'" data-status="aprovada">Marcar resolvido</button>'+
          '<button type="button" class="btn tiny ghost" data-report-review="'+esc(r.id)+'" data-status="descartada">Descartar</button>'+
        '</div>')+
      '</div>';
    }).join('');
  }
  function loadReports(){
    var sb=client(); if(!sb||!userId()) return;
    sb.from('suggestions').select('id,kind,body,page_url,verse_ref,status,created_at')
      .order('created_at',{ascending:false}).limit(200)
      .then(function(res){ if(!res.error) renderReports(res.data||[]); });
  }
  function maybeAdmin(){
    var block=document.querySelector('[data-admin-reports]');
    if(!block || adminLoaded) return;
    var sb=client(), uid=userId();
    if(!sb||!uid) return;
    sb.from('staff').select('user_id').eq('user_id',uid).maybeSingle().then(function(res){
      if(res && !res.error && res.data){ adminLoaded=true; block.hidden=false; loadReports(); }
    });
  }
  document.addEventListener('click', function(e){
    var rb=e.target.closest && e.target.closest('[data-report-review]');
    if(!rb) return;
    var sb=client(); if(!sb) return;
    rb.disabled=true;
    sb.rpc('review_suggestion', {p_id:rb.getAttribute('data-report-review'), p_status:rb.getAttribute('data-status')})
      .then(function(res){ if(!res.error) loadReports(); else rb.disabled=false; });
  });

  function init(){ mountButton(); flushPending(); maybeAdmin(); }
  document.addEventListener('bec:account', function(){ flushPending(); maybeAdmin(); if(document.querySelector('.report-modal')) syncMode(); });
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
