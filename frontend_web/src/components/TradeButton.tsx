/**
 * Enhanced Trade Execution Button with Advanced Features
 */

'use client';

import { useState, ChangeEvent } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Slider } from '@/components/ui/slider';
import { 
  Rocket, 
  TrendingUp, 
  TrendingDown, 
  Zap, 
  Calculator, 
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  BarChart3
} from 'lucide-react';
import { cn, formatCurrency, formatPercentage } from '@/lib/utils';
import toast from 'react-hot-toast';

interface TradeButtonProps {
  symbol: string;
  onTradeExecuted?: () => void;
}

export default function TradeButton({ symbol, onTradeExecuted }: TradeButtonProps) {
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [tradeType, setTradeType] = useState<'BUY' | 'SELL'>('BUY');
  const [confidence, setConfidence] = useState([0.75]);
  const [useAI, setUseAI] = useState(true);
  const [countdown, setCountdown] = useState(0);
  const [tradeSize, setTradeSize] = useState([1000]); // Default $1000
  const [slippage, setSlippage] = useState(0.1); // 0.1%
  const [showPreview, setShowPreview] = useState(false);

  const executeTrade = async () => {
    setLoading(true);
    setCountdown(3);
    
    // Countdown animation
    const countdownInterval = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownInterval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    setTimeout(async () => {
      try {
        const response = await api.executeTrade({
          symbol,
          side: useAI ? undefined : tradeType,
          confidence: useAI ? undefined : confidence[0],
          force: !useAI
        });
        
        if (response.data.status === 'filled') {
          toast.success('Trade executed successfully!', {
            duration: 4000,
            icon: '🎉',
          });
        } else {
          toast(`Trade ${response.data.status}: ${response.data.message}`, { icon: '⚠️' });
        }
        
        setShowModal(false);
        onTradeExecuted?.();
      } catch (error: any) {
        toast.error(`Trade failed: ${error.response?.data?.detail || error.message}`);
      } finally {
        setLoading(false);
        clearInterval(countdownInterval);
      }
    }, 3000);
  };

  const calculateFees = () => {
    const size = tradeSize[0];
    const feeRate = 0.001; // 0.1%
    return size * feeRate;
  };

  const calculateSlippage = () => {
    const size = tradeSize[0];
    return size * (slippage / 100);
  };

  const totalCost = tradeSize[0] + calculateFees() + calculateSlippage();

  return (
    <>
      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogTrigger asChild>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button 
              size="lg" 
              variant="gradient"
              className="text-white font-semibold px-6 py-3 rounded-xl shadow-lg hover:shadow-xl"
            >
              <Rocket className="h-5 w-5 mr-2" />
              Execute Trade
            </Button>
          </motion.div>
        </DialogTrigger>
        
        <DialogContent className="max-w-2xl bg-dark-surface border-dark-border">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-white">
              <Zap className="h-5 w-5 text-accent-cyan" />
              Execute Trade - {symbol}
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-6">
            {/* AI Toggle */}
            <Card className="bg-dark-card border-dark-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-accent-cyan/20 rounded-lg">
                      <Zap className="h-5 w-5 text-accent-cyan" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">Use AI Signal</p>
                      <p className="text-sm text-gray-400">Let the AI decide the best trade direction</p>
                    </div>
                  </div>
                  <Button
                    variant={useAI ? "default" : "outline"}
                    onClick={() => setUseAI(!useAI)}
                    className={cn(
                      "transition-all duration-300",
                      useAI && "bg-accent-cyan hover:bg-accent-cyan/90"
                    )}
                  >
                    {useAI ? <CheckCircle className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Manual Trade Controls */}
            {!useAI && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-4"
              >
                {/* Trade Type */}
                <Card className="bg-dark-card border-dark-border">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <BarChart3 className="h-5 w-5 text-accent-purple" />
                      Trade Direction
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-3">
                      <Button
                        variant={tradeType === 'BUY' ? "default" : "outline"}
                        onClick={() => setTradeType('BUY')}
                        className={cn(
                          "h-16 transition-all duration-300",
                          tradeType === 'BUY' 
                            ? "bg-accent-green hover:bg-accent-green/90 text-white" 
                            : "border-dark-border hover:border-accent-green/50"
                        )}
                      >
                        <TrendingUp className="h-6 w-6 mr-2" />
                        <div className="text-center">
                          <div className="font-bold">BUY</div>
                          <div className="text-xs opacity-75">Long Position</div>
                        </div>
                      </Button>
                      
                      <Button
                        variant={tradeType === 'SELL' ? "default" : "outline"}
                        onClick={() => setTradeType('SELL')}
                        className={cn(
                          "h-16 transition-all duration-300",
                          tradeType === 'SELL' 
                            ? "bg-accent-red hover:bg-accent-red/90 text-white" 
                            : "border-dark-border hover:border-accent-red/50"
                        )}
                      >
                        <TrendingDown className="h-6 w-6 mr-2" />
                        <div className="text-center">
                          <div className="font-bold">SELL</div>
                          <div className="text-xs opacity-75">Short Position</div>
                        </div>
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Confidence Slider */}
                <Card className="bg-dark-card border-dark-border">
                  <CardHeader>
                    <CardTitle className="text-white">Confidence Level</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-400">Confidence</span>
                        <span className="text-lg font-bold text-accent-cyan">
                          {formatPercentage(confidence[0], 0)}
                        </span>
                      </div>
                      <Slider
                        value={confidence}
                        onValueChange={setConfidence}
                        min={0.5}
                        max={1}
                        step={0.05}
                        className="w-full"
                      />
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Low (50%)</span>
                        <span>High (100%)</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Trade Size */}
            <Card className="bg-dark-card border-dark-border">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-accent-orange" />
                  Trade Size
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Amount</span>
                    <span className="text-lg font-bold text-white">
                      {formatCurrency(tradeSize[0])}
                    </span>
                  </div>
                  <Slider
                    value={tradeSize}
                    onValueChange={setTradeSize}
                    min={100}
                    max={10000}
                    step={100}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>$100</span>
                    <span>$10,000</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Cost Breakdown */}
            <Card className="bg-dark-card border-dark-border">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-accent-purple" />
                  Cost Breakdown
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Trade Size</span>
                    <span className="text-white">{formatCurrency(tradeSize[0])}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Trading Fee (0.1%)</span>
                    <span className="text-white">{formatCurrency(calculateFees())}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Est. Slippage</span>
                    <span className="text-white">{formatCurrency(calculateSlippage())}</span>
                  </div>
                  <hr className="border-dark-border" />
                  <div className="flex justify-between font-semibold">
                    <span className="text-white">Total Cost</span>
                    <span className="text-accent-cyan">{formatCurrency(totalCost)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Execution Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => setShowModal(false)}
                disabled={loading}
                className="flex-1 border-dark-border hover:bg-dark-surface"
              >
                Cancel
              </Button>
              
              <Button
                onClick={executeTrade}
                disabled={loading}
                variant="gradient"
                className="flex-1 text-white font-semibold"
              >
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.div
                      key="loading"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      {countdown > 0 ? (
                        <>
                          <Clock className="h-4 w-4 animate-spin" />
                          Executing in {countdown}s...
                        </>
                      ) : (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Executing Trade...
                        </>
                      )}
                    </motion.div>
                  ) : (
                    <motion.div
                      key="ready"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <Rocket className="h-4 w-4" />
                      Execute Trade
                    </motion.div>
                  )}
                </AnimatePresence>
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

