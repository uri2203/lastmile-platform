/**
 * Cookie Consent - Modal Invasivo (pantalla completa)
 * Bloquea la pagina hasta que el usuario acepte o configure cookies.
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'cookie_consent';
  var EXPIRY_DAYS = 90;

  function getStoredConsent() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (!data || !data.timestamp) return null;
      var created = new Date(data.timestamp);
      var now = new Date();
      var diffDays = (now - created) / (1000 * 60 * 60 * 24);
      if (diffDays > EXPIRY_DAYS) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }
      return data;
    } catch (e) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
  }

  function saveConsent(consent) {
    consent.timestamp = new Date().toISOString();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
    window.dispatchEvent(new CustomEvent('cookieConsentChange', { detail: consent }));
  }

  function createStyles() {
    if (document.getElementById('cc-styles')) return;
    var s = document.createElement('style');
    s.id = 'cc-styles';
    s.textContent = [
      '@keyframes cc-fadeIn{from{opacity:0}to{opacity:1}}',
      '@keyframes cc-fadeOut{from{opacity:1}to{opacity:0}}',
      '@keyframes cc-scaleIn{from{transform:scale(.95);opacity:0}to{transform:scale(1);opacity:1}}',

      '.cc-overlay{position:fixed;top:0;left:0;right:0;bottom:0;z-index:999999;background:rgba(0,0,0,0.7);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;animation:cc-fadeIn .3s ease-out;padding:16px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;}',
      '.cc-modal{background:#fff;border-radius:16px;width:100%;max-width:520px;max-height:90vh;overflow-y:auto;box-shadow:0 25px 80px rgba(0,0,0,0.35);animation:cc-scaleIn .35s ease-out;}',
      '.cc-header{padding:28px 28px 0;text-align:center;}',
      '.cc-icon{font-size:40px;margin-bottom:12px;}',
      '.cc-title{font-size:20px;font-weight:700;color:#111827;margin:0 0 8px;}',
      '.cc-desc{font-size:14px;color:#6b7280;line-height:1.6;margin:0;}',
      '.cc-desc a{color:#2563eb;text-decoration:underline;}',
      '.cc-body{padding:20px 28px;}',
      '.cc-category{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid #f3f4f6;}',
      '.cc-category:last-child{border-bottom:none;}',
      '.cc-cat-info{flex:1;padding-right:16px;}',
      '.cc-cat-name{font-size:14px;font-weight:600;color:#111827;margin:0 0 2px;}',
      '.cc-cat-desc{font-size:12px;color:#9ca3af;margin:0;line-height:1.4;}',
      '.cc-toggle{position:relative;width:44px;height:24px;flex-shrink:0;}',
      '.cc-toggle input{opacity:0;width:0;height:0;}',
      '.cc-toggle-slider{position:absolute;cursor:pointer;top:0;left:0;right:0;bottom:0;background:#d1d5db;border-radius:12px;transition:.3s;}',
      '.cc-toggle-slider::before{content:"";position:absolute;height:18px;width:18px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s;}',
      '.cc-toggle input:checked+.cc-toggle-slider{background:#2563eb;}',
      '.cc-toggle input:checked+.cc-toggle-slider::before{transform:translateX(20px);}',
      '.cc-toggle input:disabled+.cc-toggle-slider{background:#2563eb;opacity:.6;cursor:not-allowed;}',
      '.cc-toggle input:disabled+.cc-toggle-slider::before{transform:translateX(20px);}',
      '.cc-actions{padding:0 28px 28px;display:flex;flex-direction:column;gap:10px;}',
      '.cc-btn{padding:13px 20px;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;transition:all .2s;border:none;width:100%;text-align:center;}',
      '.cc-btn:active{transform:scale(.98);}',
      '.cc-btn-accept{background:#2563eb;color:#fff;}',
      '.cc-btn-accept:hover{background:#1d4ed8;}',
      '.cc-btn-necessary{background:#f3f4f6;color:#374151;border:1px solid #d1d5db;}',
      '.cc-btn-necessary:hover{background:#e5e7eb;}',
      '.cc-btn-reject{background:#fff;color:#6b7280;border:1px solid #e5e7eb;font-weight:500;font-size:13px;padding:10px 20px;}',
      '.cc-btn-reject:hover{background:#f9fafb;color:#374151;}',
      '.cc-footer-links{text-align:center;padding:0 28px 20px;font-size:11px;color:#9ca3af;}',
      '.cc-footer-links a{color:#6b7280;text-decoration:underline;margin:0 6px;}',
      '@media(max-width:600px){.cc-modal{max-width:100%;border-radius:12px;margin:8px;}.cc-header{padding:20px 20px 0;}.cc-body{padding:16px 20px;}.cc-actions{padding:0 20px 20px;}.cc-footer-links{padding:0 20px 16px;}}'
    ].join('\n');
    document.head.appendChild(s);
  }

  function createOverlay() {
    if (document.getElementById('cc-overlay')) return;

    // Bloquear scroll del body
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';

    var overlay = document.createElement('div');
    overlay.id = 'cc-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Consentimiento de cookies obligatorio');
    overlay.innerHTML = [
      '<div class="cc-modal">',
      '  <div class="cc-header">',
      '    <div class="cc-icon">&#127850;</div>',
      '    <h2 class="cc-title">Este sitio utiliza cookies</h2>',
      '    <p class="cc-desc">',
      '      Utilizamos cookies propias y de terceros para mejorar su experiencia, analizar el trafico y personalizar el contenido. ',
      '      Para continuar navegando <b>debe aceptar</b> o configurar sus preferencias. ',
      '      Consulte nuestra <a href="/legal/politica-cookies.html" target="_blank" rel="noopener">Politica de Cookies</a> para mas informacion.',
      '    </p>',
      '  </div>',
      '  <div class="cc-body">',
      '    <div class="cc-category">',
      '      <div class="cc-cat-info">',
      '        <p class="cc-cat-name">&#9989; Necesarias</p>',
      '        <p class="cc-cat-desc">Imprescindibles para el funcionamiento del sitio. No se pueden desactivar.</p>',
      '      </div>',
      '      <label class="cc-toggle"><input type="checkbox" checked disabled><span class="cc-toggle-slider"></span></label>',
      '    </div>',
      '    <div class="cc-category">',
      '      <div class="cc-cat-info">',
      '        <p class="cc-cat-name">&#128202; Analiticas</p>',
      '        <p class="cc-cat-desc">Nos ayudan a entender como utiliza el sitio para mejorar la experiencia.</p>',
      '      </div>',
      '      <label class="cc-toggle"><input type="checkbox" id="cc-tog-analytics"><span class="cc-toggle-slider"></span></label>',
      '    </div>',
      '    <div class="cc-category">',
      '      <div class="cc-cat-info">',
      '        <p class="cc-cat-name">&#128227; Marketing</p>',
      '        <p class="cc-cat-desc">Para mostrar publicidad relevante y medir campanas publicitarias.</p>',
      '      </div>',
      '      <label class="cc-toggle"><input type="checkbox" id="cc-tog-marketing"><span class="cc-toggle-slider"></span></label>',
      '    </div>',
      '  </div>',
      '  <div class="cc-actions">',
      '    <button class="cc-btn cc-btn-accept" id="cc-accept">Aceptar Todas</button>',
      '    <button class="cc-btn cc-btn-necessary" id="cc-necessary">Solo Necesarias</button>',
      '    <button class="cc-btn cc-btn-reject" id="cc-reject">Rechazar Todas</button>',
      '  </div>',
      '  <div class="cc-footer-links">',
      '    <a href="/legal/terminos-condiciones.html" target="_blank">Terminos</a>',
      '    <a href="/legal/aviso-privacidad.html" target="_blank">Privacidad</a>',
      '    <a href="/legal/politica-cookies.html" target="_blank">Cookies</a>',
      '    <a href="/legal/deslinde-responsabilidades.html" target="_blank">Deslinde</a>',
      '  </div>',
      '</div>'
    ].join('');

    document.body.appendChild(overlay);

    // Prevenir cierre con Escape o click afuera (es obligatorio elegir)
    overlay.addEventListener('click', function (e) {
      e.stopPropagation();
    });
    document.addEventListener('keydown', function handler(e) {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
      }
    });

    document.getElementById('cc-accept').addEventListener('click', function () {
      saveConsent({ necessary: true, analytics: true, marketing: true });
      removeOverlay();
    });

    document.getElementById('cc-necessary').addEventListener('click', function () {
      saveConsent({ necessary: true, analytics: false, marketing: false });
      removeOverlay();
    });

    document.getElementById('cc-reject').addEventListener('click', function () {
      saveConsent({ necessary: true, analytics: false, marketing: false });
      removeOverlay();
    });
  }

  function removeOverlay() {
    var overlay = document.getElementById('cc-overlay');
    if (!overlay) return;
    overlay.style.animation = 'cc-fadeOut .25s ease-in forwards';
    // Restaurar scroll
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
    setTimeout(function () { overlay.remove(); }, 250);
  }

  function init() {
    var consent = getStoredConsent();
    if (consent) {
      window.dispatchEvent(new CustomEvent('cookieConsentChange', { detail: consent }));
      return;
    }
    createStyles();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', createOverlay);
    } else {
      createOverlay();
    }
  }

  window.CookieConsent = {
    getConsent: getStoredConsent,
    reset: function () {
      localStorage.removeItem(STORAGE_KEY);
    },
    show: function () {
      createStyles();
      createOverlay();
    }
  };

  init();
})();
