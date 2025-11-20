# utils/technical_analysis.py
import pandas as pd
import pandas_ta as ta
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

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
            
            # Moving Averages
            indicators['sma_20'] = ta.sma(close_prices, length=20).iloc[-1]
            indicators['sma_50'] = ta.sma(close_prices, length=50).iloc[-1]
            indicators['ema_12'] = ta.ema(close_prices, length=12).iloc[-1]
            indicators['ema_26'] = ta.ema(close_prices, length=26).iloc[-1]
            
            # RSI
            rsi = ta.rsi(close_prices, length=14)
            indicators['rsi'] = rsi.iloc[-1] if not rsi.empty else None
            
            # MACD
            macd = ta.macd(close_prices, fast=12, slow=26, signal=9)
            if not macd.empty:
                indicators['macd'] = macd['MACD_12_26_9'].iloc[-1]
                indicators['macd_signal'] = macd['MACDs_12_26_9'].iloc[-1]
                indicators['macd_histogram'] = macd['MACDh_12_26_9'].iloc[-1]
            
            # Bollinger Bands
            bollinger = ta.bbands(close_prices, length=20, std=2)
            if not bollinger.empty:
                indicators['bb_upper'] = bollinger['BBU_20_2.0'].iloc[-1]
                indicators['bb_middle'] = bollinger['BBM_20_2.0'].iloc[-1]
                indicators['bb_lower'] = bollinger['BBL_20_2.0'].iloc[-1]
                indicators['bb_position'] = (close_prices.iloc[-1] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
            
            # Stochastic
            stoch = ta.stoch(high_prices, low_prices, close_prices, k=14, d=3)
            if not stoch.empty:
                indicators['stoch_k'] = stoch['STOCHk_14_3_3'].iloc[-1]
                indicators['stoch_d'] = stoch['STOCHd_14_3_3'].iloc[-1]
            
            # Volume indicators
            indicators['volume_sma'] = ta.sma(volume, length=20).iloc[-1]
            indicators['current_volume'] = volume.iloc[-1]
            indicators['volume_ratio'] = indicators['current_volume'] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1
            
            # Generate signals
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
            
            # Overall Signal
            bullish_signals = sum([
                1 for signal in signals.values() 
                if signal in ['BULLISH', 'OVERBOUGHT', 'STRONG_BUY']
            ])
            bearish_signals = sum([
                1 for signal in signals.values() 
                if signal in ['BEARISH', 'OVERSOLD', 'STRONG_SELL']
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
                'pivot': pivot.iloc[-1],
                'resistance_1': r1.iloc[-1],
                'support_1': s1.iloc[-1],
                'recent_high': recent_high,
                'recent_low': recent_low,
                'current_price': close.iloc[-1]
            }
            
        except Exception as e:
            return {"error": str(e)}

# Global instance
tech_analyzer = TechnicalAnalyzer()