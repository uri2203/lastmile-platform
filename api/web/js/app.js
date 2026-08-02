/* ============================================
   LAST MILE PLATFORM - SHARED APP UTILITIES
   ============================================ */

if (typeof window.API_BASE === 'undefined') {
  window.API_BASE = window.location.origin;
}

if (typeof window.HEADERS === 'undefined') {
  Object.defineProperty(window, 'HEADERS', {
    get() {
      return {
        'Content-Type': 'application/json',
        'X-Emp-Id': localStorage.getItem('lm-emp-id') || localStorage.getItem('empId') || '1'
      };
    }
  });
}

if (typeof window.getHeaders === 'undefined') {
  window.getHeaders = function () {
    return {
      'Content-Type': 'application/json',
      'X-Emp-Id': localStorage.getItem('lm-emp-id') || localStorage.getItem('empId') || '1'
    };
  };
}
