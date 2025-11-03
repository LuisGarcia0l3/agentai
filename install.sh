#!/bin/bash

# 🤖 AI Trading System - Instalador Único para Mac M2
# Instala y configura todo el sistema de trading con IA

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para imprimir con colores
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

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Banner de inicio
clear
echo "================================================================================"
print_header "🤖 AI TRADING SYSTEM - INSTALADOR PARA MAC M2"
echo "================================================================================"
echo "Este script instalará y configurará todo el sistema de trading con IA"
echo "Incluye: Python, Node.js, MongoDB, dependencias y configuración completa"
echo "================================================================================"
echo ""

# Verificar que estamos en Mac
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "Este instalador está diseñado para macOS. Sistema detectado: $OSTYPE"
    exit 1
fi

# Verificar arquitectura M2
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    print_warning "Arquitectura detectada: $ARCH (esperada: arm64 para M2)"
    read -p "¿Continuar de todos modos? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

print_success "✅ Sistema compatible detectado: macOS $ARCH"

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Función para instalar Homebrew
install_homebrew() {
    if command_exists brew; then
        print_success "✅ Homebrew ya está instalado"
        return
    fi
    
    print_status "📦 Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Agregar Homebrew al PATH para M2
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
    
    print_success "✅ Homebrew instalado correctamente"
}

# Función para instalar Python
install_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "✅ Python ya está instalado: $PYTHON_VERSION"
        return
    fi
    
    print_status "🐍 Instalando Python 3.11..."
    brew install python@3.11
    
    # Crear enlaces simbólicos
    brew link python@3.11
    
    print_success "✅ Python instalado correctamente"
}

# Función para instalar Node.js
install_nodejs() {
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "✅ Node.js ya está instalado: $NODE_VERSION"
        return
    fi
    
    print_status "📦 Instalando Node.js..."
    brew install node
    
    print_success "✅ Node.js instalado correctamente"
}

# Función para instalar MongoDB
install_mongodb() {
    if command_exists mongod; then
        print_success "✅ MongoDB ya está instalado"
        return
    fi
    
    print_status "🍃 Instalando MongoDB Community Edition..."
    
    # Agregar el tap de MongoDB
    brew tap mongodb/brew
    
    # Instalar MongoDB
    brew install mongodb-community
    
    # Crear directorios necesarios
    sudo mkdir -p /usr/local/var/mongodb
    sudo mkdir -p /usr/local/var/log/mongodb
    sudo chown $(whoami) /usr/local/var/mongodb
    sudo chown $(whoami) /usr/local/var/log/mongodb
    
    print_success "✅ MongoDB instalado correctamente"
}

# Función para instalar Redis
install_redis() {
    if command_exists redis-server; then
        print_success "✅ Redis ya está instalado"
        return
    fi
    
    print_status "🔴 Instalando Redis..."
    brew install redis
    
    print_success "✅ Redis instalado correctamente"
}

# Función para instalar dependencias adicionales
install_additional_deps() {
    print_status "🔧 Instalando dependencias adicionales..."
    
    # TA-Lib para análisis técnico
    if ! brew list ta-lib >/dev/null 2>&1; then
        print_status "📊 Instalando TA-Lib..."
        brew install ta-lib
    fi
    
    # Git (si no está instalado)
    if ! command_exists git; then
        print_status "📝 Instalando Git..."
        brew install git
    fi
    
    # Curl (debería estar, pero por si acaso)
    if ! command_exists curl; then
        print_status "🌐 Instalando curl..."
        brew install curl
    fi
    
    print_success "✅ Dependencias adicionales instaladas"
}

# Función para configurar el entorno Python
setup_python_env() {
    print_status "🐍 Configurando entorno Python..."
    
    # Actualizar pip
    python3 -m pip install --upgrade pip
    
    # Instalar virtualenv si no está
    if ! python3 -m pip show virtualenv >/dev/null 2>&1; then
        python3 -m pip install virtualenv
    fi
    
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        print_status "📦 Creando entorno virtual..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Instalar dependencias Python
    if [ -f "requirements.txt" ]; then
        print_status "📦 Instalando dependencias Python..."
        pip install -r requirements.txt
    else
        print_warning "⚠️ No se encontró requirements.txt"
    fi
    
    print_success "✅ Entorno Python configurado"
}

# Función para configurar el frontend
setup_frontend() {
    if [ -d "frontend" ]; then
        print_status "⚛️ Configurando frontend React..."
        cd frontend
        
        # Instalar dependencias
        npm install
        
        # Volver al directorio principal
        cd ..
        
        print_success "✅ Frontend configurado"
    else
        print_warning "⚠️ Directorio frontend no encontrado"
    fi
}

# Función para iniciar servicios
start_services() {
    print_status "🚀 Iniciando servicios..."
    
    # Iniciar MongoDB
    print_status "🍃 Iniciando MongoDB..."
    brew services start mongodb/brew/mongodb-community
    
    # Iniciar Redis
    print_status "🔴 Iniciando Redis..."
    brew services start redis
    
    # Esperar a que los servicios estén listos
    sleep 3
    
    print_success "✅ Servicios iniciados"
}

