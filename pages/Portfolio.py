# pages/portfolio.py
import streamlit as st
import pandas as pd
import numpy as np # Needed for np.where and np.abs
from datetime import date
from utils.portfolio_calc import (
    calculate_sip_future_value,
    calculate_monthly_sip_required,
    calculate_capital_gains
)

# Define categories for expense/income tracking
TRANSACTION_CATEGORIES = ["Investment", "Income", "Rent", "Food", "Utilities", "Travel", "Misc"]


# =========================================================================
# === STATE MANAGEMENT & HELPER FUNCTIONS ===
# =========================================================================

def initialize_portfolio_state():
    """Initialize or load the dynamic transaction history."""
    if 'transactions_df' not in st.session_state:
        # Columns for all transactions (Buy/Sell/Expense/Income)
        st.session_state.transactions_df = pd.DataFrame(
            columns=['Date', 'Type', 'Category', 'Ticker', 'Quantity', 'Price', 'Amount']
        )

def clear_transactions():
    """Wipes the transaction history from the session state."""
    st.session_state.transactions_df = pd.DataFrame(
        columns=['Date', 'Type', 'Category', 'Ticker', 'Quantity', 'Price', 'Amount']
    )
    st.info("Transaction history cleared. Please re-enter trades.")

def add_transaction(data):
    """Appends a new transaction to the session state dataframe."""
    new_tx = pd.DataFrame([data])
    st.session_state.transactions_df = pd.concat([st.session_state.transactions_df, new_tx], ignore_index=True)
    st.success(f"Transaction recorded successfully!")
    st.rerun()

def get_current_holdings():
    """Calculates current holdings (Quantity, Avg Price) from the transaction history."""
    
    investment_tx = st.session_state.transactions_df[
        st.session_state.transactions_df['Type'].isin(['Buy', 'Sell'])
    ].copy()
    
    # Ensure numeric columns are treated as such for aggregation
    for col in ['Quantity', 'Amount']:
        investment_tx[col] = pd.to_numeric(investment_tx[col], errors='coerce')
    
    if investment_tx.empty:
        # Return a DataFrame with the expected columns, even if empty
        return pd.DataFrame(columns=['Ticker', 'Quantity', 'Avg Price', 'Current Price', 'P&L', 'P&L %'])

    # Aggregate net quantity and net cost (which can be negative)
    holdings = investment_tx.groupby('Ticker').agg(
        net_quantity=('Quantity', 'sum'),
        net_cost=('Amount', 'sum')
    ).reset_index()

    # Filter out holdings where net quantity is zero (fully sold)
    holdings = holdings[holdings['net_quantity'] != 0].copy()
    
    # 🛑 FIX for Negative Prices: Calculate Avg Price using the absolute value of the cost basis (net_cost)
    # This prevents negative prices if realized profits exceed capital invested.
    holdings['Avg Price'] = holdings['net_cost'].abs() / holdings['net_quantity'].abs()
    
    holdings.rename(columns={'net_quantity': 'Quantity', 'net_cost': 'total_cost'}, inplace=True)
    
    # Placeholder for current price lookup 
    holdings['Current Price'] = holdings['Avg Price'] * 1.10
    holdings['P&L'] = (holdings['Current Price'] - holdings['Avg Price']) * holdings['Quantity']
    
    # FIX for ZeroDivisionError: Use np.where
    holdings['P&L %'] = np.where(
        holdings['total_cost'] == 0,
        0,
        (holdings['P&L'] / holdings['total_cost']) * 100
    )
    
    # Clean up and format for display
    holdings = holdings[['Ticker', 'Quantity', 'Avg Price', 'Current Price', 'P&L', 'P&L %']]
    return holdings.round(2)

# =========================================================================
# === MAIN PAGE FUNCTION ===
# =========================================================================

