/**
 * @module validators
 * @description Form validation utilities for the Last Mile Delivery app.
 * Includes email, phone, RFC, password, and required field validators.
 */

/**
 * Validates an email address against RFC 5322 simplified pattern.
 * @param {string} email - The email to validate.
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateEmail(email) {
  if (!email || typeof email !== 'string') {
    return { valid: false, error: 'El correo es requerido' };
  }
  const trimmed = email.trim();
  // RFC 5322 simplified regex
  const pattern = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
  if (!pattern.test(trimmed)) {
    return { valid: false, error: 'Correo electrónico inválido' };
  }
  return { valid: true };
}

/**
 * Validates a Mexican phone number (10 digits).
 * @param {string} phone - The phone number to validate.
 * @returns {{ valid: boolean, error?: string }}
 */
export function validatePhone(phone) {
  if (!phone || typeof phone !== 'string') {
    return { valid: false, error: 'El teléfono es requerido' };
  }
  const digits = phone.replace(/\D/g, '');
  if (digits.length !== 10) {
    return { valid: false, error: 'El teléfono debe tener 10 dígitos' };
  }
  return { valid: true };
}

/**
 * Validates a Mexican RFC (Registro Federal de Contribuyentes).
 * Format: 4 letters + 6 digits + 3 homoclave characters (alphanumeric).
 * @param {string} rfc - The RFC to validate.
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateRFC(rfc) {
  if (!rfc || typeof rfc !== 'string') {
    return { valid: false, error: 'El RFC es requerido' };
  }
  const cleaned = rfc.trim().toUpperCase();
  // Persona moral: 3 letters + 6 digits + 3 homoclave
  // Persona física: 4 letters + 6 digits + 3 homoclave
  const patternPhysical = /^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$/;
  const patternMoral = /^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$/;
  if (!patternPhysical.test(cleaned) && !patternMoral.test(cleaned)) {
    return { valid: false, error: 'RFC inválido. Formato: 4 letras + 6 dígitos + 3 caracteres' };
  }
  return { valid: true };
}

/**
 * Validates a password strength.
 * Requirements: min 8 characters, at least 1 uppercase, 1 lowercase, 1 number.
 * @param {string} password - The password to validate.
 * @returns {{ valid: boolean, error?: string }}
 */
export function validatePassword(password) {
  if (!password || typeof password !== 'string') {
    return { valid: false, error: 'La contraseña es requerida' };
  }
  if (password.length < 8) {
    return { valid: false, error: 'La contraseña debe tener al menos 8 caracteres' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, error: 'La contraseña debe incluir al menos una mayúscula' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, error: 'La contraseña debe incluir al menos una minúscula' };
  }
  if (!/\d/.test(password)) {
    return { valid: false, error: 'La contraseña debe incluir al menos un número' };
  }
  return { valid: true };
}

/**
 * Validates that a required field is not empty.
 * @param {string} value - The field value.
 * @param {string} [fieldName='Este campo'] - Name for the error message.
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateRequired(value, fieldName = 'Este campo') {
  if (value === null || value === undefined) {
    return { valid: false, error: `${fieldName} es requerido` };
  }
  if (typeof value === 'string' && value.trim().length === 0) {
    return { valid: false, error: `${fieldName} es requerido` };
  }
  return { valid: true };
}

/**
 * Validates a confirmation field matches a source field.
 * @param {string} value - The confirmation value.
 * @param {string} source - The source value to match.
 * @param {string} [fieldName='La confirmación'] - Name for the error message.
 * @returns {{ valid: boolean, error?: string }}
 */
export function validateConfirmation(value, source, fieldName = 'La confirmación') {
  if (value !== source) {
    return { valid: false, error: `${fieldName} no coincide` };
  }
  return { valid: true };
}

export default {
  validateEmail,
  validatePhone,
  validateRFC,
  validatePassword,
  validateRequired,
  validateConfirmation,
};
