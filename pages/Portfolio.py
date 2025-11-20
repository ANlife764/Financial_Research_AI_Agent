# pages/portfolio.py
import streamlit as st
import pandas as pd

def portfolio_page():
    st.header("💼 My Investment Portfolio")
    
    # Portfolio Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Value", "₹5,42,680", "+2.4%")
    with col2:
        st.metric("Today's Gain", "₹12,450", "+1.8%")
    with col3:
        st.metric("Unrealized P&L", "₹84,230", "+15.6%")
    with col4:
        st.metric("Risk Score", "Medium", "Stable")
    
    # Portfolio Holdings
    st.subheader("📦 Your Holdings")
    
    holdings_data = {
        'Stock': ['RELIANCE', 'TCS', 'HDFC Bank', 'Infosys', 'ICICI Bank'],
        'Quantity': [25, 40, 60, 80, 100],
        'Avg Price': ['2,450', '3,200', '1,480', '1,520', '780'],
        'Current Price': ['2,845', '3,812', '1,542', '1,645', '1,085'],
        'P&L': ['+9,875', '+24,480', '+3,720', '+10,000', '+30,500'],
        'P&L %': ['+16.1%', '+19.1%', '+4.2%', '+8.2%', '+39.1%']
    }
    
    st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)
    
    # Add Stock to Portfolio
    st.subheader("➕ Add Investment")
    
    with st.form("add_investment"):
        col1, col2, col3 = st.columns(3)
        with col1:
            stock = st.selectbox("Stock", ["RELIANCE.NS", "TCS.NS", "INFY.NS"])
        with col2:
            quantity = st.number_input("Quantity", min_value=1)
        with col3:
            buy_price = st.number_input("Buy Price (₹)", min_value=0.0)
        
        if st.form_submit_button("Add to Portfolio"):
            st.success(f"Added {quantity} shares of {stock} to portfolio!")
    
    # Portfolio Allocation
    st.subheader("📊 Portfolio Allocation")
    
    allocation_data = {
        'Sector': ['Technology', 'Banking', 'Energy', 'Healthcare', 'Automobile'],
        'Allocation %': [35, 25, 20, 12, 8],
        'Performance': ['+12.5%', '+8.2%', '+15.3%', '+5.6%', '-2.1%']
    }
    
    st.dataframe(pd.DataFrame(allocation_data), use_container_width=True)