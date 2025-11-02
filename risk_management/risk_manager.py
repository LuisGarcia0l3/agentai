"""
Advanced Risk Management System for AI Trading
Implements position sizing, stop-loss, portfolio risk controls
"""

import asyncio
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import logging
import numpy as np
import pandas as pd

from ..utils.database import get_mongodb_client

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskManager:
    """Advanced risk management system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Default risk parameters
        self.config = config or {
            'max_position_size': 0.02,      # 2% of portfolio per position
            'max_portfolio_risk': 0.05,     # 5% max portfolio risk
            'max_daily_loss': 0.03,         # 3% max daily loss
            'max_drawdown': 0.10,           # 10% max drawdown
            'stop_loss_percent': 0.02,      # 2% stop loss
            'take_profit_percent': 0.04,    # 4% take profit
            'max_correlation': 0.7,         # Max correlation between positions
            'volatility_lookback': 20,      # Days for volatility calculation
            'var_confidence': 0.95,         # VaR confidence level
            'max_leverage': 1.0,            # No leverage by default
            'sector_concentration': 0.25,   # Max 25% in one sector
            'currency_exposure': 0.30       # Max 30% in foreign currency
        }
        
        self.portfolio_value = 0.0
        self.cash = 0.0
        self.positions = {}
        self.daily_pnl = 0.0
        self.max_portfolio_value = 0.0
        self.risk_metrics = {}
        
    async def initialize(self, portfolio_value: float, cash: float, positions: List[Dict[str, Any]]):
        """Initialize risk manager with current portfolio state"""
        self.portfolio_value = portfolio_value
        self.cash = cash
        self.max_portfolio_value = max(self.max_portfolio_value, portfolio_value)
        
        # Convert positions to dict
        self.positions = {pos['symbol']: pos for pos in positions}
        
        # Calculate initial risk metrics
        await self._calculate_risk_metrics()
        
        logger.info(f"Risk manager initialized - Portfolio: ${portfolio_value:.2f}, Positions: {len(positions)}")
    
    async def validate_order(self, 
                           symbol: str,
                           qty: float,
                           side: str,
                           price: float,
                           order_type: str = 'market') -> Dict[str, Any]:
        """Validate order against risk parameters"""
        
        validation_result = {
            'approved': True,
            'risk_level': RiskLevel.LOW.value,
            'warnings': [],
            'rejections': [],
            'suggested_qty': qty,
            'risk_score': 0.0
        }
        
        try:
            # Calculate order value
            order_value = abs(qty) * price
            
            # 1. Position size check
            position_size_pct = order_value / self.portfolio_value
            max_position_size = self.config['max_position_size']
            
            if position_size_pct > max_position_size:
                suggested_qty = (max_position_size * self.portfolio_value) / price
                validation_result['warnings'].append(
                    f"Position size {position_size_pct:.2%} exceeds limit {max_position_size:.2%}"
                )
                validation_result['suggested_qty'] = suggested_qty
                validation_result['risk_level'] = RiskLevel.MEDIUM.value
            
            # 2. Portfolio risk check
            current_risk = await self._calculate_portfolio_risk()
            if side == 'buy':
                # Estimate additional risk from new position
                additional_risk = position_size_pct * 0.2  # Simplified risk estimate
                total_risk = current_risk + additional_risk
                
                if total_risk > self.config['max_portfolio_risk']:
                    validation_result['rejections'].append(
                        f"Total portfolio risk {total_risk:.2%} would exceed limit {self.config['max_portfolio_risk']:.2%}"
                    )
                    validation_result['approved'] = False
                    validation_result['risk_level'] = RiskLevel.HIGH.value
            
            # 3. Cash availability check
            if side == 'buy' and order_value > self.cash:
                validation_result['rejections'].append(
                    f"Insufficient cash: need ${order_value:.2f}, have ${self.cash:.2f}"
                )
                validation_result['approved'] = False
            
            # 4. Daily loss limit check
            daily_loss_pct = abs(self.daily_pnl) / self.portfolio_value if self.portfolio_value > 0 else 0
            if daily_loss_pct > self.config['max_daily_loss']:
                validation_result['rejections'].append(
                    f"Daily loss limit exceeded: {daily_loss_pct:.2%} > {self.config['max_daily_loss']:.2%}"
                )
                validation_result['approved'] = False
                validation_result['risk_level'] = RiskLevel.CRITICAL.value
            
            # 5. Drawdown check
            current_drawdown = (self.max_portfolio_value - self.portfolio_value) / self.max_portfolio_value
            if current_drawdown > self.config['max_drawdown']:
                validation_result['warnings'].append(
                    f"Portfolio in drawdown: {current_drawdown:.2%} > {self.config['max_drawdown']:.2%}"
                )
                validation_result['risk_level'] = RiskLevel.HIGH.value
            
            # 6. Correlation check (for buy orders)
            if side == 'buy' and len(self.positions) > 0:
                correlation_risk = await self._check_correlation_risk(symbol)
                if correlation_risk > self.config['max_correlation']:
                    validation_result['warnings'].append(
                        f"High correlation risk: {correlation_risk:.2f} > {self.config['max_correlation']:.2f}"
                    )
                    validation_result['risk_level'] = RiskLevel.MEDIUM.value
            
            # 7. Volatility check
            volatility = await self._get_symbol_volatility(symbol)
            if volatility and volatility > 0.5:  # 50% annualized volatility
                validation_result['warnings'].append(
                    f"High volatility asset: {volatility:.2%} annualized"
                )
                validation_result['risk_level'] = RiskLevel.MEDIUM.value
            
            # Calculate overall risk score
            validation_result['risk_score'] = self._calculate_risk_score(validation_result)
            
            # Log validation result
            logger.info(f"Order validation - {symbol} {side} {qty}: {validation_result['risk_level']} risk, approved: {validation_result['approved']}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating order: {e}")
            return {
                'approved': False,
                'risk_level': RiskLevel.CRITICAL.value,
                'warnings': [],
                'rejections': [f"Validation error: {str(e)}"],
                'suggested_qty': 0,
                'risk_score': 1.0
            }
    
    async def calculate_position_size(self, 
                                    symbol: str,
                                    entry_price: float,
                                    stop_loss_price: Optional[float] = None,
                                    risk_per_trade: Optional[float] = None) -> Dict[str, Any]:
        """Calculate optimal position size using various methods"""
        
        risk_per_trade = risk_per_trade or self.config['max_position_size']
        
        # Method 1: Fixed percentage of portfolio
        fixed_pct_size = (risk_per_trade * self.portfolio_value) / entry_price
        
        # Method 2: Risk-based sizing (if stop loss provided)
        risk_based_size = 0
        if stop_loss_price:
            risk_per_share = abs(entry_price - stop_loss_price)
            max_risk_amount = risk_per_trade * self.portfolio_value
            risk_based_size = max_risk_amount / risk_per_share if risk_per_share > 0 else 0
        
        # Method 3: Volatility-adjusted sizing
        volatility = await self._get_symbol_volatility(symbol)
        vol_adjusted_size = fixed_pct_size
        if volatility:
            # Reduce size for high volatility assets
            vol_adjustment = min(1.0, 0.2 / volatility)  # Target 20% volatility
            vol_adjusted_size = fixed_pct_size * vol_adjustment
        
        # Method 4: Kelly Criterion (simplified)
        kelly_size = await self._calculate_kelly_size(symbol, entry_price)
        
        # Choose the most conservative size
        sizes = [s for s in [fixed_pct_size, risk_based_size, vol_adjusted_size, kelly_size] if s > 0]
        recommended_size = min(sizes) if sizes else 0
        
        # Ensure size doesn't exceed cash available
        max_affordable = self.cash / entry_price
        final_size = min(recommended_size, max_affordable)
        
        return {
            'recommended_size': final_size,
            'fixed_percentage_size': fixed_pct_size,
            'risk_based_size': risk_based_size,
            'volatility_adjusted_size': vol_adjusted_size,
            'kelly_size': kelly_size,
            'max_affordable': max_affordable,
            'position_value': final_size * entry_price,
            'portfolio_percentage': (final_size * entry_price) / self.portfolio_value * 100
        }
    
    async def calculate_stop_loss(self, 
                                symbol: str,
                                entry_price: float,
                                side: str,
                                method: str = 'percentage') -> Dict[str, Any]:
        """Calculate stop loss levels using various methods"""
        
        stop_levels = {}
        
        # Method 1: Fixed percentage
        stop_pct = self.config['stop_loss_percent']
        if side == 'buy':
            stop_levels['percentage'] = entry_price * (1 - stop_pct)
        else:
            stop_levels['percentage'] = entry_price * (1 + stop_pct)
        
        # Method 2: ATR-based stop loss
        atr_stop = await self._calculate_atr_stop_loss(symbol, entry_price, side)
        if atr_stop:
            stop_levels['atr'] = atr_stop
        
        # Method 3: Support/Resistance based
        sr_stop = await self._calculate_support_resistance_stop(symbol, entry_price, side)
        if sr_stop:
            stop_levels['support_resistance'] = sr_stop
        
        # Method 4: Volatility-based
        volatility = await self._get_symbol_volatility(symbol)
        if volatility:
            vol_stop_distance = entry_price * volatility * 0.5  # Half of daily volatility
            if side == 'buy':
                stop_levels['volatility'] = entry_price - vol_stop_distance
            else:
                stop_levels['volatility'] = entry_price + vol_stop_distance
        
        # Choose recommended stop loss
        recommended_stop = stop_levels.get(method, stop_levels.get('percentage'))
        
        return {
            'recommended_stop': recommended_stop,
            'stop_levels': stop_levels,
            'risk_per_share': abs(entry_price - recommended_stop),
            'risk_percentage': abs(entry_price - recommended_stop) / entry_price * 100
        }
    
    async def calculate_take_profit(self,
                                  symbol: str,
                                  entry_price: float,
                                  side: str,
                                  risk_reward_ratio: float = 2.0) -> Dict[str, Any]:
        """Calculate take profit levels"""
        
        # Get stop loss for risk calculation
        stop_loss_info = await self.calculate_stop_loss(symbol, entry_price, side)
        risk_per_share = stop_loss_info['risk_per_share']
        
        profit_levels = {}
        
        # Method 1: Risk-reward ratio based
        profit_distance = risk_per_share * risk_reward_ratio
        if side == 'buy':
            profit_levels['risk_reward'] = entry_price + profit_distance
        else:
            profit_levels['risk_reward'] = entry_price - profit_distance
        
        # Method 2: Fixed percentage
        profit_pct = self.config['take_profit_percent']
        if side == 'buy':
            profit_levels['percentage'] = entry_price * (1 + profit_pct)
        else:
            profit_levels['percentage'] = entry_price * (1 - profit_pct)
        
        # Method 3: Resistance/Support based
        rs_profit = await self._calculate_resistance_support_profit(symbol, entry_price, side)
        if rs_profit:
            profit_levels['resistance_support'] = rs_profit
        
        recommended_profit = profit_levels['risk_reward']
        
        return {
            'recommended_profit': recommended_profit,
            'profit_levels': profit_levels,
            'profit_per_share': abs(recommended_profit - entry_price),
            'profit_percentage': abs(recommended_profit - entry_price) / entry_price * 100,
            'risk_reward_ratio': abs(recommended_profit - entry_price) / risk_per_share if risk_per_share > 0 else 0
        }
    
    async def monitor_positions(self) -> List[Dict[str, Any]]:
        """Monitor all positions for risk alerts"""
        alerts = []
        
        for symbol, position in self.positions.items():
            try:
                # Get current price
                current_price = await self._get_current_price(symbol)
                if not current_price:
                    continue
                
                # Calculate current P&L
                if position['qty'] > 0:  # Long position
                    pnl_pct = (current_price - position['avg_price']) / position['avg_price']
                else:  # Short position
                    pnl_pct = (position['avg_price'] - current_price) / position['avg_price']
                
                # Check stop loss
                stop_loss_pct = -self.config['stop_loss_percent']
                if pnl_pct <= stop_loss_pct:
                    alerts.append({
                        'type': 'stop_loss_triggered',
                        'symbol': symbol,
                        'current_pnl_pct': pnl_pct,
                        'stop_loss_pct': stop_loss_pct,
                        'severity': 'high',
                        'action': 'close_position',
                        'message': f"{symbol} hit stop loss: {pnl_pct:.2%} loss"
                    })
                
                # Check take profit
                take_profit_pct = self.config['take_profit_percent']
                if pnl_pct >= take_profit_pct:
                    alerts.append({
                        'type': 'take_profit_triggered',
                        'symbol': symbol,
                        'current_pnl_pct': pnl_pct,
                        'take_profit_pct': take_profit_pct,
                        'severity': 'medium',
                        'action': 'consider_profit_taking',
                        'message': f"{symbol} reached take profit: {pnl_pct:.2%} gain"
                    })
                
                # Check for unusual volatility
                volatility = await self._get_symbol_volatility(symbol)
                if volatility and volatility > 0.6:  # 60% annualized volatility
                    alerts.append({
                        'type': 'high_volatility',
                        'symbol': symbol,
                        'volatility': volatility,
                        'severity': 'medium',
                        'action': 'monitor_closely',
                        'message': f"{symbol} showing high volatility: {volatility:.2%}"
                    })
                
            except Exception as e:
                logger.error(f"Error monitoring position {symbol}: {e}")
        
        return alerts
    
    async def _calculate_risk_metrics(self):
        """Calculate comprehensive risk metrics"""
        try:
            # Portfolio-level metrics
            portfolio_risk = await self._calculate_portfolio_risk()
            var_95 = await self._calculate_var(0.95)
            var_99 = await self._calculate_var(0.99)
            
            # Drawdown metrics
            current_drawdown = (self.max_portfolio_value - self.portfolio_value) / self.max_portfolio_value
            
            # Concentration metrics
            concentration = await self._calculate_concentration_risk()
            
            self.risk_metrics = {
                'portfolio_risk': portfolio_risk,
                'var_95': var_95,
                'var_99': var_99,
                'current_drawdown': current_drawdown,
                'max_drawdown': self.config['max_drawdown'],
                'concentration_risk': concentration,
                'positions_count': len(self.positions),
                'cash_percentage': self.cash / self.portfolio_value if self.portfolio_value > 0 else 1.0,
                'leverage': (self.portfolio_value - self.cash) / self.portfolio_value if self.portfolio_value > 0 else 0.0,
                'last_updated': datetime.utcnow()
            }
            
            # Save to database
            db_client = await get_mongodb_client()
            await db_client.save_risk_metrics(self.risk_metrics)
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
    
    async def _calculate_portfolio_risk(self) -> float:
        """Calculate overall portfolio risk (simplified VaR)"""
        if not self.positions:
            return 0.0
        
        total_risk = 0.0
        for symbol, position in self.positions.items():
            position_value = abs(position['qty'] * position.get('current_price', position['avg_price']))
            position_weight = position_value / self.portfolio_value
            
            # Get volatility
            volatility = await self._get_symbol_volatility(symbol)
            if volatility:
                position_risk = position_weight * volatility
                total_risk += position_risk ** 2  # Simplified - assumes no correlation
        
        return math.sqrt(total_risk)
    
    async def _calculate_var(self, confidence: float) -> float:
        """Calculate Value at Risk"""
        # Simplified VaR calculation
        portfolio_risk = await self._calculate_portfolio_risk()
        
        # Z-score for confidence level
        z_scores = {0.90: 1.28, 0.95: 1.65, 0.99: 2.33}
        z_score = z_scores.get(confidence, 1.65)
        
        var = self.portfolio_value * portfolio_risk * z_score
        return var
    
    async def _calculate_concentration_risk(self) -> float:
        """Calculate concentration risk (Herfindahl index)"""
        if not self.positions:
            return 0.0
        
        total_value = sum(abs(pos['qty'] * pos.get('current_price', pos['avg_price'])) 
                         for pos in self.positions.values())
        
        if total_value == 0:
            return 0.0
        
        hhi = sum((abs(pos['qty'] * pos.get('current_price', pos['avg_price'])) / total_value) ** 2 
                 for pos in self.positions.values())
        
        return hhi
    
    async def _check_correlation_risk(self, symbol: str) -> float:
        """Check correlation risk with existing positions"""
        # Simplified correlation check - would need historical data for proper calculation
        # For now, return a placeholder value
        return 0.3  # Assume moderate correlation
    
    async def _get_symbol_volatility(self, symbol: str) -> Optional[float]:
        """Get symbol volatility (annualized)"""
        try:
            # Get historical data for volatility calculation
            db_client = await get_mongodb_client()
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.config['volatility_lookback'])
            
            market_data = await db_client.get_market_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if len(market_data) < 10:  # Need minimum data points
                return None
            
            # Calculate daily returns
            prices = [data['close'] for data in market_data]
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            
            # Calculate volatility (annualized)
            daily_vol = np.std(returns)
            annualized_vol = daily_vol * math.sqrt(252)  # 252 trading days
            
            return annualized_vol
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return None
    
    async def _calculate_kelly_size(self, symbol: str, price: float) -> float:
        """Calculate Kelly Criterion position size"""
        # Simplified Kelly calculation - would need historical win rate and avg win/loss
        # For now, return conservative estimate
        return (self.config['max_position_size'] * self.portfolio_value) / price * 0.5
    
    async def _calculate_atr_stop_loss(self, symbol: str, entry_price: float, side: str) -> Optional[float]:
        """Calculate ATR-based stop loss"""
        # Placeholder - would need ATR calculation from historical data
        atr_multiplier = 2.0
        estimated_atr = entry_price * 0.02  # 2% of price as rough ATR estimate
        
        if side == 'buy':
            return entry_price - (atr_multiplier * estimated_atr)
        else:
            return entry_price + (atr_multiplier * estimated_atr)
    
    async def _calculate_support_resistance_stop(self, symbol: str, entry_price: float, side: str) -> Optional[float]:
        """Calculate support/resistance based stop loss"""
        # Placeholder - would need technical analysis
        return None
    
    async def _calculate_resistance_support_profit(self, symbol: str, entry_price: float, side: str) -> Optional[float]:
        """Calculate resistance/support based take profit"""
        # Placeholder - would need technical analysis
        return None
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol"""
        # This would typically come from market data feed
        # For now, return the average price from position
        position = self.positions.get(symbol)
        return position.get('current_price') or position.get('avg_price') if position else None
    
    def _calculate_risk_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall risk score (0-1, where 1 is highest risk)"""
        score = 0.0
        
        # Add score based on warnings and rejections
        score += len(validation_result['warnings']) * 0.2
        score += len(validation_result['rejections']) * 0.5
        
        # Add score based on risk level
        risk_level_scores = {
            RiskLevel.LOW.value: 0.1,
            RiskLevel.MEDIUM.value: 0.3,
            RiskLevel.HIGH.value: 0.7,
            RiskLevel.CRITICAL.value: 1.0
        }
        score += risk_level_scores.get(validation_result['risk_level'], 0.1)
        
        return min(score, 1.0)
    
    async def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        await self._calculate_risk_metrics()
        
        # Get position alerts
        alerts = await self.monitor_positions()
        
        return {
            'risk_metrics': self.risk_metrics,
            'alerts': alerts,
            'portfolio_health': self._assess_portfolio_health(),
            'recommendations': await self._generate_risk_recommendations()
        }
    
    def _assess_portfolio_health(self) -> str:
        """Assess overall portfolio health"""
        if not self.risk_metrics:
            return "unknown"
        
        risk_factors = 0
        
        # Check various risk factors
        if self.risk_metrics['current_drawdown'] > 0.05:  # 5% drawdown
            risk_factors += 1
        
        if self.risk_metrics['portfolio_risk'] > 0.15:  # 15% portfolio risk
            risk_factors += 1
        
        if self.risk_metrics['concentration_risk'] > 0.3:  # High concentration
            risk_factors += 1
        
        if self.risk_metrics['leverage'] > 0.5:  # 50% leverage
            risk_factors += 1
        
        if risk_factors == 0:
            return "excellent"
        elif risk_factors == 1:
            return "good"
        elif risk_factors == 2:
            return "moderate"
        elif risk_factors == 3:
            return "poor"
        else:
            return "critical"
    
    async def _generate_risk_recommendations(self) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if not self.risk_metrics:
            return recommendations
        
        # Drawdown recommendations
        if self.risk_metrics['current_drawdown'] > 0.05:
            recommendations.append("Consider reducing position sizes due to current drawdown")
        
        # Concentration recommendations
        if self.risk_metrics['concentration_risk'] > 0.3:
            recommendations.append("Portfolio is highly concentrated - consider diversification")
        
        # Cash recommendations
        if self.risk_metrics['cash_percentage'] < 0.1:
            recommendations.append("Consider maintaining higher cash reserves")
        
        # Risk recommendations
        if self.risk_metrics['portfolio_risk'] > 0.15:
            recommendations.append("Portfolio risk is elevated - consider reducing exposure")
        
        return recommendations

# Global risk manager instance
risk_manager = RiskManager()

async def get_risk_manager() -> RiskManager:
    """Get risk manager instance"""
    return risk_manager