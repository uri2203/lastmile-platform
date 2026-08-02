/**
 * cookie-consent.js - GDPR/LGPD/CCPA compliant cookie consent banner
 * Supports: es, en, pt, fr, de, zh, ja, ko, ar, hi, it, nl (12 languages)
 * Compliant with: EU ePrivacy Directive, GDPR Art. 7, LGPD Art. 8, CCPA §1798.120
 */
class CookieConsent {
    constructor() {
        this STORAGE_KEY = 'lastmile_cookie_consent';
        this.banner = null;
        this.preferences = this.load();
    }

    translations = {
        es: {
            banner_title: 'Usamos Cookies',
            banner_desc: 'Utilizamos cookies esenciales para el funcionamiento del sitio. Puedes gestionar tus preferencias. Al continuar, aceptas nuestra',
            link_terminos: 'Politica de Privacidad',
            accept_all: 'Aceptar Todas',
            reject_all: 'Solo Esenciales',
            manage: 'Preferencias',
            save: 'Guardar Preferencias',
            close: 'Cerrar',
            category_essential: 'Cookies Esenciales',
            category_essential_desc: 'Necesarias para el funcionamiento del sitio. No se pueden desactivar.',
            category_functional: 'Cookies Funcionales',
            category_functional_desc: 'Mejoran la experiencia del usuario (idioma, tema).',
            category_analytics: 'Cookies de Analitica',
            category_analytics_desc: 'Nos ayudan a entender como se usa el sitio.',
            category_marketing: 'Cookies de Marketing',
            category_marketing_desc: 'Publicidad personalizada y remarketing.',
            privacy_link: 'Politica de Privacidad',
            cookies_link: 'Politica de Cookies'
        },
        en: {
            banner_title: 'We Use Cookies',
            banner_desc: 'We use essential cookies for site functionality. You can manage your preferences. By continuing, you accept our',
            link_terminos: 'Privacy Policy',
            accept_all: 'Accept All',
            reject_all: 'Essential Only',
            manage: 'Preferences',
            save: 'Save Preferences',
            close: 'Close',
            category_essential: 'Essential Cookies',
            category_essential_desc: 'Required for site functionality. Cannot be disabled.',
            category_functional: 'Functional Cookies',
            category_functional_desc: 'Enhance user experience (language, theme).',
            category_analytics: 'Analytics Cookies',
            category_analytics_desc: 'Help us understand how the site is used.',
            category_marketing: 'Marketing Cookies',
            category_marketing_desc: 'Personalized advertising and remarketing.',
            privacy_link: 'Privacy Policy',
            cookies_link: 'Cookie Policy'
        },
        pt: {
            banner_title: 'Usamos Cookies',
            banner_desc: 'Usamos cookies essenciais para o funcionamento do site. Voce pode gerenciar suas preferencias. Ao continuar, voce aceita nossa',
            link_terminos: 'Politica de Privacidade',
            accept_all: 'Aceitar Todas',
            reject_all: 'Apenas Essenciais',
            manage: 'Preferencias',
            save: 'Salvar Preferencias',
            close: 'Fechar',
            category_essential: 'Cookies Essenciais',
            category_essential_desc: 'Necessarias para o funcionamento do site. Nao podem ser desativadas.',
            category_functional: 'Cookies Funcionais',
            category_functional_desc: 'Melhoram a experiencia do usuario (idioma, tema).',
            category_analytics: 'Cookies de Analise',
            category_analytics_desc: 'Nos ajudam a entender como o site e usado.',
            category_marketing: 'Cookies de Marketing',
            category_marketing_desc: 'Publicidade personalizada e remarketing.',
            privacy_link: 'Politica de Privacidade',
            cookies_link: 'Politica de Cookies'
        },
        fr: {
            banner_title: 'Nous Utilisons des Cookies',
            banner_desc: 'Nous utilisons des cookies essentiels pour le fonctionnement du site. Vous pouvez gerer vos preferences. En continuant, vous acceptez notre',
            link_terminos: 'Politique de Confidentialite',
            accept_all: 'Tout Accepter',
            reject_all: 'Essentiels Uniquement',
            manage: 'Preferences',
            save: 'Enregistrer',
            close: 'Fermer',
            category_essential: 'Cookies Essentiels',
            category_essential_desc: 'Necessaires au fonctionnement du site. Ne peuvent pas etre desactives.',
            category_functional: 'Cookies Fonctionnels',
            category_functional_desc: 'Ameliorent l\'experience utilisateur (langue, theme).',
            category_analytics: 'Cookies d\'Analyse',
            category_analytics_desc: 'Nous aident a comprendre comment le site est utilise.',
            category_marketing: 'Cookies Marketing',
            category_marketing_desc: 'Publicite personnalisee et remarketing.',
            privacy_link: 'Politique de Confidentialite',
            cookies_link: 'Politique de Cookies'
        },
        de: {
            banner_title: 'Wir Verwenden Cookies',
            banner_desc: 'Wir verwenden essentielle Cookies fur die Funktionalitat der Seite. Sie konnen Ihre Einstellungen verwalten. Durch Fortfahren akzeptieren Sie unsere',
            link_terminos: 'Datenschutzrichtlinie',
            accept_all: 'Alle Akzeptieren',
            reject_all: 'Nur Essentielle',
            manage: 'Einstellungen',
            save: 'Speichern',
            close: 'Schliessen',
            category_essential: 'Essentielle Cookies',
            category_essential_desc: 'Fur die Seitenfunktionalitat erforderlich. Konnen nicht deaktiviert werden.',
            category_functional: 'Funktionale Cookies',
            category_functional_desc: 'Verbessern die Benutzererfahrung (Sprache, Theme).',
            category_analytics: 'Analyse-Cookies',
            category_analytics_desc: 'Helfen uns zu verstehen, wie die Seite genutzt wird.',
            category_marketing: 'Marketing-Cookies',
            category_marketing_desc: 'Personalisierte Werbung und Remarketing.',
            privacy_link: 'Datenschutzrichtlinie',
            cookies_link: 'Cookie-Richtlinie'
        },
        it: {
            banner_title: 'Utilizziamo i Cookie',
            banner_desc: 'Utilizziamo cookie essenziali per il funzionamento del sito. Puoi gestire le tue preferenze. Continuando, accetti la nostra',
            link_terminos: 'Informativa sulla Privacy',
            accept_all: 'Accetta Tutti',
            reject_all: 'Solo Essenziali',
            manage: 'Preferenze',
            save: 'Salva',
            close: 'Chiudi',
            category_essential: 'Cookie Essenziali',
            category_essential_desc: 'Necessari per il funzionamento del sito. Non possono essere disattivati.',
            category_functional: 'Cookie Funzionali',
            category_functional_desc: 'Migliorano l\'esperienza utente (lingua, tema).',
            category_analytics: 'Cookie di Analisi',
            category_analytics_desc: 'Ci aiutano a capire come viene utilizzato il sito.',
            category_marketing: 'Cookie di Marketing',
            category_marketing_desc: 'Pubblicita personalizzata e remarketing.',
            privacy_link: 'Informativa sulla Privacy',
            cookies_link: 'Informativa sui Cookie'
        },
        nl: {
            banner_title: 'We Gebruiken Cookies',
            banner_desc: 'We gebruiken essentiele cookies voor de werking van de site. U kunt uw voorkeuren beheren. Door verder te gaan, accepteert u ons',
            link_terminos: 'Privacybeleid',
            accept_all: 'Alles Accepteren',
            reject_all: 'Alleen Essentieel',
            manage: 'Voorkeuren',
            save: 'Opslaan',
            close: 'Sluiten',
            category_essential: 'Essentiele Cookies',
            category_essential_desc: 'Nodig voor de werking van de site. Kunnen niet worden uitgeschakeld.',
            category_functional: 'Functionele Cookies',
            category_functional_desc: 'Verbeteren de gebruikerservaring (taal, thema).',
            category_analytics: 'Analyse Cookies',
            category_analytics_desc: 'Helpen ons te begrijpen hoe de site wordt gebruikt.',
            category_marketing: 'Marketing Cookies',
            category_marketing_desc: 'Gepersonaliseerde advertenties en remarketing.',
            privacy_link: 'Privacybeleid',
            cookies_link: 'Cookiebeleid'
        },
        zh: {
            banner_title: '我们使用Cookie',
            banner_desc: '我们使用必要的Cookie来确保网站正常运行。您可以管理您的偏好设置。继续即表示您接受我们的',
            link_terminos: '隐私政策',
            accept_all: '全部接受',
            reject_all: '仅必要',
            manage: '偏好设置',
            save: '保存',
            close: '关闭',
            category_essential: '必要Cookie',
            category_essential_desc: '网站运行所必需。无法禁用。',
            category_functional: '功能性Cookie',
            category_functional_desc: '改善用户体验（语言、主题）。',
            category_analytics: '分析Cookie',
            category_analytics_desc: '帮助我们了解网站的使用情况。',
            category_marketing: '营销Cookie',
            category_marketing_desc: '个性化广告和再营销。',
            privacy_link: '隐私政策',
            cookies_link: 'Cookie政策'
        },
        ja: {
            banner_title: 'Cookieを使用しています',
            banner_desc: 'サイトの機能のために必須Cookieを使用しています。設定は管理できます。続行すると、以下に同意したことになります',
            link_terminos: 'プライバシーポリシー',
            accept_all: 'すべて許可',
            reject_all: '必須のみ',
            manage: '設定',
            save: '保存',
            close: '閉じる',
            category_essential: '必須Cookie',
            category_essential_desc: 'サイトの動作に必要。無効にできません。',
            category_functional: '機能Cookie',
            category_functional_desc: 'ユーザーエクスペリエンスを向上（言語、テーマ）。',
            category_analytics: '分析Cookie',
            category_analytics_desc: 'サイトの利用状況の理解に役立ちます。',
            category_marketing: 'マーケティングCookie',
            category_marketing_desc: 'パーソナライズされた広告とリマーケティング。',
            privacy_link: 'プライバシーポリシー',
            cookies_link: 'Cookieポリシー'
        },
        ko: {
            banner_title: 'Cookie를 사용하고 있습니다',
            banner_desc: '사이트 기능을 위한 필수 Cookie를 사용합니다. 기본 설정을 관리할 수 있습니다. 계속하면 다음에 동의하는 것입니다',
            link_terminos: '개인정보처리방침',
            accept_all: '모두 허용',
            reject_all: '필수만',
            manage: '기본 설정',
            save: '저장',
            close: '닫기',
            category_essential: '필수 Cookie',
            category_essential_desc: '사이트 작동에 필요. 비활성화할 수 없습니다.',
            category_functional: '기능 Cookie',
            category_functional_desc: '사용자 경험 향상 (언어, 테마).',
            category_analytics: '분석 Cookie',
            category_analytics_desc: '사이트 사용 방식 이해에 도움.',
            category_marketing: '마케팅 Cookie',
            category_marketing_desc: '개인화된 광고 및 리마케팅.',
            privacy_link: '개인정보처리방침',
            cookies_link: 'Cookie 정책'
        },
        ar: {
            banner_title: 'نستخدم ملفات تعريف الارتباط',
            banner_desc: 'نستخدم ملفات تعريف الارتباط الضرورية لعمل الموقع. يمكنك إدارة تفضيلاتك. بالمتابعة، أنت توافق على',
            link_terminos: 'سياسة الخصوصية',
            accept_all: 'قبول الكل',
            reject_all: 'الضرورية فقط',
            manage: 'التفضيلات',
            save: 'حفظ',
            close: 'إغلاق',
            category_essential: 'ملفات تعريف الارتباط الضرورية',
            category_essential_desc: 'ضرورية لعمل الموقع. لا يمكن تعطيلها.',
            category_functional: 'ملفات تعريف الارتباط الوظيفية',
            category_functional_desc: 'تحسين تجربة المستخدم (اللغة، المظهر).',
            category_analytics: 'ملفات تعريف الارتباط التحليلية',
            category_analytics_desc: 'تساعدنا في فهم كيفية استخدام الموقع.',
            category_marketing: 'ملفات تعريف الارتباط التسويقية',
            category_marketing_desc: 'إعلانات مخصصة إعادة الاستهداف.',
            privacy_link: 'سياسة الخصوصية',
            cookies_link: 'سياسة ملفات تعريف الارتباط'
        },
        hi: {
            banner_title: 'हम कुकीज़ का उपयोग करते हैं',
            banner_desc: 'हम साइट के कार्य के लिए आवश्यक कुकीज़ का उपयोग करते हैं। आप अपनी प्राथमिकताएँ प्रबंधित कर सकते हैं। जारी रखकर, आप हमारी',
            link_terminos: 'गोपनीयता नीति',
            accept_all: 'सभी स्वीकार करें',
            reject_all: 'केवल आवश्यक',
            manage: 'प्राथमिकताएँ',
            save: 'सहेजें',
            close: 'बंद करें',
            category_essential: 'आवश्यक कुकीज़',
            category_essential_desc: 'साइट के कार्य के लिए आवश्यक। अक्षम नहीं किया जा सकता।',
            category_functional: 'कार्यात्मक कुकीज़',
            category_functional_desc: 'उपयोगकर्ता अनुभव में सुधार (भाषा, थीम)।',
            category_analytics: 'विश्लेषण कुकीज़',
            category_analytics_desc: 'हमें समझने में मदद करती हैं कि साइट का उपयोग कैसे किया जाता है।',
            category_marketing: 'मार्केटिंग कुकीज़',
            category_marketing_desc: 'व्यक्तिगत विज्ञापन और रीमार्केटिंग।',
            privacy_link: 'गोपनीयता नीति',
            cookies_link: 'कुकी नीति'
        }
    };

