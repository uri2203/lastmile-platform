# Last Mile Platform 🚚

Plataforma SaaS de última milla para empresas de delivery en México.

## Características

- **Multi-tenant**: Cada cliente tiene sus datos separados
- **CFDI 4.0**: Facturación electrónica incluida
- **Pagos**: OXXO, SPEI, Mercado Pago, efectivo
- **App Chofer PWA**: Se instala sin Play Store, funciona offline
- **Tracking GPS**: Tiempo real
- **Whitelabel**: Tu marca, tu dominio
- **Billing SaaS**: Planes Starter/Pro/Enterprise

## Stack

- **Backend**: Python/Flask → PostgreSQL (migración desde AS/400)
- **Frontend**: HTML/CSS/JS vanilla (sin dependencias)
- **DB**: PostgreSQL 15 + Redis (cache)
- **Deploy**: Docker Compose

## Quick Start

```bash
# Clonar
git clone https://github.com/uri2203/lastmile-platform.git
cd lastmile-platform

# Deploy con Docker
docker-compose up -d

# Acceder
# API:      http://localhost:5000
# Frontend: http://localhost:80
```

## Estructura

```
api/
  server.py          # Backend Flask (70+ endpoints)
  web/               # Frontend
    index.html       # Login
    landing.html     # Página de ventas
    onboarding.html  # Registro clientes
    panel-operacion.html
    panel-admin.html
    panel-chofer.html  # PWA chofer
    panel-cliente.html
    tracking-cliente.html  # Tracking cliente final
    ayuda-cliente.html
    css/style.css    # Framework CSS
    js/app.js        # JavaScript principal
    manifest.json    # PWA manifest
    sw.js            # Service Worker
sql/
  migrate.sql        # Migración a PostgreSQL
docker-compose.yml   # Deploy
Dockerfile           # Build API
nginx.conf           # Configuración web server
```

## Licencia

Propietario - Todos los derechos reservados
