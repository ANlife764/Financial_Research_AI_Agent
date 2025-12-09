# utils/stock_data.py - FINAL CONSOLIDATED VERSION
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time # Ensure 'time' is imported from datetime
import streamlit as st
from typing import Dict, Optional, Tuple, List # Ensure List is imported

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
    """Get stock data with error handling (Used by Home page)"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        
        if df.empty or len(df) < 2:
            return None, 0, 0, 0, 0
            
        latest_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2])
        change_pct = ((latest_price - prev_price) / prev_price * 100) if prev_price > 0 else 0
        max_price = float(df["Close"].max())
        min_price = float(df["Close"].min())
        
        return df, latest_price, change_pct, max_price, min_price
        
    except Exception as e:
        return None, 0, 0, 0, 0

def get_financial_metrics(stock_name: str, ticker: str) -> Dict:
    """Get comprehensive financial metrics for analysis (Used by Home page)"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
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
    """Check Indian market status (Used by Home page)"""
    try:
        current_time = datetime.now().time()
        market_open = time(9, 15)  # 9:15 AM IST
        market_close = time(15, 30)  # 3:30 PM IST
        
        is_market_open = market_open <= current_time <= market_close
        is_weekend = datetime.now().weekday() >= 5
        
        # Check if it's a holiday (simplified check)
        today = datetime.now().date()
        holidays = [
            datetime(today.year, 1, 26).date(),  # Republic Day
            datetime(today.year, 8, 15).date(),  # Independence Day
            datetime(today.year, 10, 2).date(),  # Gandhi Jayanti
        ]
        is_holiday = today in holidays
        
        return {
            "is_open": is_market_open and not is_weekend and not is_holiday,
            "next_open": "Monday 9:15 AM" if is_weekend else "Tomorrow 9:15 AM"
        }
        
    except Exception as e:
        return {"error": str(e), "is_open": False}

# --- FUNCTIONS ADDED FOR PAGES/PORTFOLIO.PY COMPATIBILITY ---

# Ticker Search Simulation Dictionary (Needed for Portfolio Tab 1)
TICKER_SIMULATION_DATA = {
    "HDFC BANK": "HDFCBANK.NS",
    "RELIANCE IND.": "RELIANCE.NS",
    "TATA CONSULTANCY": "TCS.NS",
    "INFOSYS": "INFY.NS",
    "STATE BANK": "SBIN.NS",
    "MARUTI": "MARUTI.NS",
}

def get_ltp_and_change(ticker: str, fallback_price: float) -> Tuple[float, str, str]:
    """
    Fetches the last traded price (LTP) and calculates the change relative to 
    the opening price, returning formatting details for the UI. (Used by Portfolio)
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetching 1 day of intraday data (5m interval)
        data = stock.history(period="1d", interval="5m") 
        
        if data.empty or data['Open'].empty:
            ltp = fallback_price * 1.10
            prev_close = fallback_price
        else:
            ltp = data['Close'].iloc[-1]
            prev_close = data['Open'].iloc[0] 
            
            if prev_close == 0:
                prev_close = fallback_price 

        change = ltp - prev_close
        
        if change > 0:
            color = "green"
            arrow = "▲"
        elif change < 0:
            color = "red"
            arrow = "▼"
        else:
            color = "gray"
            arrow = "—"
            
        return round(ltp, 2), color, arrow

    except Exception as e:
        return round(fallback_price * 1.10, 2), "gray", "—"
        
def search_ticker_symbols(query: str) -> List[Tuple[str, str]]:
    """
    Searches for stock ticker symbols based on a query using simulation data. (Used by Portfolio)
    """
    if not query or len(query) < 2:
        return []
        
    query = query.upper()
    
    results = []
    for name, symbol in TICKER_SIMULATION_DATA.items():
        if query in name or query in symbol:
            results.append((symbol, name))
            
    return [(symbol, f"{symbol} - {name}") for symbol, name in results][:5]