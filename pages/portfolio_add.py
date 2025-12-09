import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd
import yfinance as yf

PORTFOLIO_FILE = "portfolio.json"
TRANSACTION = "transactions.json"
STOCKS_CSV_FILE = "D:\Financial_Research_AI_Agent\EQUITY_L.csv"

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


def load_stocks_from_csv():
    """Load all Indian stocks from CSV file - SIMPLE VERSION"""
    try:
        # Load CSV without any filtering
        df = pd.read_csv(STOCKS_CSV_FILE)
                
        # Try to find symbol and name columns
        symbol_col = None
        name_col = None
        
        for col in df.columns:
            if 'SYMBOL' in col.upper():
                symbol_col = col
            if 'NAME' in col.upper():
                name_col = col
        
       
        if symbol_col and name_col:
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'symbol': str(row[symbol_col]).strip(),
                    'name': str(row[name_col]).strip()
                })
            return stocks
        else:
            st.error("Could not find SYMBOL and NAME columns in CSV")
            return []
            
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return []

def get_current_price(symbol):
    """Get current price using yfinance"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info
        price = info.get('currentPrice') or info.get('regularMarketPrice')
        return float(price) if price else 0
    except:
        return 0

def add_stock_page():
    st.title("➕ Add Stock to Portfolio")
    
    # Load portfolio
    portfolio = load_portfolio(PORTFOLIO_FILE)
    transaction = load_portfolio(TRANSACTION)
    
    # Load stocks from CSV (show what we're getting)
    if 'all_stocks' not in st.session_state:
        st.session_state.all_stocks = load_stocks_from_csv()
    
    # Initialize selected stock
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None
    
    # === SEARCH SECTION ===
    st.subheader("Search Stock")
    
    # Search input
    search_query = st.text_input(
        "Type company name or symbol:",
        placeholder="e.g., 'Reliance', 'TCS', 'HDFC'",
        key="search_input",
        value=""
    )
    
    # Filter and display stocks
    if search_query and len(search_query) >= 2:
        query = search_query.upper()
        
        filtered_stocks = []
        for stock in st.session_state.all_stocks:
            if (query in stock['symbol'].upper() or 
                query in stock['name'].upper()):
                filtered_stocks.append(stock)
        
        if filtered_stocks:
            st.write(f"**Found {len(filtered_stocks)} matches:**")
            
            # Display as simple list
            for stock in filtered_stocks[:20]:  # Show first 20
                if st.button(f"**{stock['symbol']}** - {stock['name'][:50]}...", 
                           key=f"btn_{stock['symbol']}"):
                    st.session_state.selected_stock = stock
                    st.rerun()
        else:
            st.info(f"No stocks found for '{search_query}'")
    
    # === SELECTED STOCK ===
    if st.session_state.selected_stock:
        selected = st.session_state.selected_stock
        
        st.divider()
        st.subheader(f"Selected: {selected['symbol']}")
        st.write(f"*{selected['name']}*")
        
        # Show current price
        current_price = get_current_price(selected['symbol'])
        if current_price > 0:
            st.info(f"Current Price: **₹{current_price:,.2f}**")
        
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
        
        # Add button
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
            st.success(f"Added {quantity} shares of {selected['symbol']}!")
            st.session_state.selected_stock = None
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