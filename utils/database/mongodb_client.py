"""
MongoDB Client for AI Trading System
Provides async connection and operations for MongoDB database
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging

logger = logging.getLogger(__name__)

class MongoDBClient:
    """Async MongoDB client for trading system"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.connected = False
        
        # Connection parameters from environment
        self.mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/trading_db')
        self.database_name = os.getenv('MONGODB_DATABASE', 'trading_db')
        self.username = os.getenv('MONGODB_USERNAME')
        self.password = os.getenv('MONGODB_PASSWORD')
    
    async def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            # Create client with authentication if credentials provided
            if self.username and self.password:
                auth_url = f"mongodb://{self.username}:{self.password}@{self.mongodb_url.split('://', 1)[1]}"
                self.client = AsyncIOMotorClient(auth_url)
            else:
                self.client = AsyncIOMotorClient(self.mongodb_url)
            
            # Get database
            self.database = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            self.connected = True
            logger.info(f"Connected to MongoDB: {self.database_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from MongoDB")
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get collection by name"""
        if not self.connected or not self.database:
            raise ConnectionError("Not connected to MongoDB")
        return self.database[collection_name]
    
    # Trading-specific methods
    async def save_trade(self, trade_data: Dict[str, Any]) -> str:
        """Save trade to database"""
        collection = self.get_collection('trades')
        trade_data['timestamp'] = datetime.utcnow()
        result = await collection.insert_one(trade_data)
        return str(result.inserted_id)
    
    async def get_trades(self, 
                        symbol: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get trades with optional filters"""
        collection = self.get_collection('trades')
        
        # Build query
        query = {}
        if symbol:
            query['symbol'] = symbol
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        cursor = collection.find(query).sort('timestamp', -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def save_position(self, position_data: Dict[str, Any]) -> str:
        """Save position to database"""
        collection = self.get_collection('positions')
        position_data['updated_at'] = datetime.utcnow()
        
        # Upsert based on symbol and strategy
        filter_query = {
            'symbol': position_data['symbol'],
            'strategy_id': position_data.get('strategy_id')
        }
        
        result = await collection.replace_one(
            filter_query, 
            position_data, 
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else "updated"
    
    async def get_positions(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get current positions"""
        collection = self.get_collection('positions')
        
        query = {}
        if active_only:
            query['status'] = 'active'
        
        cursor = collection.find(query)
        return await cursor.to_list(length=None)
    
    async def save_market_data(self, market_data: List[Dict[str, Any]]) -> int:
        """Save market data batch"""
        collection = self.get_collection('market_data')
        
        # Add timestamp to each record
        for data in market_data:
            if 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow()
        
        result = await collection.insert_many(market_data)
        return len(result.inserted_ids)
    
    async def get_market_data(self,
                             symbol: str,
                             timeframe: str = '1h',
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             limit: int = 1000) -> List[Dict[str, Any]]:
        """Get market data for symbol"""
        collection = self.get_collection('market_data')
        
        query = {
            'symbol': symbol,
            'timeframe': timeframe
        }
        
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        cursor = collection.find(query).sort('timestamp', 1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def save_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """Save strategy configuration"""
        collection = self.get_collection('strategies')
        strategy_data['created_at'] = datetime.utcnow()
        result = await collection.insert_one(strategy_data)
        return str(result.inserted_id)
    
    async def get_strategies(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get strategies"""
        collection = self.get_collection('strategies')
        
        query = {}
        if active_only:
            query['status'] = 'active'
        
        cursor = collection.find(query)
        return await cursor.to_list(length=None)
    
    async def save_backtest_result(self, backtest_data: Dict[str, Any]) -> str:
        """Save backtest results"""
        collection = self.get_collection('backtests')
        backtest_data['created_at'] = datetime.utcnow()
        result = await collection.insert_one(backtest_data)
        return str(result.inserted_id)
    
    async def get_backtest_results(self, strategy_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get backtest results"""
        collection = self.get_collection('backtests')
        
        query = {}
        if strategy_id:
            query['strategy_id'] = strategy_id
        
        cursor = collection.find(query).sort('created_at', -1)
        return await cursor.to_list(length=None)
    
    async def save_agent_state(self, agent_data: Dict[str, Any]) -> str:
        """Save agent state"""
        collection = self.get_collection('agents')
        agent_data['last_update'] = datetime.utcnow()
        
        # Upsert based on agent_id
        filter_query = {'agent_id': agent_data['agent_id']}
        result = await collection.replace_one(
            filter_query,
            agent_data,
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else "updated"
    
    async def get_agent_states(self) -> List[Dict[str, Any]]:
        """Get all agent states"""
        collection = self.get_collection('agents')
        cursor = collection.find({})
        return await cursor.to_list(length=None)
    
    async def save_risk_metrics(self, risk_data: Dict[str, Any]) -> str:
        """Save risk metrics"""
        collection = self.get_collection('risk_metrics')
        risk_data['timestamp'] = datetime.utcnow()
        result = await collection.insert_one(risk_data)
        return str(result.inserted_id)
    
    async def get_latest_risk_metrics(self) -> Optional[Dict[str, Any]]:
        """Get latest risk metrics"""
        collection = self.get_collection('risk_metrics')
        result = await collection.find_one({}, sort=[('timestamp', -1)])
        return result
    
    async def save_portfolio_snapshot(self, portfolio_data: Dict[str, Any]) -> str:
        """Save portfolio snapshot"""
        collection = self.get_collection('portfolio')
        portfolio_data['timestamp'] = datetime.utcnow()
        result = await collection.insert_one(portfolio_data)
        return str(result.inserted_id)
    
    async def get_portfolio_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get portfolio history"""
        collection = self.get_collection('portfolio')
        
        start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date.replace(day=start_date.day - days)
        
        query = {'timestamp': {'$gte': start_date}}
        cursor = collection.find(query).sort('timestamp', 1)
        return await cursor.to_list(length=None)
    
    async def save_alert(self, alert_data: Dict[str, Any]) -> str:
        """Save alert"""
        collection = self.get_collection('alerts')
        alert_data['timestamp'] = datetime.utcnow()
        result = await collection.insert_one(alert_data)
        return str(result.inserted_id)
    
    async def get_alerts(self, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Get alerts"""
        collection = self.get_collection('alerts')
        
        query = {}
        if unread_only:
            query['status'] = 'unread'
        
        cursor = collection.find(query).sort('timestamp', -1)
        return await cursor.to_list(length=100)
    
    async def save_ml_model(self, model_data: Dict[str, Any]) -> str:
        """Save ML model metadata"""
        collection = self.get_collection('ml_models')
        model_data['created_at'] = datetime.utcnow()
        result = await collection.insert_one(model_data)
        return str(result.inserted_id)
    
    async def get_ml_models(self, model_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get ML models"""
        collection = self.get_collection('ml_models')
        
        query = {}
        if model_type:
            query['model_type'] = model_type
        
        cursor = collection.find(query).sort('created_at', -1)
        return await cursor.to_list(length=None)

# Global instance
mongodb_client = MongoDBClient()

async def get_mongodb_client() -> MongoDBClient:
    """Get MongoDB client instance"""
    if not mongodb_client.connected:
        await mongodb_client.connect()
    return mongodb_client