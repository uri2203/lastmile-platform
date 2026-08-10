/**
 * Cookie Consent - Modal profesional con i18n y deteccion de region.
 * Bloquea pagina hasta aceptar. Soporta 12 idiomas.
 */
(function(){
  var KEY='cookie_consent', DAYS=90;
  var savedScroll=null;

  var LEGAL_REFS={
    es:'LFPDPPP',en:'applicable privacy laws',pt:'LGPD',fr:'RGPD',
    de:'DSGVO',zh:'PIPL',ja:'APPI',ko:'PIPA',ar:'PDPA',
    hi:'DPDP Act',it:'GDPR',nl:'AVG/GDPR'
  };

  function t(key){return(window.i18n&&window.i18n.t)?window.i18n.t(key):key;}
  function lang(){return(window.i18n&&window.i18n.lang)?window.i18n.lang:'es';}

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
    c.region=lang();
    c.legal_ref=LEGAL_REFS[lang()]||LEGAL_REFS.es;
    localStorage.setItem(KEY,JSON.stringify(c));
    window.dispatchEvent(new CustomEvent('cookieConsentChange',{detail:c}));
  }

  function blockScroll(){
    savedScroll={};
    document.querySelectorAll('*').forEach(function(el){
      var s=getComputedStyle(el);
      if(s.overflow==='auto'||s.overflow==='scroll'||s.overflowY==='auto'||s.overflowY==='scroll'){
        if(el.scrollHeight>el.clientHeight+10){
          savedScroll[el.className||el.id||el.tagName]={el:el,top:el.scrollTop};
          el.style.overflow='hidden';
        }
      }
    });
    document.body.style.overflow='hidden';
    document.documentElement.style.overflow='hidden';
    document.addEventListener('wheel',preventScroll,{passive:false});
    document.addEventListener('touchmove',preventScroll,{passive:false});
  }

  function preventScroll(e){
    var modal=document.getElementById('cc-box');
    if(modal&&modal.contains(e.target))return;
    e.preventDefault();
  }

  function unblockScroll(){
    if(savedScroll){
      Object.keys(savedScroll).forEach(function(k){
        var item=savedScroll[k];
        item.el.style.overflow='';
        item.el.scrollTop=item.top;
      });
      savedScroll=null;
    }
    document.body.style.overflow='';
    document.documentElement.style.overflow='';
    document.removeEventListener('wheel',preventScroll);
    document.removeEventListener('touchmove',preventScroll);
  }

  function show(){
    if(document.getElementById('cc-overlay'))return;
    blockScroll();

    var l=lang();
    var legalRef=LEGAL_REFS[l]||LEGAL_REFS.es;
    var o=document.createElement('div');
    o.id='cc-overlay';
    o.innerHTML=
      '<div id="cc-box">'+
      '<div style="display:flex;align-items:center;gap:12px;margin-bottom:24px;padding-bottom:16px;border-bottom:1px solid #e5e7eb">'+
        '<div style="width:40px;height:40px;background:#f0fdf4;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0">'+
          '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"/><path d="M8.5 8.5v.01"/><path d="M16 15.5v.01"/><path d="M12 12v.01"/><path d="M11 17v.01"/><path d="M7 14v.01"/></svg>'+
        '</div>'+
        '<div>'+
          '<h2 style="font-size:17px;font-weight:600;color:#111827;margin:0">'+t('cookie.cookie_title')+'</h2>'+
          '<p style="font-size:12px;color:#9ca3af;margin:2px 0 0">'+t('cookie.cookie_legal_ref')+'</p>'+
        '</div>'+
      '</div>'+
      '<p style="font-size:13.5px;color:#374151;line-height:1.65;margin:0 0 16px">'+t('cookie.cookie_description')+'</p>'+
      '<p style="font-size:13.5px;color:#374151;line-height:1.65;margin:0 0 20px">'+t('cookie.cookie_more_info')+'</p>'+
      '<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:14px 16px;margin-bottom:20px">'+
        '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f3f4f6">'+
          '<div>'+
            '<span style="font-size:13px;font-weight:600;color:#111827">'+t('cookie.cookie_necessary')+'</span>'+
            '<p style="font-size:11.5px;color:#6b7280;margin:2px 0 0">'+t('cookie.cookie_necessary_desc')+'</p>'+
          '</div>'+
          '<span style="color:#16a34a;font-weight:600;font-size:12px;background:#dcfce7;padding:2px 8px;border-radius:4px">'+t('cookie.cookie_necessary_badge')+'</span>'+
        '</div>'+
        '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #f3f4f6">'+
          '<div>'+
            '<span style="font-size:13px;font-weight:600;color:#111827">'+t('cookie.cookie_analytics')+'</span>'+
            '<p style="font-size:11.5px;color:#6b7280;margin:2px 0 0">'+t('cookie.cookie_analytics_desc')+'</p>'+
          '</div>'+
          '<label class="cc-sw" style="position:relative;width:40px;height:22px;cursor:pointer;display:inline-block;flex-shrink:0">'+
            '<input type="checkbox" id="cc-tog-a" style="position:absolute;opacity:0;width:0;height:0">'+
            '<span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#d1d5db;border-radius:11px;transition:.2s"></span>'+
          '</label>'+
        '</div>'+
        '<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0">'+
          '<div>'+
            '<span style="font-size:13px;font-weight:600;color:#111827">'+t('cookie.cookie_marketing')+'</span>'+
            '<p style="font-size:11.5px;color:#6b7280;margin:2px 0 0">'+t('cookie.cookie_marketing_desc')+'</p>'+
          '</div>'+
          '<label class="cc-sw" style="position:relative;width:40px;height:22px;cursor:pointer;display:inline-block;flex-shrink:0">'+
            '<input type="checkbox" id="cc-tog-m" style="position:absolute;opacity:0;width:0;height:0">'+
            '<span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#d1d5db;border-radius:11px;transition:.2s"></span>'+
          '</label>'+
        '</div>'+
      '</div>'+
      '<div style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px">'+
        '<button id="cc-accept" disabled style="width:100%;padding:12px 20px;background:#9ca3af;color:#fff;border:none;border-radius:8px;font-size:13.5px;font-weight:600;cursor:not-allowed;letter-spacing:0.01em;opacity:.6">'+t('cookie.cookie_disabled_msg')+'</button>'+
        '<button id="cc-nec" style="width:100%;padding:12px 20px;background:#fff;color:#374151;border:1px solid #d1d5db;border-radius:8px;font-size:13.5px;font-weight:500;cursor:pointer">'+t('cookie.cookie_essential_only')+'</button>'+
      '</div>'+
      '<div style="text-align:center">'+
        '<button id="cc-rej" style="background:none;border:none;color:#9ca3af;font-size:12px;cursor:pointer;text-decoration:underline;padding:4px">'+t('cookie.cookie_reject')+'</button>'+
      '</div>'+
      '<div style="margin-top:16px;padding-top:12px;border-top:1px solid #f3f4f6;display:flex;justify-content:center;gap:16px;font-size:11px;color:#9ca3af">'+
        '<a href="/legal/terminos-condiciones.html" target="_blank" style="color:#6b7280;text-decoration:none">'+t('legal.terminos')+'</a>'+
        '<a href="/legal/aviso-privacidad.html" target="_blank" style="color:#6b7280;text-decoration:none">'+t('legal.privacidad')+'</a>'+
        '<a href="/legal/politica-cookies.html" target="_blank" style="color:#6b7280;text-decoration:none">'+t('legal.cookies')+'</a>'+
        '<a href="/legal/politica-cobros-reembolsos.html" target="_blank" style="color:#6b7280;text-decoration:none">'+t('legal.pagos')+'</a>'+
        '<a href="/legal/deslinde-responsabilidades.html" target="_blank" style="color:#6b7280;text-decoration:none">'+t('legal.deslinde')+'</a>'+
        '<a href="/legal/politica-ia.html" target="_blank" style="color:#6b7280;text-decoration:none">'+t('legal.regulaciones_ia')+'</a>'+
      '</div>'+
      '</div>';

    var css=document.createElement('style');
    css.id='cc-css';
    css.textContent=
      '#cc-overlay{position:fixed;top:0;left:0;right:0;bottom:0;z-index:999999;background:rgba(0,0,0,0.6);backdrop-filter:blur(4px);display:flex;align-items:center;justify-content:center;padding:16px;animation:ccfi .25s ease-out;overflow-y:auto}'+
      '#cc-box{background:#fff;border-radius:12px;width:100%;max-width:460px;padding:24px;box-shadow:0 20px 50px rgba(0,0,0,0.25);animation:ccsi .3s ease-out;margin:auto}'+
      '#cc-overlay *{box-sizing:border-box}'+
      '#cc-box button:hover{opacity:.85}'+
      '#cc-box button:active{transform:scale(.99)}'+
      '#cc-box a:hover{color:#1d4ed8!important}'+
      '.cc-sw input:checked+span{background:#2563eb!important}'+
      '.cc-sw input:checked+span::before{transform:translateX(18px)}'+
      '.cc-sw span::before{content:"";position:absolute;height:16px;width:16px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.2s}'+
      '@keyframes ccfi{from{opacity:0}to{opacity:1}}'+
      '@keyframes ccsi{from{transform:translateY(10px);opacity:0}to{transform:translateY(0);opacity:1}}'+
      '@media(max-width:600px){#cc-box{padding:20px;max-width:100%}}';
    document.head.appendChild(css);
    document.body.appendChild(o);

    document.querySelectorAll('.cc-sw').forEach(function(lbl){
      lbl.addEventListener('click',function(e){
        e.preventDefault();
        var cb=lbl.querySelector('input');
        cb.checked=!cb.checked;
        var togA=document.getElementById('cc-tog-a');
        var togM=document.getElementById('cc-tog-m');
        var btn=document.getElementById('cc-accept');
        if(togA.checked||togM.checked){
          btn.disabled=false;
          btn.style.background='#111827';
          btn.style.cursor='pointer';
          btn.style.opacity='1';
          btn.textContent=t('cookie.cookie_accept_all');
        }else{
          btn.disabled=true;
          btn.style.background='#9ca3af';
          btn.style.cursor='not-allowed';
          btn.style.opacity='.6';
          btn.textContent=t('cookie.cookie_disabled_msg');
        }
      });
    });

    document.getElementById('cc-accept').onclick=function(){save({necessary:true,analytics:true,marketing:true});close()};
    document.getElementById('cc-nec').onclick=function(){save({necessary:true,analytics:false,marketing:false});close()};
    document.getElementById('cc-rej').onclick=function(){save({necessary:true,analytics:false,marketing:false});close()};

    o.addEventListener('click',function(e){if(e.target===o)e.preventDefault()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')e.preventDefault()},true);
  }

  function close(){
    var o=document.getElementById('cc-overlay');
    var css=document.getElementById('cc-css');
    if(o){o.style.opacity='0';o.style.transition='opacity .2s';setTimeout(function(){o.remove()},200);}
    if(css)css.remove();
    unblockScroll();
  }

  function waitForI18n(cb){
    if(window.i18n&&window.i18n.translations&&Object.keys(window.i18n.translations).length>0){cb();return;}
    var tries=0;
    var poll=setInterval(function(){
      tries++;
      if(window.i18n&&window.i18n.translations&&Object.keys(window.i18n.translations).length>0){clearInterval(poll);cb();}
      if(tries>50){clearInterval(poll);cb();}
    },100);
  }

  function init(){
    localStorage.removeItem(KEY);
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