# Función para crear archivo .env
create_env_file() {
    print_status "⚙️ Creando archivo de configuración..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# 🤖 AI Trading System - Configuración Local Mac M2

# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-change-this

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
TRADING_MODE=paper
DEFAULT_EXCHANGE=alpaca
DEFAULT_SYMBOL=AAPL

# Risk Management
MAX_POSITION_SIZE=0.02
MAX_DAILY_LOSS=0.05
STOP_LOSS_PERCENT=0.02
TAKE_PROFIT_PERCENT=0.04

# =============================================================================
# ALPACA API (Paper Trading)
# =============================================================================
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# =============================================================================
# AI APIS
# =============================================================================
OPENAI_API_KEY=your_openai_api_key_here

# =============================================================================
# DATABASE LOCAL
# =============================================================================
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=agentai_trading
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# SERVERS
# =============================================================================
API_HOST=0.0.0.0
API_PORT=8000
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8501

# =============================================================================
# AGENTS
# =============================================================================
TRADING_AGENT_ENABLED=false
RESEARCH_AGENT_ENABLED=true
OPTIMIZER_AGENT_ENABLED=true
RISK_AGENT_ENABLED=true

# =============================================================================
# LOCAL CONFIGURATION
# =============================================================================
USE_DOCKER=false
LOCAL_DATA_PATH=./data
EOF
        print_success "✅ Archivo .env creado"
        print_warning "⚠️ IMPORTANTE: Edita el archivo .env con tus API keys"
    else
        print_success "✅ Archivo .env ya existe"
    fi
}

# Función para crear directorios necesarios
create_directories() {
    print_status "📁 Creando directorios necesarios..."
    
    mkdir -p data/storage
    mkdir -p logs
    mkdir -p models
    mkdir -p backups
    
    print_success "✅ Directorios creados"
}

# Función para verificar la instalación
verify_installation() {
    print_status "🔍 Verificando instalación..."
    
    # Verificar Python
    if command_exists python3; then
        print_success "✅ Python: $(python3 --version)"
    else
        print_error "❌ Python no encontrado"
        return 1
    fi
    
    # Verificar Node.js
    if command_exists node; then
        print_success "✅ Node.js: $(node --version)"
    else
        print_error "❌ Node.js no encontrado"
        return 1
    fi
    
    # Verificar MongoDB
    if brew services list | grep mongodb-community | grep started >/dev/null; then
        print_success "✅ MongoDB: Ejecutándose"
    else
        print_warning "⚠️ MongoDB no está ejecutándose"
    fi
    
    # Verificar Redis
    if brew services list | grep redis | grep started >/dev/null; then
        print_success "✅ Redis: Ejecutándose"
    else
        print_warning "⚠️ Redis no está ejecutándose"
    fi
    
    # Verificar conexión a MongoDB
    if command_exists mongosh; then
        if mongosh --eval "db.runCommand('ping')" --quiet >/dev/null 2>&1; then
            print_success "✅ Conexión a MongoDB: OK"
        else
            print_warning "⚠️ No se puede conectar a MongoDB"
        fi
    fi
    
    print_success "✅ Verificación completada"
}

# Función para mostrar información final
show_final_info() {
    echo ""
    echo "================================================================================"
    print_header "🎉 INSTALACIÓN COMPLETADA"
    echo "================================================================================"
    echo ""
    print_success "✅ Sistema AI Trading instalado correctamente en Mac M2"
    echo ""
    echo "📍 PRÓXIMOS PASOS:"
    echo ""
    echo "1. 📝 Editar archivo .env con tus API keys:"
    echo "   - ALPACA_API_KEY y ALPACA_SECRET_KEY (para paper trading)"
    echo "   - OPENAI_API_KEY (para agentes IA)"
    echo ""
    echo "2. 🚀 Iniciar el sistema:"
    echo "   ./run.sh"
    echo ""
    echo "3. 🌐 Acceder a las interfaces:"
    echo "   - Frontend React: http://localhost:3000"
    echo "   - API FastAPI: http://localhost:8000"
    echo "   - Dashboard Streamlit: http://localhost:8501"
    echo "   - API Docs: http://localhost:8000/docs"
    echo ""
    echo "📊 SERVICIOS INSTALADOS:"
    echo "   - MongoDB: brew services start mongodb/brew/mongodb-community"
    echo "   - Redis: brew services start redis"
    echo ""
    echo "🛠️ COMANDOS ÚTILES:"
    echo "   - Parar servicios: brew services stop mongodb/brew/mongodb-community redis"
    echo "   - Ver logs: tail -f logs/trading.log"
    echo "   - Activar entorno: source venv/bin/activate"
    echo ""
    echo "⚠️ IMPORTANTE:"
    echo "   - Siempre usa PAPER TRADING primero"
    echo "   - Revisa los logs antes de trading en vivo"
    echo "   - Haz backups regulares de tu configuración"
    echo ""
    echo "================================================================================"
    print_header "🤖 ¡HAPPY TRADING!"
    echo "================================================================================"
}

# Función principal
main() {
    print_header "🚀 INICIANDO INSTALACIÓN..."
    echo ""
    
    # Verificar permisos
    if [[ $EUID -eq 0 ]]; then
        print_error "❌ No ejecutes este script como root"
        exit 1
    fi
    
    # Instalar componentes
    install_homebrew
    install_python
    install_nodejs
    install_mongodb
    install_redis
    install_additional_deps
    
    # Configurar entorno
    setup_python_env
    setup_frontend
    create_directories
    create_env_file
    
    # Iniciar servicios
    start_services
    
    # Verificar instalación
    verify_installation
    
    # Mostrar información final
    show_final_info
}

# Ejecutar instalación
main "$@"