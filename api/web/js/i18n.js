/**
 * i18n.js - Internationalization client library for Last Mile Delivery
 * Supports: es (Spanish), en (English), pt (Portuguese)
 */
class I18n {
    constructor(defaultLang = 'es') {
        this.lang = localStorage.getItem('lastmile_lang') || defaultLang;
        this.translations = {};
        this.listeners = [];
    }

    async load(lang) {
        try {
            const resp = await fetch(`/i18n/${lang}.json`);
            if (!resp.ok) throw new Error(`Failed to load ${lang}.json`);
            this.translations[lang] = await resp.json();
            return true;
        } catch (e) {
            console.error(`i18n load error for ${lang}:`, e);
            return false;
        }
    }

    async init() {
        await Promise.all([this.load('es'), this.load('en'), this.load('pt')]);
        this.applyTranslations();
        return this;
    }

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.lang = lang;
            localStorage.setItem('lastmile_lang', lang);
            this.applyTranslations();
            this.listeners.forEach(fn => fn(lang));
        }
    }

    t(key) {
        const keys = key.split('.');
        let val = this.translations[this.lang];
        for (const k of keys) {
            if (val && typeof val === 'object') val = val[k];
            else return key;
        }
        return val || key;
    }

    onLanguageChange(fn) {
        this.listeners.push(fn);
    }

    applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const translated = this.t(key);
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translated;
            } else {
                el.textContent = translated;
            }
        });
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            el.title = this.t(el.getAttribute('data-i18n-title'));
        });
        document.documentElement.lang = this.lang;
    }

    formatDate(date, options = {}) {
        const defaults = { year: 'numeric', month: 'short', day: 'numeric' };
        const locale = { es: 'es-MX', en: 'en-US', pt: 'pt-BR' }[this.lang] || 'es-MX';
        return new Date(date).toLocaleDateString(locale, { ...defaults, ...options });
    }

    formatTime(date, options = {}) {
        const defaults = { hour: '2-digit', minute: '2-digit' };
        const locale = { es: 'es-MX', en: 'en-US', pt: 'pt-BR' }[this.lang] || 'es-MX';
        return new Date(date).toLocaleTimeString(locale, { ...defaults, ...options });
    }

    formatDateTime(date) {
        return `${this.formatDate(date)} ${this.formatTime(date)}`;
    }

    formatCurrency(amount, currency) {
        const locale = { es: 'es-MX', en: 'en-US', pt: 'pt-BR' }[this.lang] || 'es-MX';
        const curr = currency || { es: 'MXN', en: 'USD', pt: 'BRL' }[this.lang] || 'MXN';
        return new Intl.NumberFormat(locale, { style: 'currency', currency: curr }).format(amount);
    }

    formatNumber(num) {
        const locale = { es: 'es-MX', en: 'en-US', pt: 'pt-BR' }[this.lang] || 'es-MX';
        return new Intl.NumberFormat(locale).format(num);
    }

    getLanguageName(lang) {
        const names = { es: 'Espanol', en: 'English', pt: 'Portugues' };
        return names[lang] || lang;
    }

    getAvailableLanguages() {
        return [
            { code: 'es', name: 'Espanol', flag: '🇲🇽' },
            { code: 'en', name: 'English', flag: '🇺🇸' },
            { code: 'pt', name: 'Portugues', flag: '🇧🇷' },
        ];
    }

    getCountryCurrency(countryCode) {
        const map = {
            MX: 'MXN', BR: 'BRL', CO: 'COP', AR: 'ARS',
            CL: 'CLP', PE: 'PEN', UY: 'UYU', EC: 'USD'
        };
        return map[countryCode] || 'USD';
    }
}

window.i18n = new I18n();
