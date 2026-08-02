/* ============================================
   LAST MILE PLATFORM - THEME MANAGER
   Dark/Light theme with localStorage persistence
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
    // Dispatch event for charts to re-render
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
      if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
      }
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

  // Format currency
  $(amount) {
    return '$' + Number(amount || 0).toLocaleString(this._locale(), {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    });
  },
  
  // Format date
  date(d) {
    if (!d) return '-';
    return new Date(d).toLocaleDateString(this._locale(), {
      day: '2-digit', month: 'short', year: 'numeric'
    });
  },
  
  // Format datetime
  datetime(d) {
    if (!d) return '-';
    return new Date(d).toLocaleString(this._locale(), {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  },
  
  // Format number
  num(n) {
    return Number(n || 0).toLocaleString(this._locale());
  },
  
  // Relative time
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
  
  // Status badge HTML
  badge(status) {
    const map = {
      // Orders
      'CREADO': 'neutral', 'ASIGNADO': 'info', 'RECOGIDO': 'info',
      'EN_TRANSITO': 'warning', 'ENTREGADO': 'success', 'FALLIDO': 'danger', 'CANCELADO': 'danger',
      // General
      'ACTIVO': 'success', 'INACTIVO': 'danger', 'PENDIENTE': 'warning',
      'COMPLETADO': 'success', 'EN_PROCESO': 'info', 'COMPLETADO': 'success',
      // Billing
      'STARTER': 'neutral', 'PRO': 'accent', 'ENTERPRISE': 'warning',
      'PAGADO': 'success', 'VENCIDO': 'danger',
      // Support
      'ABIERTO': 'warning', 'EN_PROGRESO': 'info', 'RESUELTO': 'success',
      'CRITICA': 'danger', 'ALTA': 'warning', 'MEDIA': 'info', 'BAJA': 'neutral',
      // CFDI
      'TIMBRADA': 'success', 'PENDIENTE': 'warning', 'CANCELADA': 'danger',
      // Vehicles
      'MANTENIMIENTO': 'warning',
    };
    const variant = map[status] || 'neutral';
    return `<span class="badge badge-${variant}">${status}</span>`;
  },
  
  // Plan badge
  planBadge(plan) {
    const map = { 'STARTER': 'neutral', 'PRO': 'accent', 'ENTERPRISE': 'warning' };
    return `<span class="badge badge-${map[plan] || 'neutral'}">${plan}</span>`;
  },
  
  // Toast notification
  toast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const icons = { success: 'check-circle', error: 'times-circle', warning: 'exclamation-triangle', info: 'info-circle' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<i class="fas fa-${icons[type] || 'info-circle'}"></i><span>${message}</span>`;
    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  },
  
  // API call
  async api(endpoint, options = {}) {
    const API_BASE = window.API_BASE || 'http://localhost:5000';
    try {
      const headers = {
        'Content-Type': 'application/json',
        'X-Emp-Id': localStorage.getItem('lm-emp-id') || '1',
        ...(options.headers || {})
      };
      const resp = await fetch(API_BASE + endpoint, { ...options, headers });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (err) {
      console.warn('API unavailable, using demo data:', err.message);
      return { success: false, error: err.message };
    }
  },
  
  // Debounce
  debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  },
  
  // Generate UUID
  uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0;
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }
};

// Auto-init on DOM ready
document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
