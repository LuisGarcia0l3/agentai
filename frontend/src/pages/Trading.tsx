import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import TradingPanel from '../components/TradingPanel';
import MarketAnalysis from '../components/MarketAnalysis';
import StrategyConfig from '../components/StrategyConfig';

interface TradeOrder {
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  orderType: 'market' | 'limit' | 'stop';
  limitPrice?: number;
  stopPrice?: number;
}

interface TradingStrategy {
  id: string;
  name: string;
  type: 'scalping' | 'swing' | 'position';
  symbols: string[];
  riskManagement: {
    maxPositionSize: number;
    stopLoss: number;
    takeProfit: number;
    maxDailyLoss: number;
  };
  technicalIndicators: {
    rsi: { enabled: boolean; period: number; overbought: number; oversold: number };
    macd: { enabled: boolean; fast: number; slow: number; signal: number };
    bollinger: { enabled: boolean; period: number; stdDev: number };
    sma: { enabled: boolean; periods: number[] };
  };
  mlModel: {
    enabled: boolean;
    model: 'random_forest' | 'xgboost' | 'lstm' | 'ensemble';
    confidence: number;
  };
  isActive: boolean;
}

const Trading: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [currentPrice] = useState(152.30);
  const [activeTab, setActiveTab] = useState<'trading' | 'analysis' | 'strategy'>('trading');

  const handleTrade = async (trade: TradeOrder) => {
    try {
      // Simular llamada a API
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast.success(
        `Orden ${trade.side.toUpperCase()} ejecutada: ${trade.quantity} ${trade.symbol} a $${
          trade.orderType === 'market' ? currentPrice.toFixed(2) : 
          trade.limitPrice?.toFixed(2) || trade.stopPrice?.toFixed(2)
        }`
      );
      
      console.log('Trade executed:', trade);
    } catch (error) {
      toast.error('Error ejecutando la orden');
      console.error('Trade error:', error);
    }
  };

  const handleSaveStrategy = async (strategy: TradingStrategy) => {
    try {
      // Simular guardado de estrategia
      await new Promise(resolve => setTimeout(resolve, 500));
      
      toast.success(`Estrategia "${strategy.name}" guardada correctamente`);
      console.log('Strategy saved:', strategy);
    } catch (error) {
      toast.error('Error guardando la estrategia');
      console.error('Strategy save error:', error);
    }
  };

  const handleStartStrategy = async (strategyId: string) => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      toast.success('Estrategia iniciada');
      console.log('Strategy started:', strategyId);
    } catch (error) {
      toast.error('Error iniciando la estrategia');
      console.error('Strategy start error:', error);
    }
  };

  const handleStopStrategy = async (strategyId: string) => {
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      toast.success('Estrategia detenida');
      console.log('Strategy stopped:', strategyId);
    } catch (error) {
      toast.error('Error deteniendo la estrategia');
      console.error('Strategy stop error:', error);
    }
  };

  const tabs = [
    { id: 'trading', name: 'Trading', description: 'Ejecutar órdenes de compra y venta' },
    { id: 'analysis', name: 'Análisis', description: 'Análisis técnico y de mercado' },
    { id: 'strategy', name: 'Estrategias', description: 'Configurar estrategias automatizadas' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Centro de Trading
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Ejecuta trades, analiza mercados y configura estrategias automatizadas
          </p>
        </div>
        
        {/* Current Symbol Info */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {selectedSymbol}
            </div>
            <div className="text-lg text-green-600 font-semibold">
              ${currentPrice.toFixed(2)}
            </div>
            <div className="text-sm text-gray-500 dark:text-gray-400">
              +2.5% (+$3.85)
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <div className="text-center">
                <div>{tab.name}</div>
                <div className="text-xs text-gray-400 mt-1">{tab.description}</div>
              </div>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        {activeTab === 'trading' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Trading Panel */}
            <div className="lg:col-span-1">
              <TradingPanel
                symbol={selectedSymbol}
                currentPrice={currentPrice}
                onTrade={handleTrade}
              />
            </div>
            
            {/* Market Data and Charts */}
            <div className="lg:col-span-2">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  Gráfico de Precios - {selectedSymbol}
                </h3>
                
                {/* Placeholder for chart */}
                <div className="h-96 bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-gray-400 dark:text-gray-500 mb-2">
                      📈 Gráfico de Trading
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Aquí se mostraría el gráfico interactivo de precios con indicadores técnicos
                    </p>
                  </div>
                </div>
                
                {/* Quick Stats */}
                <div className="grid grid-cols-4 gap-4 mt-6">
                  <div className="text-center">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Apertura</div>
                    <div className="font-semibold text-gray-900 dark:text-white">$149.85</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Máximo</div>
                    <div className="font-semibold text-gray-900 dark:text-white">$153.20</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Mínimo</div>
                    <div className="font-semibold text-gray-900 dark:text-white">$148.90</div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Volumen</div>
                    <div className="font-semibold text-gray-900 dark:text-white">2.5M</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <MarketAnalysis
            symbol={selectedSymbol}
            onSymbolChange={setSelectedSymbol}
          />
        )}

        {activeTab === 'strategy' && (
          <StrategyConfig
            onSaveStrategy={handleSaveStrategy}
            onStartStrategy={handleStartStrategy}
            onStopStrategy={handleStopStrategy}
          />
        )}
      </motion.div>

      {/* Recent Activity */}
      {activeTab === 'trading' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Actividad Reciente
          </h3>
          
          <div className="space-y-3">
            {[
              { time: '10:30', action: 'BUY', symbol: 'AAPL', qty: 50, price: 152.30, status: 'Ejecutada' },
              { time: '10:15', action: 'SELL', symbol: 'MSFT', qty: 25, price: 305.80, status: 'Ejecutada' },
              { time: '09:45', action: 'BUY', symbol: 'GOOGL', qty: 10, price: 2650.00, status: 'Pendiente' },
            ].map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    {activity.time}
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    activity.action === 'BUY' 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                  }`}>
                    {activity.action}
                  </div>
                  <div className="font-medium text-gray-900 dark:text-white">
                    {activity.qty} {activity.symbol}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    @ ${activity.price}
                  </div>
                </div>
                <div className={`px-2 py-1 rounded text-xs font-medium ${
                  activity.status === 'Ejecutada'
                    ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                }`}>
                  {activity.status}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default Trading;