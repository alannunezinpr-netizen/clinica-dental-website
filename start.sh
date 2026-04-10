#!/bin/bash
# Script de inicio para producción local
# Uso: ./start.sh

cd "$(dirname "$0")"

# Verificar que existe el .env
if [ ! -f .env ]; then
    echo "ERROR: No se encontró el archivo .env"
    echo "Copia .env.example a .env y configura las variables."
    exit 1
fi

# Instalar dependencias si no están instaladas
pip3 install -q -r requirements.txt

# Iniciar el servidor
echo "Iniciando Clínica Dental Sistema de Gestión..."
echo "Accede en: http://localhost:8080"
python3 app.py
