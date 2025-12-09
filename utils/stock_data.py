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



def get_financial_metrics(stock_name, ticker):
    """Get comprehensive fundamental metrics with better error handling"""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Helper function to safely get values
        def safe_get(key, default='N/A'):
            value = info.get(key, default)
            if value is None:
                return default
            return value
        
        # Format market cap
        market_cap = safe_get('marketCap', 0)
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            if market_cap >= 1e12:
                formatted_market_cap = f"₹{market_cap/1e12:.2f} Lakh Cr"
            elif market_cap >= 1e7:
                formatted_market_cap = f"₹{market_cap/1e7:.2f} Cr"
            else:
                formatted_market_cap = f"₹{market_cap:,.0f}"
        else:
            formatted_market_cap = 'N/A'
        
        # Format ratios with 2 decimal places
        pe_ratio = safe_get('trailingPE', 'N/A')
        if isinstance(pe_ratio, (int, float)):
            pe_ratio = f"{pe_ratio:.2f}"
        
        pb_ratio = safe_get('priceToBook', 'N/A')
        if isinstance(pb_ratio, (int, float)):
            pb_ratio = f"{pb_ratio:.2f}"
        
        # Format percentages
        def format_percent(value, default='N/A'):
            if isinstance(value, (int, float)):
                return f"{value:.2f}%" if abs(value) < 100 else f"{value:.0f}%"
            return default
        
        roe = format_percent(safe_get('returnOnEquity'))
        roa = format_percent(safe_get('returnOnAssets'))
        profit_margins = format_percent(safe_get('profitMargins'))
        operating_margins = format_percent(safe_get('operatingMargins'))
        
        # Revenue growth (already in decimal form, convert to %)
        revenue_growth = safe_get('revenueGrowth', 'N/A')
        if isinstance(revenue_growth, (int, float)):
            revenue_growth = f"{revenue_growth*100:.2f}%"
        
        # Dividend yield (already in decimal form)
        dividend_yield = safe_get('dividendYield', 'N/A')
        if isinstance(dividend_yield, (int, float)):
            dividend_yield = f"{dividend_yield*100:.2f}%"
        
        # Debt to equity (show as ratio)
        debt_to_equity = safe_get('debtToEquity', 'N/A')
        if isinstance(debt_to_equity, (int, float)):
            debt_to_equity = f"{debt_to_equity:.2f}"
        
        # Current ratio
        current_ratio = safe_get('currentRatio', 'N/A')
        if isinstance(current_ratio, (int, float)):
            current_ratio = f"{current_ratio:.2f}"
        
        # Free cash flow (format in Cr)
        free_cashflow = safe_get('freeCashflow', 'N/A')
        if isinstance(free_cashflow, (int, float)) and free_cashflow != 0:
            if abs(free_cashflow) >= 1e7:
                free_cashflow = f"₹{free_cashflow/1e7:.2f} Cr"
            else:
                free_cashflow = f"₹{free_cashflow:,.0f}"
        
        return {
            'market_cap': formatted_market_cap,
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'debt_to_equity': debt_to_equity,
            'current_ratio': current_ratio,
            'roe': roe,
            'roa': roa,
            'profit_margins': profit_margins,
            'operating_margins': operating_margins,
            'revenue_growth': revenue_growth,
            'dividend_yield': dividend_yield,
            'free_cashflow': free_cashflow,
            'sector': safe_get('sector', 'N/A'),
            'industry': safe_get('industry', 'N/A'),
            'beta': safe_get('beta', 'N/A')
        }
        
    except Exception as e:
        print(f"Error getting financial metrics for {ticker}: {e}")
        # Return a dictionary with N/A values but proper structure
        return {
            'market_cap': 'N/A',
            'pe_ratio': 'N/A',
            'pb_ratio': 'N/A',
            'debt_to_equity': 'N/A',
            'current_ratio': 'N/A',
            'roe': 'N/A',
            'roa': 'N/A',
            'profit_margins': 'N/A',
            'operating_margins': 'N/A',
            'revenue_growth': 'N/A',
            'dividend_yield': 'N/A',
            'free_cashflow': 'N/A',
            'sector': 'N/A',
            'industry': 'N/A',
            'beta': 'N/A'
        }
