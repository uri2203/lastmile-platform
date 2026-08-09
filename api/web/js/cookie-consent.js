/**
 * Cookie Consent Banner - Last Mile Delivery SaaS Platform
 * Manages cookie consent with localStorage persistence.
 * Includes banner, configuration modal, and category toggles.
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
      var diffMs = now - created;
      var diffDays = diffMs / (1000 * 60 * 60 * 24);
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
    applyConsent(consent);
  }

  function applyConsent(consent) {
    window.dispatchEvent(new CustomEvent('cookieConsentChange', { detail: consent }));
  }

  function createStyles() {
    if (document.getElementById('cc-styles')) return;
    var style = document.createElement('style');
    style.id = 'cc-styles';
    style.textContent = [
      '@keyframes cc-slideUp { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }',
      '@keyframes cc-fadeIn { from { opacity: 0; } to { opacity: 1; } }',
      '@keyframes cc-fadeOut { from { opacity: 1; } to { opacity: 0; } }',

      '.cc-banner { position: fixed; bottom: 0; left: 0; right: 0; z-index: 99999; background: #ffffff; box-shadow: 0 -4px 24px rgba(0,0,0,0.12); padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; animation: cc-slideUp 0.4s ease-out; border-top: 1px solid #e5e7eb; }',
      '.cc-banner-inner { max-width: 1200px; margin: 0 auto; padding: 20px 24px; display: flex; flex-direction: column; gap: 16px; }',
      '.cc-banner-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }',
      '.cc-banner-text { flex: 1; }',
      '.cc-banner-title { font-size: 17px; font-weight: 600; color: #111827; margin: 0 0 6px 0; }',
      '.cc-banner-desc { font-size: 13.5px; color: #4b5563; line-height: 1.55; margin: 0; }',
      '.cc-banner-desc a { color: #2563eb; text-decoration: underline; text-underline-offset: 2px; }',
      '.cc-banner-desc a:hover { color: #1d4ed8; }',
      '.cc-banner-actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }',
      '.cc-btn { padding: 9px 18px; border-radius: 8px; font-size: 13.5px; font-weight: 500; cursor: pointer; transition: all 0.2s ease; border: none; white-space: nowrap; }',
      '.cc-btn:hover { transform: translateY(-1px); }',
      '.cc-btn:active { transform: translateY(0); }',
      '.cc-btn-reject { background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; }',
      '.cc-btn-reject:hover { background: #e5e7eb; }',
      '.cc-btn-necessary { background: #f9fafb; color: #374151; border: 1px solid #d1d5db; }',
      '.cc-btn-necessary:hover { background: #e5e7eb; }',
      '.cc-btn-configure { background: transparent; color: #2563eb; border: 1px solid #bfdbfe; padding: 9px 14px; }',
      '.cc-btn-configure:hover { background: #eff6ff; }',
      '.cc-btn-accept { background: #2563eb; color: #ffffff; }',
      '.cc-btn-accept:hover { background: #1d4ed8; }',

      '.cc-modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 100000; display: flex; align-items: center; justify-content: center; animation: cc-fadeIn 0.25s ease-out; padding: 16px; }',
      '.cc-modal { background: #ffffff; border-radius: 14px; width: 100%; max-width: 480px; max-height: 85vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.2); animation: cc-slideUp 0.3s ease-out; }',
      '.cc-modal-header { padding: 22px 24px 0 24px; display: flex; justify-content: space-between; align-items: center; }',
      '.cc-modal-title { font-size: 18px; font-weight: 600; color: #111827; margin: 0; }',
      '.cc-modal-close { background: none; border: none; font-size: 22px; color: #6b7280; cursor: pointer; padding: 4px 8px; border-radius: 6px; line-height: 1; }',
      '.cc-modal-close:hover { background: #f3f4f6; color: #374151; }',
      '.cc-modal-body { padding: 18px 24px; }',
      '.cc-modal-desc { font-size: 13.5px; color: #6b7280; line-height: 1.5; margin: 0 0 20px 0; }',

      '.cc-category { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid #f3f4f6; }',
      '.cc-category:last-child { border-bottom: none; }',
      '.cc-category-info { flex: 1; padding-right: 16px; }',
      '.cc-category-name { font-size: 14px; font-weight: 500; color: #111827; margin: 0 0 3px 0; }',
      '.cc-category-desc { font-size: 12.5px; color: #9ca3af; margin: 0; line-height: 1.4; }',

      '.cc-toggle { position: relative; width: 44px; height: 24px; flex-shrink: 0; }',
      '.cc-toggle input { opacity: 0; width: 0; height: 0; }',
      '.cc-toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: #d1d5db; border-radius: 12px; transition: 0.3s; }',
      '.cc-toggle-slider::before { content: ""; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px; background: #ffffff; border-radius: 50%; transition: 0.3s; }',
      '.cc-toggle input:checked + .cc-toggle-slider { background: #2563eb; }',
      '.cc-toggle input:checked + .cc-toggle-slider::before { transform: translateX(20px); }',
      '.cc-toggle input:disabled + .cc-toggle-slider { background: #2563eb; opacity: 0.6; cursor: not-allowed; }',
      '.cc-toggle input:disabled + .cc-toggle-slider::before { transform: translateX(20px); }',

      '.cc-modal-footer { padding: 0 24px 22px 24px; display: flex; justify-content: flex-end; }',
      '.cc-btn-save { background: #2563eb; color: #ffffff; padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; border: none; transition: all 0.2s ease; }',
      '.cc-btn-save:hover { background: #1d4ed8; transform: translateY(-1px); }',
      '.cc-btn-save:active { transform: translateY(0); }',

      '@media (max-width: 600px) {',
      '  .cc-banner-inner { padding: 16px; gap: 12px; }',
      '  .cc-banner-title { font-size: 15px; }',
      '  .cc-banner-desc { font-size: 13px; }',
      '  .cc-banner-actions { flex-direction: column; align-items: stretch; }',
      '  .cc-btn { text-align: center; padding: 11px 18px; }',
      '  .cc-modal { max-width: 100%; border-radius: 12px; }',
      '  .cc-modal-header { padding: 18px 18px 0 18px; }',
      '  .cc-modal-body { padding: 16px 18px; }',
      '  .cc-modal-footer { padding: 0 18px 18px 18px; }',
      '  .cc-category { flex-direction: column; align-items: flex-start; gap: 10px; }',
      '  .cc-toggle { align-self: flex-end; }',
      '}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function createBanner() {
    if (document.getElementById('cc-banner')) return;

    var banner = document.createElement('div');
    banner.id = 'cc-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-label', 'Consentimiento de cookies');
    banner.innerHTML = [
      '<div class="cc-banner-inner">',
      '  <div class="cc-banner-header">',
      '    <div class="cc-banner-text">',
      '      <h2 class="cc-banner-title">Usamos Cookies</h2>',
      '      <p class="cc-banner-desc">',
      '        Utilizamos cookies para mejorar su experiencia, analizar el tr\u00e1fico y personalizar el contenido. Al continuar navegando, usted acepta nuestro uso de cookies. ',
      '        <a href="/legal/politica-cookies.html" target="_blank" rel="noopener">Pol\u00edtica de Cookies</a>',
      '      </p>',
      '    </div>',
      '  </div>',
      '  <div class="cc-banner-actions">',
      '    <button class="cc-btn cc-btn-reject" id="cc-btn-reject">Rechazar</button>',
      '    <button class="cc-btn cc-btn-necessary" id="cc-btn-necessary">Solo Necesarias</button>',
      '    <button class="cc-btn cc-btn-configure" id="cc-btn-configure">Configurar</button>',
      '    <button class="cc-btn cc-btn-accept" id="cc-btn-accept">Aceptar Todas</button>',
      '  </div>',
      '</div>'
    ].join('');

    document.body.appendChild(banner);

    document.getElementById('cc-btn-reject').addEventListener('click', function () {
      saveConsent({ necessary: true, analytics: false, marketing: false });
      removeBanner();
    });

    document.getElementById('cc-btn-necessary').addEventListener('click', function () {
      saveConsent({ necessary: true, analytics: false, marketing: false });
      removeBanner();
    });

    document.getElementById('cc-btn-configure').addEventListener('click', function () {
      openModal();
    });

    document.getElementById('cc-btn-accept').addEventListener('click', function () {
      saveConsent({ necessary: true, analytics: true, marketing: true });
      removeBanner();
    });
  }

  function removeBanner() {
    var banner = document.getElementById('cc-banner');
    if (!banner) return;
    banner.style.animation = 'cc-slideUp 0.3s ease-in reverse forwards';
    setTimeout(function () { banner.remove(); }, 300);
  }

  function openModal() {
    if (document.getElementById('cc-modal-overlay')) return;

    var stored = getStoredConsent();
    var analyticsChecked = stored ? stored.analytics : false;
    var marketingChecked = stored ? stored.marketing : false;

    var overlay = document.createElement('div');
    overlay.id = 'cc-modal-overlay';
    overlay.innerHTML = [
      '<div class="cc-modal" role="dialog" aria-label="Configuraci\u00f3n de cookies">',
      '  <div class="cc-modal-header">',
      '    <h3 class="cc-modal-title">Configurar Cookies</h3>',
      '    <button class="cc-modal-close" id="cc-modal-close" aria-label="Cerrar">&times;</button>',
      '  </div>',
      '  <div class="cc-modal-body">',
      '    <p class="cc-modal-desc">',
      '      Gestione sus preferencias de cookies. Las cookies necesarias son esenciales para el funcionamiento del sitio y no pueden desactivarse.',
      '    </p>',
      '    <div class="cc-category">',
      '      <div class="cc-category-info">',
      '        <p class="cc-category-name">Necesarias</p>',
      '        <p class="cc-category-desc">Imprescindibles para el funcionamiento b\u00e1sico del sitio.</p>',
      '      </div>',
      '      <label class="cc-toggle">',
      '        <input type="checkbox" checked disabled>',
      '        <span class="cc-toggle-slider"></span>',
      '      </label>',
      '    </div>',
      '    <div class="cc-category">',
      '      <div class="cc-category-info">',
      '        <p class="cc-category-name">Anal\u00edticas</p>',
      '        <p class="cc-category-desc">Nos ayudan a entender c\u00f3mo utiliza el sitio para mejorar la experiencia.</p>',
      '      </div>',
      '      <label class="cc-toggle">',
      '        <input type="checkbox" id="cc-toggle-analytics"' + (analyticsChecked ? ' checked' : '') + '>',
      '        <span class="cc-toggle-slider"></span>',
      '      </label>',
      '    </div>',
      '    <div class="cc-category">',
      '      <div class="cc-category-info">',
      '        <p class="cc-category-name">Marketing</p>',
      '        <p class="cc-category-desc">Utilizadas para mostrar publicidad relevante y medir campa\u00f1as.</p>',
      '      </div>',
      '      <label class="cc-toggle">',
      '        <input type="checkbox" id="cc-toggle-marketing"' + (marketingChecked ? ' checked' : '') + '>',
      '        <span class="cc-toggle-slider"></span>',
      '      </label>',
      '    </div>',
      '  </div>',
      '  <div class="cc-modal-footer">',
      '    <button class="cc-btn-save" id="cc-btn-save">Guardar Preferencias</button>',
      '  </div>',
      '</div>'
    ].join('');

    document.body.appendChild(overlay);

    document.getElementById('cc-modal-close').addEventListener('click', closeModal);
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', function handler(e) {
      if (e.key === 'Escape') {
        closeModal();
        document.removeEventListener('keydown', handler);
      }
    });

    document.getElementById('cc-btn-save').addEventListener('click', function () {
      var analytics = document.getElementById('cc-toggle-analytics').checked;
      var marketing = document.getElementById('cc-toggle-marketing').checked;
      saveConsent({ necessary: true, analytics: analytics, marketing: marketing });
      closeModal();
      removeBanner();
    });
  }

  function closeModal() {
    var overlay = document.getElementById('cc-modal-overlay');
    if (!overlay) return;
    overlay.style.animation = 'cc-fadeOut 0.2s ease-in forwards';
    setTimeout(function () { overlay.remove(); }, 200);
  }

  function init() {
    var consent = getStoredConsent();
    if (consent) {
      applyConsent(consent);
      return;
    }
    createStyles();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', createBanner);
    } else {
      createBanner();
    }
  }

  window.CookieConsent = {
    getConsent: getStoredConsent,
    reset: function () {
      localStorage.removeItem(STORAGE_KEY);
    },
    show: function () {
      createStyles();
      createBanner();
    }
  };

  init();
})();
