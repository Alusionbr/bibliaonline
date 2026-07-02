// Biblioteca pessoal: Coleções (bec.collections) e Cadernos (bec.notebooks).
//  - Tudo funciona sem conta, salvo neste navegador (localStorage).
//  - Alterações chamam BEC_SYNC.markDirty() para sincronizar quando houver conta.
//  - Cada app só liga se a página tiver o container correspondente.
(function(){
  'use strict';

  function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
  function load(key, fallback){try{return JSON.parse(localStorage.getItem(key)||'null')||fallback;}catch(e){return fallback;}}
  function save(key, value){
    try{localStorage.setItem(key,JSON.stringify(value));}catch(e){}
    if(window.BEC_SYNC) window.BEC_SYNC.markDirty();
    document.dispatchEvent(new CustomEvent('bec:library-change'));
  }
  function uid(){return Date.now().toString(36)+Math.random().toString(36).slice(2,7);}
  function download(name, text){
    var b=new Blob([text],{type:'text/plain'}), u=URL.createObjectURL(b);
    var a=document.createElement('a'); a.href=u; a.download=name; document.body.appendChild(a);
    a.click(); a.remove(); URL.revokeObjectURL(u);
  }
  function confirmModal(msg, yesLabel, onYes){
    var ov=document.createElement('div'); ov.className='bec-modal';
    ov.innerHTML='<div class="bec-modal-box"><p>'+esc(msg)+'</p>'+
      '<div class="bec-modal-actions"><button type="button" class="btn ghost" data-no>Cancelar</button>'+
      '<button type="button" class="btn danger" data-yes>'+esc(yesLabel)+'</button></div></div>';
    ov.addEventListener('click', function(e){
      if(e.target===ov || (e.target.closest && e.target.closest('[data-no]'))) ov.remove();
      else if(e.target.closest && e.target.closest('[data-yes]')){ ov.remove(); onYes(); }
    });
    document.body.appendChild(ov);
  }
  function fmtDate(iso){
    try{return new Date(iso).toLocaleDateString('pt-BR');}catch(e){return '';}
  }

  // ---------- Coleções ----------
  (function(){
    var root=document.querySelector('[data-collections-app]');
    if(!root) return;
    var KEY='bec.collections';
    var openId=null;

    function favs(){return load('bec.favs',{});}

    function listView(){
      var all=load(KEY,{});
      var ids=Object.keys(all).sort(function(a,b){return (all[b].createdAt||'').localeCompare(all[a].createdAt||'');});
      var cards=ids.map(function(id){
        var c=all[id], n=(c.items||[]).length;
        return '<button type="button" class="study-card link-card library-card" data-open="'+esc(id)+'">'+
          '<span>'+n+(n===1?' item':' itens')+'</span><h3>'+esc(c.name)+'</h3><p>'+esc(c.desc||'')+'</p></button>';
      }).join('');
      root.innerHTML=
        '<form class="library-form" data-col-form>'+
          '<label>Nome da coleção <input name="name" required maxlength="80" placeholder="Versículos sobre oração"></label>'+
          '<label>Descrição <input name="desc" maxlength="160" placeholder="Opcional"></label>'+
          '<button type="submit" class="btn primary">Criar coleção</button>'+
        '</form>'+
        (ids.length
          ? '<div class="study-card-grid">'+cards+'</div>'
          : '<p class="muted-line">Nenhuma coleção ainda. Crie a primeira e adicione versículos dos seus favoritos.</p>');
    }

    function detailView(id){
      var all=load(KEY,{});
      var c=all[id];
      if(!c){ openId=null; listView(); return; }
      var items=(c.items||[]).map(function(it,i){
        return '<div class="fav-row"><a href="'+esc(it.url||'#')+'">'+esc(it.ref)+'</a>'+
          '<button type="button" class="btn tiny ghost" data-rm-item="'+i+'">Remover</button></div>';
      }).join('');
      var inCol={};
      (c.items||[]).forEach(function(it){inCol[it.ref]=1;});
      var f=favs();
      var options=Object.keys(f).sort().filter(function(ref){return !inCol[ref];}).map(function(ref){
        return '<div class="fav-row"><span>'+esc(ref)+'</span>'+
          '<button type="button" class="btn tiny" data-add-fav="'+esc(ref)+'">+ Adicionar</button></div>';
      }).join('');
      root.innerHTML=
        '<p><button type="button" class="btn ghost" data-back>← Todas as coleções</button></p>'+
        '<div class="section-title"><h2>'+esc(c.name)+'</h2><span>'+esc(c.desc||'')+'</span></div>'+
        ((c.items||[]).length ? '<div class="library-rows">'+items+'</div>' : '<p class="muted-line">Coleção vazia. Adicione versículos dos favoritos abaixo.</p>')+
        '<div class="section-title"><h3>Adicionar dos favoritos</h3></div>'+
        (options ? '<div class="library-rows">'+options+'</div>' : '<p class="muted-line">Sem favoritos disponíveis. Toque em ☆ Favoritar durante a leitura para trazê-los para cá.</p>')+
        '<p class="map-actions"><button type="button" class="btn danger ghost" data-del-col>Excluir coleção</button></p>';
    }

    function render(){ if(openId) detailView(openId); else listView(); }

    root.addEventListener('submit', function(e){
      var form=e.target.closest && e.target.closest('[data-col-form]');
      if(!form) return;
      e.preventDefault();
      var name=(form.name.value||'').trim();
      if(!name) return;
      var all=load(KEY,{});
      var id=uid();
      all[id]={name:name, desc:(form.desc.value||'').trim(), items:[], createdAt:new Date().toISOString()};
      save(KEY, all);
      openId=id;
      render();
    });

    root.addEventListener('click', function(e){
      var t=e.target;
      var open=t.closest && t.closest('[data-open]');
      if(open){ openId=open.getAttribute('data-open'); render(); return; }
      if(t.closest && t.closest('[data-back]')){ openId=null; render(); return; }
      var add=t.closest && t.closest('[data-add-fav]');
      if(add && openId){
        var all=load(KEY,{}), c=all[openId]; if(!c) return;
        var ref=add.getAttribute('data-add-fav'), item=favs()[ref]||{};
        c.items=c.items||[];
        c.items.push({ref:ref, url:item.url||'', addedAt:new Date().toISOString()});
        save(KEY, all); render(); return;
      }
      var rm=t.closest && t.closest('[data-rm-item]');
      if(rm && openId){
        var all2=load(KEY,{}), c2=all2[openId]; if(!c2) return;
        c2.items.splice(+rm.getAttribute('data-rm-item'),1);
        save(KEY, all2); render(); return;
      }
      if(t.closest && t.closest('[data-del-col]') && openId){
        var all3=load(KEY,{}), c3=all3[openId]; if(!c3) return;
        confirmModal('Excluir a coleção "'+c3.name+'"? Os versículos continuam nos seus favoritos.', 'Excluir', function(){
          delete all3[openId]; openId=null; save(KEY, all3); render();
        });
      }
    });

    document.addEventListener('bec:study-sync', render);
    render();
  })();

  // ---------- Cadernos ----------
  (function(){
    var root=document.querySelector('[data-notebooks-app]');
    if(!root) return;
    var KEY='bec.notebooks';
    var openId=null, saveTimer=null;

    function listView(){
      var all=load(KEY,{});
      var ids=Object.keys(all).sort(function(a,b){return (all[b].updatedAt||'').localeCompare(all[a].updatedAt||'');});
      var cards=ids.map(function(id){
        var n=all[id];
        var preview=(n.body||'').replace(/\s+/g,' ').slice(0,90);
        return '<button type="button" class="study-card link-card library-card" data-open="'+esc(id)+'">'+
          '<span>Atualizado em '+fmtDate(n.updatedAt)+'</span><h3>'+esc(n.title)+'</h3><p>'+esc(preview||'Caderno vazio')+'</p></button>';
      }).join('');
      root.innerHTML=
        '<form class="library-form" data-nb-form>'+
          '<label>Título do caderno <input name="title" required maxlength="80" placeholder="Estudo de Romanos"></label>'+
          '<button type="submit" class="btn primary">Criar caderno</button>'+
        '</form>'+
        (ids.length
          ? '<div class="study-card-grid">'+cards+'</div>'
          : '<p class="muted-line">Nenhum caderno ainda. Crie um para reunir notas, perguntas e referências de um estudo.</p>');
    }

    function editView(id){
      var all=load(KEY,{});
      var n=all[id];
      if(!n){ openId=null; listView(); return; }
      root.innerHTML=
        '<p><button type="button" class="btn ghost" data-back>← Todos os cadernos</button></p>'+
        '<div class="section-title"><h2>'+esc(n.title)+'</h2><span class="nb-status" data-nb-status></span></div>'+
        '<textarea class="nb-editor" data-nb-body placeholder="Escreva suas notas, perguntas e referências…">'+esc(n.body||'')+'</textarea>'+
        '<p class="map-actions">'+
          '<button type="button" class="btn ghost" data-nb-export>Baixar .txt</button>'+
          '<button type="button" class="btn danger ghost" data-del-nb>Excluir caderno</button>'+
        '</p>';
    }

    function render(){ if(openId) editView(openId); else listView(); }

    function setStatus(msg){
      var el=root.querySelector('[data-nb-status]');
      if(el) el.textContent=msg||'';
    }

    root.addEventListener('submit', function(e){
      var form=e.target.closest && e.target.closest('[data-nb-form]');
      if(!form) return;
      e.preventDefault();
      var title=(form.title.value||'').trim();
      if(!title) return;
      var all=load(KEY,{});
      var id=uid(), now=new Date().toISOString();
      all[id]={title:title, body:'', createdAt:now, updatedAt:now};
      save(KEY, all);
      openId=id;
      render();
    });

    root.addEventListener('input', function(e){
      var ta=e.target.closest && e.target.closest('[data-nb-body]');
      if(!ta || !openId) return;
      setStatus('Salvando…');
      clearTimeout(saveTimer);
      saveTimer=setTimeout(function(){
        var all=load(KEY,{}), n=all[openId]; if(!n) return;
        n.body=ta.value;
        n.updatedAt=new Date().toISOString();
        save(KEY, all);
        setStatus('Salvo ✓');
      },600);
    });

    root.addEventListener('click', function(e){
      var t=e.target;
      var open=t.closest && t.closest('[data-open]');
      if(open){ openId=open.getAttribute('data-open'); render(); return; }
      if(t.closest && t.closest('[data-back]')){ openId=null; render(); return; }
      if(t.closest && t.closest('[data-nb-export]') && openId){
        var all=load(KEY,{}), n=all[openId]; if(!n) return;
        download((n.title||'caderno').toLowerCase().replace(/[^a-z0-9]+/gi,'-')+'.txt', n.title+'\n\n'+(n.body||''));
        return;
      }
      if(t.closest && t.closest('[data-del-nb]') && openId){
        var all2=load(KEY,{}), n2=all2[openId]; if(!n2) return;
        confirmModal('Excluir o caderno "'+n2.title+'"? Esta ação não pode ser desfeita.', 'Excluir', function(){
          delete all2[openId]; openId=null; save(KEY, all2); render();
        });
      }
    });

    document.addEventListener('bec:study-sync', function(){ if(!openId) render(); });
    render();
  })();
})();
