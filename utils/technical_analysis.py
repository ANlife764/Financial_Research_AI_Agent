# utils/technical_analysis.py
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

# Import ta modules
import ta
import ta.trend
import ta.momentum
import ta.volatility
import ta.volume

class TechnicalAnalyzer:
    def __init__(self):
        self.indicators_config = {
            'sma': {'periods': [20, 50]},
            'ema': {'periods': [12, 26]},
            'rsi': {'period': 14},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger': {'period': 20, 'std': 2},
            'stochastic': {'k': 14, 'd': 3}
        }
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators"""
        if df is None or df.empty:
            return {}
        
        try:
            # Ensure we have enough data
            if len(df) < 50:
                return {"error": "Insufficient data for technical analysis"}
            
            close_prices = df['Close']
            high_prices = df['High']
            low_prices = df['Low']
            volume = df['Volume']
            
            indicators = {}
            current_price = close_prices.iloc[-1]
            indicators['current_price'] = float(current_price)
            
            # ===== MOVING AVERAGES =====
            # SMA 20
            sma_20_indicator = ta.trend.SMAIndicator(close=close_prices, window=20)
            indicators['sma_20'] = float(sma_20_indicator.sma_indicator().iloc[-1]) if not sma_20_indicator.sma_indicator().isna().iloc[-1] else None
            
            # SMA 50
            sma_50_indicator = ta.trend.SMAIndicator(close=close_prices, window=50)
            indicators['sma_50'] = float(sma_50_indicator.sma_indicator().iloc[-1]) if not sma_50_indicator.sma_indicator().isna().iloc[-1] else None
            
            # EMA 12
            ema_12_indicator = ta.trend.EMAIndicator(close=close_prices, window=12)
            indicators['ema_12'] = float(ema_12_indicator.ema_indicator().iloc[-1]) if not ema_12_indicator.ema_indicator().isna().iloc[-1] else None
            
            # EMA 26
            ema_26_indicator = ta.trend.EMAIndicator(close=close_prices, window=26)
            indicators['ema_26'] = float(ema_26_indicator.ema_indicator().iloc[-1]) if not ema_26_indicator.ema_indicator().isna().iloc[-1] else None
            
            # ===== RSI =====
            rsi_indicator = ta.momentum.RSIIndicator(close=close_prices, window=14)
            rsi_series = rsi_indicator.rsi()
            indicators['rsi'] = float(rsi_series.iloc[-1]) if not rsi_series.isna().iloc[-1] else None
            
            # ===== MACD =====
            macd_indicator = ta.trend.MACD(
                close=close_prices,
                window_slow=26,
                window_fast=12,
                window_sign=9
            )
            macd_line = macd_indicator.macd()
            macd_signal_line = macd_indicator.macd_signal()
            macd_diff = macd_indicator.macd_diff()
            
            indicators['macd'] = float(macd_line.iloc[-1]) if not macd_line.isna().iloc[-1] else None
            indicators['macd_signal'] = float(macd_signal_line.iloc[-1]) if not macd_signal_line.isna().iloc[-1] else None
            indicators['macd_histogram'] = float(macd_diff.iloc[-1]) if not macd_diff.isna().iloc[-1] else None
            
            # ===== BOLLINGER BANDS =====
            bb_indicator = ta.volatility.BollingerBands(
                close=close_prices,
                window=20,
                window_dev=2
            )
            bb_upper = bb_indicator.bollinger_hband()
            bb_middle = bb_indicator.bollinger_mavg()
            bb_lower = bb_indicator.bollinger_lband()
            
            indicators['bb_upper'] = float(bb_upper.iloc[-1]) if not bb_upper.isna().iloc[-1] else None
            indicators['bb_middle'] = float(bb_middle.iloc[-1]) if not bb_middle.isna().iloc[-1] else None
            indicators['bb_lower'] = float(bb_lower.iloc[-1]) if not bb_lower.isna().iloc[-1] else None
            
            # Calculate BB position (0-1 scale)
            if all([indicators['bb_upper'], indicators['bb_lower']]):
                bb_range = indicators['bb_upper'] - indicators['bb_lower']
                if bb_range > 0:
                    indicators['bb_position'] = (current_price - indicators['bb_lower']) / bb_range
                else:
                    indicators['bb_position'] = 0.5
            else:
                indicators['bb_position'] = 0.5
            
            # ===== STOCHASTIC =====
            stoch_indicator = ta.momentum.StochasticOscillator(
                high=high_prices,
                low=low_prices,
                close=close_prices,
                window=14,
                smooth_window=3
            )
            stoch_k = stoch_indicator.stoch()
            stoch_d = stoch_indicator.stoch_signal()
            
            indicators['stoch_k'] = float(stoch_k.iloc[-1]) if not stoch_k.isna().iloc[-1] else None
            indicators['stoch_d'] = float(stoch_d.iloc[-1]) if not stoch_d.isna().iloc[-1] else None
            
            # ===== VOLUME INDICATORS =====
            # Volume SMA
            volume_sma_indicator = ta.volume.VolumeWeightedAveragePrice(
                high=high_prices,
                low=low_prices,
                close=close_prices,
                volume=volume,
                window=20
            )
            indicators['volume_sma'] = float(volume_sma_indicator.volume_weighted_average_price().iloc[-1]) if not volume_sma_indicator.volume_weighted_average_price().isna().iloc[-1] else None
            
            # Current volume
            indicators['current_volume'] = float(volume.iloc[-1])
            
            # Volume ratio
            indicators['volume_ratio'] = indicators['current_volume'] / indicators['volume_sma'] if indicators['volume_sma'] and indicators['volume_sma'] > 0 else 1
            
            # ===== GENERATE SIGNALS =====
            indicators['signals'] = self.generate_signals(indicators)
            
            return indicators
            
        except Exception as e:
            return {"error": f"Technical analysis error: {str(e)}"}
    
    def generate_signals(self, indicators: Dict) -> Dict:
        """Generate trading signals based on technical indicators"""
        signals = {}
        
        try:
            # RSI Signals
            rsi = indicators.get('rsi')
            if rsi:
                if rsi > 70:
                    signals['rsi_signal'] = 'OVERSOLD'
                    signals['rsi_strength'] = 'STRONG_SELL'
                elif rsi < 30:
                    signals['rsi_signal'] = 'OVERBOUGHT'
                    signals['rsi_strength'] = 'STRONG_BUY'
                else:
                    signals['rsi_signal'] = 'NEUTRAL'
                    signals['rsi_strength'] = 'HOLD'
            
            # Moving Average Signals
            sma_20 = indicators.get('sma_20')
            sma_50 = indicators.get('sma_50')
            current_price = indicators.get('current_price')
            
            if all([sma_20, sma_50, current_price]):
                if current_price > sma_20 > sma_50:
                    signals['trend'] = 'BULLISH'
                elif current_price < sma_20 < sma_50:
                    signals['trend'] = 'BEARISH'
                else:
                    signals['trend'] = 'SIDEWAYS'
            
            # MACD Signals
            macd = indicators.get('macd')
            macd_signal = indicators.get('macd_signal')
            
            if macd and macd_signal:
                if macd > macd_signal and indicators.get('macd_histogram', 0) > 0:
                    signals['macd_signal'] = 'BULLISH'
                elif macd < macd_signal and indicators.get('macd_histogram', 0) < 0:
                    signals['macd_signal'] = 'BEARISH'
                else:
                    signals['macd_signal'] = 'NEUTRAL'
            
            # Bollinger Band Signals
            bb_position = indicators.get('bb_position')
            if bb_position:
                if bb_position > 0.8:
                    signals['bb_signal'] = 'OVERBOUGHT'
                elif bb_position < 0.2:
                    signals['bb_signal'] = 'OVERSOLD'
                else:
                    signals['bb_signal'] = 'NEUTRAL'
            
            # Stochastic Signals
            stoch_k = indicators.get('stoch_k')
            stoch_d = indicators.get('stoch_d')
            if stoch_k and stoch_d:
                if stoch_k > 80 and stoch_d > 80:
                    signals['stoch_signal'] = 'OVERBOUGHT'
                elif stoch_k < 20 and stoch_d < 20:
                    signals['stoch_signal'] = 'OVERSOLD'
                elif stoch_k > stoch_d:
                    signals['stoch_signal'] = 'BULLISH_CROSS'
                elif stoch_k < stoch_d:
                    signals['stoch_signal'] = 'BEARISH_CROSS'
            
            # Overall Signal
            bullish_signals = sum([
                1 for signal in signals.values() 
                if signal in ['BULLISH', 'OVERBOUGHT', 'STRONG_BUY', 'BULLISH_CROSS']
            ])
            bearish_signals = sum([
                1 for signal in signals.values() 
                if signal in ['BEARISH', 'OVERSOLD', 'STRONG_SELL', 'BEARISH_CROSS']
            ])
            
            if bullish_signals > bearish_signals:
                signals['overall'] = 'BUY'
            elif bearish_signals > bullish_signals:
                signals['overall'] = 'SELL'
            else:
                signals['overall'] = 'HOLD'
            
            return signals
            
        except Exception as e:
            return {"error": f"Signal generation error: {str(e)}"}
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """Calculate support and resistance levels"""
        try:
            high = df['High']
            low = df['Low']
            close = df['Close']
            
            # Pivot Points
            pivot = (high + low + close) / 3
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            
            # Recent highs and lows
            recent_high = high.tail(window).max()
            recent_low = low.tail(window).min()
            
            return {
                'pivot': float(pivot.iloc[-1]),
                'resistance_1': float(r1.iloc[-1]),
                'support_1': float(s1.iloc[-1]),
                'recent_high': float(recent_high),
                'recent_low': float(recent_low),
                'current_price': float(close.iloc[-1])
            }
            
        except Exception as e:
            return {"error": str(e)}

# Global instance
tech_analyzer = TechnicalAnalyzer()