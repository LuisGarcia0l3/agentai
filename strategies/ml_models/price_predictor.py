"""
Machine Learning Price Prediction Models
Implements various ML models for price prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import joblib
import os

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb

# Deep learning imports
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available - LSTM models disabled")

from ...utils.database import get_mongodb_client

logger = logging.getLogger(__name__)

class TechnicalIndicators:
    """Calculate technical indicators for feature engineering"""
    
    @staticmethod
    def sma(data: pd.Series, window: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=window).mean()
    
    @staticmethod
    def ema(data: pd.Series, window: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=window).mean()
    
    @staticmethod
    def rsi(data: pd.Series, window: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD Indicator"""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(data: pd.Series, window: int = 20, num_std: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        
        return {
            'upper': sma + (std * num_std),
            'middle': sma,
            'lower': sma - (std * num_std)
        }
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_window: int = 14, d_window: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_window).min()
        highest_high = high.rolling(window=k_window).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }

class LSTMModel(nn.Module):
    """LSTM Neural Network for price prediction"""
    
    def __init__(self, input_size: int, hidden_size: int = 50, num_layers: int = 2, dropout: float = 0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_size, 1)
        
    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(x.device)
        
        # LSTM forward pass
        out, _ = self.lstm(x, (h0, c0))
        
        # Take the last output
        out = self.dropout(out[:, -1, :])
        out = self.fc(out)
        
        return out

