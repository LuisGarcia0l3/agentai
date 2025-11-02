"""
Alpaca Broker Implementation for AI Trading System
Handles paper trading and live trading through Alpaca API
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import logging

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError
from alpaca_trade_api.entity import Order, Position, Account, Asset

from ..base_broker import BaseBroker
from ...utils.database import get_mongodb_client

logger = logging.getLogger(__name__)

class AlpacaBroker(BaseBroker):
    """Alpaca broker implementation for paper and live trading"""
    
    def __init__(self):
        super().__init__()
        
        # Alpaca API credentials
        self.api_key = os.getenv('ALPACA_API_KEY')
        self.secret_key = os.getenv('ALPACA_SECRET_KEY')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not found in environment variables")
        
        # Initialize Alpaca API
        self.api = tradeapi.REST(
            key_id=self.api_key,
            secret_key=self.secret_key,
            base_url=self.base_url,
            api_version='v2'
        )
        
        self.connected = False
        self.account_info = None
        
    async def connect(self) -> bool:
        """Connect to Alpaca API"""
        try:
            # Test connection by getting account info
            self.account_info = self.api.get_account()
            self.connected = True
            
            logger.info(f"Connected to Alpaca - Account: {self.account_info.id}")
            logger.info(f"Account Status: {self.account_info.status}")
            logger.info(f"Buying Power: ${self.account_info.buying_power}")
            logger.info(f"Portfolio Value: ${self.account_info.portfolio_value}")
            
            return True
            
        except APIError as e:
            logger.error(f"Failed to connect to Alpaca: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from Alpaca API"""
        self.connected = False
        logger.info("Disconnected from Alpaca")
    
    def _validate_connection(self):
        """Validate connection before operations"""
        if not self.connected:
            raise ConnectionError("Not connected to Alpaca. Call connect() first.")
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        self._validate_connection()
        
        try:
            account = self.api.get_account()
            return {
                'account_id': account.id,
                'status': account.status,
                'currency': account.currency,
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'last_equity': float(account.last_equity),
                'multiplier': int(account.multiplier),
                'day_trade_count': int(account.day_trade_count),
                'daytrade_buying_power': float(account.daytrade_buying_power),
                'regt_buying_power': float(account.regt_buying_power),
                'pattern_day_trader': account.pattern_day_trader,
                'trading_blocked': account.trading_blocked,
                'transfers_blocked': account.transfers_blocked,
                'account_blocked': account.account_blocked,
                'created_at': account.created_at.isoformat() if account.created_at else None,
                'trade_suspended_by_user': account.trade_suspended_by_user,
                'shorting_enabled': account.shorting_enabled,
                'long_market_value': float(account.long_market_value),
                'short_market_value': float(account.short_market_value),
                'initial_margin': float(account.initial_margin),
                'maintenance_margin': float(account.maintenance_margin),
                'sma': float(account.sma) if account.sma else 0.0
            }
        except APIError as e:
            logger.error(f"Error getting account info: {e}")
            raise
    
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        self._validate_connection()
        
        try:
            positions = self.api.list_positions()
            position_list = []
            
            for pos in positions:
                position_data = {
                    'symbol': pos.symbol,
                    'qty': float(pos.qty),
                    'side': 'long' if float(pos.qty) > 0 else 'short',
                    'market_value': float(pos.market_value),
                    'cost_basis': float(pos.cost_basis),
                    'unrealized_pl': float(pos.unrealized_pl),
                    'unrealized_plpc': float(pos.unrealized_plpc),
                    'avg_entry_price': float(pos.avg_entry_price),
                    'current_price': float(pos.current_price) if pos.current_price else None,
                    'lastday_price': float(pos.lastday_price) if pos.lastday_price else None,
                    'change_today': float(pos.change_today) if pos.change_today else None
                }
                position_list.append(position_data)
            
            return position_list
            
        except APIError as e:
            logger.error(f"Error getting positions: {e}")
            raise
    
    async def place_order(self, 
                         symbol: str,
                         qty: Union[int, float],
                         side: str,
                         order_type: str = 'market',
                         time_in_force: str = 'day',
                         limit_price: Optional[float] = None,
                         stop_price: Optional[float] = None,
                         trail_price: Optional[float] = None,
                         trail_percent: Optional[float] = None,
                         extended_hours: bool = False,
                         client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """Place an order"""
        self._validate_connection()
        
        try:
            # Validate parameters
            if side not in ['buy', 'sell']:
                raise ValueError("Side must be 'buy' or 'sell'")
            
            if order_type not in ['market', 'limit', 'stop', 'stop_limit', 'trailing_stop']:
                raise ValueError("Invalid order type")
            
            # Build order parameters
            order_params = {
                'symbol': symbol.upper(),
                'qty': abs(qty),
                'side': side,
                'type': order_type,
                'time_in_force': time_in_force,
                'extended_hours': extended_hours
            }
            
            # Add price parameters based on order type
            if order_type == 'limit' and limit_price:
                order_params['limit_price'] = limit_price
            elif order_type == 'stop' and stop_price:
                order_params['stop_price'] = stop_price
            elif order_type == 'stop_limit' and limit_price and stop_price:
                order_params['limit_price'] = limit_price
                order_params['stop_price'] = stop_price
            elif order_type == 'trailing_stop':
                if trail_price:
                    order_params['trail_price'] = trail_price
                elif trail_percent:
                    order_params['trail_percent'] = trail_percent
                else:
                    raise ValueError("Trailing stop orders require trail_price or trail_percent")
            
            if client_order_id:
                order_params['client_order_id'] = client_order_id
            
            # Place the order
            order = self.api.submit_order(**order_params)
            
            # Convert to dict
            order_data = {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'asset_id': order.asset_id,
                'asset_class': order.asset_class,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty),
                'side': order.side,
                'order_type': order.order_type,
                'time_in_force': order.time_in_force,
                'limit_price': float(order.limit_price) if order.limit_price else None,
                'stop_price': float(order.stop_price) if order.stop_price else None,
                'trail_price': float(order.trail_price) if order.trail_price else None,
                'trail_percent': float(order.trail_percent) if order.trail_percent else None,
                'status': order.status,
                'extended_hours': order.extended_hours,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'updated_at': order.updated_at.isoformat() if order.updated_at else None,
                'submitted_at': order.submitted_at.isoformat() if order.submitted_at else None,
                'filled_at': order.filled_at.isoformat() if order.filled_at else None,
                'expired_at': order.expired_at.isoformat() if order.expired_at else None,
                'canceled_at': order.canceled_at.isoformat() if order.canceled_at else None,
                'failed_at': order.failed_at.isoformat() if order.failed_at else None,
                'replaced_at': order.replaced_at.isoformat() if order.replaced_at else None,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None,
                'hwm': float(order.hwm) if order.hwm else None,
                'legs': order.legs
            }
            
            # Save to database
            db_client = await get_mongodb_client()
            await db_client.save_trade({
                'order_id': order.id,
                'symbol': symbol,
                'side': side,
                'qty': float(qty),
                'order_type': order_type,
                'status': order.status,
                'broker': 'alpaca',
                'order_data': order_data
            })
            
            logger.info(f"Order placed: {order.id} - {side} {qty} {symbol} @ {order_type}")
            return order_data
            
        except APIError as e:
            logger.error(f"Error placing order: {e}")
            raise
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        self._validate_connection()
        
        try:
            self.api.cancel_order(order_id)
            logger.info(f"Order canceled: {order_id}")
            return True
            
        except APIError as e:
            logger.error(f"Error canceling order {order_id}: {e}")
            return False
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        self._validate_connection()
        
        try:
            order = self.api.get_order(order_id)
            
            return {
                'id': order.id,
                'client_order_id': order.client_order_id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'filled_qty': float(order.filled_qty),
                'side': order.side,
                'order_type': order.order_type,
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
            }
            
        except APIError as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    async def get_orders(self, 
                        status: Optional[str] = None,
                        limit: int = 50,
                        after: Optional[datetime] = None,
                        until: Optional[datetime] = None,
                        direction: str = 'desc',
                        nested: bool = True,
                        symbols: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get orders with filters"""
        self._validate_connection()
        
        try:
            orders = self.api.list_orders(
                status=status,
                limit=limit,
                after=after,
                until=until,
                direction=direction,
                nested=nested,
                symbols=symbols
            )
            
            order_list = []
            for order in orders:
                order_data = {
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty),
                    'filled_qty': float(order.filled_qty),
                    'side': order.side,
                    'order_type': order.order_type,
                    'status': order.status,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'filled_avg_price': float(order.filled_avg_price) if order.filled_avg_price else None
                }
                order_list.append(order_data)
            
            return order_list
            
        except APIError as e:
            logger.error(f"Error getting orders: {e}")
            raise
    
    async def get_market_data(self, 
                             symbol: str,
                             timeframe: str = '1Day',
                             start: Optional[datetime] = None,
                             end: Optional[datetime] = None,
                             limit: int = 1000) -> List[Dict[str, Any]]:
        """Get market data for symbol"""
        self._validate_connection()
        
        try:
            # Convert timeframe to Alpaca format
            alpaca_timeframe = self._convert_timeframe(timeframe)
            
            # Get bars
            bars = self.api.get_bars(
                symbol,
                alpaca_timeframe,
                start=start,
                end=end,
                limit=limit
            ).df
            
            # Convert to list of dicts
            market_data = []
            for index, row in bars.iterrows():
                data_point = {
                    'symbol': symbol,
                    'timestamp': index.to_pydatetime(),
                    'timeframe': timeframe,
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']),
                    'trade_count': int(row.get('trade_count', 0)),
                    'vwap': float(row.get('vwap', 0))
                }
                market_data.append(data_point)
            
            return market_data
            
        except APIError as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            raise
    
    def _convert_timeframe(self, timeframe: str) -> str:
        """Convert timeframe to Alpaca format"""
        timeframe_map = {
            '1m': '1Min',
            '5m': '5Min',
            '15m': '15Min',
            '30m': '30Min',
            '1h': '1Hour',
            '1d': '1Day',
            '1w': '1Week',
            '1M': '1Month'
        }
        return timeframe_map.get(timeframe, '1Day')
    
    async def get_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get asset information"""
        self._validate_connection()
        
        try:
            asset = self.api.get_asset(symbol)
            
            return {
                'id': asset.id,
                'symbol': asset.symbol,
                'name': asset.name,
                'exchange': asset.exchange,
                'asset_class': asset.asset_class,
                'status': asset.status,
                'tradable': asset.tradable,
                'marginable': asset.marginable,
                'shortable': asset.shortable,
                'easy_to_borrow': asset.easy_to_borrow,
                'fractionable': asset.fractionable
            }
            
        except APIError as e:
            logger.error(f"Error getting asset info for {symbol}: {e}")
            return None
    
    async def get_portfolio_history(self, 
                                   period: str = '1M',
                                   timeframe: str = '1D',
                                   extended_hours: bool = False) -> Dict[str, Any]:
        """Get portfolio history"""
        self._validate_connection()
        
        try:
            history = self.api.get_portfolio_history(
                period=period,
                timeframe=timeframe,
                extended_hours=extended_hours
            )
            
            return {
                'timestamp': [ts.isoformat() for ts in history.timestamp],
                'equity': [float(eq) for eq in history.equity],
                'profit_loss': [float(pl) for pl in history.profit_loss],
                'profit_loss_pct': [float(plp) for plp in history.profit_loss_pct],
                'base_value': float(history.base_value),
                'timeframe': history.timeframe
            }
            
        except APIError as e:
            logger.error(f"Error getting portfolio history: {e}")
            raise
    
    async def close_position(self, symbol: str, qty: Optional[float] = None) -> Dict[str, Any]:
        """Close position (partial or full)"""
        self._validate_connection()
        
        try:
            if qty:
                # Close partial position
                order = self.api.close_position(symbol, qty=qty)
            else:
                # Close full position
                order = self.api.close_position(symbol)
            
            logger.info(f"Position closed: {symbol} - {qty if qty else 'full'}")
            
            return {
                'id': order.id,
                'symbol': order.symbol,
                'qty': float(order.qty),
                'side': order.side,
                'status': order.status
            }
            
        except APIError as e:
            logger.error(f"Error closing position {symbol}: {e}")
            raise
    
    async def close_all_positions(self) -> List[Dict[str, Any]]:
        """Close all positions"""
        self._validate_connection()
        
        try:
            orders = self.api.close_all_positions()
            
            closed_orders = []
            for order in orders:
                order_data = {
                    'id': order.id,
                    'symbol': order.symbol,
                    'qty': float(order.qty),
                    'side': order.side,
                    'status': order.status
                }
                closed_orders.append(order_data)
            
            logger.info(f"All positions closed: {len(closed_orders)} orders")
            return closed_orders
            
        except APIError as e:
            logger.error(f"Error closing all positions: {e}")
            raise
    
    async def get_clock(self) -> Dict[str, Any]:
        """Get market clock"""
        self._validate_connection()
        
        try:
            clock = self.api.get_clock()
            
            return {
                'timestamp': clock.timestamp.isoformat(),
                'is_open': clock.is_open,
                'next_open': clock.next_open.isoformat(),
                'next_close': clock.next_close.isoformat()
            }
            
        except APIError as e:
            logger.error(f"Error getting market clock: {e}")
            raise
    
    async def get_calendar(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get market calendar"""
        self._validate_connection()
        
        try:
            calendar = self.api.get_calendar(start=start, end=end)
            
            calendar_data = []
            for day in calendar:
                day_data = {
                    'date': day.date.isoformat(),
                    'open': day.open.isoformat(),
                    'close': day.close.isoformat()
                }
                calendar_data.append(day_data)
            
            return calendar_data
            
        except APIError as e:
            logger.error(f"Error getting market calendar: {e}")
            raise