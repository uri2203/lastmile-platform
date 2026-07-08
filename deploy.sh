#!/bin/bash
# ============================================
# Last Mile Platform - Deploy Script
# Ejecutar en el servidor Linux
# ============================================
set -e

echo "========================================="
echo "  LAST MILE PLATFORM - DEPLOY"
echo "========================================="
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Instalando Docker Compose..."
    sudo apt-get install -y docker-compose-plugin
fi

# Copiar archivos
echo "Preparando archivos..."
cd "$(dirname "$0")"

# Levantar servicios
echo "Levantando servicios..."
docker compose up -d --build

echo ""
echo "========================================="
echo "  DEPLOY COMPLETADO"
echo "========================================="
echo ""
echo "  Frontend:  http://$(hostname -I | awk '{print $1}'):80"
echo "  API:       http://$(hostname -I | awk '{print $1}'):5000"
echo "  PostgreSQL: localhost:5432"
echo ""
echo "  Usuario:  admin@delmx.com"
echo "  Pass:     admin123"
echo ""
echo "  Para ver logs: docker compose logs -f"
echo "  Para parar:    docker compose down"
echo "========================================="
