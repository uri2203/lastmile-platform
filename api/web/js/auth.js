/**
 * Last Mile - Cliente de autenticacion.
 *
 * - Guarda/lee el token JWT en sessionStorage (no en localStorage plano).
 * - Envuelve window.fetch para adjuntar "Authorization: Bearer <token>" a
 *   toda llamada a /api (excepto el propio login).
 * - Si el backend responde 401, intenta refresh con refresh_token antes de cerrar sesion.
 */
(function () {
  var TOKEN_KEY = 'lm_token';
  var REFRESH_KEY = 'lm_refresh_token';
  var LOGIN_URL = '/login';

  function getToken() {
    try { return sessionStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }

  function getRefreshToken() {
    try { return localStorage.getItem(REFRESH_KEY) || ''; } catch (e) { return ''; }
  }

  function setRefreshToken(t) {
    try { localStorage.setItem(REFRESH_KEY, t || ''); } catch (e) {}
  }

  function clearRefreshToken() {
    try { localStorage.removeItem(REFRESH_KEY); } catch (e) {}
  }

  window.LMAuth = {
    token: getToken,
    setToken: function (t) {
      try { sessionStorage.setItem(TOKEN_KEY, t || ''); } catch (e) {}
    },
    setRefreshToken: setRefreshToken,
    logout: function () {
      try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
      try { localStorage.removeItem(REFRESH_KEY); } catch (e) {}
      try {
        localStorage.removeItem('empId');
        localStorage.removeItem('rol');
        localStorage.removeItem('user');
      } catch (e) {}
      window.location.href = LOGIN_URL;
    },
    // Llamar al cargar un panel protegido: redirige al login si no hay token.
    requireAuth: function () {
      if (!getToken()) { window.location.href = LOGIN_URL; return false; }
      return true;
    }
  };

  var _fetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    init = init || {};
    var url = (typeof input === 'string') ? input : (input && input.url) || '';
    var isApi = url.indexOf('/api/') !== -1;
    var isLogin = url.indexOf('/api/auth/login') !== -1;
    var isRefresh = url.indexOf('/api/auth/refresh') !== -1;

    if (isApi && !isLogin && !isRefresh) {
      var token = getToken();
      if (token) {
        var base = init.headers || (typeof input !== 'string' && input.headers) || {};
        var headers = new Headers(base);
        if (!headers.has('Authorization')) {
          headers.set('Authorization', 'Bearer ' + token);
        }
        init.headers = headers;
      }
    }

    return _fetch(input, init).then(function (resp) {
      if (resp.status === 401 && isApi && !isLogin && !isRefresh) {
        var refreshToken = getRefreshToken();
        if (refreshToken) {
          return _fetch('/api/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
          }).then(function (r) { return r.json(); }).then(function (data) {
            if (data.success && data.token) {
              window.LMAuth.setToken(data.token);
              init.headers = init.headers || new Headers();
              if (init.headers instanceof Headers) {
                init.headers.set('Authorization', 'Bearer ' + data.token);
              }
              return _fetch(input, init);
            }
            window.LMAuth.logout();
            return resp;
          }).catch(function () {
            window.LMAuth.logout();
            return resp;
          });
        }
        window.LMAuth.logout();
      }
      return resp;
    });
  };
})();
