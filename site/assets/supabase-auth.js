/* Supabase Auth Client — cliente leve sem SDK externo, chamadas diretas à API GoTrue */

(function() {
  'use strict';

  // config
  var SUPABASE_URL = 'https://pxqhpntifbtjaoqtirao.supabase.co';
  var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB4cWhwbnRpZmJ0amFvcXRpcmFvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI1OTY3ODYsImV4cCI6MjA5ODE3Mjc4Nn0.s8ZJUMzQI7ACsb48I4lkcqj0Y2lQXoD-zIfojRCaRug';
  var GOTRUE_BASE = SUPABASE_URL + '/auth/v1';
  var STORAGE_KEY = 'bec.auth';

  window.BecAuth = {
    getSession: getSession,
    login: login,
    logout: logout,
    signUpWithMagicLink: signUpWithMagicLink,
    onAuthStateChanged: onAuthStateChanged
  };

  var listeners = [];

  function storeSession(session) {
    try {
      if (session) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch (e) {}
  }

  function getStoredSession() {
    try {
      var data = localStorage.getItem(STORAGE_KEY);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      return null;
    }
  }

  function getSession() {
    return getStoredSession();
  }

  function refreshSession(session) {
    if (!session || !session.refresh_token) return Promise.reject(new Error('No refresh token'));

    return fetch(GOTRUE_BASE + '/token?grant_type=refresh_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: session.refresh_token })
    })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) return Promise.reject(new Error(data.error_description || data.error));
        var newSession = {
          access_token: data.access_token,
          token_type: data.token_type,
          expires_in: data.expires_in,
          expires_at: Date.now() + (data.expires_in * 1000),
          refresh_token: data.refresh_token || session.refresh_token,
          user: data.user
        };
        storeSession(newSession);
        notifyListeners(newSession);
        return newSession;
      });
  }

  function login(email, password) {
    return fetch(GOTRUE_BASE + '/token?grant_type=password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + SUPABASE_ANON_KEY
      },
      body: JSON.stringify({ email: email, password: password })
    })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) return Promise.reject(new Error(data.error_description || data.error));
        var session = {
          access_token: data.access_token,
          token_type: data.token_type,
          expires_in: data.expires_in,
          expires_at: Date.now() + (data.expires_in * 1000),
          refresh_token: data.refresh_token,
          user: data.user
        };
        storeSession(session);
        notifyListeners(session);
        return session;
      });
  }

  function logout() {
    storeSession(null);
    notifyListeners(null);
    return Promise.resolve();
  }

  function signUpWithMagicLink(email) {
    var redirectUrl = window.location.origin + '/conta/';
    return fetch(GOTRUE_BASE + '/otp', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + SUPABASE_ANON_KEY
      },
      body: JSON.stringify({
        email: email,
        data: {},
        create_user: true
      })
    })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.error) return Promise.reject(new Error(data.error_description || data.error));
        return data;
      });
  }

  function onAuthStateChanged(callback) {
    listeners.push(callback);
    // dispara imediatamente com estado atual
    callback(getStoredSession());
    return function unsubscribe() {
      listeners = listeners.filter(function(l) { return l !== callback; });
    };
  }

  function notifyListeners(session) {
    listeners.forEach(function(cb) { cb(session); });
  }

  // monitora token expiring (opcional: refresh automático antes de expirar)
  var refreshTimeout = null;
  function scheduleRefresh() {
    if (refreshTimeout) clearTimeout(refreshTimeout);
    var session = getStoredSession();
    if (!session || !session.expires_at) return;

    var expiresIn = session.expires_at - Date.now();
    // refresh 1min antes de expirar (mínimo 5s de delay)
    var delay = Math.max(5000, expiresIn - 60000);

    refreshTimeout = setTimeout(function() {
      refreshSession(session).catch(function() {
        // se refresh falhar, logout
        logout();
      });
    }, delay);
  }

  // agende refresh no carregamento
  scheduleRefresh();

  // atualize schedule sempre que a sessão muda
  var originalNotify = notifyListeners;
  notifyListeners = function(session) {
    scheduleRefresh();
    originalNotify(session);
  };
})();
