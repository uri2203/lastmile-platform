# Contribuir a Last Mile Platform

Gracias por tu interes en contribuir!

## Development Setup

```bash
# Clonar
git clone https://github.com/uri2203/lastmile-platform.git
cd lastmile-platform

# Backend
cd api
pip install -r requirements.txt
python server.py

# El server arranca en http://localhost:5000
```

## Estandares de codigo

- Python: PEP 8 (max 120 chars por linea)
- HTML/CSS/JS: Sin framework, vanilla
- Commits: Descriptivos, en ingles o espanol

## Pull Request Process

1. Fork + clone
2. Crear rama feature (`git checkout -b feature/mi-feature`)
3. Hacer cambios
4. Probar localmente
5. Push (`git push origin feature/mi-feature`)
6. Abrir PR con descripcion clara

## Structure

- `api/server.py` - Backend Flask
- `api/web/` - Frontend HTML/CSS/JS
- `sql/migrate.sql` - Schema PostgreSQL
- `docs/` - Landing page para GitHub Pages
