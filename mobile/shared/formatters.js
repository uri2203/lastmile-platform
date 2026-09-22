/**
 * @module formatters
 * @description Data formatting utilities for the Last Mile Delivery app.
 * Includes currency, date, time, phone, RFC, and status formatters.
 */

/**
 * Formats a number as MXN currency.
 * @param {number} amount - The amount to format.
 * @returns {string} Formatted currency string (e.g., "$1,234.56 MXN").
 */
export function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '$0.00 MXN';
  const num = Number(amount);
  if (isNaN(num)) return '$0.00 MXN';
  return num.toLocaleString('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }) + ' MXN';
}

/**
 * Formats a date string or Date object to "DD Mon YYYY".
 * @param {string|Date} date - The date to format.
 * @returns {string} Formatted date (e.g., "22 Sep 2026").
 */
export function formatDate(date) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';
  const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
  const day = String(d.getDate()).padStart(2, '0');
  return `${day} ${months[d.getMonth()]} ${d.getFullYear()}`;
}

/**
 * Formats a date to "DD Mon YYYY, HH:mm".
 * @param {string|Date} date - The date to format.
 * @returns {string} Formatted datetime (e.g., "22 Sep 2026, 14:30").
 */
export function formatDateTime(date) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';
  const datePart = formatDate(d);
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${datePart}, ${hours}:${minutes}`;
}

/**
 * Formats a date as relative time in Spanish.
 * @param {string|Date} date - The date to format.
 * @returns {string} Relative time (e.g., "hace 5 min", "hace 2 horas").
 */
export function formatRelativeTime(date) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  if (isNaN(d.getTime())) return '';

  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHrs = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHrs / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);

  if (diffSec < 0) return 'ahora mismo';
  if (diffSec < 60) return 'hace unos segundos';
  if (diffMin === 1) return 'hace 1 min';
  if (diffMin < 60) return `hace ${diffMin} min`;
  if (diffHrs === 1) return 'hace 1 hora';
  if (diffHrs < 24) return `hace ${diffHrs} horas`;
  if (diffDays === 1) return 'hace 1 día';
  if (diffDays < 7) return `hace ${diffDays} días`;
  if (diffWeeks === 1) return 'hace 1 semana';
  if (diffWeeks < 4) return `hace ${diffWeeks} semanas`;
  if (diffMonths === 1) return 'hace 1 mes';
  if (diffMonths < 12) return `hace ${diffMonths} meses`;
  return formatDate(d);
}

/**
 * Formats a phone number as "(XX) XXXX-XXXX".
 * @param {string} phone - 10-digit phone string.
 * @returns {string} Formatted phone (e.g., "(55) 1234-5678").
 */
export function formatPhone(phone) {
  if (!phone) return '';
  const digits = phone.replace(/\D/g, '');
  if (digits.length !== 10) return phone;
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
}

/**
 * Formats an RFC string in uppercase.
 * @param {string} rfc - The RFC value.
 * @returns {string} Uppercase RFC (e.g., "AOAE781008V98").
 */
export function formatRFC(rfc) {
  if (!rfc) return '';
  return rfc.trim().toUpperCase();
}

/**
 * Returns the display label and color for a delivery status.
 * @param {string} status - The delivery status code.
 * @returns {{ label: string, color: string, bgColor: string }}
 */
export function formatStatus(status) {
  const statuses = {
    PENDIENTE: { label: 'Pendiente', color: '#d97706', bgColor: '#fef3c7' },
    ASIGNADO: { label: 'Asignado', color: '#7c3aed', bgColor: '#ede9fe' },
    EN_RUTA: { label: 'En ruta', color: '#2563eb', bgColor: '#dbeafe' },
    ENTREGADO: { label: 'Entregado', color: '#16a34a', bgColor: '#dcfce7' },
    CANCELADO: { label: 'Cancelado', color: '#dc2626', bgColor: '#fee2e2' },
    FALLIDO: { label: 'Fallido', color: '#b91c1c', bgColor: '#fef2f2' },
    DEVUELTO: { label: 'Devuelto', color: '#9333ea', bgColor: '#f3e8ff' },
  };
  return statuses[status] || { label: status || 'Desconocido', color: '#6b7280', bgColor: '#f3f4f6' };
}

/**
 * Truncates text to a max length with ellipsis.
 * @param {string} text - The text to truncate.
 * @param {number} maxLength - Maximum length.
 * @returns {string}
 */
export function truncate(text, maxLength = 50) {
  if (!text || text.length <= maxLength) return text || '';
  return text.slice(0, maxLength) + '...';
}

export default {
  formatCurrency,
  formatDate,
  formatDateTime,
  formatRelativeTime,
  formatPhone,
  formatRFC,
  formatStatus,
  truncate,
};
