/**
 * i18n.js - Internationalization client library for Last Mile Delivery
 * Supports: es, en, pt, fr, de, zh, ja, ko, ar, hi, it, nl (12 languages)
 */
class I18n {
    constructor(defaultLang = 'es') {
        this.lang = localStorage.getItem('lastmile_lang') || defaultLang;
        this.translations = {};
        this.listeners = [];
        this.rtlLanguages = ['ar'];
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
        const langs = ['es', 'en', 'pt', 'fr', 'de', 'zh', 'ja', 'ko', 'ar', 'hi', 'it', 'nl'];
        await Promise.all(langs.map(l => this.load(l)));
        this.applyTranslations();
        return this;
    }

    isRTL() {
        return this.rtlLanguages.includes(this.lang);
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
        document.documentElement.dir = this.isRTL() ? 'rtl' : 'ltr';
    }

    formatDate(date, options = {}) {
        const defaults = { year: 'numeric', month: 'short', day: 'numeric' };
        const locale = this._getLocale();
        return new Date(date).toLocaleDateString(locale, { ...defaults, ...options });
    }

    formatTime(date, options = {}) {
        const defaults = { hour: '2-digit', minute: '2-digit' };
        const locale = this._getLocale();
        return new Date(date).toLocaleTimeString(locale, { ...defaults, ...options });
    }

    formatDateTime(date) {
        return `${this.formatDate(date)} ${this.formatTime(date)}`;
    }

    formatCurrency(amount, currency) {
        const locale = this._getLocale();
        const curr = currency || this._getCurrency();
        return new Intl.NumberFormat(locale, { style: 'currency', currency: curr }).format(amount);
    }

    formatNumber(num) {
        const locale = this._getLocale();
        return new Intl.NumberFormat(locale).format(num);
    }

    _getLocale() {
        const map = {
            es: 'es-MX', en: 'en-US', pt: 'pt-BR', fr: 'fr-FR',
            de: 'de-DE', zh: 'zh-CN', ja: 'ja-JP', ko: 'ko-KR',
            ar: 'ar-SA', hi: 'hi-IN', it: 'it-IT', nl: 'nl-NL'
        };
        return map[this.lang] || 'es-MX';
    }

    _getCurrency() {
        const map = {
            es: 'MXN', en: 'USD', pt: 'BRL', fr: 'EUR',
            de: 'EUR', zh: 'CNY', ja: 'JPY', ko: 'KRW',
            ar: 'SAR', hi: 'INR', it: 'EUR', nl: 'EUR'
        };
        return map[this.lang] || 'MXN';
    }

    getLanguageName(lang) {
        const names = {
            es: 'Español', en: 'English', pt: 'Português', fr: 'Français',
            de: 'Deutsch', zh: '中文', ja: '日本語', ko: '한국어',
            ar: 'العربية', hi: 'हिन्दी', it: 'Italiano', nl: 'Nederlands'
        };
        return names[lang] || lang;
    }

    getAvailableLanguages() {
        return [
            { code: 'es', name: 'Español', flag: '🇲🇽' },
            { code: 'en', name: 'English', flag: '🇺🇸' },
            { code: 'pt', name: 'Português', flag: '🇧🇷' },
            { code: 'fr', name: 'Français', flag: '🇫🇷' },
            { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
            { code: 'zh', name: '中文', flag: '🇨🇳' },
            { code: 'ja', name: '日本語', flag: '🇯🇵' },
            { code: 'ko', name: '한국어', flag: '🇰🇷' },
            { code: 'ar', name: 'العربية', flag: '🇸🇦' },
            { code: 'hi', name: 'हिन्दी', flag: '🇮🇳' },
            { code: 'it', name: 'Italiano', flag: '🇮🇹' },
            { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
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
