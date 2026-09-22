/**
 * Cookie Consent - Banner inferior profesional con i18n.
 * Recuerda la decisión del usuario. Muestra una sola vez.
 */
(function(){
  var KEY='cookie_consent', DAYS=90;

  var TEXTS={
    es:{title:'Usamos cookies',desc:'Utilizamos cookies para mejorar tu experiencia, analizar el tráfico y personalizar el contenido. Puedes aceptar todas o configurar tus preferencias.',necesary:'Necesarias',necessary_desc:'Esenciales para el funcionamiento del sitio',analytics:'Analíticas',analytics_desc:'Nos ayudan a entender cómo usas la plataforma',marketing:'Marketing',marketing_desc:'Para mostrarte contenido relevante',accept:'Aceptar todas',essential:'Solo esenciales',reject:'Rechazar',learn_more:'Más información'},
    en:{title:'We use cookies',desc:'We use cookies to improve your experience, analyze traffic and personalize content. You can accept all or configure your preferences.',necessary:'Necessary',necessary_desc:'Essential for site functionality',analytics:'Analytics',analytics_desc:'Help us understand how you use the platform',marketing:'Marketing',marketing_desc:'To show you relevant content',accept:'Accept all',essential:'Essential only',reject:'Reject',learn_more:'Learn more'},
    pt:{title:'Usamos cookies',desc:'Utilizamos cookies para melhorar sua experiência, analisar tráfego e personalizar o conteúdo. Você pode aceitar todas ou configurar suas preferências.',necessary:'Necessárias',necessary_desc:'Essenciais para o funcionamento do site',analytics:'Analíticas',analytics_desc:'Nos ajudam a entender como você usa a plataforma',marketing:'Marketing',marketing_desc:'Para mostrar conteúdo relevante',accept:'Aceitar todas',essential:'Somente essenciais',reject:'Rejeitar',learn_more:'Mais informações'}
  };

  function t(key){
    var l=(window.i18n&&window.i18n.lang)?window.i18n.lang:'es';
    var texts=TEXTS[l]||TEXTS.es;
    var simpleKey=key.split('.').pop();
    return texts[simpleKey]||key;
  }

  function get(){
    try{
      var r=localStorage.getItem(KEY);
      if(!r)return null;
      var d=JSON.parse(r);
      if(!d||!d.timestamp)return null;
      if((Date.now()-new Date(d.timestamp).getTime())/(864e5)>DAYS){localStorage.removeItem(KEY);return null;}
      return d;
    }catch(e){localStorage.removeItem(KEY);return null;}
  }

  function save(c){
    c.timestamp=new Date().toISOString();
    localStorage.setItem(KEY,JSON.stringify(c));
    window.dispatchEvent(new CustomEvent('cookieConsentChange',{detail:c}));
  }

  function show(){
    if(document.getElementById('cc-banner'))return;

    var o=document.createElement('div');
    o.id='cc-banner';
    o.innerHTML=
      '<div id="cc-inner">'+
      '<div class="cc-content">'+
        '<div class="cc-icon">'+
          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"/><path d="M8.5 8.5v.01"/><path d="M16 15.5v.01"/><path d="M12 12v.01"/><path d="M11 17v.01"/><path d="M7 14v.01"/></svg>'+
        '</div>'+
        '<div class="cc-text">'+
          '<strong>'+t('cookie.title')+'</strong>'+
          '<span>'+t('cookie.desc')+'</span>'+
        '</div>'+
      '</div>'+
      '<div class="cc-actions">'+
        '<button id="cc-accept" class="cc-btn cc-btn-primary">'+t('cookie.accept')+'</button>'+
        '<button id="cc-nec" class="cc-btn cc-btn-ghost">'+t('cookie.essential')+'</button>'+
        '<a href="/legal/politica-cookies.html" target="_blank" class="cc-link">'+t('cookie.learn_more')+'</a>'+
      '</div>'+
      '</div>';

    var css=document.createElement('style');
    css.id='cc-css';
    css.textContent=
      '#cc-banner{position:fixed;bottom:0;left:0;right:0;z-index:999999;padding:16px;animation:ccSlideUp .4s ease-out}'+
      '#cc-inner{max-width:900px;margin:0 auto;background:#1e293b;border:1px solid rgba(255,255,255,0.1);border-radius:14px;padding:18px 24px;box-shadow:0 -8px 32px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}'+
      '#cc-banner *{box-sizing:border-box}'+
      '.cc-content{display:flex;align-items:center;gap:14px;flex:1;min-width:200px}'+
      '.cc-icon{width:36px;height:36px;background:rgba(245,158,11,0.15);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0}'+
      '.cc-text{display:flex;flex-direction:column;gap:3px}'+
      '.cc-text strong{font-size:14px;color:#f8fafc;margin:0}'+
      '.cc-text span{font-size:12px;color:#94a3b8;margin:0;line-height:1.5}'+
      '.cc-actions{display:flex;align-items:center;gap:10px;flex-shrink:0}'+
      '.cc-btn{padding:8px 18px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:all .15s;white-space:nowrap}'+
      '.cc-btn-primary{background:#f59e0b;color:#0f172a}.cc-btn-primary:hover{background:#fbbf24;transform:translateY(-1px)}'+
      '.cc-btn-ghost{background:transparent;color:#94a3b8;border:1px solid rgba(255,255,255,0.15)}.cc-btn-ghost:hover{border-color:rgba(255,255,255,0.3);color:#e2e8f0}'+
      '.cc-link{color:#64748b;font-size:12px;text-decoration:none;white-space:nowrap}.cc-link:hover{color:#94a3b8}'+
      '@keyframes ccSlideUp{from{transform:translateY(100%);opacity:0}to{transform:translateY(0);opacity:1}}'+
      '@media(max-width:700px){#cc-inner{flex-direction:column;align-items:stretch;padding:16px}.cc-actions{justify-content:center;flex-wrap:wrap}}';

    document.head.appendChild(css);
    document.body.appendChild(o);

    document.getElementById('cc-accept').onclick=function(){save({necessary:true,analytics:true,marketing:true});close()};
    document.getElementById('cc-nec').onclick=function(){save({necessary:true,analytics:false,marketing:false});close()};
  }

  function close(){
    var o=document.getElementById('cc-banner');
    var css=document.getElementById('cc-css');
    if(o){o.style.opacity='0';o.style.transition='opacity .3s';setTimeout(function(){o.remove()},300);}
    if(css)css.remove();
  }

  function waitForI18n(cb){
    if(window.i18n&&window.i18n.translations&&Object.keys(window.i18n.translations).length>0){cb();return;}
    var tries=0;
    var poll=setInterval(function(){
      tries++;
      if(window.i18n&&window.i18n.translations&&Object.keys(window.i18n.translations).length>0){clearInterval(poll);cb();}
      if(tries>30){clearInterval(poll);cb();}
    },100);
  }

  function init(){
    if(get())return;
    waitForI18n(function(){
      if(document.readyState==='loading'){
        document.addEventListener('DOMContentLoaded',show);
      }else{
        show();
      }
    });
  }

  window.CookieConsent={getConsent:get,reset:function(){localStorage.removeItem(KEY)},show:show};
  init();
})();