    t(key) {
        const lang = localStorage.getItem('lastmile_lang') || 'es';
        return (this.translations[lang] && this.translations[lang][key]) || this.translations['es'][key] || key;
    }

    load() {
        try {
            const raw = localStorage.getItem(this.STORAGE_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch { return null; }
    }

    save(prefs) {
        this.preferences = prefs;
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(prefs));
    }

    hasConsent() {
        return this.preferences !== null;
    }

    getConsent(category) {
        if (!this.preferences) return category === 'essential';
        return this.preferences[category] === true;
    }

    showBanner() {
        if (this.hasConsent()) return;

        this.banner = document.createElement('div');
        this.banner.id = 'cookie-consent-banner';
        this.banner.innerHTML = `
        <style>
        #cookie-consent-banner{position:fixed;bottom:0;left:0;right:0;z-index:99999;background:var(--bg-secondary,#1a1a2e);border-top:1px solid var(--border-primary,#333);padding:20px 24px;box-shadow:0 -4px 20px rgba(0,0,0,0.3);animation:slideUp .3s ease}
        @keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}
        .cc-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
        .cc-text{flex:1;min-width:300px;font-size:13px;color:var(--text-primary,#e0e0e0);line-height:1.5}
        .cc-text a{color:var(--accent,#6366f1);text-decoration:underline}
        .cc-buttons{display:flex;gap:8px;flex-wrap:wrap}
        .cc-btn{padding:8px 16px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;border:none;transition:all .15s}
        .cc-btn-accept{background:#6366f1;color:#fff}.cc-btn-accept:hover{opacity:.9}
        .cc-btn-reject{background:transparent;color:var(--text-secondary,#999);border:1px solid var(--border-secondary,#555)}.cc-btn-reject:hover{color:var(--text-primary,#fff);border-color:var(--text-primary,#fff)}
        .cc-btn-manage{background:transparent;color:var(--accent,#6366f1);border:1px solid var(--accent,#6366f1)}.cc-btn-manage:hover{background:var(--accent,#6366f1);color:#fff}
        #cc-prefs{display:none;position:fixed;bottom:0;left:0;right:0;z-index:99999;background:var(--bg-secondary,#1a1a2e);border-top:1px solid var(--border-primary,#333);padding:24px;box-shadow:0 -4px 20px rgba(0,0,0,0.3);max-height:70vh;overflow-y:auto}
        .cc-pref-inner{max-width:800px;margin:0 auto}
        .cc-pref-title{font-size:16px;font-weight:600;color:var(--text-primary,#fff);margin-bottom:16px}
        .cc-pref-item{display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid var(--border-primary,#333)}
        .cc-pref-label{font-size:13px;color:var(--text-primary,#e0e0e0)}
        .cc-pref-desc{font-size:11px;color:var(--text-muted,#888);margin-top:2px}
        .cc-toggle{position:relative;width:36px;height:20px;background:var(--border-primary,#555);border-radius:10px;cursor:pointer;transition:.2s;flex-shrink:0}
        .cc-toggle.active{background:#6366f1}
        .cc-toggle::after{content:'';position:absolute;width:16px;height:16px;background:#fff;border-radius:50%;top:2px;left:2px;transition:.2s}
        .cc-toggle.active::after{transform:translateX(16px)}
        .cc-toggle.disabled{opacity:.5;cursor:not-allowed}
        .cc-pref-buttons{display:flex;gap:8px;margin-top:16px;justify-content:flex-end}
        </style>
        <div class="cc-inner">
            <div class="cc-text">
                <strong>${this.t('banner_title')}</strong><br>
                ${this.t('banner_desc')} <a href="/privacidad" target="_blank">${this.t('privacy_link')}</a> y <a href="/cookies" target="_blank">${this.t('cookies_link')}</a>.
            </div>
            <div class="cc-buttons">
                <button class="cc-btn cc-btn-reject" onclick="window.cookieConsent.rejectAll()">${this.t('reject_all')}</button>
                <button class="cc-btn cc-btn-manage" onclick="window.cookieConsent.showPrefs()">${this.t('manage')}</button>
                <button class="cc-btn cc-btn-accept" onclick="window.cookieConsent.acceptAll()">${this.t('accept_all')}</button>
            </div>
        </div>`;
        document.body.appendChild(this.banner);
    }

    showPrefs() {
        if (this.banner) this.banner.style.display = 'none';

        const existing = document.getElementById('cc-prefs');
        if (existing) existing.remove();

        const prefs = this.preferences || { essential: true, functional: false, analytics: false, marketing: false };

        const el = document.createElement('div');
        el.id = 'cc-prefs';
        el.innerHTML = `
        <div class="cc-pref-inner">
            <div class="cc-pref-title">${this.t('manage')}</div>
            <div class="cc-pref-item">
                <div><div class="cc-pref-label">${this.t('category_essential')}</div><div class="cc-pref-desc">${this.t('category_essential_desc')}</div></div>
                <div class="cc-toggle active disabled" data-cat="essential"></div>
            </div>
            <div class="cc-pref-item">
                <div><div class="cc-pref-label">${this.t('category_functional')}</div><div class="cc-pref-desc">${this.t('category_functional_desc')}</div></div>
                <div class="cc-toggle ${prefs.functional ? 'active' : ''}" data-cat="functional" onclick="this.classList.toggle('active')"></div>
            </div>
            <div class="cc-pref-item">
                <div><div class="cc-pref-label">${this.t('category_analytics')}</div><div class="cc-pref-desc">${this.t('category_analytics_desc')}</div></div>
                <div class="cc-toggle ${prefs.analytics ? 'active' : ''}" data-cat="analytics" onclick="this.classList.toggle('active')"></div>
            </div>
            <div class="cc-pref-item">
                <div><div class="cc-pref-label">${this.t('category_marketing')}</div><div class="cc-pref-desc">${this.t('category_marketing_desc')}</div></div>
                <div class="cc-toggle ${prefs.marketing ? 'active' : ''}" data-cat="marketing" onclick="this.classList.toggle('active')"></div>
            </div>
            <div class="cc-pref-buttons">
                <button class="cc-btn cc-btn-reject" onclick="window.cookieConsent.rejectAll()">${this.t('reject_all')}</button>
                <button class="cc-btn cc-btn-accept" onclick="window.cookieConsent.savePrefs()">${this.t('save')}</button>
            </div>
        </div>`;
        document.body.appendChild(el);
    }

    acceptAll() {
        this.save({ essential: true, functional: true, analytics: true, marketing: true, timestamp: Date.now() });
        this.removeBanner();
        this.applyConsent();
    }

    rejectAll() {
        this.save({ essential: true, functional: false, analytics: false, marketing: false, timestamp: Date.now() });
        this.removeBanner();
        this.applyConsent();
    }

    savePrefs() {
        const toggles = document.querySelectorAll('#cc-prefs .cc-toggle');
        const prefs = { essential: true, timestamp: Date.now() };
        toggles.forEach(t => {
            prefs[t.dataset.cat] = t.classList.contains('active');
        });
        this.save(prefs);
        this.removeBanner();
        this.applyConsent();
    }

    removeBanner() {
        if (this.banner) { this.banner.remove(); this.banner = null; }
        const prefs = document.getElementById('cc-prefs');
        if (prefs) prefs.remove();
    }

    applyConsent() {
        if (!this.preferences) return;

        if (!this.preferences.analytics) {
            document.querySelectorAll('script[data-cookie="analytics"]').forEach(s => s.remove());
            window['ga'] = undefined;
            window['gtag'] = undefined;
        }
        if (!this.preferences.marketing) {
            document.querySelectorAll('script[data-cookie="marketing"]').forEach(s => s.remove());
        }
        if (!this.preferences.functional) {
            document.querySelectorAll('script[data-cookie="functional"]').forEach(s => s.remove());
        }

        document.dispatchEvent(new CustomEvent('cookieConsentUpdated', { detail: this.preferences }));
    }

    init() {
        this.showBanner();
        if (this.hasConsent()) this.applyConsent();
    }
}

window.cookieConsent = new CookieConsent();
document.addEventListener('DOMContentLoaded', () => window.cookieConsent.init());
