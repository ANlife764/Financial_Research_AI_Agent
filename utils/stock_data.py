# utils/stock_data.py - CORRECTED VERSION
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, Optional, Tuple
import time
import requests_cache

# Cache for API calls
session = requests_cache.CachedSession('yfinance.cache', expire_after=300)

# Indian stock mappings with sectors
INDIAN_STOCKS = {
    "Reliance": {"ticker": "RELIANCE.NS", "sector": "Energy"},
    "TCS": {"ticker": "TCS.NS", "sector": "IT"},
    "Infosys": {"ticker": "INFY.NS", "sector": "IT"},
    "HDFC Bank": {"ticker": "HDFCBANK.NS", "sector": "Banking"},
    "ICICI Bank": {"ticker": "ICICIBANK.NS", "sector": "Banking"},
    "Bajaj Finance": {"ticker": "BAJFINANCE.NS", "sector": "Financial Services"}
}

def get_stock_data(ticker: str, period: str = "1mo", interval: str = "1d") -> Tuple[Optional[pd.DataFrame], float, float, float, float]:
    """Get stock data with caching and error handling"""
    try:
        stock = yf.Ticker(ticker, session=session)
        df = stock.history(period=period, interval=interval)
        
        if df.empty:
            return None, 0, 0, 0, 0
            
        latest_price = float(df["Close"].iloc[-1])
        change_pct = float((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100)
        max_price = float(df["Close"].max())
        min_price = float(df["Close"].min())
        
        return df, latest_price, change_pct, max_price, min_price
        
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {str(e)}")
        return None, 0, 0, 0, 0

def get_financial_metrics(stock_name: str, ticker: str) -> Dict:
    """Get comprehensive financial metrics for analysis"""
    try:
        stock = yf.Ticker(ticker, session=session)
        info = stock.info
        
        # Basic financial metrics
        market_cap = info.get('marketCap', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        
        # Format market cap for Indian context
        if market_cap != 'N/A' and isinstance(market_cap, (int, float)):
            if market_cap >= 1e12:  # Lakh Crore
                market_cap_formatted = f"₹{market_cap/1e12:.2f} Lakh Cr"
            elif market_cap >= 1e7:  # Crore
                market_cap_formatted = f"₹{market_cap/1e7:.2f} Cr"
            else:
                market_cap_formatted = f"₹{market_cap:,.0f}"
        else:
            market_cap_formatted = 'N/A'
        
        return {
            "market_cap": market_cap_formatted,
            "pe_ratio": pe_ratio,
            "pb_ratio": info.get('priceToBook', 'N/A'),
            "debt_to_equity": info.get('debtToEquity', 'N/A'),
            "roe": info.get('returnOnEquity', 'N/A'),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A')
        }
        
    except Exception as e:
        return {"error": str(e)}

def get_market_status() -> Dict:
    """Check Indian market status"""
    try:
        current_time = datetime.now().time()
        market_open = time(9, 15)  # 9:15 AM IST
        market_close = time(15, 30)  # 3:30 PM IST
        
        is_market_open = market_open <= current_time <= market_close
        is_weekend = datetime.now().weekday() >= 5
        
        return {
            "is_open": is_market_open and not is_weekend,
            "next_open": "Monday 9:15 AM" if is_weekend else "Tomorrow 9:15 AM"
        }
        
    except Exception as e:
        return {"error": str(e), "is_open": False}