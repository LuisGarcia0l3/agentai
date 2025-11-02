"""
Base Broker Interface for AI Trading System
Defines the common interface for all broker implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

class BaseBroker(ABC):
    """Abstract base class for all broker implementations"""
    
    def __init__(self):
        self.connected = False
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the broker API"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the broker API"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get current positions"""
        pass
    
    @abstractmethod
    async def place_order(self, 
                         symbol: str,
                         qty: Union[int, float],
                         side: str,
                         order_type: str = 'market',
                         **kwargs) -> Dict[str, Any]:
        """Place an order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    async def get_orders(self, **kwargs) -> List[Dict[str, Any]]:
        """Get orders with filters"""
        pass
    
    @abstractmethod
    async def get_market_data(self, 
                             symbol: str,
                             timeframe: str = '1h',
                             **kwargs) -> List[Dict[str, Any]]:
        """Get market data for symbol"""
        pass
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self.connected
    
    def get_name(self) -> str:
        """Get broker name"""
        return self.name