def get_fundamental_metrics(ticker):
    """Get comprehensive fundamental metrics for Indian stocks"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Format market cap in Indian notation
        market_cap = info.get('marketCap', 0)
        formatted_market_cap = format_market_cap(market_cap)
        
        # Calculate key ratios
        pe_ratio = info.get('trailingPE', 'N/A')
        pb_ratio = info.get('priceToBook', 'N/A')
        
        # Financial health metrics
        debt_to_equity = info.get('debtToEquity', 'N/A')
        current_ratio = info.get('currentRatio', 'N/A')
        
        # Profitability metrics
        roe = info.get('returnOnEquity', 'N/A')
        roa = info.get('returnOnAssets', 'N/A')
        profit_margins = info.get('profitMargins', 'N/A')
        operating_margins = info.get('operatingMargins', 'N/A')
        
        # Growth metrics
        revenue_growth = info.get('revenueGrowth', 'N/A')
        earnings_growth = info.get('earningsGrowth', 'N/A')
        
        # Dividend information
        dividend_yield = info.get('dividendYield', 'N/A')
        if dividend_yield and isinstance(dividend_yield, float):
            dividend_yield = f"{dividend_yield * 100:.2f}%"
        
        return {
            'market_cap': formatted_market_cap,
            'pe_ratio': pe_ratio,
            'pb_ratio': pb_ratio,
            'debt_to_equity': debt_to_equity,
            'current_ratio': current_ratio,
            'roe': roe,
            'roa': roa,
            'profit_margins': profit_margins,
            'operating_margins': operating_margins,
            'revenue_growth': revenue_growth,
            'earnings_growth': earnings_growth,
            'dividend_yield': dividend_yield,
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'beta': info.get('beta', 'N/A'),
            'free_cashflow': info.get('freeCashflow', 'N/A'),
            'total_debt': info.get('totalDebt', 'N/A')
        }
    except Exception as e:
        print(f"Error getting fundamentals for {ticker}: {e}")
        return {'error': str(e)}

def format_market_cap(market_cap):
    """Format market cap in Indian notation (Cr, Lakh Cr)"""
    if not market_cap or market_cap == 'N/A':
        return 'N/A'
    
    # Convert to Indian Rupees (assuming market cap is in INR from yfinance)
    if market_cap >= 1e12:  # More than 1 lakh crore
        return f"₹{market_cap/1e12:.2f} Lakh Cr"
    elif market_cap >= 1e7:  # More than 1 crore
        return f"₹{market_cap/1e7:.2f} Cr"
    else:
        return f"₹{market_cap:,.0f}"

def get_indian_sector_performance():
    """Get performance of major Indian sectors"""
    sector_etfs = {
        'Nifty Bank': '^NSEBANK',
        'Nifty IT': '^CNXIT',
        'Nifty Pharma': '^CNXPHARMA',
        'Nifty Auto': '^CNXAUTO',
        'Nifty FMCG': '^CNXFMCG',
        'Nifty Metal': '^CNXMETAL',
        'Nifty Realty': '^CNXREALTY'
    }
    
    sector_data = []
    for sector_name, sector_ticker in sector_etfs.items():
        try:
            df = yf.download(sector_ticker, period='1d')
            if not df.empty:
                change = ((df['Close'].iloc[-1] - df['Open'].iloc[0]) / df['Open'].iloc[0]) * 100
                sector_data.append({
                    'Sector': sector_name,
                    'Change %': f"{change:.2f}%",
                    'Status': '📈' if change > 0 else '📉'
                })
        except:
            continue
    
    return sector_data