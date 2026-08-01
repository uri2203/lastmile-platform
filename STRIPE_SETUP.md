# LAST MILE DELIVERY - Stripe Payment Setup Guide

## RESUMEN

Este documento explica cómo configurar los pagos con Stripe para la plataforma Last Mile Delivery. La plataforma soporta **3 planes de suscripción** con cobro recurrente mensual.

---

## PLANES DE SUSCRIPCIÓN

| Plan | Precio MXN/mes | Usuarios | Choferes | Pedidos/mes | Features |
|------|----------------|----------|----------|-------------|----------|
| **STARTER** | $999 | 5 | 10 | 500 | Tracking básico, Reportes básicos, Soporte email |
| **PRO** | $2,499 | 15 | 30 | 2,000 | + Reportes avanzados, Soporte teléfono, API, WhatsApp |
| **ENTERPRISE** | $5,999 | 50 | 100 | 10,000 | + SSO, SLA, Branding custom, Soporte dedicado |

---

## CONFIGURACIÓN PASO A PASO

### Paso 1: Crear Products y Prices (Script Automático)

```bash
# 1. Asegúrate de tener STRIPE_SECRET_KEY en tu .env
echo "STRIPE_SECRET_KEY=sk_test_TU_KEY_AQUI" >> api/.env

# 2. Ejecutar el script
cd api
pip install stripe python-dotenv
python stripe_setup.py
```

El script creará automáticamente:
- 3 Products en Stripe
- 3 Prices (recurrentes mensuales, MXN)
- 1 Webhook Endpoint

### Paso 2: Configurar Variables de Entorno

Copiar las keys generadas a tu `.env`:

```env
# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

### Paso 3: Configurar Webhook en Dashboard (si no se creó automáticamente)

1. Ir a **Stripe Dashboard** → **Developers** → **Webhooks**
2. Click **Add endpoint**
3. URL: `https://lastmile-platform.onrender.com/api/billing/webhook/stripe`
4. Seleccionar eventos:
   - `checkout.session.completed`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
5. Copiar el **Signing secret** (whsec_...)

### Paso 4: Variables en Render

En el dashboard de Render, agregar al servicio `lastmile-platform`:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

---

## FLUJO DE PAGO

### Checkout Flow (Frontend → Backend → Stripe)

```
1. Usuario selecciona plan en onboarding.html
2. Frontend llama POST /api/billing/checkout
3. Backend crea Checkout Session en Stripe
4. Redirect a Stripe Checkout (hosted page)
5. Usuario paga con tarjeta
6. Stripe redirige a success_url
7. Webhook confirma pago → activate subscription
```

### Webhook Events (Stripe → Backend)

| Evento | Acción |
|--------|--------|
| `checkout.session.completed` | Activar suscripción, actualizar plan |
| `invoice.paid` | Registrar pago, actualizar fecha próximo cobro |
| `invoice.payment_failed` | Marcar como pendiente, notificar |
| `customer.subscription.deleted` | Cancelar suscripción, downgradear a Starter |

---

## MÉTODOS DE PAGO SOPORTADOS

### Stripe (Internacional)
- Tarjetas de crédito/débito (Visa, Mastercard, Amex)
- Apple Pay, Google Pay
- SEPA, iDEAL (futuro)

### MercadoPago (México/LATAM)
- OXXO (pago en efectivo)
- SPEI (transferencia bancaria)
- Tarjetas de crédito/débito
- MercadoPago Wallet

---

## TESTING

### Stripe Test Cards

| Card | Result |
|------|--------|
| `4242 4242 4242 4242` | Pago exitoso |
| `4000 0000 0000 0002` | Pago rechazado |
| `4000 0025 0000 3155` | 3D Secure requerido |

### Testing Webhook

```bash
# Instalar Stripe CLI
stripe listen --forward-to localhost:5000/api/billing/webhook/stripe

# Trigger test event
stripe trigger checkout.session.completed
```

---

## ENDPOINTS API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/billing/planes` | Listar planes disponibles |
| GET | `/api/billing/estado` | Estado de facturación del tenant |
| POST | `/api/billing/checkout` | Crear sesión de checkout |
| GET | `/api/billing/dashboard` | Dashboard de facturación |
| GET | `/api/billing/limits` | Verificar límites del plan |
| POST | `/api/billing/track` | Registrar uso |
| POST | `/api/billing/auto-charge` | Cobros automáticos (cron) |
| POST | `/api/billing/webhook/stripe` | Webhook Stripe |
| POST | `/api/billing/webhook/mercadopago` | Webhook MercadoPago |

---

## SEGURIDAD

- API Keys NUNCA en código fuente, solo en variables de entorno
- Webhooks verificados por firma (HMAC SHA256)
- Rate limiting en todos los endpoints
- HTTPS obligatorio en producción
- Tenant isolation en todas las queries

---

## TROUBLESHOOTING

### Error: "Stripe no configurado"
- Verificar que `STRIPE_SECRET_KEY` esté en las variables de entorno
- Verificar que no esté vacía

### Error: "Invalid webhook signature"
- Verificar que `STRIPE_WEBHOOK_SECRET` coincida con el del Dashboard
- Verificar que el webhook URL sea accesible (HTTPS)

### Error: "No such price: price_..."
- Verificar que `STRIPE_PRICE_*` esté configurado correctamente
- Ejecutar `stripe_setup.py` para crear los prices

### Pago no se refleja
- Verificar webhook en Dashboard (Stripe → Webhooks → Attempts)
- Verificar logs en Render
- Verificar tabla SAAS_COBROS en base de datos
