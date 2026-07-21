/**
 * Last Mile - Cliente de autenticacion.
 *
 * - Guarda/lee el token JWT en sessionStorage (no en localStorage plano).
 * - Envuelve window.fetch para adjuntar "Authorization: Bearer <token>" a
 *   toda llamada a /api (excepto el propio login).
 * - Si el backend responde 401, limpia la sesion y redirige al login.
 */
(function () {
  var TOKEN_KEY = 'lm_token';
  var LOGIN_URL = '/login';

  function getToken() {
    try { return sessionStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }

  window.LMAuth = {
    token: getToken,
    setToken: function (t) {
      try { sessionStorage.setItem(TOKEN_KEY, t || ''); } catch (e) {}
    },
    logout: function () {
      try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
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

    if (isApi && !isLogin) {
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
      if (resp.status === 401 && isApi && !isLogin) {
        window.LMAuth.logout();
      }
      return resp;
    });
  };
})();
