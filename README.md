# Last Mile Platform

Plataforma SaaS de ultima milla para empresas de delivery en Mexico.

![CI](https://github.com/uri2203/lastmile-platform/actions/workflows/ci.yml/badge.svg)
![Pages](https://github.com/uri2203/lastmile-platform/actions/workflows/pages.yml/badge.svg)
![Docker](https://github.com/uri2203/lastmile-platform/actions/workflows/docker.yml/badge.svg)

## Landing Page

**https://uri2203.github.io/lastmile-platform/**

## Caracteristicas

- **Multi-tenant**: Cada cliente tiene sus datos separados. Un solo servidor atiende a todos.
- **Whitelabel**: Tu marca, tu dominio, tu logo. Los clientes ven TU marca, no la nuestra.
- **CFDI 4.0**: Facturacion electronica incluida. Timbrado automatico al SAT.
- **Pagos**: OXXO, SPEI, Mercado Pago, tarjeta, efectivo. Conciliacion bancaria.
- **App Chofer PWA**: Se instala sin Play Store. Funciona offline. GPS tracking.
- **Tracking GPS**: Tiempo real para clientes. Historial completo de rutas.
- **Billing SaaS**: Planes Starter/Pro/Enterprise. Cobro mensual, 0% comision.
- **API REST**: 70+ endpoints para integraciones con tu sistema existente.

## Por que no Rappi/Uber?

| | Rappi/Uber | Paquetexpress | **Last Mile Platform** |
|---|---|---|---|
| Comision por envio | 20-30% | Variable | **0% - Solo mensualidad** |
| Tu marca / Whitelabel | No | No | **Si, 100%** |
| CFDI 4.0 incluido | No | No | **Si** |
| App chofer propia | Si, de ellos | No | **Si, PWA tuya** |
| Control total de datos | No | No | **Si** |

## Stack Tecnico

- **Backend**: Python/Flask (70+ endpoints REST)
- **Frontend**: HTML/CSS/JS vanilla (sin dependencias)
- **DB**: PostgreSQL 15 (migracion desde DB2/400 AS/400)
- **Cache**: Redis
- **Deploy**: Docker Compose
- **CI/CD**: GitHub Actions
- **Landing**: GitHub Pages

## Quick Start

```bash
# Clonar
git clone https://github.com/uri2203/lastmile-platform.git
cd lastmile-platform

# Deploy con Docker (recomendado)
docker-compose up -d

# Acceder
# API:      http://localhost:5000
# Frontend: http://localhost:80
# Landing:  http://localhost:3000
```

## Quick Start sin Docker

```bash
# Backend
cd api
pip install -r requirements.txt
python server.py

# Frontend (necesitas nginx o similar en puerto 80)
```

## Estructura

```
lastmile-platform/
├── api/
│   ├── server.py              # Backend Flask (70+ endpoints)
│   ├── requirements.txt       # Dependencias Python
│   └── web/                   # Frontend
│       ├── index.html         # Login / Panel principal
│       ├── landing.html       # Pagina de ventas
│       ├── onboarding.html    # Registro clientes
│       ├── panel-operacion.html
│       ├── panel-admin.html
│       ├── panel-chofer.html  # PWA chofer
│       ├── panel-cliente.html
│       ├── tracking-cliente.html  # Tracking cliente final
│       ├── ayuda-cliente.html
│       ├── css/style.css      # Framework CSS
│       ├── js/app.js          # JavaScript principal
│       ├── manifest.json      # PWA manifest
│       └── sw.js              # Service Worker
├── docs/
│   └── index.html             # Landing para GitHub Pages
├── sql/
│   └── migrate.sql            # Migracion a PostgreSQL
├── dashboard/
│   └── index.html             # Dashboard
├── config/
│   └── alertas.properties     # Configuracion de alertas
├── src/                       # Java AS/400 (exploradores, reportes)
├── .github/
│   └── workflows/
│       ├── pages.yml          # Deploy landing a GitHub Pages
│       ├── ci.yml             # CI: lint + test
│       └── docker.yml         # Build + publish Docker image
├── docker-compose.yml         # Deploy completo
├── Dockerfile                 # Build API
├── nginx.conf                 # Configuracion web server
└── deploy.sh                  # Script de despliegue
```

## API Endpoints (70+)

| Modulo | Endpoints |
|--------|-----------|
| **Pedidos** | CRUD, asignacion, estado, tracking |
| **Choferes** | CRUD, rendimiento, ubicacion GPS |
| **Vehiculos** | CRUD, flota, mantenimiento |
| **Rutas** | CRUD, optimizacion, zonas |
| **Clientes** | CRUD, historial, top clientes |
| **CFDI 4.0** | Empresas fiscales, facturas, timbrado, cancelacion |
| **Pagos** | Metodos, transacciones, OXXO, Mercado Pago |
| **Notificaciones** | Push, email, SMS, dispositivos |
| **Reportes** | Entregas, rendimiento, costos |
| **KPIs** | Dashboard, metricas, alertas |
| **SaaS** | Planes, suscripciones, cobros, uso |
| **Whitelabel** | Configuracion por tenant |
| **Tracking** | GPS tiempo real, historial |

## Planes de Precio

| Plan | Precio | Choferes | Envios/mes | Incluye |
|------|--------|----------|------------|---------|
| **Starter** | $999 MXN/mes | 5 | 1,000 | CFDI, App PWA |
| **Pro** | $2,499 MXN/mes | 25 | 10,000 | Todo + Whitelabel + Pagos |
| **Enterprise** | $5,999 MXN/mes | Ilimitado | Ilimitado | Todo + API + Soporte dedicado |

## Contribuir

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-feature`)
3. Commit tus cambios (`git commit -m 'Add nueva feature'`)
4. Push a la rama (`git push origin feature/nueva-feature`)
5. Abre un Pull Request

## Licencia

Propietario - Todos los derechos reservados

## Contacto

- **Email**: ventas@lastmile.mx
- **GitHub**: [uri2203](https://github.com/uri2203)
