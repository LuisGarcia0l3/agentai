#!/usr/bin/env python3
"""
🤖 AI Trading System - Main Entry Point

Sistema de trading avanzado con agentes IA autónomos.
Combina análisis técnico, machine learning y optimización automática.

Author: AI Trading System
Version: 2.0.0
"""

import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
import uvicorn

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our components
try:
    from utils.database import get_mongodb_client
    from execution.paper_trading.paper_trading_engine import get_paper_trading_engine
    from risk_management.risk_manager import get_risk_manager
    from agents.trading_agent.trading_agent import create_trading_agent
    from execution.brokers.alpaca_broker import AlpacaBroker
except ImportError as e:
    logger.error(f"Error importing components: {e}")
    sys.exit(1)


class AITradingSystem:
    """Sistema principal de trading con agentes IA."""
    
    def __init__(self):
        """Inicializar el sistema de trading."""
        self.logger = logger
        self.db_client = None
        self.paper_engine = None
        self.risk_manager = None
        self.trading_agent = None
        self.alpaca_broker = None
        self.api_process = None
        self.frontend_process = None
        self.streamlit_process = None
        self.is_running = False
        
    async def initialize(self):
        """Inicializar todos los componentes del sistema."""
        self.logger.info("🚀 Inicializando AI Trading System v2.0...")
        
        try:
            # 1. Inicializar base de datos
            self.logger.info("📊 Conectando a MongoDB...")
            self.db_client = await get_mongodb_client()
            self.logger.info("✅ MongoDB conectado")
            
            # 2. Inicializar broker de Alpaca
            self.logger.info("🏦 Inicializando broker Alpaca...")
            self.alpaca_broker = AlpacaBroker()
            broker_connected = await self.alpaca_broker.connect()
            if broker_connected:
                self.logger.info("✅ Alpaca broker conectado")
            else:
                self.logger.warning("⚠️ No se pudo conectar a Alpaca - continuando con paper trading")
            
            # 3. Inicializar paper trading engine
            self.logger.info("📈 Inicializando paper trading engine...")
            self.paper_engine = await get_paper_trading_engine()
            self.logger.info("✅ Paper trading engine inicializado")
            
            # 4. Inicializar risk manager
            self.logger.info("🛡️ Inicializando risk manager...")
            self.risk_manager = await get_risk_manager()
            
            # Obtener información de cuenta para inicializar risk manager
            if broker_connected:
                account_info = await self.alpaca_broker.get_account_info()
                positions = await self.alpaca_broker.get_positions()
                await self.risk_manager.initialize(
                    portfolio_value=account_info['portfolio_value'],
                    cash=account_info['cash'],
                    positions=positions
                )
            else:
                # Usar paper trading data
                paper_account = await self.paper_engine.get_account_info()
                paper_positions = await self.paper_engine.get_positions()
                await self.risk_manager.initialize(
                    portfolio_value=paper_account['portfolio_value'],
                    cash=paper_account['cash'],
                    positions=paper_positions
                )
            
            self.logger.info("✅ Risk manager inicializado")
            
            # 5. Inicializar agente de trading (opcional)
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.logger.info("🤖 Inicializando agente de trading IA...")
                self.trading_agent = await create_trading_agent(openai_api_key=openai_key)
                self.logger.info("✅ Agente de trading IA inicializado")
            else:
                self.logger.warning("⚠️ No se encontró OPENAI_API_KEY - agente IA deshabilitado")
            
            self.logger.info("🎉 Sistema inicializado exitosamente!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando sistema: {e}")
            return False
    
    def start_api_server(self):
        """Iniciar servidor FastAPI."""
        try:
            self.logger.info("🌐 Iniciando servidor FastAPI...")
            api_host = os.getenv('API_HOST', '0.0.0.0')
            api_port = int(os.getenv('API_PORT', '8000'))
            debug = os.getenv('DEBUG', 'true').lower() == 'true'
            
            self.api_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "api.main:app",
                "--host", api_host,
                "--port", str(api_port),
                "--reload" if debug else "--no-reload"
            ])
            self.logger.info(f"✅ API iniciada en http://{api_host}:{api_port}")
        except Exception as e:
            self.logger.error(f"❌ Error iniciando API: {e}")
    
    def start_frontend_server(self):
        """Iniciar servidor React."""
        try:
            frontend_path = Path(__file__).parent / "frontend"
            if frontend_path.exists():
                self.logger.info("⚛️ Iniciando frontend React...")
                
                # Verificar si npm está disponible
                try:
                    subprocess.run(["npm", "--version"], check=True, capture_output=True)
                    
                    # Instalar dependencias si es necesario
                    if not (frontend_path / "node_modules").exists():
                        self.logger.info("📦 Instalando dependencias...")
                        subprocess.run(["npm", "install"], cwd=frontend_path, check=True)
                    
                    # Iniciar servidor
                    self.frontend_process = subprocess.Popen([
                        "npm", "run", "dev"
                    ], cwd=frontend_path)
                    
                    self.logger.info("✅ Frontend iniciado en http://localhost:3000")
                except subprocess.CalledProcessError:
                    self.logger.warning("⚠️ npm no disponible, saltando frontend React")
            else:
                self.logger.warning("⚠️ Directorio frontend no encontrado")
        except Exception as e:
            self.logger.error(f"❌ Error iniciando frontend: {e}")
    
    def start_streamlit_dashboard(self):
        """Iniciar dashboard Streamlit."""
        try:
            self.logger.info("📊 Iniciando dashboard Streamlit...")
            dashboard_path = Path(__file__).parent / "dashboard" / "streamlit_app" / "main.py"
            dashboard_host = os.getenv('DASHBOARD_HOST', '0.0.0.0')
            dashboard_port = int(os.getenv('DASHBOARD_PORT', '8501'))
            
            if dashboard_path.exists():
                self.streamlit_process = subprocess.Popen([
                    sys.executable, "-m", "streamlit", "run",
                    str(dashboard_path),
                    "--server.port", str(dashboard_port),
                    "--server.address", dashboard_host,
                    "--server.headless", "true"
                ])
                self.logger.info(f"✅ Streamlit iniciado en http://{dashboard_host}:{dashboard_port}")
            else:
                self.logger.warning("⚠️ Dashboard Streamlit no encontrado")
        except Exception as e:
            self.logger.error(f"❌ Error iniciando Streamlit: {e}")
    
    def show_access_urls(self):
        """Mostrar URLs de acceso."""
        api_host = os.getenv('API_HOST', '0.0.0.0')
        api_port = os.getenv('API_PORT', '8000')
        dashboard_host = os.getenv('DASHBOARD_HOST', '0.0.0.0')
        dashboard_port = os.getenv('DASHBOARD_PORT', '8501')
        
        print("\n" + "=" * 80)
        print("🌐 URLS DE ACCESO")
        print("=" * 80)
        print(f"📊 Dashboard React:    http://localhost:3000")
        print(f"🚀 API FastAPI:        http://{api_host}:{api_port}")
        print(f"📈 API Docs:           http://{api_host}:{api_port}/docs")
        print(f"📋 Dashboard Streamlit: http://{dashboard_host}:{dashboard_port}")
        print("=" * 80)
        print("💡 Usa Ctrl+C para detener el sistema")
        print("=" * 80 + "\n")
        
    async def run(self):
        """Ejecutar el sistema principal."""
        self.is_running = True
        
        try:
            # Inicializar sistema
            success = await self.initialize()
            if not success:
                self.logger.error("❌ Falló la inicialización del sistema")
                return
            
            # Mostrar modo de trading
            trading_mode = os.getenv('TRADING_MODE', 'paper')
            if trading_mode == "paper":
                self.logger.info("📊 Ejecutando en modo Paper Trading")
            else:
                self.logger.warning("⚠️ Ejecutando en modo LIVE TRADING")
            
            # Iniciar servidores web
            self.start_api_server()
            time.sleep(2)  # Esperar a que inicie la API
            
            self.start_frontend_server()
            self.start_streamlit_dashboard()
            
            # Mostrar URLs
            self.show_access_urls()
            
            # Iniciar agente de trading si está habilitado
            trading_agent_enabled = os.getenv('TRADING_AGENT_ENABLED', 'false').lower() == 'true'
            if trading_agent_enabled and self.trading_agent:
                self.logger.info("🤖 Iniciando Trading Agent...")
                # Aquí podrías iniciar el agente en background
                # asyncio.create_task(self.trading_agent.analyze_and_trade(['AAPL', 'MSFT']))
            
            # Mantener el sistema ejecutándose
            while self.is_running:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Sistema detenido por el usuario")
        except Exception as e:
            self.logger.error(f"❌ Error crítico: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Limpiar recursos al cerrar."""
        self.logger.info("🧹 Limpiando recursos...")
        self.is_running = False
        
        # Detener procesos
        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait()
        
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()
            
        if self.streamlit_process:
            self.streamlit_process.terminate()
            self.streamlit_process.wait()
        
        # Cerrar conexiones de broker
        if self.alpaca_broker:
            await self.alpaca_broker.disconnect()
        
        self.logger.info("✅ Limpieza completada")


def main():
    """Función principal."""
    print("=" * 80)
    print("🤖 AI TRADING SYSTEM v2.0")
    print("=" * 80)
    print("Sistema de trading avanzado con agentes IA")
    
    trading_mode = os.getenv('TRADING_MODE', 'paper')
    exchange = os.getenv('DEFAULT_EXCHANGE', 'alpaca')
    symbol = os.getenv('DEFAULT_SYMBOL', 'AAPL')
    environment = os.getenv('ENVIRONMENT', 'development')
    
    print(f"Modo: {trading_mode.upper()}")
    print(f"Exchange: {exchange.upper()}")
    print(f"Símbolo: {symbol}")
    print(f"Entorno: {environment.upper()}")
    print("=" * 80)
    print("Características:")
    print("• Análisis técnico automatizado")
    print("• Agentes IA autónomos con LangChain")
    print("• Gestión de riesgo inteligente")
    print("• Dashboard React + FastAPI")
    print("• Machine Learning (Random Forest, LSTM)")
    print("• Paper Trading con Alpaca")
    print("• MongoDB para persistencia")
    print("=" * 80)
    print("⚠️  ADVERTENCIA: Siempre usa paper trading primero")
    print("=" * 80)
    
    # Crear y ejecutar el sistema
    system = AITradingSystem()
    
    try:
        asyncio.run(system.run())
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())