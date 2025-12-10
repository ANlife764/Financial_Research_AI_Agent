import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import yfinance as yf

PORTFOLIO_FILE = "portfolio.json"
TRANSACTION = "transactions.json"

def load_portfolio(FILE):
    """Load portfolio from JSON file"""
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_portfolio(portfolio):
    """Save portfolio to JSON file"""
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=2)

def save_transactions(transactions):
    with open(TRANSACTION, "w") as f:
        json.dump(transactions, f, indent=2)

def search_stocks_yfinance(query, exchange='auto'):
    """Search for stocks using yfinance - supports both NSE and BSE"""
    try:
        # If exchange is 'auto', try both NSE and BSE
        if exchange == 'auto':
            # Try NSE first
            nse_ticker = yf.Ticker(f"{query.upper()}.NS")
            nse_info = nse_ticker.info
            
            if 'symbol' in nse_info and nse_info['symbol'].endswith('.NS'):
                return [{
                    'symbol': nse_info['symbol'].replace('.NS', ''),
                    'name': nse_info.get('longName', nse_info.get('shortName', query.upper())),
                    'exchange': 'NSE'
                }]
            
            # If NSE not found, try BSE
            bse_ticker = yf.Ticker(f"{query.upper()}.BO")
            bse_info = bse_ticker.info
            
            if 'symbol' in bse_info and bse_info['symbol'].endswith('.BO'):
                return [{
                    'symbol': bse_info['symbol'].replace('.BO', ''),
                    'name': bse_info.get('longName', bse_info.get('shortName', query.upper())),
                    'exchange': 'BSE'
                }]
    except Exception as e:
        st.error(f"Error searching: {e}")
    
    return []

def get_current_price(symbol, exchange='NSE'):
    try:
        # Detect index tickers (NIFTY, BANKNIFTY)
        index_map = {
            "NIFTY_50": "^NSEI",
            "NIFTY50": "^NSEI",
            "NIFTY": "^NSEI",
            "NIFTY BANK": "^NSEBANK",
            "BANKNIFTY": "^NSEBANK"
        }

        if symbol.upper() in index_map:
            ticker = yf.Ticker(index_map[symbol.upper()])
        else:
            suffix = ".NS" if exchange == "NSE" else ".BO"
            ticker = yf.Ticker(symbol + suffix)

        data = ticker.history(period="1d")

        if not data.empty:
            return float(data["Close"].iloc[-1])

        return 0

    except Exception as e:
        print("Error:", e)
        return 0

def add_stock_page():
    st.title("➕ Add Stock to Portfolio")
    
    # Load portfolio
    portfolio = load_portfolio(PORTFOLIO_FILE)
    transaction = load_portfolio(TRANSACTION)
    
    # Initialize selected stock
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None
    
    # === SEARCH SECTION ===
    st.subheader("Search Stock")
    
    # Search input
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "Enter stock symbol:",
            placeholder="e.g., 'RELIANCE' or '500325'",
            key="search_input"
        )
    
    with col2:
        st.write("")
        search_clicked = st.button("🔍 Search", type="primary")
    
    # Perform search
    if search_clicked and search_query.strip():
        query = search_query.strip().upper()
        
        # Search using yfinance with selected exchange
        found_stocks = search_stocks_yfinance(query, 'auto')
        
        if found_stocks:
            st.session_state.search_results = found_stocks
            st.session_state.search_query = query
        else:
            st.error(f"No stock found for symbol '{query}'")
            st.session_state.search_results = []
    
    # Display search results
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.write(f"**Search results for '{st.session_state.search_query}':**")
        
        for stock in st.session_state.search_results:
            button_text = f"**{stock['symbol']}** ({stock['exchange']}) - {stock['name'][:60]}..."
            if st.button(button_text, key=f"btn_{stock['symbol']}_{stock['exchange']}"):
                st.session_state.selected_stock = stock
                st.rerun()
    
    # === SELECTED STOCK ===
    if st.session_state.selected_stock:
        selected = st.session_state.selected_stock
        
        st.divider()
        st.subheader(f"Selected: {selected['symbol']}")
        st.write(f"*{selected['name']}*")
        st.write(f"**Exchange:** {selected.get('exchange', 'NSE')}")
        
        # Show current price
        exchange = selected.get('exchange', 'NSE')
        current_price = get_current_price(selected['symbol'], exchange)
        if current_price > 0:
            st.info(f"Current Price: **₹{current_price:,.2f}**")
        else:
            st.warning("Current price not available")
        
        # === PURCHASE DETAILS ===
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quantity = st.number_input("Quantity", min_value=1, value=10)
        
        with col2:
            buy_price = st.number_input("Buy Price (₹)", min_value=0.0, 
                                       value=float(current_price) if current_price > 0 else 100.0,
                                       format="%.2f")
        
        with col3:
            buy_date = st.date_input("Date", datetime.today())
        
        # Add exchange to saved data
        if st.button("✅ Add to Portfolio", type="primary"):
            portfolio.append({
                'ticker': selected['symbol'],
                'name': selected['name'],
                'quantity': quantity,
                'price': buy_price,
                'date': buy_date.strftime("%Y-%m-%d"),
                'Type': 'Buy'
            })
            transaction.append({
                'ticker': selected['symbol'],
                'name': selected['name'],
                'quantity': quantity,
                'price': buy_price,
                'date': buy_date.strftime("%Y-%m-%d"),
                'Type': 'Buy'
                
            })
            
            save_portfolio(portfolio)
            save_transactions(transaction)
            st.success(f"Added {quantity} shares of {selected['symbol']} ({selected.get('exchange', 'NSE')})!")
            st.session_state.selected_stock = None
            st.session_state.search_results = []
            st.rerun()
        
        if st.button("❌ Cancel"):
            st.session_state.selected_stock = None
            st.rerun()
    
    # Back button
    st.divider()
    if st.button("← Back to Portfolio"):
        st.session_state.current_page = "Portfolio"
        st.rerun()

if __name__ == "__main__":
    add_stock_page()