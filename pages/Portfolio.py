import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import yfinance as yf

PORTFOLIO_FILE = "portfolio.json"
TRANSACTION = "transactions.json"

def load_portfolio(FILE):
    """Load portfolio from JSON safely."""
    if not os.path.exists(FILE):
        return []

    try:
        with open(FILE, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        return []


def save_portfolio(portfolio):
    """Save portfolio to JSON file."""
    with open("portfolio.json", "w") as f:
        json.dump(portfolio, f, indent=4)

def save_transactions(transactions):
    """Save portfolio to JSON file."""
    with open("transactions.json", "w") as f:
        json.dump(transactions, f, indent=4)

import yfinance as yf

def fetch_prices(tickers):
    """Fetch live/last close prices for NSE/BSE tickers."""
    prices = {}

    index_map = {
        "NIFTY_50": "^NSEI",
        "NIFTY50": "^NSEI",
        "NIFTY": "^NSEI",
        "NIFTY BANK": "^NSEBANK",
        "BANKNIFTY": "^NSEBANK",
    }

    for symbol in tickers:
        key = symbol.upper().strip()

        try:
            # If the symbol is a known index
            if key in index_map:
                yf_symbol = index_map[key]
                ticker = yf.Ticker(yf_symbol)
                data = ticker.history(period="1d")
                prices[symbol] = float(data["Close"].iloc[-1]) if not data.empty else None
                continue

            # Try NSE first
            ticker_nse = yf.Ticker(key + ".NS")
            data_nse = ticker_nse.history(period="1d")

            if not data_nse.empty:
                prices[symbol] = float(data_nse["Close"].iloc[-1])
                continue

            # Fallback → Try BSE
            ticker_bse = yf.Ticker(key + ".BO")
            data_bse = ticker_bse.history(period="1d")

            if not data_bse.empty:
                prices[symbol] = float(data_bse["Close"].iloc[-1])
            else:
                prices[symbol] = None

        except Exception:
            prices[symbol] = None

    return prices


def portfolio_page():
    """Main portfolio page function."""
    
    st.title("📊 My Investment Portfolio")

    # Add Stock Button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Expense Tracker", key="exp_tr_btn", use_container_width=True):
            st.session_state.current_page = "Extr"
            st.rerun()
    with col2:
        if st.button("SIP Calculator", key = "sip_calc_btn", use_container_width = True):
            st.session_state.current_page = "SIP"
            st.rerun()
    with col3:
        if st.button("Tax Calculator",  key = "tax_calc_btn", use_container_width = True):
            st.session_state.current_page = "Tax"
            st.rerun()

    # Load saved portfolio
    portfolio = load_portfolio(PORTFOLIO_FILE)
    transactions = load_portfolio(TRANSACTION)

    # Handle empty portfolio early
    if not portfolio:
        st.info("Your portfolio is empty. Add assets to see them here.")
        return

    tickers = [item["ticker"] for item in portfolio]

    # Fetch live prices
    with st.spinner("Fetching latest prices..."):
        live_prices = fetch_prices(tickers)

    # Calculate totals
    total_invested = 0
    total_value = 0
    
    for asset in portfolio:
        ticker = asset["ticker"]
        live_price = live_prices.get(ticker, 0) or 0
        value = asset["quantity"] * live_price
        total_invested += asset["quantity"] * asset["price"]
        total_value += value

    # Display summary metrics
    st.caption(f"Last updated: **{datetime.now().strftime('%d %b %Y, %I:%M %p')}**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Invested", f"₹{total_invested:,.2f}")
    col2.metric("Current Value", f"₹{total_value:,.2f}")
    
    net_pl = total_value - total_invested
    pl_percent = (net_pl / total_invested * 100) if total_invested > 0 else 0
    col3.metric("Net P/L", f"₹{net_pl:,.2f}", delta=f"{pl_percent:.1f}%")

    st.divider()

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1: st.subheader("📦 Your Holdings")
    with col2: 
        if st.button("➕ Add Stock", key="add_stock_btn", type="primary", use_container_width=True):
            st.session_state.current_page = "AddStock"
            st.rerun()
    with col3:
        if st.button("🔄 Refresh Prices", use_container_width=True):
            st.rerun()

    # Initialize session state for selling
    if 'selling_stock' not in st.session_state:
        st.session_state.selling_stock = None

    # Display each stock as an interactive card/button
    for i, asset in enumerate(portfolio):
        ticker = asset["ticker"]
        qty = asset["quantity"]
        buy_price = asset["price"]
        live_price = live_prices.get(ticker, 0) or 0
        
        value = qty * live_price
        invested = qty * buy_price
        pnl = value - invested
        pnl_percent = (pnl / invested * 100) if invested > 0 else 0
        
        # Create a container for each stock
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                st.markdown(f"### {ticker}")
                if 'name' in asset:
                    st.caption(asset['name'])
            
            with col2:
                st.metric(
                    "Current Value", 
                    f"₹{value:,.2f}",
                    delta=f"{pnl_percent:+.1f}%"
                )
            
            with col3:
                st.markdown(f"**Quantity:** {qty:,} shares")
                st.markdown(f"**Avg Buy Price:** ₹{buy_price:,.2f}")
                st.markdown(f"**Current Price:** ₹{live_price:,.2f}")
            
            with col4:
                if st.button("💰 Sell", key=f"sell_btn_{i}", use_container_width=True):
                    st.session_state.selling_stock = i
                    st.rerun()
        
        # Show sell form if this stock is selected for selling
        if st.session_state.selling_stock == i:
            with st.container(border=True):
                st.markdown(f"### 💰 Sell {ticker}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    max_qty = asset["quantity"]
                    sell_qty = st.number_input(
                        "Quantity to Sell",
                        min_value=1,
                        max_value=max_qty,
                        value=1,
                        step=1,
                        key=f"sell_qty_{i}"
                    )
                
                with col2:
                    sell_price = st.number_input(
                        "Sell Price (₹)",
                        min_value=0.0,
                        value=float(live_price) if live_price else buy_price,
                        step=1.0,
                        format="%.2f",
                        key=f"sell_price_{i}"
                    )
                
                with col3:
                    sell_date = st.date_input(
                        "Sell Date",
                        datetime.today(),
                        key=f"sell_date_{i}"
                    )
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    if st.button("✅ Confirm Sale", type="primary", key=f"confirm_sell_{i}"):
                        # Calculate sale proceeds
                        sale_amount = sell_qty * sell_price
                        
                        # Update portfolio
                        if sell_qty == max_qty:
                            # Remove stock entirely
                            portfolio.pop(i)
                            transactions.append({
                                'ticker': asset['ticker'],
                                'name': asset['name'],
                                'quantity': sell_qty,
                                'price': sell_price,
                                'date': sell_date.strftime("%Y-%m-%d"),
                                'Type': 'Sell'
                            })
                        else:
                            # Reduce quantity
                            portfolio[i]["quantity"] -= sell_qty
                            transactions.append({
                                'ticker': asset['ticker'],
                                'name': asset['name'],
                                'quantity': sell_qty,
                                'price': sell_price,
                                'date': sell_date.strftime("%Y-%m-%d"),
                                'Type': 'Sell'
                            })
                        
                        # Save changes
                        save_portfolio(portfolio)
                        save_transactions(transactions)
                        # Show success message
                        st.success(f"Sold {sell_qty} shares of {ticker} for ₹{sale_amount:,.2f}")
                        st.balloons()
                        
                        # Reset selling state
                        st.session_state.selling_stock = None
                        st.rerun()
                
                with col3:
                    if st.button("❌ Cancel", key=f"cancel_sell_{i}"):
                        st.session_state.selling_stock = None
                        st.rerun()
                
                # Show sale summary
                st.info(f"""
                **Sale Summary:**
                - Selling: {sell_qty} of {max_qty} shares
                - Sale Value: ₹{sell_qty * sell_price:,.2f}
                - Remaining: {max_qty - sell_qty} shares
                """)

    # If selling is active but no specific stock, show message
    if st.session_state.selling_stock is not None and st.session_state.selling_stock >= len(portfolio):
        st.session_state.selling_stock = None

    # Also show traditional table view in expander
    with st.expander("📋 View as Table"):
        rows = []
        for asset in portfolio:
            ticker = asset["ticker"]
            qty = asset["quantity"]
            buy_price = asset["price"]
            live_price = live_prices.get(ticker)
            safe_price = live_price if live_price is not None else 0
            value = qty * safe_price
            invested = qty * buy_price
            pnl = value - invested
            
            rows.append({
                "Ticker": ticker,
                "Quantity": qty,
                "Buy Price": round(buy_price, 2),
                "Live Price": round(safe_price, 2) if live_price is not None else "N/A",
                "Value": round(value, 2),
                "P/L": round(pnl, 2),
                "P/L %": f"{(pnl/invested*100):.1f}%" if invested > 0 else "N/A"
            })
        
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No holdings to display")
            
