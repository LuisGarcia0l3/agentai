import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

interface TradingPanelProps {
  symbol: string;
  currentPrice: number;
  onTrade: (trade: TradeOrder) => void;
}

interface TradeOrder {
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  orderType: 'market' | 'limit' | 'stop';
  limitPrice?: number;
  stopPrice?: number;
}

const TradingPanel: React.FC<TradingPanelProps> = ({ symbol, currentPrice, onTrade }) => {
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState<number>(10);
  const [orderType, setOrderType] = useState<'market' | 'limit' | 'stop'>('market');
  const [limitPrice, setLimitPrice] = useState<number>(currentPrice);
  const [stopPrice, setStopPrice] = useState<number>(currentPrice * 0.95);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const trade: TradeOrder = {
        symbol,
        side,
        quantity,
        orderType,
        limitPrice: orderType === 'limit' ? limitPrice : undefined,
        stopPrice: orderType === 'stop' ? stopPrice : undefined,
      };

      await onTrade(trade);
    } catch (error) {
      console.error('Error placing trade:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const estimatedCost = orderType === 'market' ? currentPrice * quantity : limitPrice * quantity;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Panel de Trading
        </h3>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-500 dark:text-gray-400">Live</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Symbol and Price */}
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Símbolo</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{symbol}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600 dark:text-gray-400">Precio Actual</p>
              <p className="text-xl font-bold text-green-600">${currentPrice.toFixed(2)}</p>
            </div>
          </div>
        </div>

        {/* Buy/Sell Toggle */}
        <div className="flex rounded-lg bg-gray-100 dark:bg-gray-700 p-1">
          <button
            type="button"
            onClick={() => setSide('buy')}
            className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md font-medium transition-colors ${
              side === 'buy'
                ? 'bg-green-500 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <ArrowUpIcon className="h-4 w-4 mr-2" />
            Comprar
          </button>
          <button
            type="button"
            onClick={() => setSide('sell')}
            className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md font-medium transition-colors ${
              side === 'sell'
                ? 'bg-red-500 text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <ArrowDownIcon className="h-4 w-4 mr-2" />
            Vender
          </button>
        </div>

        {/* Order Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Tipo de Orden
          </label>
          <select
            value={orderType}
            onChange={(e) => setOrderType(e.target.value as 'market' | 'limit' | 'stop')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="market">Mercado</option>
            <option value="limit">Límite</option>
            <option value="stop">Stop</option>
          </select>
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Cantidad
          </label>
          <div className="relative">
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(Number(e.target.value))}
              min="1"
              step="1"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              placeholder="Ingresa la cantidad"
            />
            <div className="absolute inset-y-0 right-0 flex items-center pr-3">
              <ChartBarIcon className="h-4 w-4 text-gray-400" />
            </div>
          </div>
        </div>

        {/* Limit Price (if limit order) */}
        {orderType === 'limit' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Precio Límite
            </label>
            <div className="relative">
              <input
                type="number"
                value={limitPrice}
                onChange={(e) => setLimitPrice(Number(e.target.value))}
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Precio límite"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                <CurrencyDollarIcon className="h-4 w-4 text-gray-400" />
              </div>
            </div>
          </div>
        )}

        {/* Stop Price (if stop order) */}
        {orderType === 'stop' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Precio Stop
            </label>
            <div className="relative">
              <input
                type="number"
                value={stopPrice}
                onChange={(e) => setStopPrice(Number(e.target.value))}
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Precio stop"
              />
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                <ExclamationTriangleIcon className="h-4 w-4 text-gray-400" />
              </div>
            </div>
          </div>
        )}

        {/* Order Summary */}
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Resumen de la Orden
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Acción:</span>
              <span className={`font-medium ${side === 'buy' ? 'text-green-600' : 'text-red-600'}`}>
                {side === 'buy' ? 'Comprar' : 'Vender'} {quantity} {symbol}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Tipo:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {orderType === 'market' ? 'Mercado' : orderType === 'limit' ? 'Límite' : 'Stop'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Costo Estimado:</span>
              <span className="font-medium text-gray-900 dark:text-white">
                ${estimatedCost.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full flex items-center justify-center py-3 px-4 rounded-md font-medium text-white transition-colors ${
            side === 'buy'
              ? 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
              : 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
          } focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isLoading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
          ) : (
            <CheckCircleIcon className="h-5 w-5 mr-2" />
          )}
          {isLoading ? 'Procesando...' : `${side === 'buy' ? 'Comprar' : 'Vender'} ${symbol}`}
        </button>

        {/* Paper Trading Warning */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
            <p className="text-sm text-blue-700 dark:text-blue-300">
              <strong>Modo Paper Trading:</strong> Esta es una simulación. No se ejecutarán trades reales.
            </p>
          </div>
        </div>
      </form>
    </motion.div>
  );
};

export default TradingPanel;