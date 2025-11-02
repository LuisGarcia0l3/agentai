"""
AI Trading Agent using LangChain
Autonomous trading agent that makes decisions based on market analysis
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from pydantic import BaseModel, Field

from ...execution.paper_trading.paper_trading_engine import get_paper_trading_engine
from ...risk_management.risk_manager import get_risk_manager
from ...strategies.ml_models.price_predictor import create_price_predictor
from ...utils.database import get_mongodb_client

logger = logging.getLogger(__name__)

class MarketAnalysisTool(BaseTool):
    """Tool for analyzing market conditions"""
    
    name = "market_analysis"
    description = "Analyze current market conditions for a given symbol including price, trends, and technical indicators"
    
    def _run(self, symbol: str) -> str:
        """Analyze market conditions"""
        try:
            # This would typically fetch real market data
            # For now, return a structured analysis
            analysis = {
                "symbol": symbol,
                "current_price": 150.25,
                "price_change_24h": 2.5,
                "volume": 1250000,
                "rsi": 65.2,
                "macd_signal": "bullish",
                "trend": "upward",
                "support_level": 148.0,
                "resistance_level": 155.0,
                "volatility": "moderate"
            }
            return json.dumps(analysis)
        except Exception as e:
            return f"Error analyzing market: {str(e)}"
    
    async def _arun(self, symbol: str) -> str:
        """Async version of market analysis"""
        return self._run(symbol)

class PredictionTool(BaseTool):
    """Tool for getting ML price predictions"""
    
    name = "price_prediction"
    description = "Get machine learning price predictions for a symbol"
    
    def _run(self, symbol: str) -> str:
        """Get price prediction"""
        try:
            # Placeholder prediction
            prediction = {
                "symbol": symbol,
                "current_price": 150.25,
                "predicted_price": 152.80,
                "confidence": 0.75,
                "prediction_horizon": "1_day",
                "model_used": "ensemble",
                "predicted_change_pct": 1.7
            }
            return json.dumps(prediction)
        except Exception as e:
            return f"Error getting prediction: {str(e)}"
    
    async def _arun(self, symbol: str) -> str:
        """Async version of prediction"""
        return self._run(symbol)

class RiskAssessmentTool(BaseTool):
    """Tool for risk assessment"""
    
    name = "risk_assessment"
    description = "Assess risk for a potential trade including position sizing and risk metrics"
    
    def _run(self, symbol: str, side: str, quantity: float, price: float) -> str:
        """Assess trade risk"""
        try:
            risk_assessment = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "position_value": quantity * price,
                "portfolio_percentage": 2.5,
                "risk_level": "medium",
                "max_loss": 500.0,
                "stop_loss_price": price * 0.98,
                "take_profit_price": price * 1.04,
                "risk_reward_ratio": 2.0,
                "approved": True
            }
            return json.dumps(risk_assessment)
        except Exception as e:
            return f"Error assessing risk: {str(e)}"
    
    async def _arun(self, symbol: str, side: str, quantity: float, price: float) -> str:
        """Async version of risk assessment"""
        return self._run(symbol, side, quantity, price)

class OrderExecutionTool(BaseTool):
    """Tool for executing trades"""
    
    name = "execute_order"
    description = "Execute a trading order with specified parameters"
    
    def _run(self, symbol: str, side: str, quantity: float, order_type: str = "market", limit_price: Optional[float] = None) -> str:
        """Execute trading order"""
        try:
            # Placeholder order execution
            order_result = {
                "order_id": "12345",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "status": "filled",
                "fill_price": limit_price or 150.25,
                "timestamp": datetime.utcnow().isoformat()
            }
            return json.dumps(order_result)
        except Exception as e:
            return f"Error executing order: {str(e)}"
    
    async def _arun(self, symbol: str, side: str, quantity: float, order_type: str = "market", limit_price: Optional[float] = None) -> str:
        """Async version of order execution"""
        return self._run(symbol, side, quantity, order_type, limit_price)

class PortfolioTool(BaseTool):
    """Tool for portfolio information"""
    
    name = "portfolio_info"
    description = "Get current portfolio information including positions, cash, and performance"
    
    def _run(self) -> str:
        """Get portfolio information"""
        try:
            portfolio_info = {
                "total_value": 105000.0,
                "cash": 25000.0,
                "positions_value": 80000.0,
                "day_pnl": 1250.0,
                "total_pnl": 5000.0,
                "positions_count": 5,
                "buying_power": 25000.0,
                "positions": [
                    {"symbol": "AAPL", "quantity": 100, "avg_price": 150.0, "current_value": 15025.0},
                    {"symbol": "MSFT", "quantity": 50, "avg_price": 300.0, "current_value": 15100.0}
                ]
            }
            return json.dumps(portfolio_info)
        except Exception as e:
            return f"Error getting portfolio info: {str(e)}"
    
    async def _arun(self) -> str:
        """Async version of portfolio info"""
        return self._run()

class TradingAgent:
    """AI Trading Agent using LangChain"""
    
    def __init__(self, agent_id: str = "trading_agent_001"):
        self.agent_id = agent_id
        self.llm = None
        self.agent_executor = None
        self.memory = None
        self.tools = []
        self.is_active = False
        self.trading_enabled = False
        
        # Trading parameters
        self.max_position_size = 0.05  # 5% of portfolio
        self.risk_tolerance = "medium"
        self.trading_style = "swing"  # swing, day, scalp
        
        # Performance tracking
        self.trades_made = 0
        self.successful_trades = 0
        self.total_pnl = 0.0
        
    async def initialize(self, openai_api_key: Optional[str] = None):
        """Initialize the trading agent"""
        
        try:
            # Initialize LLM
            if not openai_api_key:
                logger.warning("No OpenAI API key provided - using placeholder")
                # In production, this would require a valid API key
                return False
            
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,  # Low temperature for consistent trading decisions
                openai_api_key=openai_api_key
            )
            
            # Initialize tools
            self.tools = [
                MarketAnalysisTool(),
                PredictionTool(),
                RiskAssessmentTool(),
                OrderExecutionTool(),
                PortfolioTool()
            ]
            
            # Initialize memory
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                return_messages=True,
                k=10  # Keep last 10 interactions
            )
            
            # Create agent prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create agent
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                memory=self.memory,
                verbose=True,
                max_iterations=5,
                early_stopping_method="generate"
            )
            
            self.is_active = True
            logger.info(f"Trading agent {self.agent_id} initialized successfully")
            
            # Save agent state
            await self._save_agent_state()
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing trading agent: {e}")
            return False
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the trading agent"""
        
        return f"""
You are an AI Trading Agent with ID {self.agent_id}. Your role is to analyze markets, make trading decisions, and manage risk.

CORE RESPONSIBILITIES:
1. Analyze market conditions using available tools
2. Make informed trading decisions based on data
3. Manage risk and position sizing
4. Execute trades when conditions are favorable
5. Monitor and adjust positions as needed

TRADING PARAMETERS:
- Max position size: {self.max_position_size * 100}% of portfolio
- Risk tolerance: {self.risk_tolerance}
- Trading style: {self.trading_style}
- Trading enabled: {self.trading_enabled}

DECISION FRAMEWORK:
1. Always analyze market conditions first
2. Get ML predictions for price direction
3. Assess risk before any trade
4. Only trade when risk/reward is favorable (min 2:1 ratio)
5. Never risk more than 2% of portfolio on a single trade
6. Always set stop-loss and take-profit levels

RISK MANAGEMENT RULES:
- Never exceed maximum position size
- Always validate trades with risk assessment tool
- Monitor portfolio exposure and diversification
- Cut losses quickly, let profits run
- Avoid trading during high volatility without clear signals

COMMUNICATION STYLE:
- Be concise and data-driven
- Explain your reasoning for each decision
- Provide specific price levels and risk metrics
- Alert on any risk concerns immediately

Remember: Capital preservation is more important than profits. When in doubt, don't trade.
"""
    
    async def analyze_and_trade(self, symbols: List[str]) -> Dict[str, Any]:
        """Analyze symbols and make trading decisions"""
        
        if not self.is_active:
            return {"error": "Agent not initialized"}
        
        results = {
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "symbols_analyzed": symbols,
            "decisions": [],
            "trades_executed": [],
            "alerts": []
        }
        
        try:
            for symbol in symbols:
                logger.info(f"Analyzing {symbol}...")
                
                # Create analysis prompt
                analysis_prompt = f"""
                Analyze {symbol} for potential trading opportunities:
                
                1. Get current market analysis for {symbol}
                2. Get price prediction for {symbol}
                3. Check current portfolio status
                4. Based on the analysis, decide if we should:
                   - BUY (if bullish signals and good risk/reward)
                   - SELL (if bearish signals or risk management)
                   - HOLD (if no clear opportunity)
                
                If you decide to trade, also:
                - Assess the risk for the proposed trade
                - Execute the order if risk is acceptable
                
                Provide your reasoning and specific price levels.
                """
                
                # Get agent decision
                response = await self.agent_executor.ainvoke({
                    "input": analysis_prompt
                })
                
                decision = {
                    "symbol": symbol,
                    "analysis": response.get("output", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                results["decisions"].append(decision)
                
                # Parse decision for trades (simplified)
                if "BUY" in response.get("output", "").upper() and self.trading_enabled:
                    # This would be more sophisticated in practice
                    trade_result = await self._execute_trade_decision(symbol, "buy", response.get("output", ""))
                    if trade_result:
                        results["trades_executed"].append(trade_result)
                
                elif "SELL" in response.get("output", "").upper() and self.trading_enabled:
                    trade_result = await self._execute_trade_decision(symbol, "sell", response.get("output", ""))
                    if trade_result:
                        results["trades_executed"].append(trade_result)
                
                # Small delay between symbols
                await asyncio.sleep(1)
            
            # Save results
            await self._save_analysis_results(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in analyze_and_trade: {e}")
            results["error"] = str(e)
            return results
    
    async def _execute_trade_decision(self, symbol: str, side: str, reasoning: str) -> Optional[Dict[str, Any]]:
        """Execute a trade decision"""
        
        try:
            # This is a simplified implementation
            # In practice, would parse the reasoning for specific parameters
            
            quantity = 10  # Placeholder
            order_type = "market"
            
            # Execute through paper trading engine
            paper_engine = await get_paper_trading_engine()
            
            order_result = await paper_engine.place_order(
                symbol=symbol,
                qty=quantity,
                side=side,
                order_type=order_type
            )
            
            if order_result.get("status") != "rejected":
                self.trades_made += 1
                
                trade_record = {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "order_id": order_result.get("order_id"),
                    "reasoning": reasoning,
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent_id": self.agent_id
                }
                
                return trade_record
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing trade decision: {e}")
            return None
    
    async def monitor_positions(self) -> Dict[str, Any]:
        """Monitor existing positions and make adjustments"""
        
        if not self.is_active:
            return {"error": "Agent not initialized"}
        
        try:
            monitoring_prompt = """
            Monitor current portfolio positions:
            
            1. Get current portfolio information
            2. For each position, analyze if we should:
               - HOLD (position is performing well)
               - REDUCE (take some profits or cut losses)
               - CLOSE (exit completely)
            
            Consider:
            - Current P&L of each position
            - Risk management rules
            - Market conditions
            - Technical levels (support/resistance)
            
            Provide specific recommendations with reasoning.
            """
            
            response = await self.agent_executor.ainvoke({
                "input": monitoring_prompt
            })
            
            monitoring_result = {
                "agent_id": self.agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "monitoring_analysis": response.get("output", ""),
                "actions_taken": []
            }
            
            # Save monitoring results
            await self._save_monitoring_results(monitoring_result)
            
            return monitoring_result
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")
            return {"error": str(e)}
    
    async def get_market_outlook(self, timeframe: str = "daily") -> Dict[str, Any]:
        """Get overall market outlook"""
        
        if not self.is_active:
            return {"error": "Agent not initialized"}
        
        try:
            outlook_prompt = f"""
            Provide a comprehensive market outlook for {timeframe} timeframe:
            
            1. Analyze overall market sentiment
            2. Identify key opportunities and risks
            3. Suggest portfolio adjustments if needed
            4. Highlight any major economic events or catalysts
            
            Focus on actionable insights for trading decisions.
            """
            
            response = await self.agent_executor.ainvoke({
                "input": outlook_prompt
            })
            
            outlook = {
                "agent_id": self.agent_id,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat(),
                "outlook": response.get("output", ""),
                "confidence": 0.75  # Placeholder
            }
            
            return outlook
            
        except Exception as e:
            logger.error(f"Error getting market outlook: {e}")
            return {"error": str(e)}
    
    async def _save_agent_state(self):
        """Save agent state to database"""
        
        try:
            db_client = await get_mongodb_client()
            
            agent_state = {
                "agent_id": self.agent_id,
                "agent_type": "trading_agent",
                "is_active": self.is_active,
                "trading_enabled": self.trading_enabled,
                "max_position_size": self.max_position_size,
                "risk_tolerance": self.risk_tolerance,
                "trading_style": self.trading_style,
                "trades_made": self.trades_made,
                "successful_trades": self.successful_trades,
                "total_pnl": self.total_pnl,
                "last_update": datetime.utcnow(),
                "status": "active" if self.is_active else "inactive"
            }
            
            await db_client.save_agent_state(agent_state)
            
        except Exception as e:
            logger.error(f"Error saving agent state: {e}")
    
    async def _save_analysis_results(self, results: Dict[str, Any]):
        """Save analysis results to database"""
        
        try:
            db_client = await get_mongodb_client()
            
            analysis_record = {
                "agent_id": self.agent_id,
                "analysis_type": "symbol_analysis",
                "results": results,
                "timestamp": datetime.utcnow()
            }
            
            await db_client.get_collection('agent_analyses').insert_one(analysis_record)
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
    
    async def _save_monitoring_results(self, results: Dict[str, Any]):
        """Save monitoring results to database"""
        
        try:
            db_client = await get_mongodb_client()
            
            monitoring_record = {
                "agent_id": self.agent_id,
                "monitoring_type": "position_monitoring",
                "results": results,
                "timestamp": datetime.utcnow()
            }
            
            await db_client.get_collection('agent_monitoring').insert_one(monitoring_record)
            
        except Exception as e:
            logger.error(f"Error saving monitoring results: {e}")
    
    def enable_trading(self):
        """Enable live trading"""
        self.trading_enabled = True
        logger.info(f"Trading enabled for agent {self.agent_id}")
    
    def disable_trading(self):
        """Disable live trading"""
        self.trading_enabled = False
        logger.info(f"Trading disabled for agent {self.agent_id}")
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get agent performance summary"""
        
        win_rate = (self.successful_trades / max(self.trades_made, 1)) * 100
        
        return {
            "agent_id": self.agent_id,
            "is_active": self.is_active,
            "trading_enabled": self.trading_enabled,
            "trades_made": self.trades_made,
            "successful_trades": self.successful_trades,
            "win_rate": win_rate,
            "total_pnl": self.total_pnl,
            "risk_tolerance": self.risk_tolerance,
            "trading_style": self.trading_style,
            "last_update": datetime.utcnow().isoformat()
        }

# Factory function
async def create_trading_agent(agent_id: str = None, openai_api_key: str = None) -> TradingAgent:
    """Create and initialize a trading agent"""
    
    if not agent_id:
        agent_id = f"trading_agent_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    agent = TradingAgent(agent_id)
    
    # Initialize with API key if provided
    if openai_api_key:
        await agent.initialize(openai_api_key)
    
    return agent