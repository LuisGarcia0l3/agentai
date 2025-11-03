import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowPathIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';

interface MarketAnalysisProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
}

interface TechnicalIndicator {
  name: string;
  value: number;
  signal: 'buy' | 'sell' | 'neutral';
  description: string;
}

interface MarketSentiment {
  overall: 'bullish' | 'bearish' | 'neutral';
  score: number;
  factors: string[];
}

interface PriceLevel {
  type: 'support' | 'resistance';
  price: number;
  strength: 'weak' | 'moderate' | 'strong';
}

const MarketAnalysis: React.FC<MarketAnalysisProps> = ({ symbol, onSymbolChange }) => {
  const [indicators, setIndicators] = useState<TechnicalIndicator[]>([]);
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [priceLevels, setPriceLevels] = useState<PriceLevel[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1h' | '4h' | '1d' | '1w'>('1d');

  // Símbolos populares
  const popularSymbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'];

  // Simular datos de análisis técnico
  const generateMockData = () => {
    const mockIndicators: TechnicalIndicator[] = [
      {
        name: 'RSI (14)',
        value: 65.2,
        signal: 'neutral',
        description: 'Índice de Fuerza Relativa indica momentum neutral'
      },
      {
        name: 'MACD',
        value: 1.25,
        signal: 'buy',
        description: 'MACD por encima de la línea de señal - tendencia alcista'
      },
      {
        name: 'SMA 20',
        value: 152.30,
        signal: 'buy',
        description: 'Precio por encima de la media móvil de 20 períodos'
      },
      {
        name: 'SMA 50',
        value: 148.75,
        signal: 'buy',
        description: 'Precio por encima de la media móvil de 50 períodos'
      },
      {
        name: 'Bollinger Bands',
        value: 0.75,
        signal: 'neutral',
        description: 'Precio en el rango medio de las Bandas de Bollinger'
      },
      {
        name: 'Stochastic',
        value: 72.8,
        signal: 'sell',
        description: 'Oscilador estocástico en zona de sobrecompra'
      },
    ];

    const mockSentiment: MarketSentiment = {
      overall: 'bullish',
      score: 0.72,
      factors: [
        'Volumen por encima del promedio',
        'Tendencia alcista confirmada',
        'Soporte técnico fuerte',
        'Momentum positivo'
      ]
    };

    const mockPriceLevels: PriceLevel[] = [
      { type: 'resistance', price: 155.50, strength: 'strong' },
      { type: 'resistance', price: 153.20, strength: 'moderate' },
      { type: 'support', price: 148.00, strength: 'strong' },
      { type: 'support', price: 150.75, strength: 'weak' },
    ];

    setIndicators(mockIndicators);
    setSentiment(mockSentiment);
    setPriceLevels(mockPriceLevels);
    setLastUpdate(new Date());
  };

  const refreshAnalysis = async () => {
    setIsLoading(true);
    // Simular llamada a API
    await new Promise(resolve => setTimeout(resolve, 1500));
    generateMockData();
    setIsLoading(false);
  };

  useEffect(() => {
    generateMockData();
  }, [symbol, selectedTimeframe]);

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy': return 'text-green-600 bg-green-50 border-green-200';
      case 'sell': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'buy': return <TrendingUpIcon className="h-4 w-4" />;
      case 'sell': return <TrendingDownIcon className="h-4 w-4" />;
      default: return <InformationCircleIcon className="h-4 w-4" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'text-green-600';
      case 'bearish': return 'text-red-600';
      default: return 'text-yellow-600';
    }
  };

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'strong': return 'bg-blue-500';
      case 'moderate': return 'bg-yellow-500';
      default: return 'bg-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Symbol Selector */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
            <ChartBarIcon className="h-5 w-5 mr-2" />
            Análisis de Mercado
          </h3>
          <button
            onClick={refreshAnalysis}
            disabled={isLoading}
            className="flex items-center px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <ArrowPathIcon className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            {isLoading ? 'Actualizando...' : 'Actualizar'}
          </button>
        </div>

        {/* Symbol and Timeframe Selection */}
        <div className="flex flex-wrap gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Símbolo
            </label>
            <select
              value={symbol}
              onChange={(e) => onSymbolChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            >
              {popularSymbols.map(sym => (
                <option key={sym} value={sym}>{sym}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Timeframe
            </label>
            <div className="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-1">
              {(['1h', '4h', '1d', '1w'] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setSelectedTimeframe(tf)}
                  className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                    selectedTimeframe === tf
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="text-xs text-gray-500 dark:text-gray-400">
          Última actualización: {lastUpdate.toLocaleTimeString()}
        </div>
      </motion.div>

      {/* Market Sentiment */}
      {sentiment && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
        >
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Sentimiento del Mercado
          </h4>
          
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <div className={`text-2xl font-bold ${getSentimentColor(sentiment.overall)}`}>
                {sentiment.overall.toUpperCase()}
              </div>
              <div className="ml-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Score</div>
                <div className="text-lg font-semibold text-gray-900 dark:text-white">
                  {(sentiment.score * 100).toFixed(0)}%
                </div>
              </div>
            </div>
            
            {/* Sentiment Meter */}
            <div className="w-32 h-4 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  sentiment.overall === 'bullish' ? 'bg-green-500' :
                  sentiment.overall === 'bearish' ? 'bg-red-500' : 'bg-yellow-500'
                }`}
                style={{ width: `${sentiment.score * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="space-y-2">
            <h5 className="font-medium text-gray-900 dark:text-white">Factores Clave:</h5>
            <ul className="space-y-1">
              {sentiment.factors.map((factor, index) => (
                <li key={index} className="flex items-center text-sm text-gray-600 dark:text-gray-400">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}

      {/* Technical Indicators */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
      >
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Indicadores Técnicos
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {indicators.map((indicator, index) => (
            <div
              key={index}
              className="border border-gray-200 dark:border-gray-600 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <h5 className="font-medium text-gray-900 dark:text-white">
                  {indicator.name}
                </h5>
                <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getSignalColor(indicator.signal)}`}>
                  {getSignalIcon(indicator.signal)}
                  <span className="ml-1">{indicator.signal.toUpperCase()}</span>
                </div>
              </div>
              
              <div className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                {indicator.value.toFixed(2)}
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {indicator.description}
              </p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Support and Resistance Levels */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
      >
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Niveles de Soporte y Resistencia
        </h4>

        <div className="space-y-3">
          {priceLevels
            .sort((a, b) => b.price - a.price)
            .map((level, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    level.type === 'resistance' ? 'bg-red-500' : 'bg-green-500'
                  }`}></div>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-white">
                      ${level.price.toFixed(2)}
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      {level.type === 'resistance' ? 'Resistencia' : 'Soporte'}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center">
                  <div className={`w-16 h-2 rounded-full mr-2 ${getStrengthColor(level.strength)}`}></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                    {level.strength}
                  </span>
                </div>
              </div>
            ))}
        </div>

        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-start">
            <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2 mt-0.5" />
            <div className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Tip:</strong> Los niveles de soporte y resistencia son zonas donde el precio tiende a reaccionar. 
              Úsalos para planificar entradas y salidas de tus trades.
            </div>
          </div>
        </div>
      </motion.div>

      {/* AI Analysis Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl shadow-lg p-6 border border-purple-200 dark:border-purple-800"
      >
        <div className="flex items-center mb-4">
          <EyeIcon className="h-5 w-5 text-purple-600 dark:text-purple-400 mr-2" />
          <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
            Resumen IA
          </h4>
        </div>

        <div className="prose dark:prose-invert max-w-none">
          <p className="text-gray-700 dark:text-gray-300">
            Basado en el análisis técnico actual de <strong>{symbol}</strong>, los indicadores muestran 
            una tendencia <strong className={getSentimentColor(sentiment?.overall || 'neutral')}>
            {sentiment?.overall || 'neutral'}</strong>. 
            El RSI en {indicators.find(i => i.name.includes('RSI'))?.value.toFixed(1)} sugiere un momentum moderado, 
            mientras que el MACD confirma la dirección de la tendencia.
          </p>
          
          <p className="text-gray-700 dark:text-gray-300 mt-3">
            <strong>Recomendación:</strong> Considera los niveles de soporte en ${priceLevels.find(l => l.type === 'support')?.price.toFixed(2)} 
            y resistencia en ${priceLevels.find(l => l.type === 'resistance')?.price.toFixed(2)} para tus decisiones de trading.
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default MarketAnalysis;