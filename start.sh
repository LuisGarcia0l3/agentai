#!/bin/bash

# Script de inicio para AI Trading System
echo "🚀 Iniciando AI Trading System..."

# Función para manejar señales de terminación
cleanup() {
    echo "🛑 Deteniendo servicios..."
    kill $API_PID $FRONTEND_PID $STREAMLIT_PID 2>/dev/null
    wait
    exit 0
}

# Configurar manejo de señales
trap cleanup SIGTERM SIGINT

# Crear directorios necesarios
mkdir -p logs data/storage models

# Esperar a que MongoDB esté disponible
echo "⏳ Esperando conexión a MongoDB..."
while ! nc -z mongodb 27017; do
    sleep 1
done
echo "✅ MongoDB conectado"

# Esperar a que Redis esté disponible
echo "⏳ Esperando conexión a Redis..."
while ! nc -z redis 6379; do
    sleep 1
done
echo "✅ Redis conectado"

# Inicializar base de datos si es necesario
echo "🔧 Inicializando sistema..."
python -c "
import asyncio
from utils.database import get_mongodb_client

async def init_db():
    try:
        client = await get_mongodb_client()
        print('✅ Base de datos inicializada')
    except Exception as e:
        print(f'❌ Error inicializando base de datos: {e}')

asyncio.run(init_db())
"

# Iniciar API FastAPI
echo "🌐 Iniciando API FastAPI..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

# Esperar a que la API esté lista
sleep 5

# Iniciar Dashboard Streamlit
echo "📊 Iniciando Dashboard Streamlit..."
streamlit run dashboard/streamlit_app/main.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!

# Iniciar Frontend React (en modo desarrollo)
echo "🎨 Iniciando Frontend React..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Mostrar estado de los servicios
echo ""
echo "🎉 AI Trading System iniciado exitosamente!"
echo ""
echo "📍 Servicios disponibles:"
echo "   • API FastAPI:      http://localhost:8000"
echo "   • Dashboard:        http://localhost:8501"
echo "   • Frontend React:   http://localhost:3000"
echo "   • API Docs:         http://localhost:8000/docs"
echo ""
echo "📊 Métricas y monitoreo:"
echo "   • Prometheus:       http://localhost:9090"
echo "   • Grafana:          http://localhost:3000"
echo ""
echo "💾 Base de datos:"
echo "   • MongoDB:          mongodb://localhost:27017"
echo "   • Redis:            redis://localhost:6379"
echo ""

# Iniciar agentes IA si están habilitados
if [ "$TRADING_AGENT_ENABLED" = "true" ]; then
    echo "🤖 Iniciando Agentes IA..."
    python -c "
import asyncio
from agents.trading_agent.trading_agent import create_trading_agent

async def start_agents():
    try:
        agent = await create_trading_agent()
        print('✅ Agentes IA iniciados')
    except Exception as e:
        print(f'❌ Error iniciando agentes: {e}')

asyncio.run(start_agents())
    " &
fi

# Mantener el contenedor ejecutándose
echo "🔄 Sistema en ejecución. Presiona Ctrl+C para detener."
wait $API_PID $FRONTEND_PID $STREAMLIT_PID