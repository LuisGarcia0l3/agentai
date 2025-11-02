#!/usr/bin/env python3
"""
🤖 AI Trading System - Main Entry Point

Sistema de trading avanzado con agentes IA autónomos.
Combina análisis técnico, machine learning y optimización automática.

Author: Luis (AI Trading System)
Version: 1.0.0
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from utils.config.settings import Settings
from utils.logging.logger import setup_logging
from dashboard.streamlit_app.app import run_dashboard
from agents.trading_agent.agent import TradingAgent
from data.feeds.market_data import MarketDataManager


class AITradingSystem:
    """Sistema principal de trading con agentes IA."""
    
    def __init__(self):
        """Inicializar el sistema de trading."""
        self.settings = Settings()
        self.logger = setup_logging()
        self.market_data = MarketDataManager()
        self.trading_agent: Optional[TradingAgent] = None
        
    async def initialize(self):
        """Inicializar todos los componentes del sistema."""
        self.logger.info("🚀 Inicializando AI Trading System...")
        
        # Inicializar conexiones de datos
        await self.market_data.initialize()
        
        # Inicializar agente de trading
        self.trading_agent = TradingAgent(
            market_data=self.market_data,
            settings=self.settings
        )
        
        self.logger.info("✅ Sistema inicializado correctamente")
        
    async def run(self):
        """Ejecutar el sistema principal."""
        try:
            await self.initialize()
            
            if self.settings.TRADING_MODE == "paper":
                self.logger.info("📊 Ejecutando en modo Paper Trading")
            else:
                self.logger.warning("⚠️ Ejecutando en modo LIVE TRADING")
            
            # Ejecutar agentes en paralelo
            tasks = []
            
            if self.settings.TRADING_AGENT_ENABLED:
                tasks.append(self.trading_agent.run())
            
            # Ejecutar dashboard en paralelo
            if self.settings.DEBUG:
                tasks.append(self._run_dashboard())
            
            # Ejecutar todas las tareas
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Sistema detenido por el usuario")
        except Exception as e:
            self.logger.error(f"❌ Error crítico: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def _run_dashboard(self):
        """Ejecutar el dashboard en un hilo separado."""
        import threading
        dashboard_thread = threading.Thread(target=run_dashboard)
        dashboard_thread.daemon = True
        dashboard_thread.start()
        
        # Mantener el hilo vivo
        while True:
            await asyncio.sleep(1)
    
    async def cleanup(self):
        """Limpiar recursos al cerrar."""
        self.logger.info("🧹 Limpiando recursos...")
        
        if self.trading_agent:
            await self.trading_agent.stop()
        
        await self.market_data.close()
        self.logger.info("✅ Limpieza completada")


def main():
    """Función principal."""
    print("""
    🤖 AI Trading System
    ==================
    Sistema de trading avanzado con agentes IA
    
    Características:
    • Análisis técnico automatizado
    • Machine Learning predictivo  
    • Agentes IA autónomos
    • Gestión de riesgo inteligente
    • Dashboard en tiempo real
    
    ⚠️  ADVERTENCIA: Siempre usa paper trading primero
    """)
    
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