/**
 * Enhanced Symbol Selector Component with Live Prices
 */

'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Star } from 'lucide-react';
import { cn, formatCurrency, getChangeColor } from '@/lib/utils';

interface SymbolSelectorProps {
  selected: string;
  onSelect: (symbol: string) => void;
}

interface SymbolData {
  value: string;
  label: string;
  icon: string;
  price?: number;
  change24h?: number;
  volume?: number;
}

const SUPPORTED_SYMBOLS: SymbolData[] = [
  { value: 'BTCUSD', label: 'BTC/USD', icon: '₿' },
];

export default function SymbolSelector({ selected, onSelect }: SymbolSelectorProps) {
  const [symbolsData, setSymbolsData] = useState<SymbolData[]>(SUPPORTED_SYMBOLS);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSymbolData();
    const interval = setInterval(fetchSymbolData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchSymbolData = async () => {
    setLoading(true);
    try {
      const updatedSymbols = await Promise.all(
        SUPPORTED_SYMBOLS.map(async (symbol) => {
          try {
            const response = await api.getTicker(symbol.value);
            const ticker = response.data;
            return {
              ...symbol,
              price: parseFloat(ticker.spot_price || ticker.close || '0'),
              change24h: parseFloat(ticker.ltp_change_24h || ticker.change_24h || '0'),
              volume: parseFloat(ticker.volume || '0'),
            };
          } catch (error) {
            console.error(`Failed to fetch data for ${symbol.value}:`, error);
            return symbol;
          }
        })
      );
      setSymbolsData(updatedSymbols);
    } catch (error) {
      console.error('Failed to fetch symbol data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleFavorite = (symbol: string) => {
    setFavorites(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const sortedSymbols = [...symbolsData].sort((a, b) => {
    // Favorites first, then by volume
    const aIsFavorite = favorites.includes(a.value);
    const bIsFavorite = favorites.includes(b.value);
    
    if (aIsFavorite && !bIsFavorite) return -1;
    if (!aIsFavorite && bIsFavorite) return 1;
    
    return (b.volume || 0) - (a.volume || 0);
  });

  return (
    <Card className="trading-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-accent-cyan" />
          Trading Symbols
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {sortedSymbols.map((symbol, index) => (
            <motion.div
              key={symbol.value}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              onClick={() => onSelect(symbol.value)}
              className={cn(
                "group relative p-4 rounded-xl border-2 transition-all duration-300 cursor-pointer",
                selected === symbol.value
                  ? "border-accent-cyan bg-accent-cyan/10 shadow-lg shadow-accent-cyan/20"
                  : "border-dark-border bg-dark-surface hover:border-accent-cyan/50 hover:bg-dark-card/50"
              )}
            >
              {/* Favorite Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavorite(symbol.value);
                }}
                className="absolute top-2 right-2 p-1 rounded-full hover:bg-white/10 transition-colors z-10"
              >
                <Star 
                  className={cn(
                    "h-4 w-4 transition-colors",
                    favorites.includes(symbol.value) 
                      ? "fill-accent-orange text-accent-orange" 
                      : "text-gray-500 group-hover:text-accent-orange"
                  )} 
                />
              </button>

              {/* Symbol Info */}
              <div className="text-center">
                <motion.div 
                  animate={selected === symbol.value ? { scale: [1, 1.1, 1] } : {}}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-3xl mb-2"
                >
                  {symbol.icon}
                </motion.div>
                
                <div className="text-sm font-semibold text-white mb-1">
                  {symbol.label}
                </div>

                {/* Price and Change */}
                {symbol.price && (
                  <div className="space-y-1">
                    <div className="text-lg font-bold text-white">
                      {formatCurrency(symbol.price)}
                    </div>
                    
                    {symbol.change24h !== undefined && (
                      <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className={cn(
                          "flex items-center justify-center gap-1 text-sm font-medium",
                          getChangeColor(symbol.change24h)
                        )}
                      >
                        {symbol.change24h >= 0 ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        {Math.abs(symbol.change24h).toFixed(2)}%
                      </motion.div>
                    )}

                    {symbol.volume && (
                      <div className="text-xs text-gray-400">
                        Vol: {symbol.volume.toLocaleString()}
                      </div>
                    )}
                  </div>
                )}

                {loading && !symbol.price && (
                  <div className="space-y-2">
                    <div className="animate-pulse bg-gray-700 h-4 rounded w-16 mx-auto"></div>
                    <div className="animate-pulse bg-gray-700 h-3 rounded w-12 mx-auto"></div>
                  </div>
                )}
              </div>

              {/* Selection Indicator */}
              {selected === symbol.value && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute inset-0 border-2 border-accent-cyan rounded-xl pointer-events-none"
                >
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-accent-cyan rounded-full"></div>
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