def portfolio_page():
    initialize_portfolio_state()
    st.title("💼 AI Financial Portfolio & Planning")
    
    # --- Create Tabs for Organization ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Portfolio Tracker", 
        "📈 SIP & Goals", 
        "💸 Expense Tracker", 
        "⚖️ Tax Calculations"
    ])

    # ---------------------------------------------------------------------
    # TAB 1: PORTFOLIO TRACKER
    # ---------------------------------------------------------------------
    with tab1:
        st.header("Simple Portfolio Tracker")
        
        # TEMPORARY: Clear data button
        if st.button("🔴 Clear ALL Transaction History", help="Clears all data to re-test calculations. REMOVE THIS BUTTON LATER."):
            clear_transactions()
            st.rerun() 
            
        current_holdings = get_current_holdings()

        # Dynamic Summary 
        col1, col2, col3, col4 = st.columns(4)
        
        # Check if empty *before* trying to calculate sum or access columns
        is_empty = current_holdings.empty
        total_value = (current_holdings['Current Price'] * current_holdings['Quantity']).sum() if not is_empty else 0
        total_pnl = current_holdings['P&L'].sum() if not is_empty else 0
        total_quantity = current_holdings['Quantity'].sum() if not is_empty else 0
        
        with col1: st.metric("Total Value", f"₹{total_value:,.0f}", "+0.0%")
        with col2: st.metric("Unrealized P&L", f"₹{total_pnl:,.0f}", "+0.0%")
        with col3: st.metric("Total Investments", f"{total_quantity:,.0f}", "Shares")
        with col4: st.metric("Risk Score", "Medium", "Stable")
        
        # Portfolio Holdings Display
        st.subheader("📦 Your Holdings")
        if is_empty:
            st.info("No investment transactions recorded yet. Use the form below to add one!")
        else:
            st.dataframe(current_holdings, use_container_width=True)
            
        # Add Transaction Form (Now handles all types)
        st.subheader("➕ Record Investment/Trade")
        with st.form("record_trade_form"):
            col_tx1, col_tx2, col_tx3 = st.columns(3)
            tx_date = col_tx1.date_input("Date", date.today())
            tx_type = col_tx2.selectbox("Transaction Type", ["Buy", "Sell"])
            ticker = col_tx3.text_input("Ticker (e.g., RELIANCE.NS)", value="", max_chars=20).upper()
            
            col_qty, col_price = st.columns(2)
            quantity = col_qty.number_input("Quantity", min_value=1, step=1)
            price = col_price.number_input("Price / Unit (₹)", min_value=0.01)
            
            if st.form_submit_button("Record Trade"):
                data = {
                    'Date': tx_date, 'Type': tx_type, 'Category': "Investment", 
                    'Ticker': ticker, 'Quantity': quantity, 'Price': price, 
                    'Amount': quantity * price if tx_type == 'Buy' else -quantity * price # Ensure Sell is negative
                }
                add_transaction(data)

    # ---------------------------------------------------------------------
    # TAB 2: SIP & GOALS
    # ---------------------------------------------------------------------
    with tab2:
        st.header("SIP & Goal Planning")
        
        # SIP Calculator
        st.subheader("Systematic Investment Plan (SIP) Calculator")
        with st.form("sip_form"):
            sip_amount = st.number_input("Monthly SIP Amount (₹)", min_value=100.0, value=5000.0, step=100.0)
            sip_return = st.slider("Expected Annual Return (%)", min_value=5.0, max_value=25.0, value=12.0, step=0.5)
            sip_years = st.slider("Investment Duration (Years)", min_value=1, max_value=40, value=15)
            
            if st.form_submit_button("Calculate Future Value"):
                future_value = calculate_sip_future_value(sip_amount, sip_return, sip_years)
                st.metric("Estimated Future Value", f"₹{future_value:,.0f}")
                
        st.markdown("---")
        
        # Goal-Based Investment
        st.subheader("Goal-Based Investment Suggestions")
        with st.form("goal_form"):
            goal_amount = st.number_input("Goal Amount Needed (₹)", min_value=1000.0, value=500000.0, step=1000.0)
            goal_return = st.slider("Expected Annual Return (%)", min_value=5.0, max_value=25.0, value=12.0, step=0.5, key='g_ret')
            goal_years = st.slider("Goal Timeline (Years)", min_value=1, max_value=40, value=10, key='g_years')
            
            if st.form_submit_button("Calculate Required SIP"):
                required_sip = calculate_monthly_sip_required(goal_amount, goal_return, goal_years)
                st.success(f"To reach **₹{goal_amount:,.0f}** in {goal_years} years, you need to invest a monthly SIP of:")
                st.metric("Required Monthly SIP", f"₹{required_sip:,.0f}")

    # ---------------------------------------------------------------------
    # TAB 3: EXPENSE TRACKER
    # ---------------------------------------------------------------------
    with tab3:
        st.header("💸 Expense Tracking with Categories")
        
        # Add Expense/Income Form
        st.subheader("➕ Record Expense or Income")
        with st.form("record_expense_form"):
            col_exp1, col_exp2 = st.columns(2)
            exp_date = col_exp1.date_input("Date", date.today(), key='exp_date')
            exp_type = col_exp2.selectbox("Type", ["Expense", "Income"])
            
            col_exp3, col_exp4 = st.columns(2)
            exp_category = col_exp3.selectbox("Category", TRANSACTION_CATEGORIES)
            exp_amount = col_exp4.number_input("Amount (₹)", min_value=0.01)
            
            if st.form_submit_button("Record Expense/Income"):
                data = {
                    'Date': exp_date, 'Type': exp_type, 'Category': exp_category, 
                    'Ticker': '', 'Quantity': 0, 'Price': 0.0, 
                    'Amount': exp_amount
                }
                add_transaction(data)
                
        st.markdown("---")
        
        # Display and summarize expenses
        expense_df = st.session_state.transactions_df[
            st.session_state.transactions_df['Type'].isin(["Expense", "Income"])
        ].copy()
        
        st.subheader("Summary by Category")
        if not expense_df.empty:
            expense_summary = expense_df.groupby(['Type', 'Category'])['Amount'].sum().reset_index()
            expense_summary['Amount'] = expense_summary.apply(
                lambda row: row['Amount'] if row['Type'] == 'Income' else -row['Amount'], axis=1
            )
            st.dataframe(expense_summary.style.format({'Amount': '₹{:,.2f}'}), use_container_width=True)
        else:
            st.info("No expense or income transactions recorded yet.")

    # ---------------------------------------------------------------------
    # TAB 4: TAX CALCULATIONS
    # ---------------------------------------------------------------------
    with tab4:
        st.header("⚖️ Indian Tax Implications (LTCG/STCG)")
        
        if st.button("Calculate Capital Gains"):
            investment_tx = st.session_state.transactions_df[
                st.session_state.transactions_df['Type'].isin(["Buy", "Sell"])
            ].copy()
            
            if not investment_tx.empty:
                try:
                    gains_df, tax_summary = calculate_capital_gains(investment_tx)
                    
                    st.subheader("Realized Gains Breakdown")
                    st.dataframe(gains_df, use_container_width=True)

                    st.subheader("Tax Liability Summary (Simplified Equity Rules)")
                    
                    col_stcg, col_ltcg, col_total = st.columns(3)
                    col_stcg.metric("STCG Tax Payable (15%)", f"₹{tax_summary['STCG Tax (15%)']:,.0f}")
                    col_ltcg.metric("LTCG Tax Payable (10%)", f"₹{tax_summary['LTCG Tax (10%)']:,.0f}")
                    
                    col_total.metric("Total Tax Payable", f"₹{tax_summary['Total Tax Payable']:,.0f}")

                except Exception as e:
                    st.error(f"Error during tax calculation: {e}. Ensure you have matching Buy/Sell transactions.")
            else:
                st.warning("Please record some 'Buy' and 'Sell' transactions to calculate capital gains.")