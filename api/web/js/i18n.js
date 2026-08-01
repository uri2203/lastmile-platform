/**
 * LAST MILE DELIVERY - i18n Client Library
 * Multi-language support for the platform.
 */

class I18n {
  constructor(defaultLang = 'es') {
    this.currentLang = localStorage.getItem('lastmile_lang') || defaultLang;
    this.translations = {};
    this.loaded = false;
  }

  async loadTranslations(lang) {
    try {
      const response = await fetch(`/i18n/${lang}.json`);
      if (!response.ok) throw new Error(`Failed to load ${lang}.json`);
      this.translations[lang] = await response.json();
      this.loaded = true;
      return true;
    } catch (error) {
      console.error(`[i18n] Error loading ${lang}:`, error);
      return false;
    }
  }

  async init() {
    await this.loadTranslations(this.currentLang);
    this.updateDOM();
  }

  setLanguage(lang) {
    this.currentLang = lang;
    localStorage.setItem('lastmile_lang', lang);
    this.updateDOM();
  }

  getLanguage() {
    return this.currentLang;
  }

  t(key) {
    const keys = key.split('.');
    let value = this.translations[this.currentLang];

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return key;
      }
    }

    return value || key;
  }

  updateDOM() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(el => {
      const key = el.getAttribute('data-i18n');
      const translation = this.t(key);
      if (translation !== key) {
        if (el.tagName === 'INPUT' && el.type !== 'button') {
          el.placeholder = translation;
        } else {
          el.textContent = translation;
        }
      }
    });

    const placeholders = document.querySelectorAll('[data-i18n-placeholder]');
    placeholders.forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      const translation = this.t(key);
      if (translation !== key) {
        el.placeholder = translation;
      }
    });

    const titles = document.querySelectorAll('[data-i18n-title]');
    titles.forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      const translation = this.t(key);
      if (translation !== key) {
        el.title = translation;
      }
    });
  }

  getLanguages() {
    return [
      { code: 'es', name: 'Espanol', flag: '🇲🇽' },
      { code: 'en', name: 'English', flag: '🇺🇸' },
      { code: 'pt', name: 'Portugues', flag: '🇧🇷' }
    ];
  }

  formatDate(date, options = {}) {
    const defaultOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    };
    return new Date(date).toLocaleDateString(this.currentLang, { ...defaultOptions, ...options });
  }

  formatCurrency(amount, currency = 'MXN') {
    const locales = {
      'es': 'es-MX',
      'en': 'en-US',
      'pt': 'pt-BR'
    };
    return new Intl.NumberFormat(locales[this.currentLang] || 'es-MX', {
      style: 'currency',
      currency: currency
    }).format(amount);
  }

  formatNumber(number) {
    const locales = {
      'es': 'es-MX',
      'en': 'en-US',
      'pt': 'pt-BR'
    };
    return new Intl.NumberFormat(locales[this.currentLang] || 'es-MX').format(number);
  }
}

window.i18n = new I18n();

document.addEventListener('DOMContentLoaded', () => {
  window.i18n.init();
});

function createLanguageSelector() {
  const selector = document.createElement('div');
  selector.className = 'language-selector';
  selector.style.cssText = 'position:fixed;top:10px;right:10px;z-index:1000;';

  const currentLang = window.i18n.getLanguage();
  const languages = window.i18n.getLanguages();

  selector.innerHTML = `
    <select onchange="window.i18n.setLanguage(this.value); location.reload();" style="padding:5px 10px;border-radius:5px;border:1px solid #ccc;background:white;font-size:12px;">
      ${languages.map(lang => `
        <option value="${lang.code}" ${lang.code === currentLang ? 'selected' : ''}>
          ${lang.flag} ${lang.name}
        </option>
      `).join('')}
    </select>
  `;

  document.body.appendChild(selector);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createLanguageSelector);
} else {
  createLanguageSelector();
}