class PricePredictor:
    """Main price prediction class with multiple ML models"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.models = {}
        self.scalers = {}
        self.feature_columns = []
        self.model_performance = {}
        
        # Model configurations
        self.model_configs = {
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': 42
            },
            'xgboost': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42
            },
            'lightgbm': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 100,
                'max_depth': 6,
                'learning_rate': 0.1,
                'random_state': 42
            }
        }
        
        self.sequence_length = 60  # For LSTM
        self.prediction_horizon = 1  # Predict 1 step ahead
        
    async def prepare_data(self, days_back: int = 365) -> pd.DataFrame:
        """Prepare and engineer features from market data"""
        
        # Get market data from database
        db_client = await get_mongodb_client()
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        market_data = await db_client.get_market_data(
            symbol=self.symbol,
            start_date=start_date,
            end_date=end_date,
            limit=days_back * 24  # Assuming hourly data
        )
        
        if len(market_data) < 100:
            raise ValueError(f"Insufficient data for {self.symbol}: {len(market_data)} records")
        
        # Convert to DataFrame
        df = pd.DataFrame(market_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate technical indicators
        df = self._engineer_features(df)
        
        # Remove NaN values
        df = df.dropna().reset_index(drop=True)
        
        logger.info(f"Prepared {len(df)} data points for {self.symbol}")
        return df
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer technical features"""
        
        # Price-based features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['price_change'] = df['close'] - df['open']
        df['high_low_pct'] = (df['high'] - df['low']) / df['close']
        df['volume_change'] = df['volume'].pct_change()
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            df[f'sma_{window}'] = TechnicalIndicators.sma(df['close'], window)
            df[f'ema_{window}'] = TechnicalIndicators.ema(df['close'], window)
            df[f'price_sma_{window}_ratio'] = df['close'] / df[f'sma_{window}']
        
        # RSI
        df['rsi'] = TechnicalIndicators.rsi(df['close'])
        df['rsi_oversold'] = (df['rsi'] < 30).astype(int)
        df['rsi_overbought'] = (df['rsi'] > 70).astype(int)
        
        # MACD
        macd_data = TechnicalIndicators.macd(df['close'])
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        df['macd_bullish'] = (df['macd'] > df['macd_signal']).astype(int)
        
        # Bollinger Bands
        bb_data = TechnicalIndicators.bollinger_bands(df['close'])
        df['bb_upper'] = bb_data['upper']
        df['bb_middle'] = bb_data['middle']
        df['bb_lower'] = bb_data['lower']
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Stochastic
        stoch_data = TechnicalIndicators.stochastic(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch_data['k']
        df['stoch_d'] = stoch_data['d']
        
        # Volatility features
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['volatility_ratio'] = df['volatility'] / df['volatility'].rolling(window=50).mean()
        
        # Volume features
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Lag features
        for lag in [1, 2, 3, 5]:
            df[f'close_lag_{lag}'] = df['close'].shift(lag)
            df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
            df[f'volume_lag_{lag}'] = df['volume'].shift(lag)
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        # Target variable (next period close price)
        df['target'] = df['close'].shift(-self.prediction_horizon)
        df['target_returns'] = df['target'].pct_change()
        
        return df
    
    def _prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target for training"""
        
        # Select feature columns (exclude non-feature columns)
        exclude_cols = ['timestamp', 'symbol', 'target', 'target_returns', 'open', 'high', 'low', 'close', 'volume']
        self.feature_columns = [col for col in df.columns if col not in exclude_cols]
        
        # Prepare features and target
        X = df[self.feature_columns].values
        y = df['target'].values
        
        # Remove rows with NaN values
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        logger.info(f"Prepared features: {X.shape}, Target: {y.shape}")
        logger.info(f"Feature columns: {len(self.feature_columns)}")
        
        return X, y
    
    async def train_models(self, test_size: float = 0.2) -> Dict[str, Any]:
        """Train multiple ML models"""
        
        # Prepare data
        df = await self.prepare_data()
        X, y = self._prepare_features(df)
        
        if len(X) < 100:
            raise ValueError(f"Insufficient data for training: {len(X)} samples")
        
        # Split data (time series split)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['features'] = scaler
        
        # Scale target
        target_scaler = StandardScaler()
        y_train_scaled = target_scaler.fit_transform(y_train.reshape(-1, 1)).ravel()
        y_test_scaled = target_scaler.transform(y_test.reshape(-1, 1)).ravel()
        self.scalers['target'] = target_scaler
        
        results = {}
        
        # Train traditional ML models
        ml_models = {
            'random_forest': RandomForestRegressor(**self.model_configs['random_forest']),
            'xgboost': xgb.XGBRegressor(**self.model_configs['xgboost']),
            'lightgbm': lgb.LGBMRegressor(**self.model_configs['lightgbm']),
            'gradient_boosting': GradientBoostingRegressor(**self.model_configs['gradient_boosting']),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(alpha=1.0)
        }
        
        for name, model in ml_models.items():
            try:
                logger.info(f"Training {name} model...")
                
                # Train model
                model.fit(X_train_scaled, y_train_scaled)
                
                # Make predictions
                y_pred_train = model.predict(X_train_scaled)
                y_pred_test = model.predict(X_test_scaled)
                
                # Inverse transform predictions
                y_pred_train_orig = target_scaler.inverse_transform(y_pred_train.reshape(-1, 1)).ravel()
                y_pred_test_orig = target_scaler.inverse_transform(y_pred_test.reshape(-1, 1)).ravel()
                
                # Calculate metrics
                train_metrics = self._calculate_metrics(y_train, y_pred_train_orig)
                test_metrics = self._calculate_metrics(y_test, y_pred_test_orig)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train_scaled, y_train_scaled, cv=5, scoring='neg_mean_squared_error')
                
                # Store model and results
                self.models[name] = model
                results[name] = {
                    'train_metrics': train_metrics,
                    'test_metrics': test_metrics,
                    'cv_score_mean': -cv_scores.mean(),
                    'cv_score_std': cv_scores.std(),
                    'feature_importance': self._get_feature_importance(model, name)
                }
                
                logger.info(f"{name} - Test RMSE: {test_metrics['rmse']:.4f}, R²: {test_metrics['r2']:.4f}")
                
            except Exception as e:
                logger.error(f"Error training {name}: {e}")
                results[name] = {'error': str(e)}
        
        # Train LSTM model if PyTorch is available
        if TORCH_AVAILABLE:
            try:
                lstm_results = await self._train_lstm_model(df, test_size)
                results['lstm'] = lstm_results
            except Exception as e:
                logger.error(f"Error training LSTM: {e}")
                results['lstm'] = {'error': str(e)}
        
        # Store performance metrics
        self.model_performance = results
        
        # Save models
        await self._save_models()
        
        logger.info(f"Training completed for {len(results)} models")
        return results
    
    async def _train_lstm_model(self, df: pd.DataFrame, test_size: float) -> Dict[str, Any]:
        """Train LSTM model"""
        
        # Prepare sequence data for LSTM
        X_seq, y_seq = self._prepare_sequence_data(df)
        
        # Split data
        split_idx = int(len(X_seq) * (1 - test_size))
        X_train, X_test = X_seq[:split_idx], X_seq[split_idx:]
        y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train)
        y_train_tensor = torch.FloatTensor(y_train)
        X_test_tensor = torch.FloatTensor(X_test)
        y_test_tensor = torch.FloatTensor(y_test)
        
        # Create data loaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=32, shuffle=False)
        
        # Initialize model
        input_size = X_train.shape[2]
        model = LSTMModel(input_size=input_size)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=0.001)
        
        # Training loop
        model.train()
        epochs = 50
        train_losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs.squeeze(), batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(train_loader)
            train_losses.append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"LSTM Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
        
        # Evaluation
        model.eval()
        with torch.no_grad():
            y_pred_train = model(X_train_tensor).squeeze().numpy()
            y_pred_test = model(X_test_tensor).squeeze().numpy()
        
        # Calculate metrics
        train_metrics = self._calculate_metrics(y_train, y_pred_train)
        test_metrics = self._calculate_metrics(y_test, y_pred_test)
        
        # Store LSTM model
        self.models['lstm'] = model
        
        return {
            'train_metrics': train_metrics,
            'test_metrics': test_metrics,
            'train_losses': train_losses,
            'epochs': epochs
        }
    
    def _prepare_sequence_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequence data for LSTM"""
        
        # Use only numeric columns for LSTM
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        exclude_cols = ['target', 'target_returns']
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        data = df[feature_cols + ['target']].dropna()
        
        # Normalize data
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data)
        self.scalers['lstm'] = scaler
        
        # Create sequences
        X, y = [], []
        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i-self.sequence_length:i, :-1])  # All features except target
            y.append(scaled_data[i, -1])  # Target
        
        return np.array(X), np.array(y)
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate regression metrics"""
        
        # Remove NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true_clean = y_true[mask]
        y_pred_clean = y_pred[mask]
        
        if len(y_true_clean) == 0:
            return {'rmse': float('inf'), 'mae': float('inf'), 'r2': -float('inf')}
        
        rmse = np.sqrt(mean_squared_error(y_true_clean, y_pred_clean))
        mae = mean_absolute_error(y_true_clean, y_pred_clean)
        r2 = r2_score(y_true_clean, y_pred_clean)
        
        # Calculate directional accuracy
        y_true_direction = np.diff(y_true_clean) > 0
        y_pred_direction = np.diff(y_pred_clean) > 0
        directional_accuracy = np.mean(y_true_direction == y_pred_direction) if len(y_true_direction) > 0 else 0
        
        return {
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'directional_accuracy': directional_accuracy
        }
    
    def _get_feature_importance(self, model, model_name: str) -> Optional[Dict[str, float]]:
        """Get feature importance from model"""
        
        try:
            if hasattr(model, 'feature_importances_'):
                importance = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importance = np.abs(model.coef_)
            else:
                return None
            
            # Create importance dictionary
            feature_importance = dict(zip(self.feature_columns, importance))
            
            # Sort by importance
            sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            return sorted_importance
            
        except Exception as e:
            logger.error(f"Error getting feature importance for {model_name}: {e}")
            return None
    
    async def predict(self, model_name: str = 'best') -> Dict[str, Any]:
        """Make price prediction"""
        
        if not self.models:
            raise ValueError("No trained models available. Train models first.")
        
        # Get latest data
        df = await self.prepare_data(days_back=100)  # Get recent data
        
        if model_name == 'best':
            # Select best performing model
            model_name = self._select_best_model()
        
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        model = self.models[model_name]
        
        # Prepare features
        if model_name == 'lstm':
            prediction = await self._predict_lstm(df)
        else:
            # Traditional ML prediction
            X, _ = self._prepare_features(df)
            X_scaled = self.scalers['features'].transform(X[-1:])  # Latest data point
            
            # Make prediction
            y_pred_scaled = model.predict(X_scaled)
            prediction = self.scalers['target'].inverse_transform(y_pred_scaled.reshape(-1, 1))[0, 0]
        
        # Get current price for comparison
        current_price = df['close'].iloc[-1]
        predicted_change = (prediction - current_price) / current_price
        
        return {
            'symbol': self.symbol,
            'model_used': model_name,
            'current_price': current_price,
            'predicted_price': prediction,
            'predicted_change_pct': predicted_change * 100,
            'prediction_timestamp': datetime.utcnow(),
            'confidence': self._calculate_prediction_confidence(model_name)
        }
    
    async def _predict_lstm(self, df: pd.DataFrame) -> float:
        """Make LSTM prediction"""
        
        X_seq, _ = self._prepare_sequence_data(df)
        
        if len(X_seq) == 0:
            raise ValueError("Insufficient data for LSTM prediction")
        
        # Use latest sequence
        X_latest = torch.FloatTensor(X_seq[-1:])
        
        model = self.models['lstm']
        model.eval()
        
        with torch.no_grad():
            prediction_scaled = model(X_latest).item()
        
        # Inverse transform
        # Create dummy array for inverse transform
        dummy_data = np.zeros((1, len(self.scalers['lstm'].feature_names_in_)))
        dummy_data[0, -1] = prediction_scaled
        prediction = self.scalers['lstm'].inverse_transform(dummy_data)[0, -1]
        
        return prediction
    
    def _select_best_model(self) -> str:
        """Select best performing model based on test metrics"""
        
        if not self.model_performance:
            return list(self.models.keys())[0]
        
        best_model = None
        best_score = float('inf')
        
        for model_name, performance in self.model_performance.items():
            if 'test_metrics' in performance:
                # Use RMSE as primary metric (lower is better)
                score = performance['test_metrics']['rmse']
                if score < best_score:
                    best_score = score
                    best_model = model_name
        
        return best_model or list(self.models.keys())[0]
    
    def _calculate_prediction_confidence(self, model_name: str) -> float:
        """Calculate prediction confidence based on model performance"""
        
        if model_name not in self.model_performance:
            return 0.5
        
        performance = self.model_performance[model_name]
        
        if 'test_metrics' not in performance:
            return 0.5
        
        # Use R² score as confidence measure
        r2 = performance['test_metrics']['r2']
        confidence = max(0.0, min(1.0, r2))  # Clamp between 0 and 1
        
        return confidence
    
    async def _save_models(self):
        """Save trained models to database and disk"""
        
        try:
            # Create models directory
            models_dir = f"/root/agentai/models/{self.symbol}"
            os.makedirs(models_dir, exist_ok=True)
            
            # Save traditional ML models
            for name, model in self.models.items():
                if name != 'lstm':
                    model_path = os.path.join(models_dir, f"{name}.joblib")
                    joblib.dump(model, model_path)
                else:
                    # Save LSTM model
                    model_path = os.path.join(models_dir, f"{name}.pth")
                    torch.save(model.state_dict(), model_path)
            
            # Save scalers
            scalers_path = os.path.join(models_dir, "scalers.joblib")
            joblib.dump(self.scalers, scalers_path)
            
            # Save to database
            db_client = await get_mongodb_client()
            model_metadata = {
                'symbol': self.symbol,
                'model_type': 'price_predictor',
                'models': list(self.models.keys()),
                'feature_columns': self.feature_columns,
                'performance': self.model_performance,
                'model_path': models_dir,
                'created_at': datetime.utcnow()
            }
            
            await db_client.save_ml_model(model_metadata)
            
            logger.info(f"Models saved for {self.symbol}")
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    async def load_models(self):
        """Load trained models from disk"""
        
        try:
            models_dir = f"/root/agentai/models/{self.symbol}"
            
            if not os.path.exists(models_dir):
                logger.warning(f"No saved models found for {self.symbol}")
                return False
            
            # Load scalers
            scalers_path = os.path.join(models_dir, "scalers.joblib")
            if os.path.exists(scalers_path):
                self.scalers = joblib.load(scalers_path)
            
            # Load traditional ML models
            for model_file in os.listdir(models_dir):
                if model_file.endswith('.joblib') and model_file != 'scalers.joblib':
                    model_name = model_file.replace('.joblib', '')
                    model_path = os.path.join(models_dir, model_file)
                    self.models[model_name] = joblib.load(model_path)
                
                elif model_file.endswith('.pth') and TORCH_AVAILABLE:
                    # Load LSTM model
                    model_name = model_file.replace('.pth', '')
                    model_path = os.path.join(models_dir, model_file)
                    
                    # Need to recreate model architecture
                    # This is simplified - in practice, save architecture info
                    input_size = len(self.feature_columns) if self.feature_columns else 10
                    model = LSTMModel(input_size=input_size)
                    model.load_state_dict(torch.load(model_path))
                    model.eval()
                    self.models[model_name] = model
            
            logger.info(f"Loaded {len(self.models)} models for {self.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False
    
    async def get_model_summary(self) -> Dict[str, Any]:
        """Get summary of trained models"""
        
        return {
            'symbol': self.symbol,
            'models_trained': list(self.models.keys()),
            'feature_count': len(self.feature_columns),
            'performance': self.model_performance,
            'best_model': self._select_best_model() if self.models else None,
            'last_updated': datetime.utcnow()
        }

# Factory function
async def create_price_predictor(symbol: str) -> PricePredictor:
    """Create and optionally load existing price predictor"""
    predictor = PricePredictor(symbol)
    
    # Try to load existing models
    await predictor.load_models()
    
    return predictor