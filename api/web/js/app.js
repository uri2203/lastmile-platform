/**
 * app.js - Shared utilities for all panels.
 * Includes: Utils, ThemeManager, LMAuth
 */

/* ============================================
   THEME MANAGER
   ============================================ */
const ThemeManager = {
  STORAGE_KEY: 'lm-theme',
  init() {
    const saved = localStorage.getItem(this.STORAGE_KEY) || 'dark';
    this.apply(saved);
    this.bindToggleButtons();
  },
  apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.STORAGE_KEY, theme);
    this.updateToggleIcons(theme);
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  },
  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    this.apply(next);
  },
  get() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
  },
  updateToggleIcons(theme) {
    document.querySelectorAll('.theme-toggle').forEach(btn => {
      const icon = btn.querySelector('i');
      if (icon) icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    });
  },
  bindToggleButtons() {
    document.querySelectorAll('.theme-toggle').forEach(btn => {
      btn.addEventListener('click', () => this.toggle());
    });
  }
};

/* ============================================
   SHARED UTILITIES
   ============================================ */
const Utils = {
  _locale() {
    try { return (window.i18n && window.i18n._getLocale && window.i18n._getLocale()) || 'es-MX'; } catch(e) { return 'es-MX'; }
  },
  $(amount) {
    return '$' + Number(amount || 0).toLocaleString(this._locale(), { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },
  date(d) {
    if (!d) return '-';
    return new Date(d).toLocaleDateString(this._locale(), { day: '2-digit', month: 'short', year: 'numeric' });
  },
  datetime(d) {
    if (!d) return '-';
    return new Date(d).toLocaleString(this._locale(), { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  },
  num(n) {
    return Number(n || 0).toLocaleString(this._locale());
  },
  relative(d) {
    if (!d) return '-';
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'ahora';
    if (mins < 60) return mins + 'm';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + 'h';
    const days = Math.floor(hrs / 24);
    return days + 'd';
  },
  badge(status) {
    const map = {
      'CREADO': 'neutral', 'ASIGNADO': 'info', 'RECOGIDO': 'info',
      'EN_TRANSITO': 'warning', 'ENTREGADO': 'success', 'FALLIDO': 'danger', 'CANCELADO': 'danger',
      'ACTIVO': 'success', 'INACTIVO': 'danger', 'PENDIENTE': 'warning',
      'COMPLETADO': 'success', 'EN_PROCESO': 'info',
      'STARTER': 'neutral', 'PRO': 'accent', 'ENTERPRISE': 'warning',
      'PAGADO': 'success', 'VENCIDO': 'danger',
      'ABIERTO': 'warning', 'EN_PROGRESO': 'info', 'RESUELTO': 'success',
      'CRITICA': 'danger', 'ALTA': 'warning', 'MEDIA': 'info', 'BAJA': 'neutral',
      'TIMBRADA': 'success', 'CANCELADA': 'danger', 'MANTENIMIENTO': 'warning',
      'EN LINEA': 'success', 'OFFLINE': 'danger',
    };
    const variant = map[status] || 'neutral';
    return '<span class="badge badge-' + variant + '">' + status + '</span>';
  },
  planBadge(plan) {
    const map = { 'STARTER': 'neutral', 'PRO': 'accent', 'ENTERPRISE': 'warning' };
    return '<span class="badge badge-' + (map[plan] || 'neutral') + '">' + plan + '</span>';
  },
  toast(message, type) {
    type = type || 'success';
    var container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    var icons = { success: 'check-circle', error: 'times-circle', warning: 'exclamation-triangle', info: 'info-circle' };
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.innerHTML = '<i class="fas fa-' + (icons[type] || 'info-circle') + '"></i><span>' + message + '</span>';
    container.appendChild(toast);
    requestAnimationFrame(function() { toast.classList.add('show'); });
    setTimeout(function() {
      toast.classList.remove('show');
      setTimeout(function() { toast.remove(); }, 300);
    }, 3500);
  },
  async api(endpoint, options) {
    options = options || {};
    var API_BASE = window.API_BASE || window.location.origin;
    try {
      var headers = Object.assign({
        'Content-Type': 'application/json',
        'X-Emp-Id': localStorage.getItem('lm-emp-id') || localStorage.getItem('empId') || '1'
      }, options.headers || {});
      var token = '';
      try { token = sessionStorage.getItem('lm_token') || ''; } catch(e) {}
      if (token && !headers['Authorization']) headers['Authorization'] = 'Bearer ' + token;
      var resp = await fetch(API_BASE + endpoint, Object.assign({}, options, { headers: headers }));
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      return await resp.json();
    } catch (err) {
      console.warn('API unavailable:', err.message);
      return { success: false, error: err.message };
    }
  },
  debounce(fn, delay) {
    delay = delay || 300;
    var timer;
    return function() {
      var args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function() { fn.apply(null, args); }, delay);
    };
  },
  uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }
};

/* ============================================
   AUTH MODULE
   ============================================ */
(function() {
  var TOKEN_KEY = 'lm_token';
  var REFRESH_KEY = 'lm_refresh_token';
  var LOGIN_URL = 'index.html';

  function getToken() {
    try { return sessionStorage.getItem(TOKEN_KEY) || ''; } catch (e) { return ''; }
  }

  function getRefreshToken() {
    try { return localStorage.getItem(REFRESH_KEY) || ''; } catch (e) { return ''; }
  }

  window.LMAuth = {
    token: getToken,
    getToken: getToken,
    setToken: function(t) {
      try { sessionStorage.setItem(TOKEN_KEY, t || ''); } catch (e) {}
    },
    setRefreshToken: function(t) {
      try { localStorage.setItem(REFRESH_KEY, t || ''); } catch (e) {}
    },
    logout: function() {
      try { sessionStorage.removeItem(TOKEN_KEY); } catch (e) {}
      try { localStorage.removeItem(REFRESH_KEY); } catch (e) {}
      try {
        localStorage.removeItem('empId');
        localStorage.removeItem('rol');
        localStorage.removeItem('user');
      } catch (e) {}
      window.location.href = LOGIN_URL;
    },
    requireAuth: function() {
      if (!getToken()) { window.location.href = LOGIN_URL; return false; }
      return true;
    }
  };

  var _fetch = window.fetch.bind(window);
  window.fetch = function(input, init) {
    init = init || {};
    var url = (typeof input === 'string') ? input : (input && input.url) || '';
    var isApi = url.indexOf('/api/') !== -1;
    var isLogin = url.indexOf('/api/auth/login') !== -1;
    var isRefresh = url.indexOf('/api/auth/refresh') !== -1;

    if (isApi && !isLogin && !isRefresh) {
      var token = getToken();
      if (token) {
        var headers = new Headers(init.headers || {});
        if (!headers.has('Authorization')) {
          headers.set('Authorization', 'Bearer ' + token);
        }
        init.headers = headers;
      }
    }

    return _fetch(input, init).then(function(resp) {
      if (resp.status === 401 && isApi && !isLogin && !isRefresh) {
        var refreshToken = getRefreshToken();
        if (refreshToken) {
          return _fetch('/api/auth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
          }).then(function(r) { return r.json(); }).then(function(data) {
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
          }).catch(function() {
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

// Auto-init
document.addEventListener('DOMContentLoaded', function() {
  ThemeManager.init();
});
