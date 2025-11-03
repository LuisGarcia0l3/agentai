import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  CogIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  BoltIcon,
  AdjustmentsHorizontalIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
} from '@heroicons/react/24/outline';

interface StrategyConfigProps {
  onSaveStrategy: (strategy: TradingStrategy) => void;
  onStartStrategy: (strategyId: string) => void;
  onStopStrategy: (strategyId: string) => void;
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

const StrategyConfig: React.FC<StrategyConfigProps> = ({
  onSaveStrategy,
  onStartStrategy,
  onStopStrategy,
}) => {
  const [strategy, setStrategy] = useState<TradingStrategy>({
    id: '',
    name: '',
    type: 'swing',
    symbols: ['AAPL'],
    riskManagement: {
      maxPositionSize: 0.02,
      stopLoss: 0.02,
      takeProfit: 0.04,
      maxDailyLoss: 0.05,
    },
    technicalIndicators: {
      rsi: { enabled: true, period: 14, overbought: 70, oversold: 30 },
      macd: { enabled: true, fast: 12, slow: 26, signal: 9 },
      bollinger: { enabled: false, period: 20, stdDev: 2 },
      sma: { enabled: true, periods: [20, 50] },
    },
    mlModel: {
      enabled: true,
      model: 'ensemble',
      confidence: 0.7,
    },
    isActive: false,
  });

  const [activeTab, setActiveTab] = useState<'general' | 'risk' | 'indicators' | 'ml'>('general');
  const [savedStrategies, setSavedStrategies] = useState<TradingStrategy[]>([]);

  const handleSave = () => {
    const newStrategy = {
      ...strategy,
      id: strategy.id || `strategy_${Date.now()}`,
    };
    
    setStrategy(newStrategy);
    setSavedStrategies(prev => {
      const existing = prev.findIndex(s => s.id === newStrategy.id);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = newStrategy;
        return updated;
      }
      return [...prev, newStrategy];
    });
    
    onSaveStrategy(newStrategy);
  };

  const handleStart = (strategyId: string) => {
    setSavedStrategies(prev =>
      prev.map(s => s.id === strategyId ? { ...s, isActive: true } : s)
    );
    onStartStrategy(strategyId);
  };

  const handleStop = (strategyId: string) => {
    setSavedStrategies(prev =>
      prev.map(s => s.id === strategyId ? { ...s, isActive: false } : s)
    );
    onStopStrategy(strategyId);
  };

  const tabs = [
    { id: 'general', name: 'General', icon: CogIcon },
    { id: 'risk', name: 'Riesgo', icon: ShieldCheckIcon },
    { id: 'indicators', name: 'Indicadores', icon: ChartBarIcon },
    { id: 'ml', name: 'ML/IA', icon: BoltIcon },
  ];

