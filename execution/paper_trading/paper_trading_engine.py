"""
Paper Trading Engine for AI Trading System
Simulates real trading without actual money
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import logging

from ...utils.database import get_mongodb_client
from ..brokers.alpaca_broker import AlpacaBroker

logger = logging.getLogger(__name__)

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class PaperTradingEngine:
    """Paper trading engine that simulates real trading"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # symbol -> position data
        self.orders = {}     # order_id -> order data
        self.trades = []     # executed trades history
        self.portfolio_value = initial_capital
        
        # Market data source (using Alpaca for real market data)
        self.market_data_source = AlpacaBroker()
        self.connected = False
        
        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.max_drawdown = 0.0
        self.peak_value = initial_capital
        
    async def connect(self) -> bool:
        """Connect to market data source"""
        try:
            success = await self.market_data_source.connect()
            if success:
                self.connected = True
                logger.info("Paper trading engine connected to market data")
                
                # Initialize database connection
                db_client = await get_mongodb_client()
                await self._load_state_from_db(db_client)
                
            return success
        except Exception as e:
            logger.error(f"Failed to connect paper trading engine: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from market data source"""
        if self.market_data_source:
            await self.market_data_source.disconnect()
        self.connected = False
        logger.info("Paper trading engine disconnected")
    
    async def _load_state_from_db(self, db_client):
        """Load paper trading state from database"""
        try:
            # Load positions
            positions = await db_client.get_positions()
            for pos in positions:
                if pos.get('broker') == 'paper':
                    self.positions[pos['symbol']] = pos
            
            # Load pending orders
            orders = await db_client.get_collection('orders').find({
                'broker': 'paper',
                'status': {'$in': ['pending', 'partially_filled']}
            }).to_list(length=None)
            
            for order in orders:
                self.orders[order['order_id']] = order
            
            # Calculate current portfolio value
            await self._update_portfolio_value()
            
            logger.info(f"Loaded paper trading state - Cash: ${self.cash:.2f}, Positions: {len(self.positions)}")
            
        except Exception as e:
            logger.error(f"Error loading paper trading state: {e}")
    
    async def _save_state_to_db(self, db_client):
        """Save paper trading state to database"""
        try:
            # Save positions
            for symbol, position in self.positions.items():
                await db_client.save_position(position)
            
            # Save portfolio snapshot
            await db_client.save_portfolio_snapshot({
                'broker': 'paper',
                'cash': self.cash,
                'portfolio_value': self.portfolio_value,
                'total_pnl': self.total_pnl,
                'positions_count': len(self.positions),
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': self.winning_trades / max(self.total_trades, 1),
                'max_drawdown': self.max_drawdown
            })
            
        except Exception as e:
            logger.error(f"Error saving paper trading state: {e}")
    
    async def place_order(self,
                         symbol: str,
                         qty: Union[int, float],
                         side: str,
                         order_type: str = 'market',
                         limit_price: Optional[float] = None,
                         stop_price: Optional[float] = None,
                         time_in_force: str = 'day',
                         client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place a paper trading order"""
        
        if not self.connected:
            raise ConnectionError("Paper trading engine not connected")
        
        # Generate order ID
        order_id = client_order_id or str(uuid.uuid4())
        
        # Validate order
        validation_result = await self._validate_order(symbol, qty, side, order_type, limit_price, stop_price)
        if not validation_result['valid']:
            return {
                'order_id': order_id,
                'status': OrderStatus.REJECTED.value,
                'rejection_reason': validation_result['reason']
            }
        
        # Get current market price
        current_price = await self._get_current_price(symbol)
        if not current_price:
            return {
                'order_id': order_id,
                'status': OrderStatus.REJECTED.value,
                'rejection_reason': f"Unable to get market price for {symbol}"
            }
        
        # Create order
        order = {
            'order_id': order_id,
            'symbol': symbol.upper(),
            'qty': abs(float(qty)),
            'side': side.lower(),
            'order_type': order_type.lower(),
            'limit_price': limit_price,
            'stop_price': stop_price,
            'time_in_force': time_in_force,
            'status': OrderStatus.PENDING.value,
            'filled_qty': 0.0,
            'avg_fill_price': 0.0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'broker': 'paper',
            'current_market_price': current_price
        }
        
        # Try to fill immediately for market orders
        if order_type.lower() == 'market':
            await self._fill_order(order, current_price)
        else:
            # Store pending order
            self.orders[order_id] = order
        
        # Save to database
        db_client = await get_mongodb_client()
        await db_client.get_collection('orders').insert_one(order)
        
        logger.info(f"Paper order placed: {order_id} - {side} {qty} {symbol} @ {order_type}")
        
        return {
            'order_id': order_id,
            'status': order['status'],
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'order_type': order_type,
            'created_at': order['created_at'].isoformat()
        }
    
    async def _validate_order(self, symbol: str, qty: float, side: str, order_type: str, 
                             limit_price: Optional[float], stop_price: Optional[float]) -> Dict[str, Any]:
        """Validate order parameters"""
        
        # Check basic parameters
        if qty <= 0:
            return {'valid': False, 'reason': 'Quantity must be positive'}
        
        if side.lower() not in ['buy', 'sell']:
            return {'valid': False, 'reason': 'Side must be buy or sell'}
        
        if order_type.lower() not in ['market', 'limit', 'stop', 'stop_limit']:
            return {'valid': False, 'reason': 'Invalid order type'}
        
        # Check price parameters
        if order_type.lower() in ['limit', 'stop_limit'] and not limit_price:
            return {'valid': False, 'reason': 'Limit price required for limit orders'}
        
        if order_type.lower() in ['stop', 'stop_limit'] and not stop_price:
            return {'valid': False, 'reason': 'Stop price required for stop orders'}
        
        # Check buying power for buy orders
        if side.lower() == 'buy':
            current_price = await self._get_current_price(symbol)
            if not current_price:
                return {'valid': False, 'reason': f'Unable to get price for {symbol}'}
            
            order_value = qty * (limit_price or current_price)
            if order_value > self.cash:
                return {'valid': False, 'reason': f'Insufficient buying power. Need ${order_value:.2f}, have ${self.cash:.2f}'}
        
        # Check position for sell orders
        elif side.lower() == 'sell':
            position = self.positions.get(symbol.upper())
            if not position or position['qty'] < qty:
                available_qty = position['qty'] if position else 0
                return {'valid': False, 'reason': f'Insufficient shares. Need {qty}, have {available_qty}'}
        
        return {'valid': True, 'reason': None}
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol"""
        try:
            # Get latest market data
            market_data = await self.market_data_source.get_market_data(
                symbol=symbol,
                timeframe='1m',
                limit=1
            )
            
            if market_data:
                return market_data[-1]['close']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    async def _fill_order(self, order: Dict[str, Any], fill_price: float):
        """Fill an order at the specified price"""
        
        symbol = order['symbol']
        qty = order['qty']
        side = order['side']
        
        # Calculate fill details
        fill_value = qty * fill_price
        commission = self._calculate_commission(fill_value)
        
        # Update cash and positions
        if side == 'buy':
            self.cash -= (fill_value + commission)
            
            # Update position
            if symbol in self.positions:
                # Add to existing position
                current_pos = self.positions[symbol]
                total_qty = current_pos['qty'] + qty
                total_cost = (current_pos['qty'] * current_pos['avg_price']) + fill_value
                avg_price = total_cost / total_qty
                
                self.positions[symbol].update({
                    'qty': total_qty,
                    'avg_price': avg_price,
                    'market_value': total_qty * fill_price,
                    'unrealized_pnl': (fill_price - avg_price) * total_qty,
                    'updated_at': datetime.utcnow()
                })
            else:
                # Create new position
                self.positions[symbol] = {
                    'symbol': symbol,
                    'qty': qty,
                    'avg_price': fill_price,
                    'market_value': fill_value,
                    'unrealized_pnl': 0.0,
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'broker': 'paper',
                    'status': 'active'
                }
        
        else:  # sell
            self.cash += (fill_value - commission)
            
            # Update position
            if symbol in self.positions:
                current_pos = self.positions[symbol]
                realized_pnl = (fill_price - current_pos['avg_price']) * qty
                
                if current_pos['qty'] == qty:
                    # Close position completely
                    del self.positions[symbol]
                else:
                    # Reduce position
                    new_qty = current_pos['qty'] - qty
                    self.positions[symbol].update({
                        'qty': new_qty,
                        'market_value': new_qty * fill_price,
                        'unrealized_pnl': (fill_price - current_pos['avg_price']) * new_qty,
                        'updated_at': datetime.utcnow()
                    })
                
                # Track realized PnL
                self.total_pnl += realized_pnl
                if realized_pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1
        
        # Update order status
        order.update({
            'status': OrderStatus.FILLED.value,
            'filled_qty': qty,
            'avg_fill_price': fill_price,
            'filled_at': datetime.utcnow(),
            'commission': commission
        })
        
        # Record trade
        trade = {
            'trade_id': str(uuid.uuid4()),
            'order_id': order['order_id'],
            'symbol': symbol,
            'side': side,
            'qty': qty,
            'price': fill_price,
            'value': fill_value,
            'commission': commission,
            'timestamp': datetime.utcnow(),
            'broker': 'paper'
        }
        
        self.trades.append(trade)
        self.total_trades += 1
        
        # Update portfolio value
        await self._update_portfolio_value()
        
        # Save to database
        db_client = await get_mongodb_client()
        await db_client.save_trade(trade)
        await self._save_state_to_db(db_client)
        
        logger.info(f"Order filled: {order['order_id']} - {side} {qty} {symbol} @ ${fill_price:.2f}")
    
    def _calculate_commission(self, trade_value: float) -> float:
        """Calculate commission for trade (Alpaca is commission-free)"""
        return 0.0  # Alpaca doesn't charge commissions
    
    async def _update_portfolio_value(self):
        """Update total portfolio value"""
        total_value = self.cash
        
        # Add market value of all positions
        for symbol, position in self.positions.items():
            current_price = await self._get_current_price(symbol)
            if current_price:
                market_value = position['qty'] * current_price
                total_value += market_value
                
                # Update position market value and unrealized PnL
                position['market_value'] = market_value
                position['unrealized_pnl'] = (current_price - position['avg_price']) * position['qty']
        
        self.portfolio_value = total_value
        
        # Update max drawdown
        if total_value > self.peak_value:
            self.peak_value = total_value
        
        current_drawdown = (self.peak_value - total_value) / self.peak_value
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order['status'] != OrderStatus.PENDING.value:
            return False
        
        # Update order status
        order.update({
            'status': OrderStatus.CANCELLED.value,
            'cancelled_at': datetime.utcnow()
        })
        
        # Remove from pending orders
        del self.orders[order_id]
        
        # Update in database
        db_client = await get_mongodb_client()
        await db_client.get_collection('orders').update_one(
            {'order_id': order_id},
            {'$set': order}
        )
        
        logger.info(f"Order cancelled: {order_id}")
        return True
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get paper trading account information"""
        await self._update_portfolio_value()
        
        return {
            'account_id': 'paper_trading',
            'broker': 'paper',
            'cash': self.cash,
            'buying_power': self.cash,
            'portfolio_value': self.portfolio_value,
            'total_pnl': self.total_pnl,
            'day_pnl': 0.0,  # TODO: Calculate daily PnL
            'positions_count': len(self.positions),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.winning_trades / max(self.total_trades, 1),
            'max_drawdown': self.max_drawdown,
            'initial_capital': self.initial_capital,
            'return_pct': ((self.portfolio_value - self.initial_capital) / self.initial_capital) * 100
        }
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        await self._update_portfolio_value()
        return list(self.positions.values())
    
    async def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get orders"""
        orders = list(self.orders.values())
        
        if status:
            orders = [order for order in orders if order['status'] == status]
        
        return orders
    
    async def get_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get trade history"""
        return self.trades[-limit:] if limit else self.trades
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        await self._update_portfolio_value()
        
        total_return = self.portfolio_value - self.initial_capital
        return_pct = (total_return / self.initial_capital) * 100
        
        # Calculate Sharpe ratio (simplified)
        # TODO: Implement proper Sharpe ratio calculation with daily returns
        sharpe_ratio = return_pct / max(self.max_drawdown * 100, 1)
        
        return {
            'total_return': total_return,
            'return_percentage': return_pct,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.winning_trades / max(self.total_trades, 1),
            'profit_factor': abs(self.total_pnl) / max(abs(self.total_pnl - total_return), 1),
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'portfolio_value': self.portfolio_value,
            'cash': self.cash,
            'positions_value': self.portfolio_value - self.cash
        }
    
    async def process_pending_orders(self):
        """Process pending orders (check for fills)"""
        if not self.orders:
            return
        
        filled_orders = []
        
        for order_id, order in self.orders.items():
            if order['status'] != OrderStatus.PENDING.value:
                continue
            
            symbol = order['symbol']
            current_price = await self._get_current_price(symbol)
            
            if not current_price:
                continue
            
            should_fill = False
            fill_price = current_price
            
            # Check fill conditions based on order type
            if order['order_type'] == 'limit':
                if order['side'] == 'buy' and current_price <= order['limit_price']:
                    should_fill = True
                    fill_price = order['limit_price']
                elif order['side'] == 'sell' and current_price >= order['limit_price']:
                    should_fill = True
                    fill_price = order['limit_price']
            
            elif order['order_type'] == 'stop':
                if order['side'] == 'buy' and current_price >= order['stop_price']:
                    should_fill = True
                elif order['side'] == 'sell' and current_price <= order['stop_price']:
                    should_fill = True
            
            elif order['order_type'] == 'stop_limit':
                # Stop triggered, now check limit
                if order['side'] == 'buy' and current_price >= order['stop_price']:
                    if current_price <= order['limit_price']:
                        should_fill = True
                        fill_price = order['limit_price']
                elif order['side'] == 'sell' and current_price <= order['stop_price']:
                    if current_price >= order['limit_price']:
                        should_fill = True
                        fill_price = order['limit_price']
            
            if should_fill:
                await self._fill_order(order, fill_price)
                filled_orders.append(order_id)
        
        # Remove filled orders from pending
        for order_id in filled_orders:
            if order_id in self.orders:
                del self.orders[order_id]
    
    async def start_order_processing(self, interval: int = 60):
        """Start background order processing"""
        while self.connected:
            try:
                await self.process_pending_orders()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in order processing: {e}")
                await asyncio.sleep(interval)

# Global paper trading engine instance
paper_trading_engine = PaperTradingEngine()

async def get_paper_trading_engine() -> PaperTradingEngine:
    """Get paper trading engine instance"""
    if not paper_trading_engine.connected:
        await paper_trading_engine.connect()
    return paper_trading_engine