#!/bin/bash

# 🤖 AI Trading System - Script de Ejecución
# Inicia el sistema completo de trading con IA

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
clear
echo "================================================================================"
echo -e "${BLUE}🤖 AI TRADING SYSTEM - INICIANDO...${NC}"
echo "================================================================================"

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    print_error "❌ No se encontró main.py. Ejecuta desde el directorio del proyecto."
    exit 1
fi

# Verificar servicios
print_status "🔍 Verificando servicios..."

# Verificar MongoDB
if ! pgrep -x "mongod" > /dev/null; then
    print_warning "⚠️ MongoDB no está ejecutándose. Iniciando..."
    brew services start mongodb/brew/mongodb-community
    sleep 3
fi

# Verificar Redis
if ! pgrep -x "redis-server" > /dev/null; then
    print_warning "⚠️ Redis no está ejecutándose. Iniciando..."
    brew services start redis
    sleep 2
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    print_status "🐍 Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar archivo .env
if [ ! -f ".env" ]; then
    print_error "❌ No se encontró archivo .env. Ejecuta ./install.sh primero."
    exit 1
fi

# Función para manejar la terminación
cleanup() {
    print_status "🛑 Deteniendo servicios..."
    kill $API_PID $FRONTEND_PID $STREAMLIT_PID 2>/dev/null || true
    wait
    print_success "✅ Sistema detenido"
    exit 0
}

# Configurar trap para cleanup
trap cleanup SIGTERM SIGINT

# Crear directorios si no existen
mkdir -p logs data/storage models

# Iniciar API FastAPI
print_status "🚀 Iniciando API FastAPI..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > logs/api.log 2>&1 &
API_PID=$!

# Esperar a que la API esté lista
sleep 3

# Iniciar Frontend React
if [ -d "frontend" ]; then
    print_status "⚛️ Iniciando Frontend React..."
    cd frontend
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
else
    print_warning "⚠️ Directorio frontend no encontrado"
    FRONTEND_PID=""
fi

# Iniciar Dashboard Streamlit
if [ -f "dashboard/streamlit_app/main.py" ]; then
    print_status "📊 Iniciando Dashboard Streamlit..."
    streamlit run dashboard/streamlit_app/main.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit.log 2>&1 &
    STREAMLIT_PID=$!
else
    print_warning "⚠️ Dashboard Streamlit no encontrado"
    STREAMLIT_PID=""
fi

# Mostrar URLs de acceso
echo ""
echo "================================================================================"
echo -e "${GREEN}🎉 SISTEMA INICIADO CORRECTAMENTE${NC}"
echo "================================================================================"
echo ""
echo "🌐 ACCESO A INTERFACES:"
echo "   📊 Frontend React:     http://localhost:3000"
echo "   🚀 API FastAPI:        http://localhost:8000"
echo "   📈 Dashboard Streamlit: http://localhost:8501"
echo "   📋 API Docs:           http://localhost:8000/docs"
echo ""
echo "📊 SERVICIOS:"
echo "   🍃 MongoDB:            mongodb://localhost:27017"
echo "   🔴 Redis:              redis://localhost:6379"
echo ""
echo "📝 LOGS:"
echo "   📄 API:                tail -f logs/api.log"
echo "   📄 Frontend:           tail -f logs/frontend.log"
echo "   📄 Streamlit:          tail -f logs/streamlit.log"
echo ""
echo "================================================================================"
echo -e "${YELLOW}💡 Presiona Ctrl+C para detener el sistema${NC}"
echo "================================================================================"

# Mantener el script ejecutándose
wait $API_PID $FRONTEND_PID $STREAMLIT_PID