  return (
    <div className="space-y-6">
      {/* Strategy List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
      >
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Estrategias Guardadas
        </h3>
        
        {savedStrategies.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            No hay estrategias guardadas. Crea una nueva estrategia abajo.
          </p>
        ) : (
          <div className="space-y-3">
            {savedStrategies.map((savedStrategy) => (
              <div
                key={savedStrategy.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white">
                    {savedStrategy.name}
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {savedStrategy.type} • {savedStrategy.symbols.join(', ')}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      savedStrategy.isActive ? 'bg-green-500' : 'bg-gray-400'
                    }`}
                  ></div>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {savedStrategy.isActive ? 'Activa' : 'Inactiva'}
                  </span>
                  {savedStrategy.isActive ? (
                    <button
                      onClick={() => handleStop(savedStrategy.id)}
                      className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                    >
                      <StopIcon className="h-4 w-4" />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStart(savedStrategy.id)}
                      className="p-2 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded-lg transition-colors"
                    >
                      <PlayIcon className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Strategy Configuration */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700"
      >
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Configurar Estrategia
          </h3>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {/* General Tab */}
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Nombre de la Estrategia
                </label>
                <input
                  type="text"
                  value={strategy.name}
                  onChange={(e) => setStrategy({ ...strategy, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Mi Estrategia de Trading"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Tipo de Estrategia
                </label>
                <select
                  value={strategy.type}
                  onChange={(e) => setStrategy({ ...strategy, type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="scalping">Scalping (1-5 min)</option>
                  <option value="swing">Swing Trading (días-semanas)</option>
                  <option value="position">Position Trading (semanas-meses)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Símbolos (separados por coma)
                </label>
                <input
                  type="text"
                  value={strategy.symbols.join(', ')}
                  onChange={(e) => setStrategy({ 
                    ...strategy, 
                    symbols: e.target.value.split(',').map(s => s.trim()).filter(s => s) 
                  })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="AAPL, MSFT, GOOGL"
                />
              </div>
            </div>
          )}

          {/* Risk Management Tab */}
          {activeTab === 'risk' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tamaño Máximo de Posición (%)
                  </label>
                  <input
                    type="number"
                    value={strategy.riskManagement.maxPositionSize * 100}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      riskManagement: {
                        ...strategy.riskManagement,
                        maxPositionSize: Number(e.target.value) / 100
                      }
                    })}
                    min="0.1"
                    max="10"
                    step="0.1"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Stop Loss (%)
                  </label>
                  <input
                    type="number"
                    value={strategy.riskManagement.stopLoss * 100}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      riskManagement: {
                        ...strategy.riskManagement,
                        stopLoss: Number(e.target.value) / 100
                      }
                    })}
                    min="0.5"
                    max="10"
                    step="0.1"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Take Profit (%)
                  </label>
                  <input
                    type="number"
                    value={strategy.riskManagement.takeProfit * 100}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      riskManagement: {
                        ...strategy.riskManagement,
                        takeProfit: Number(e.target.value) / 100
                      }
                    })}
                    min="1"
                    max="20"
                    step="0.1"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Pérdida Máxima Diaria (%)
                  </label>
                  <input
                    type="number"
                    value={strategy.riskManagement.maxDailyLoss * 100}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      riskManagement: {
                        ...strategy.riskManagement,
                        maxDailyLoss: Number(e.target.value) / 100
                      }
                    })}
                    min="1"
                    max="10"
                    step="0.1"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Technical Indicators Tab */}
          {activeTab === 'indicators' && (
            <div className="space-y-6">
              {/* RSI */}
              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-gray-900 dark:text-white">RSI</h4>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={strategy.technicalIndicators.rsi.enabled}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        technicalIndicators: {
                          ...strategy.technicalIndicators,
                          rsi: { ...strategy.technicalIndicators.rsi, enabled: e.target.checked }
                        }
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                {strategy.technicalIndicators.rsi.enabled && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Período</label>
                      <input
                        type="number"
                        value={strategy.technicalIndicators.rsi.period}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          technicalIndicators: {
                            ...strategy.technicalIndicators,
                            rsi: { ...strategy.technicalIndicators.rsi, period: Number(e.target.value) }
                          }
                        })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Sobrecompra</label>
                      <input
                        type="number"
                        value={strategy.technicalIndicators.rsi.overbought}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          technicalIndicators: {
                            ...strategy.technicalIndicators,
                            rsi: { ...strategy.technicalIndicators.rsi, overbought: Number(e.target.value) }
                          }
                        })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Sobreventa</label>
                      <input
                        type="number"
                        value={strategy.technicalIndicators.rsi.oversold}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          technicalIndicators: {
                            ...strategy.technicalIndicators,
                            rsi: { ...strategy.technicalIndicators.rsi, oversold: Number(e.target.value) }
                          }
                        })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* MACD */}
              <div className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-gray-900 dark:text-white">MACD</h4>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={strategy.technicalIndicators.macd.enabled}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        technicalIndicators: {
                          ...strategy.technicalIndicators,
                          macd: { ...strategy.technicalIndicators.macd, enabled: e.target.checked }
                        }
                      })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                  </label>
                </div>
                {strategy.technicalIndicators.macd.enabled && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Rápido</label>
                      <input
                        type="number"
                        value={strategy.technicalIndicators.macd.fast}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          technicalIndicators: {
                            ...strategy.technicalIndicators,
                            macd: { ...strategy.technicalIndicators.macd, fast: Number(e.target.value) }
                          }
                        })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Lento</label>
                      <input
                        type="number"
                        value={strategy.technicalIndicators.macd.slow}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          technicalIndicators: {
                            ...strategy.technicalIndicators,
                            macd: { ...strategy.technicalIndicators.macd, slow: Number(e.target.value) }
                          }
                        })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">Señal</label>
                      <input
                        type="number"
                        value={strategy.technicalIndicators.macd.signal}
                        onChange={(e) => setStrategy({
                          ...strategy,
                          technicalIndicators: {
                            ...strategy.technicalIndicators,
                            macd: { ...strategy.technicalIndicators.macd, signal: Number(e.target.value) }
                          }
                        })}
                        className="w-full px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ML/AI Tab */}
          {activeTab === 'ml' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-900 dark:text-white">Usar Modelos de Machine Learning</h4>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={strategy.mlModel.enabled}
                    onChange={(e) => setStrategy({
                      ...strategy,
                      mlModel: { ...strategy.mlModel, enabled: e.target.checked }
                    })}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {strategy.mlModel.enabled && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Modelo de ML
                    </label>
                    <select
                      value={strategy.mlModel.model}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        mlModel: { ...strategy.mlModel, model: e.target.value as any }
                      })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                    >
                      <option value="random_forest">Random Forest</option>
                      <option value="xgboost">XGBoost</option>
                      <option value="lstm">LSTM Neural Network</option>
                      <option value="ensemble">Ensemble (Todos)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Confianza Mínima ({(strategy.mlModel.confidence * 100).toFixed(0)}%)
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="0.95"
                      step="0.05"
                      value={strategy.mlModel.confidence}
                      onChange={(e) => setStrategy({
                        ...strategy,
                        mlModel: { ...strategy.mlModel, confidence: Number(e.target.value) }
                      })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                    />
                    <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                      <span>50%</span>
                      <span>95%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Save Button */}
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleSave}
              className="w-full flex items-center justify-center py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              <AdjustmentsHorizontalIcon className="h-5 w-5 mr-2" />
              Guardar Estrategia
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default StrategyConfig;