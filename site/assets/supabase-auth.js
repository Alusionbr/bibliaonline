/* Supabase Auth Client — cliente leve sem SDK externo, chamadas diretas à API GoTrue
   Carregado em todas as páginas. Gerencia sessão, nav dinâmico e verificação de staff. */

(function() {
  'use strict';

  var SUPABASE_URL = 'https://pxqhpntifbtjaoqtirao.supabase.co';
  var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB4cWhwbnRpZmJ0amFvcXRpcmFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI1OTY3ODYsImV4cCI6MjA5ODE3Mjc4Nn0.s8ZJUMzQI7ACsb48I4lkcqj0Y2lQXoD-zIfojRCaRug';
  var GOTRUE_BASE = SUPABASE_URL + '/auth/v1';
  var REST_BASE   = SUPABASE_URL + '/rest/v1';
  var STORAGE_KEY = 'bec.auth';

  window.BecAuth = {
    getSession:           getSession,
    login:                login,
    logout:               logout,
    signUpWithMagicLink:  signUpWithMagicLink,
    onAuthStateChanged:   onAuthStateChanged,
    isStaff:              isStaff
  };

  /* -------- armazenamento -------- */

  function storeSession(s) {
    try {
      if (s) localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
      else    localStorage.removeItem(STORAGE_KEY);
    } catch(e) {}
  }

  function getStoredSession() {
    try { var d = localStorage.getItem(STORAGE_KEY); return d ? JSON.parse(d) : null; }
    catch(e) { return null; }
  }

  function getSession() { return getStoredSession(); }

  /* -------- autenticação -------- */

  // headers base para chamadas sem token de usuário (anon)
  function anonHeaders(extra) {
    var h = { 'Content-Type': 'application/json', 'apikey': SUPABASE_ANON_KEY };
    for (var k in extra) h[k] = extra[k];
    return h;
  }

  // headers para chamadas autenticadas (access_token do usuário)
  function authHeaders(accessToken, extra) {
    var h = {
      'Content-Type':  'application/json',
      'apikey':        SUPABASE_ANON_KEY,
      'Authorization': 'Bearer ' + accessToken
    };
    for (var k in extra) h[k] = extra[k];
    return h;
  }

  function refreshSession(session) {
    if (!session || !session.refresh_token) return Promise.reject(new Error('No refresh token'));
    return fetch(GOTRUE_BASE + '/token?grant_type=refresh_token', {
      method: 'POST',
      headers: anonHeaders(),
      body: JSON.stringify({ refresh_token: session.refresh_token })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.error) return Promise.reject(new Error(data.error_description || data.error));
      var s = {
        access_token:  data.access_token,
        token_type:    data.token_type,
        expires_in:    data.expires_in,
        expires_at:    Date.now() + (data.expires_in * 1000),
        refresh_token: data.refresh_token || session.refresh_token,
        user:          data.user
      };
      storeSession(s);
      notifyListeners(s);
      return s;
    });
  }

  function login(email, password) {
    return fetch(GOTRUE_BASE + '/token?grant_type=password', {
      method: 'POST',
      headers: anonHeaders(),
      body: JSON.stringify({ email: email, password: password })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.error) return Promise.reject(new Error(data.error_description || data.error));
      var s = {
        access_token:  data.access_token,
        token_type:    data.token_type,
        expires_in:    data.expires_in,
        expires_at:    Date.now() + (data.expires_in * 1000),
        refresh_token: data.refresh_token,
        user:          data.user
      };
      storeSession(s);
      notifyListeners(s);
      return s;
    });
  }

  function logout() {
    var s = getStoredSession();
    // sinaliza o GoTrue para invalidar o token (melhor prática)
    if (s && s.access_token) {
      fetch(GOTRUE_BASE + '/logout', {
        method: 'POST',
        headers: authHeaders(s.access_token)
      }).catch(function(){});
    }
    storeSession(null);
    notifyListeners(null);
    return Promise.resolve();
  }

  function signUpWithMagicLink(email) {
    return fetch(GOTRUE_BASE + '/otp', {
      method: 'POST',
      headers: anonHeaders(),
      body: JSON.stringify({ email: email, data: {}, create_user: true })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.error) return Promise.reject(new Error(data.error_description || data.error));
      return data;
    });
  }

  /* -------- verificação de staff -------- */

  var _staffCache = null; // null = não verificado, true/false = resultado

  function isStaff() {
    if (_staffCache !== null) return Promise.resolve(_staffCache);
    var s = getStoredSession();
    if (!s || !s.access_token || !s.user) return Promise.resolve(false);

    return fetch(REST_BASE + '/staff?select=uid&uid=eq.' + encodeURIComponent(s.user.id), {
      headers: authHeaders(s.access_token, { 'Accept': 'application/json' })
    })
    .then(function(r) { return r.json(); })
    .then(function(rows) {
      _staffCache = Array.isArray(rows) && rows.length > 0;
      return _staffCache;
    })
    .catch(function() { return false; });
  }

  /* -------- listeners -------- */

  var listeners = [];

  function onAuthStateChanged(callback) {
    listeners.push(callback);
    callback(getStoredSession());
    return function() {
      listeners = listeners.filter(function(l) { return l !== callback; });
    };
  }

  function notifyListeners(session) {
    _staffCache = null; // reseta cache de staff ao mudar sessão
    scheduleRefresh();
    listeners.forEach(function(cb) { cb(session); });
  }

  /* -------- refresh automático -------- */

  var refreshTimeout = null;
  function scheduleRefresh() {
    if (refreshTimeout) clearTimeout(refreshTimeout);
    var s = getStoredSession();
    if (!s || !s.expires_at) return;
    var delay = Math.max(5000, s.expires_at - Date.now() - 60000);
    refreshTimeout = setTimeout(function() {
      refreshSession(s).catch(function() { logout(); });
    }, delay);
  }
  scheduleRefresh();

  /* -------- nav dinâmica (todas as páginas) -------- */

  document.addEventListener('DOMContentLoaded', function() {
    var authLink = document.querySelector('.auth-link');
    if (!authLink) return;

    var dropdown = null;

    function closeDropdown() {
      if (dropdown) {
        dropdown.remove();
        dropdown = null;
      }
    }

    function buildDropdown(session, isStaffUser) {
      var el = document.createElement('div');
      el.className = 'auth-dropdown';
      el.setAttribute('role', 'menu');

      var email = session.user ? (session.user.email || '') : '';
      var shortEmail = email.length > 22 ? email.slice(0, 20) + '…' : email;

      var inner = '<div class="auth-dd-email">' + escHtml(shortEmail) + '</div>';
      if (isStaffUser) {
        inner += '<a href="' + sitePrefix() + 'admin/" class="auth-dd-item" role="menuitem">⚙ Admin</a>';
      }
      inner += '<button type="button" class="auth-dd-item auth-dd-logout" role="menuitem">Sair</button>';
      el.innerHTML = inner;

      el.querySelector('.auth-dd-logout').addEventListener('click', function() {
        logout().then(function() {
          closeDropdown();
          // se está em /conta/ ou /admin/, volta à home
          if (/\/(conta|admin)\//.test(location.pathname)) {
            location.href = sitePrefix() + 'index.html';
          }
        });
      });

      return el;
    }

    function sitePrefix() {
      // deriva o prefixo do site a partir do src do supabase-auth.js
      var s = document.querySelector('script[src*="supabase-auth"]');
      var src = s ? s.getAttribute('src') : '';
      return src.replace(/assets\/supabase-auth\.js.*$/, '');
    }

    function escHtml(s) {
      return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    function updateNavAuth(session) {
      if (!authLink) return;

      if (!session || !session.user) {
        // deslogado
        authLink.textContent = '👤';
        authLink.title = 'Entrar';
        authLink.setAttribute('aria-label', 'Entrar na conta');
        authLink.href = sitePrefix() + 'conta/';
        closeDropdown();
        return;
      }

      // logado: ícone vira botão de conta
      var initial = (session.user.email || '?').charAt(0).toUpperCase();
      authLink.textContent = initial;
      authLink.title = session.user.email || 'Conta';
      authLink.setAttribute('aria-label', 'Menu da conta');
      authLink.href = '#';
      authLink.className = 'rt auth-link auth-avatar';

      // verifica staff para montar dropdown corretamente
      isStaff().then(function(staff) {
        authLink.removeEventListener('click', authLink._authClickHandler);
        authLink._authClickHandler = function(e) {
          e.preventDefault();
          if (dropdown) {
            closeDropdown();
            return;
          }
          dropdown = buildDropdown(session, staff);
          // posiciona abaixo do ícone
          var rect = authLink.getBoundingClientRect();
          dropdown.style.top = (rect.bottom + window.scrollY + 6) + 'px';
          dropdown.style.right = (window.innerWidth - rect.right) + 'px';
          document.body.appendChild(dropdown);
        };
        authLink.addEventListener('click', authLink._authClickHandler);
      });
    }

    onAuthStateChanged(function(session) {
      updateNavAuth(session);
    });

    // fecha dropdown ao clicar fora
    document.addEventListener('click', function(e) {
      if (dropdown && !dropdown.contains(e.target) && e.target !== authLink) {
        closeDropdown();
      }
    });
  });

})();
