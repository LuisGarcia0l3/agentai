// MongoDB initialization script for AI Trading System
// This script creates the necessary collections and indexes

// Switch to trading database
db = db.getSiblingDB('trading_db');

// Create collections
db.createCollection('trades');
db.createCollection('positions');
db.createCollection('market_data');
db.createCollection('strategies');
db.createCollection('backtests');
db.createCollection('agents');
db.createCollection('risk_metrics');
db.createCollection('portfolio');
db.createCollection('alerts');
db.createCollection('ml_models');

// Create indexes for better performance

// Trades collection indexes
db.trades.createIndex({ "timestamp": 1 });
db.trades.createIndex({ "symbol": 1, "timestamp": 1 });
db.trades.createIndex({ "strategy_id": 1 });
db.trades.createIndex({ "agent_id": 1 });

// Positions collection indexes
db.positions.createIndex({ "symbol": 1 });
db.positions.createIndex({ "status": 1 });
db.positions.createIndex({ "created_at": 1 });

// Market data collection indexes
db.market_data.createIndex({ "symbol": 1, "timestamp": 1 });
db.market_data.createIndex({ "timestamp": 1 });
db.market_data.createIndex({ "timeframe": 1 });

// Strategies collection indexes
db.strategies.createIndex({ "name": 1 });
db.strategies.createIndex({ "status": 1 });
db.strategies.createIndex({ "created_at": 1 });

// Backtests collection indexes
db.backtests.createIndex({ "strategy_id": 1 });
db.backtests.createIndex({ "created_at": 1 });
db.backtests.createIndex({ "status": 1 });

// Agents collection indexes
db.agents.createIndex({ "agent_type": 1 });
db.agents.createIndex({ "status": 1 });
db.agents.createIndex({ "last_update": 1 });

// Risk metrics collection indexes
db.risk_metrics.createIndex({ "timestamp": 1 });
db.risk_metrics.createIndex({ "metric_type": 1 });

// Portfolio collection indexes
db.portfolio.createIndex({ "timestamp": 1 });
db.portfolio.createIndex({ "account_id": 1 });

// Alerts collection indexes
db.alerts.createIndex({ "timestamp": 1 });
db.alerts.createIndex({ "alert_type": 1 });
db.alerts.createIndex({ "status": 1 });

// ML models collection indexes
db.ml_models.createIndex({ "model_type": 1 });
db.ml_models.createIndex({ "created_at": 1 });
db.ml_models.createIndex({ "status": 1 });

print("MongoDB initialization completed successfully!");
print("Created collections: trades, positions, market_data, strategies, backtests, agents, risk_metrics, portfolio, alerts, ml_models");
print("Created indexes for optimal query performance");