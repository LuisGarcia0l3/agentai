# 🤖 AI Trading System v2.0

Sistema de trading avanzado con agentes de inteligencia artificial, análisis técnico automatizado y gestión de riesgo inteligente para Mac M2.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [Componentes Principales](#-componentes-principales)
- [API Reference](#-api-reference)
- [Desarrollo](#-desarrollo)
- [Troubleshooting](#-troubleshooting)
- [Contribución](#-contribución)

## 🚀 Características

### ✨ Funcionalidades Principales

- **🤖 Agentes IA Autónomos**: Agentes especializados con LangChain y GPT-4
- **📊 Machine Learning**: Modelos predictivos (Random Forest, XGBoost, LSTM)
- **🛡️ Gestión de Riesgo**: Sistema avanzado de validación y control de riesgo
- **📈 Paper Trading**: Trading simulado seguro con Alpaca Markets
- **⚛️ Frontend Moderno**: Dashboard React con métricas en tiempo real
- **🍃 MongoDB Local**: Base de datos local para Mac M2
- **🔧 Configuración Flexible**: Sistema de configuración modular
- **📱 Responsive Design**: Interfaz adaptable a diferentes dispositivos

### 🎯 Características Técnicas

- **Análisis Técnico Automatizado**: RSI, MACD, Bollinger Bands, SMA/EMA
- **Predicción de Precios**: Múltiples modelos de ML con ensemble
- **Backtesting Avanzado**: Pruebas históricas de estrategias
- **Optimización Automática**: Ajuste de parámetros con algoritmos genéticos
- **Alertas Inteligentes**: Notificaciones basadas en condiciones de mercado
- **API RESTful**: Interfaz completa para integración externa

## 🏗️ Arquitectura del Sistema

```
AI Trading System v2.0
├── 🏦 Alpaca Broker Integration
│   ├── Paper Trading Engine
│   ├── Real-time Market Data
│   └── Order Management
├── 📊 MongoDB Local Database
│   ├── Market Data Storage
│   ├── Trading History
│   ├── Strategy Configurations
│   └── Performance Metrics
├── 🛡️ Risk Management System
│   ├── Position Sizing
│   ├── Stop Loss/Take Profit
│   ├── Portfolio Risk Analysis
│   └── Drawdown Protection
├── 🤖 ML Models & AI Agents
│   ├── Price Prediction Models
│   ├── LangChain Trading Agent
│   ├── Research Agent
│   └── Risk Assessment Agent
├── ⚛️ React Frontend
│   ├── Trading Dashboard
│   ├── Strategy Configuration
│   ├── Market Analysis
│   └── Performance Analytics
├── 🚀 FastAPI Backend
│   ├── RESTful API
│   ├── WebSocket Streams
│   ├── Authentication
│   └── Data Processing
└── 📈 Streamlit Analytics
    ├── Advanced Charts
    ├── Backtesting Interface
    └── Performance Reports
```

## 🛠️ Instalación

### Requisitos del Sistema

- **macOS**: Big Sur (11.0) o superior
- **Procesador**: Apple Silicon M1/M2 (recomendado)
- **RAM**: 8GB mínimo, 16GB recomendado
- **Almacenamiento**: 5GB libres
- **Internet**: Conexión estable para datos de mercado

### Instalación Automática

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/agentai-trading.git
cd agentai-trading

# 2. Ejecutar instalador automático
./install.sh
```

El instalador automático se encarga de:
- ✅ Instalar Homebrew (si no está instalado)
- ✅ Instalar Python 3.11
- ✅ Instalar Node.js 18+
- ✅ Instalar MongoDB Community Edition
- ✅ Instalar Redis
- ✅ Instalar dependencias adicionales (TA-Lib, Git)
- ✅ Configurar entorno virtual Python
- ✅ Instalar dependencias del frontend
- ✅ Crear directorios necesarios
- ✅ Generar archivo .env
- ✅ Iniciar servicios

### Instalación Manual

Si prefieres instalar manualmente:

```bash
# Instalar Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias del sistema
brew install python@3.11 node mongodb-community redis ta-lib git

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias Python
pip install -r requirements.txt

# Instalar dependencias del frontend
cd frontend
npm install
cd ..

# Iniciar servicios
brew services start mongodb/brew/mongodb-community
brew services start redis
```

## ⚙️ Configuración

### 1. Configuración Básica

Edita el archivo `.env` con tus credenciales:

```bash
# =============================================================================
# CONFIGURACIÓN GENERAL
# =============================================================================
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=tu-clave-secreta-aqui

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
TRADING_MODE=paper
DEFAULT_EXCHANGE=alpaca
DEFAULT_SYMBOL=AAPL

# =============================================================================
# ALPACA API (Paper Trading)
# =============================================================================
ALPACA_API_KEY=tu_alpaca_api_key_aqui
ALPACA_SECRET_KEY=tu_alpaca_secret_key_aqui
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# =============================================================================
# AI APIS
# =============================================================================
OPENAI_API_KEY=tu_openai_api_key_aqui

# =============================================================================
# DATABASE LOCAL
# =============================================================================
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=agentai_trading
REDIS_URL=redis://localhost:6379/0
```

### 2. Obtener API Keys

#### Alpaca Markets (Paper Trading)
1. Visita [Alpaca Markets](https://alpaca.markets/)
2. Crea una cuenta gratuita
3. Ve a "Paper Trading" en el dashboard
4. Genera tus API keys
5. Copia `API Key` y `Secret Key` al archivo `.env`

#### OpenAI (Agentes IA)
1. Visita [OpenAI Platform](https://platform.openai.com/)
2. Crea una cuenta y configura billing
3. Ve a "API Keys"
4. Genera una nueva API key
5. Copia la key al archivo `.env`

### 3. Configuración de MongoDB

MongoDB se instala localmente y no requiere configuración adicional. Los datos se almacenan en:
- **Ruta de datos**: `/usr/local/var/mongodb`
- **Logs**: `/usr/local/var/log/mongodb`
- **Puerto**: `27017`

## 🚀 Uso del Sistema

### Iniciar el Sistema

```bash
# Método 1: Script automático (recomendado)
./run.sh

# Método 2: Manual
source venv/bin/activate
python main.py

# Método 3: Con Docker (opcional)
docker-compose up --build
```

### Acceso a Interfaces

Una vez iniciado, accede a:

- **🎨 Frontend React**: http://localhost:3000
- **🚀 API FastAPI**: http://localhost:8000
- **📊 Dashboard Streamlit**: http://localhost:8501
- **📋 API Docs**: http://localhost:8000/docs

### Navegación del Frontend

#### 1. Dashboard Principal
- **Métricas en tiempo real**: Portfolio, P&L, posiciones activas
- **Gráficos interactivos**: Performance, asset allocation
- **Estado de agentes**: Monitoreo de agentes IA
- **Alertas recientes**: Notificaciones del sistema

#### 2. Centro de Trading
- **Panel de Trading**: Ejecutar órdenes de compra/venta
- **Análisis de Mercado**: Indicadores técnicos y análisis IA
- **Configuración de Estrategias**: Crear y gestionar estrategias automatizadas

#### 3. Backtesting
- **Pruebas Históricas**: Evaluar estrategias con datos pasados
- **Optimización**: Encontrar parámetros óptimos
- **Reportes Detallados**: Métricas de performance

#### 4. Agentes IA
- **Estado de Agentes**: Monitoreo en tiempo real
- **Configuración**: Ajustar parámetros de agentes
- **Logs y Actividad**: Historial de decisiones

#### 5. Configuración
- **Parámetros de Trading**: Risk management, símbolos
- **Conexiones API**: Configurar brokers y servicios
- **Preferencias**: Tema, notificaciones, idioma

## 🧩 Componentes Principales

### 1. Sistema de Trading

#### Paper Trading Engine
```python
from execution.paper_trading.paper_trading_engine import get_paper_trading_engine

# Obtener engine
engine = await get_paper_trading_engine()

# Ejecutar orden
order = await engine.place_order(
    symbol="AAPL",
    qty=10,
    side="buy",
    order_type="market"
)

# Obtener posiciones
positions = await engine.get_positions()
```

#### Risk Manager
```python
from risk_management.risk_manager import get_risk_manager

# Obtener risk manager
risk_mgr = await get_risk_manager()

# Validar orden
validation = await risk_mgr.validate_order(
    symbol="AAPL",
    qty=10,
    side="buy",
    price=150.0
)

if validation['approved']:
    # Ejecutar orden
    pass
```

### 2. Modelos de Machine Learning

#### Price Predictor
```python
from strategies.ml_models.price_predictor import create_price_predictor

# Crear predictor
predictor = await create_price_predictor("AAPL")

# Entrenar modelos
results = await predictor.train_models()

# Hacer predicción
prediction = await predictor.predict(model_name="ensemble")
```

### 3. Agentes IA

#### Trading Agent
```python
from agents.trading_agent.trading_agent import create_trading_agent

# Crear agente
agent = await create_trading_agent(openai_api_key="tu_key")

# Analizar y hacer trading
results = await agent.analyze_and_trade(["AAPL", "MSFT"])

# Monitorear posiciones
monitoring = await agent.monitor_positions()
```

### 4. Base de Datos

#### MongoDB Client
```python
from utils.database import get_mongodb_client

# Obtener cliente
db = await get_mongodb_client()

# Guardar datos de mercado
await db.save_market_data({
    "symbol": "AAPL",
    "price": 150.0,
    "timestamp": datetime.utcnow()
})

# Obtener historial
history = await db.get_market_data(
    symbol="AAPL",
    start_date=datetime(2024, 1, 1),
    end_date=datetime.utcnow()
)
```

## 📡 API Reference

### Endpoints Principales

#### Trading
```bash
# Obtener información de cuenta
GET /api/v1/account

# Obtener posiciones
GET /api/v1/positions

# Ejecutar orden
POST /api/v1/orders
{
  "symbol": "AAPL",
  "qty": 10,
  "side": "buy",
  "type": "market"
}

# Obtener órdenes
GET /api/v1/orders

# Cancelar orden
DELETE /api/v1/orders/{order_id}
```

#### Market Data
```bash
# Obtener datos de mercado
GET /api/v1/market/{symbol}

# Obtener historial
GET /api/v1/market/{symbol}/history?start=2024-01-01&end=2024-12-31

# Obtener indicadores técnicos
GET /api/v1/market/{symbol}/indicators
```

#### Estrategias
```bash
# Listar estrategias
GET /api/v1/strategies

# Crear estrategia
POST /api/v1/strategies
{
  "name": "Mi Estrategia",
  "type": "swing",
  "symbols": ["AAPL", "MSFT"],
  "parameters": {...}
}

# Iniciar estrategia
POST /api/v1/strategies/{strategy_id}/start

# Detener estrategia
POST /api/v1/strategies/{strategy_id}/stop
```

#### Agentes IA
```bash
# Estado de agentes
GET /api/v1/agents/status

# Configurar agente
PUT /api/v1/agents/{agent_id}/config
{
  "enabled": true,
  "parameters": {...}
}

# Obtener análisis de agente
GET /api/v1/agents/{agent_id}/analysis
```

## 💻 Desarrollo

### Estructura del Proyecto

```
agentai/
├── 📁 agents/                 # Agentes IA
│   └── trading_agent/
├── 📁 api/                    # FastAPI backend
│   ├── main.py
│   └── routes/
├── 📁 dashboard/              # Streamlit dashboard
│   └── streamlit_app/
├── 📁 execution/              # Sistemas de ejecución
│   ├── brokers/
│   └── paper_trading/
├── 📁 frontend/               # React frontend
│   ├── src/
│   ├── public/
│   └── package.json
├── 📁 risk_management/        # Gestión de riesgo
├── 📁 strategies/             # Estrategias y ML
│   └── ml_models/
├── 📁 utils/                  # Utilidades
│   ├── config/
│   ├── database/
│   └── logging/
├── 📄 main.py                 # Punto de entrada
├── 📄 requirements.txt        # Dependencias Python
├── 📄 install.sh             # Instalador
├── 📄 run.sh                 # Script de ejecución
└── 📄 README.md              # Documentación
```

### Configuración de Desarrollo

```bash
# Activar entorno de desarrollo
source venv/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar tests
pytest tests/

# Linting
flake8 .
black .

# Frontend development
cd frontend
npm run dev
```

## 🔧 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión a MongoDB

```bash
# Verificar estado
brew services list | grep mongodb

# Reiniciar servicio
brew services restart mongodb/brew/mongodb-community

# Verificar logs
tail -f /usr/local/var/log/mongodb/mongo.log
```

#### 2. Error de API Keys

```bash
# Verificar archivo .env
cat .env | grep -E "(ALPACA|OPENAI)"

# Probar conexión
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('ALPACA_API_KEY:', os.getenv('ALPACA_API_KEY')[:10] + '...')
"
```

#### 3. Problemas con el Frontend

```bash
# Limpiar cache
cd frontend
rm -rf node_modules package-lock.json
npm install

# Verificar puerto
lsof -i :3000
```

### Logs del Sistema

```bash
# Logs principales
tail -f logs/trading.log

# Logs de API
tail -f logs/api.log

# Logs de agentes
tail -f logs/agents.log

# Logs de MongoDB
tail -f /usr/local/var/log/mongodb/mongo.log
```

## 🛡️ Seguridad y Mejores Prácticas

### Seguridad

1. **Nunca uses trading en vivo sin pruebas extensas**
2. **Mantén tus API keys seguras y nunca las compartas**
3. **Usa siempre paper trading para probar nuevas estrategias**
4. **Haz backups regulares de tu configuración**
5. **Monitorea constantemente el sistema en producción**

### Mejores Prácticas

1. **Gestión de Riesgo**:
   - Nunca arriesgues más del 2% por trade
   - Usa stop-loss en todas las posiciones
   - Diversifica tu portfolio
   - Monitorea el drawdown

2. **Desarrollo de Estrategias**:
   - Siempre haz backtesting primero
   - Usa datos out-of-sample para validación
   - Considera los costos de transacción
   - Evita el overfitting

3. **Monitoreo**:
   - Revisa logs regularmente
   - Monitorea métricas de performance
   - Configura alertas para eventos críticos
   - Mantén un diario de trading

## 🤝 Contribución

### Cómo Contribuir

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Guías de Contribución

- Sigue las convenciones de código existentes
- Agrega tests para nuevas funcionalidades
- Actualiza la documentación
- Usa commits descriptivos

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

- **Documentación**: Este README
- **Issues**: GitHub Issues
- **Discusiones**: GitHub Discussions

## 🙏 Agradecimientos

- [Alpaca Markets](https://alpaca.markets/) por la API de trading
- [OpenAI](https://openai.com/) por los modelos de IA
- [LangChain](https://langchain.com/) por el framework de agentes
- [React](https://reactjs.org/) por el framework de frontend
- [FastAPI](https://fastapi.tiangolo.com/) por el framework de backend
- [MongoDB](https://www.mongodb.com/) por la base de datos
- [Streamlit](https://streamlit.io/) por el framework de dashboards

---

**⚠️ DISCLAIMER**: Este sistema es para fines educativos y de investigación. El trading conlleva riesgos significativos. Nunca inviertas dinero que no puedas permitirte perder. Siempre usa paper trading primero y consulta con un asesor financiero antes de hacer trading en vivo.

**🤖 Happy Trading!**