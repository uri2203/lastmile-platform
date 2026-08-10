/**
 * Cookie Consent - Modal invasivo. Bloquea pagina hasta aceptar.
 * Compatible con paneles que usan scroll en .main-content
 */
(function(){
  var KEY='cookie_consent', DAYS=90;
  var savedScroll=null;

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

  function blockScroll(){
    savedScroll={};
    // Bloquear todos los contenedores con scroll
    var containers=document.querySelectorAll('body, html, .main-content, [style*="overflow"], [class*="content"]');
    containers.forEach(function(el){
      var s=getComputedStyle(el);
      if(s.overflow==='auto'||s.overflow==='scroll'||s.overflowY==='auto'||s.overflowY==='scroll'){
        savedScroll[el.className||el.tagName]={el:el,top:el.scrollTop};
        el.style.overflow='hidden';
        el.scrollTop=0;
      }
    });
    // Fallback: block body y html
    document.body.style.overflow='hidden';
    document.documentElement.style.overflow='hidden';
    // Prevenir scroll con wheel/touch
    document.addEventListener('wheel',preventScroll,{passive:false});
    document.addEventListener('touchmove',preventScroll,{passive:false});
  }

  function preventScroll(e){
    // Permitir scroll DENTRO del modal
    var modal=document.getElementById('cc-box');
    if(modal && modal.contains(e.target))return;
    e.preventDefault();
  }

  function unblockScroll(){
    // Restaurar contenedores
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

    var o=document.createElement('div');
    o.id='cc-overlay';
    o.innerHTML=
      '<div id="cc-box">'+
      '<div style="text-align:center;margin-bottom:20px;font-size:42px">&#127850;</div>'+
      '<h2 style="font-size:22px;font-weight:700;color:#111;margin:0 0 12px;text-align:center">Este sitio utiliza cookies</h2>'+
      '<p style="font-size:14px;color:#555;line-height:1.6;text-align:center;margin:0 0 20px">'+
        'Utilizamos cookies propias y de terceros para mejorar su experiencia, analizar el trafico y personalizar el contenido. '+
        '<b>Debe aceptar</b> o configurar sus preferencias para continuar. '+
        '<a href="/legal/politica-cookies.html" target="_blank" style="color:#2563eb">Politica de Cookies</a>'+
      '</p>'+
      '<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin-bottom:20px">'+
        '<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f3f4f6">'+
          '<div><b style="color:#111">Necesarias</b><br><small style="color:#999">Imprescindibles para el sitio</small></div>'+
          '<span style="color:#2563eb;font-size:20px">&#10003;</span>'+
        '</div>'+
        '<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f3f4f6">'+
          '<div><b style="color:#111">Analiticas</b><br><small style="color:#999">Entender como usa el sitio</small></div>'+
          '<label class="cc-sw" data-for="cc-tog-a" style="position:relative;width:44px;height:24px;cursor:pointer;display:inline-block">'+
            '<input type="checkbox" id="cc-tog-a" style="opacity:0;width:0;height:0;position:absolute">'+
            '<span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#d1d5db;border-radius:12px;transition:.3s"></span>'+
          '</label>'+
        '</div>'+
        '<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0">'+
          '<div><b style="color:#111">Marketing</b><br><small style="color:#999">Publicidad relevante</small></div>'+
          '<label class="cc-sw" data-for="cc-tog-m" style="position:relative;width:44px;height:24px;cursor:pointer;display:inline-block">'+
            '<input type="checkbox" id="cc-tog-m" style="opacity:0;width:0;height:0;position:absolute">'+
            '<span style="position:absolute;top:0;left:0;right:0;bottom:0;background:#d1d5db;border-radius:12px;transition:.3s"></span>'+
          '</label>'+
        '</div>'+
      '</div>'+
      '<button id="cc-accept" style="width:100%;padding:14px;background:#2563eb;color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;margin-bottom:10px">Aceptar Todas</button>'+
      '<button id="cc-nec" style="width:100%;padding:14px;background:#f3f4f6;color:#374151;border:1px solid #d1d5db;border-radius:10px;font-size:15px;font-weight:500;cursor:pointer;margin-bottom:10px">Solo Necesarias</button>'+
      '<button id="cc-rej" style="width:100%;padding:10px;background:transparent;color:#999;border:none;font-size:13px;cursor:pointer;margin-bottom:8px">Rechazar Todas</button>'+
      '<div style="text-align:center;font-size:11px;color:#aaa">'+
        '<a href="/legal/terminos-condiciones.html" target="_blank" style="color:#888;text-decoration:underline;margin:0 6px">Terminos</a> |'+
        '<a href="/legal/aviso-privacidad.html" target="_blank" style="color:#888;text-decoration:underline;margin:0 6px">Privacidad</a> |'+
        '<a href="/legal/politica-cookies.html" target="_blank" style="color:#888;text-decoration:underline;margin:0 6px">Cookies</a>'+
      '</div>'+
      '</div>';

    // Estilos
    var css=document.createElement('style');
    css.id='cc-css';
    css.textContent=
      '#cc-overlay{position:fixed;top:0;left:0;right:0;bottom:0;z-index:999999;background:rgba(0,0,0,0.75);backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;padding:16px;animation:ccfi .3s ease-out;overflow-y:auto}'+
      '#cc-box{background:#fff;border-radius:16px;width:100%;max-width:480px;padding:28px;box-shadow:0 25px 60px rgba(0,0,0,0.3);animation:ccsi .35s ease-out;margin:auto}'+
      '#cc-overlay *{box-sizing:border-box}'+
      '#cc-box button:hover{opacity:.9;transform:translateY(-1px)}'+
      '#cc-box button:active{transform:scale(.98)}'+
      '#cc-box a:hover{color:#1d4ed8!important}'+
      '.cc-sw input:checked+span{background:#2563eb!important}'+
      '.cc-sw input:checked+span::before{transform:translateX(20px)}'+
      '.cc-sw span::before{content:"";position:absolute;height:18px;width:18px;left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.3s}'+
      '@keyframes ccfi{from{opacity:0}to{opacity:1}}'+
      '@keyframes ccsi{from{transform:scale(.95);opacity:0}to{transform:scale(1);opacity:1}}'+
      '@media(max-width:600px){#cc-box{padding:20px;max-width:100%}}';
    document.head.appendChild(css);
    document.body.appendChild(o);

    // Toggle switches - click en label alterna checkbox
    document.querySelectorAll('.cc-sw').forEach(function(lbl){
      lbl.addEventListener('click',function(e){
        e.preventDefault();
        var cb=lbl.querySelector('input');
        cb.checked=!cb.checked;
        cb.dispatchEvent(new Event('change'));
      });
    });

    document.getElementById('cc-accept').onclick=function(){save({necessary:true,analytics:true,marketing:true});close()};
    document.getElementById('cc-nec').onclick=function(){save({necessary:true,analytics:false,marketing:false});close()};
    document.getElementById('cc-rej').onclick=function(){save({necessary:true,analytics:false,marketing:false});close()};

    // No cerrar con click afuera
    o.addEventListener('click',function(e){if(e.target===o)e.preventDefault()});
    // No cerrar con Escape
    document.addEventListener('keydown',function(e){if(e.key==='Escape')e.preventDefault()},true);
  }

  function close(){
    var o=document.getElementById('cc-overlay');
    var css=document.getElementById('cc-css');
    if(o){o.style.opacity='0';o.style.transition='opacity .2s';setTimeout(function(){o.remove()},200);}
    if(css)css.remove();
    unblockScroll();
  }

  function init(){
    var c=get();
    if(c){window.dispatchEvent(new CustomEvent('cookieConsentChange',{detail:c}));return;}
    if(document.readyState==='loading'){
      document.addEventListener('DOMContentLoaded',show);
    }else{
      show();
    }
  }

  window.CookieConsent={getConsent:get,reset:function(){localStorage.removeItem(KEY)},show:show};
  init();
})();
