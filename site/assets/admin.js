/* Lógica da página /admin/ — verifica staff via Supabase e libera o painel */

(function() {
  'use strict';

  var elLoading = document.getElementById('admin-loading');
  var elDenied  = document.getElementById('admin-denied');
  var elContent = document.getElementById('admin-content');
  var elGreeting    = document.querySelector('.admin-greeting');
  var elSessionInfo = document.getElementById('admin-session-info');
  var elLogout  = document.getElementById('admin-logout');

  function show(el) { if (el) el.hidden = false; }
  function hide(el) { if (el) el.hidden = true; }

  function deny() {
    hide(elLoading);
    show(elDenied);
  }

  function grant(session) {
    hide(elLoading);
    show(elContent);

    if (elGreeting) {
      elGreeting.textContent = 'Bem-vindo, ' + (session.user.email || 'admin') + '.';
    }

    if (elSessionInfo) {
      var uid   = session.user ? session.user.id : '—';
      var email = session.user ? (session.user.email || '—') : '—';
      var exp   = session.expires_at ? new Date(session.expires_at).toLocaleString('pt-BR') : '—';
      elSessionInfo.innerHTML =
        '<span>UID: ' + uid + '</span>' +
        '<span>E-mail: ' + email + '</span>' +
        '<span>Token expira: ' + exp + '</span>';
    }
  }

  function init() {
    if (!window.BecAuth) { deny(); return; }

    var session = window.BecAuth.getSession();
    if (!session || !session.user) { deny(); return; }

    // Verifica se está na tabela public.staff
    window.BecAuth.isStaff().then(function(staff) {
      if (!staff) { deny(); return; }
      grant(session);
    }).catch(function() { deny(); });
  }

  if (elLogout) {
    elLogout.addEventListener('click', function() {
      if (window.BecAuth) {
        window.BecAuth.logout().then(function() {
          // deriva prefixo a partir do src do admin.js
          var s = document.querySelector('script[src*="admin.js"]');
          var src = s ? s.getAttribute('src') : '../';
          var prefix = src.replace(/assets\/admin\.js.*$/, '');
          location.href = prefix + 'index.html';
        });
      }
    });
  }

  // aguarda supabase-auth.js carregar (DOMContentLoaded já passou; roda direto)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
