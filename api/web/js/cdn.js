/**
 * CDN Loader with Local Fallback
 * Carga librerias desde CDN y fallback a vendor local si falla.
 */
const CDN = {
  libs: {
    'leaflet': {
      js: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
      css: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
      local: '/js/vendor/leaflet.js'
    },
    'socket.io': {
      js: 'https://cdn.socket.io/4.7.5/socket.io.min.js',
      local: '/js/vendor/socket.io.js'
    },
    'chart.js': {
      js: 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.js',
      local: '/js/vendor/chart.js'
    },
    'qrcode': {
      js: 'https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js',
      local: '/js/vendor/qrcode.js'
    },
    'jspdf': {
      js: 'https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js',
      local: '/js/vendor/jspdf.js'
    },
    'html2canvas': {
      js: 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js',
      local: '/js/vendor/html2canvas.js'
    },
    'axios': {
      js: 'https://cdn.jsdelivr.net/npm/axios@1.6.2/dist/axios.min.js',
      local: '/js/vendor/axios.js'
    }
  },

  _loaded: {},

  load(name) {
    if (this._loaded[name]) {
      return Promise.resolve();
    }

    const lib = this.libs[name];
    if (!lib) {
      return Promise.reject(new Error(`Unknown library: ${name}`));
    }

    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = lib.js;
      script.crossOrigin = 'anonymous';
      script.onload = () => {
        this._loaded[name] = true;
        resolve();
      };
      script.onerror = () => {
        console.warn(`[CDN] Failed to load ${name} from CDN, trying local fallback...`);
        const local = document.createElement('script');
        local.src = lib.local;
        local.onload = () => {
          this._loaded[name] = true;
          resolve();
        };
        local.onerror = () => {
          console.error(`[CDN] Failed to load ${name} from both CDN and local`);
          reject(new Error(`Failed to load ${name}`));
        };
        document.head.appendChild(local);
      };
      document.head.appendChild(script);

      if (lib.css) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = lib.css;
        link.crossOrigin = 'anonymous';
        document.head.appendChild(link);
      }
    });
  },

  loadMultiple(names) {
    return Promise.all(names.map(name => this.load(name)));
  },

  isLoaded(name) {
    return !!this._loaded[name];
  }
};

window.CDN = CDN;
