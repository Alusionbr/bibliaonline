/* Lógica da página de conta (/conta/) — carregado apenas nesta página */

(function() {
  'use strict';

  var loginForm = document.getElementById('login-form');
  var loginError = document.getElementById('login-error');
  var logoutBtn = document.getElementById('logout-btn');
  var magicLinkBtn = document.getElementById('magic-link-btn');
  var oauthGoogle = document.getElementById('oauth-google');
  var oauthApple = document.getElementById('oauth-apple');

  var loggedOutState = document.getElementById('auth-state-logged-out');
  var loggedInState = document.getElementById('auth-state-logged-in');
  var loadingState = document.getElementById('auth-loading');
  var userEmailEl = document.getElementById('user-email');

  function showLoading(show) {
    loadingState.hidden = !show;
    if (show) {
      loggedOutState.hidden = true;
      loggedInState.hidden = true;
    }
  }

  function showError(msg) {
    if (loginError) {
      loginError.textContent = msg;
      loginError.hidden = false;
    }
  }

  function clearError() {
    if (loginError) {
      loginError.hidden = true;
      loginError.textContent = '';
    }
  }

  function updateUI(session) {
    if (session && session.user) {
      loggedOutState.hidden = true;
      loggedInState.hidden = false;
      userEmailEl.textContent = 'E-mail: ' + (session.user.email || 'Desconhecido');
    } else {
      loggedOutState.hidden = false;
      loggedInState.hidden = true;
    }
    loadingState.hidden = true;
  }

  // monitora mudanças de autenticação
  if (window.BecAuth) {
    window.BecAuth.onAuthStateChanged(function(session) {
      updateUI(session);
    });
  }

  // login form submit
  if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
      e.preventDefault();
      clearError();

      var email = document.getElementById('login-email').value.trim();
      var password = document.getElementById('login-password').value;

      if (!email || !password) {
        showError('Preencha e-mail e senha.');
        return;
      }

      showLoading(true);

      if (!window.BecAuth) {
        showError('Autenticação não disponível.');
        showLoading(false);
        return;
      }

      window.BecAuth.login(email, password)
        .then(function(session) {
          clearError();
          updateUI(session);
          showLoading(false);
          // redirecione para home após sucesso
          setTimeout(function() {
            window.location.href = '../index.html';
          }, 1000);
        })
        .catch(function(err) {
          showError('Erro ao fazer login: ' + (err.message || 'Tente novamente.'));
          showLoading(false);
        });
    });
  }

  // logout button
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
      if (window.BecAuth) {
        showLoading(true);
        window.BecAuth.logout().then(function() {
          updateUI(null);
          showLoading(false);
          clearError();
        });
      }
    });
  }

  // magic link
  if (magicLinkBtn) {
    magicLinkBtn.addEventListener('click', function() {
      var email = prompt('Digite seu e-mail para receber um link mágico:');
      if (!email) return;

      email = email.trim().toLowerCase();
      if (!email.includes('@')) {
        alert('E-mail inválido.');
        return;
      }

      showLoading(true);
      clearError();

      if (!window.BecAuth) {
        showError('Autenticação não disponível.');
        showLoading(false);
        return;
      }

      window.BecAuth.signUpWithMagicLink(email)
        .then(function() {
          showLoading(false);
          alert('Link mágico enviado para ' + email + '. Verifique seu e-mail.');
        })
        .catch(function(err) {
          showError('Erro ao enviar link: ' + (err.message || 'Tente novamente.'));
          showLoading(false);
        });
    });
  }

  // OAuth (ainda não ativo — buttons desabilitados)
  if (oauthGoogle) {
    oauthGoogle.addEventListener('click', function() {
      alert('Google OAuth ainda não está ativado.');
    });
  }

  if (oauthApple) {
    oauthApple.addEventListener('click', function() {
      alert('Apple OAuth ainda não está ativado.');
    });
  }

  // estado inicial
  updateUI(window.BecAuth ? window.BecAuth.getSession() : null);
})();
