# pages/portfolio.py
import streamlit as st
import pandas as pd
import numpy as np 
from datetime import date
from utils.portfolio_calc import (
    calculate_sip_future_value,
    calculate_monthly_sip_required,
    calculate_capital_gains
)
from utils.stock_data import get_ltp_and_change, search_ticker_symbols 


# Define categories for expense/income tracking
TRANSACTION_CATEGORIES = ["Investment", "Income", "Rent", "Food", "Utilities", "Travel", "Misc"]


# =========================================================================
# === STATE MANAGEMENT & HELPER FUNCTIONS ===
# =========================================================================

def initialize_portfolio_state():
    """Initialize or load the dynamic transaction history."""
    if 'transactions_df' not in st.session_state:
        dtype_map = {
            'Date': 'object', 'Type': 'object', 'Category': 'object', 
            'Ticker': 'object', 'Quantity': np.float64, 'Price': np.float64, 
            'Amount': np.float64
        }
        st.session_state.transactions_df = pd.DataFrame(
            columns=dtype_map.keys()
        ).astype(dtype_map)
        
    if 'prefill_ticker' in st.session_state:
        del st.session_state.prefill_ticker
    if 'prefill_type' in st.session_state:
        del st.session_state.prefill_type


def clear_transactions():
    """Wipes the transaction history from the session state."""
    dtype_map = {
        'Date': 'object', 'Type': 'object', 'Category': 'object', 
        'Ticker': 'object', 'Quantity': np.float64, 'Price': np.float64, 
        'Amount': np.float64
    }
    st.session_state.transactions_df = pd.DataFrame(
        columns=dtype_map.keys()
    ).astype(dtype_map)
    st.info("Transaction history cleared. Please re-enter trades.")

def add_transaction(data):
    """Appends a new transaction to the session state dataframe."""
    
    if data['Type'] == 'Sell':
        data['Quantity'] = -data['Quantity']
        
    new_tx = pd.DataFrame([data])
    st.session_state.transactions_df = pd.concat([st.session_state.transactions_df, new_tx], ignore_index=True)
    st.success(f"Transaction recorded successfully!")
    st.rerun()

def get_current_holdings():
    """Calculates current holdings (Quantity, Avg Price, LTP, Color) from the transaction history."""
    
    investment_tx = st.session_state.transactions_df[
        st.session_state.transactions_df['Type'].isin(['Buy', 'Sell'])
    ].copy()
    
    for col in ['Quantity', 'Amount']:
        investment_tx[col] = pd.to_numeric(investment_tx[col], errors='coerce')
    
    if investment_tx.empty:
        return pd.DataFrame(columns=['Ticker', 'Quantity', 'Avg Price', 'Current Price', 'P&L', 'P&L %', 'Color', 'Arrow'])

    holdings = investment_tx.groupby('Ticker').agg(
        net_quantity=('Quantity', 'sum'),
        net_cost=('Amount', 'sum')
    ).reset_index()

    holdings = holdings[holdings['net_quantity'] != 0].copy()
    
    holdings['Avg Price'] = holdings['net_cost'].abs() / holdings['net_quantity'].abs()
    
    holdings.rename(columns={'net_quantity': 'Quantity', 'net_cost': 'total_cost'}, inplace=True)
    
    # --- FETCH LTP and COLOR/ARROW (Relies on utils/stock_data.py) ---
    ltp_data = [get_ltp_and_change(row['Ticker'], row['Avg Price']) for index, row in holdings.iterrows()]

    holdings['Current Price'] = [item[0] for item in ltp_data]
    holdings['Color'] = [item[1] for item in ltp_data]
    holdings['Arrow'] = [item[2] for item in ltp_data]
    # --- END LTP Integration ---

    holdings['P&L'] = (holdings['Current Price'] - holdings['Avg Price']) * holdings['Quantity']
    
    holdings['P&L %'] = np.where(
        holdings['total_cost'] == 0,
        0,
        (holdings['P&L'] / holdings['total_cost']) * 100
    )
    
    holdings = holdings[['Ticker', 'Quantity', 'Avg Price', 'Current Price', 'P&L', 'P&L %', 'Color', 'Arrow']]
    return holdings.round(2)
    
def get_expense_df():
    """Filters and formats the transaction history for the Expense Tracker view."""
    expense_df = st.session_state.transactions_df[
        st.session_state.transactions_df['Type'].isin(["Expense", "Income"])
    ].copy()

    if expense_df.empty:
        return pd.DataFrame(columns=['S.No.', 'Date', 'Tx Type', 'Category', 'Amount (₹)']) 

    # 1. Use the original DataFrame index as the stable ID
    expense_df = expense_df.reset_index().rename(columns={'index': 'ID'})
    
    # 2. Formatting columns for display
    expense_df['Date'] = pd.to_datetime(expense_df['Date']).dt.date
    expense_df['Amount (₹)'] = expense_df['Amount'].abs().round(2)
    expense_df.rename(columns={'Type': 'Tx Type', 'Category': 'Category'}, inplace=True)

    # 3. Add Serial Number (S.No.) and set it as the displayed index
    expense_df.index = np.arange(1, len(expense_df) + 1)
    
    # Return the formatted DataFrame
    return expense_df[['ID', 'Date', 'Tx Type', 'Category', 'Amount (₹)']]


def delete_expense_entry_by_s_no(s_no, expense_df):
    """Deletes an entry by its displayed Serial Number (S.No.)."""
    
    try:
        original_index_to_delete = expense_df.loc[s_no, 'ID']
        
        st.session_state.transactions_df.drop(original_index_to_delete, inplace=True)
        st.success(f"Entry {s_no} deleted successfully.")
        st.rerun()
        
    except KeyError:
        st.error(f"Error: Could not find entry with S.No. {s_no}. Please check the number.")


# =========================================================================
# === MAIN PAGE FUNCTION ===
# =========================================================================

def portfolio_page():
    initialize_portfolio_state()
    st.title("💼 AI Financial Portfolio & Planning")
    
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
        
        if st.button("🔴 Clear ALL Transaction History", help="Clears all data to re-test calculations. REMOVE THIS BUTTON LATER."):
            clear_transactions()
            st.rerun() 
            
        current_holdings = get_current_holdings()

        # Dynamic Summary 
        col1, col2, col3, col4 = st.columns(4)
        
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
            st.info("No investment transactions recorded yet.")
        else:
            
            # --- Holdings Display (LTP & Color Coded) ---
            
            cols = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 1.5]) 
            headers = ["Ticker", "Quantity", "Avg Price", "LTP", "P&L", "P&L %"]
            
            for col, header in zip(cols, headers):
                col.write(f"**{header}**")

            st.markdown("---") 

            for index, row in current_holdings.iterrows():
                
                cols = st.columns([1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
                ticker = row['Ticker']
                qty = int(row['Quantity'])
                
                ltp_color = row['Color']
                ltp_arrow = row['Arrow']
                
                # Display Holding Data
                cols[0].write(ticker)
                cols[1].write(qty)
                cols[2].write(f"₹{row['Avg Price']:,.2f}")
                
                # Display LTP with color coding and arrow
                cols[3].markdown(
                    f"<span style='color: {ltp_color}; font-weight: bold;'>{ltp_arrow} ₹{row['Current Price']:,.2f}</span>", 
                    unsafe_allow_html=True
                )
                
                cols[4].write(f"₹{row['P&L']:,.0f}")
                cols[5].write(f"{row['P&L %']:,.1f}%")
            
            st.markdown("---")
            # --- END Holdings Display ---


        # Add Transaction Form (The core of the transaction management)
        st.subheader("➕ Record Investment/Trade")
        
        with st.form("record_trade_form"):
            
            col_tx1, col_tx2, col_tx3 = st.columns(3)
            tx_date = col_tx1.date_input("Date", date.today(), key='tx_date')
            
            tx_type = col_tx2.selectbox("Transaction Type", ["Buy", "Sell"], key='tx_type_form')
            
            # --- Ticker Selection: Simple Text Input ---
            ticker = col_tx3.text_input("Ticker Symbol (e.g., RELIANCE.NS)", value="", max_chars=20, key='tx_ticker_search').upper()
            
            held_qty = 0 # Default held quantity
            current_held_tickers = current_holdings['Ticker'].tolist()

            # 4. Update held_qty for validation if selling the selected ticker
            if tx_type == 'Sell' and ticker in current_held_tickers:
                 held_qty = current_holdings[current_holdings['Ticker'] == ticker]['Quantity'].iloc[0]
            # --- End Ticker Selection Logic ---


            col_qty, col_price = st.columns(2) 
            qty_label = f"Quantity (Max Sell: {int(held_qty)})" if tx_type == 'Sell' else "Quantity"
            
            quantity = col_qty.number_input(qty_label, min_value=1, step=1, key='tx_qty')
            price = col_price.number_input("Price / Unit (₹)", min_value=0.01, key='tx_price')

            # --- Submission Logic with Validation Check ---
            if st.form_submit_button("Record Trade"):
                
                if not ticker or ticker == "N/A":
                    st.error("Please enter a Ticker Symbol.")
                    st.stop()
                    
                # VALIDATION CHECK: Prevent selling more than held
                if tx_type == 'Sell':
                    final_held_qty = current_holdings[current_holdings['Ticker'] == ticker]['Quantity'].sum() if ticker in current_held_tickers else 0
                    
                    if final_held_qty == 0:
                        st.error(f"Cannot sell {ticker}: You do not currently hold this stock.")
                        st.stop()
                    
                    if quantity > final_held_qty:
                        st.error(f"Cannot sell {quantity} shares of {ticker}. You only hold {final_held_qty} shares.")
                        st.stop()
                
                # If validation passes, process transaction:
                data = {
                    'Date': tx_date, 'Type': tx_type, 'Category': "Investment", 
                    'Ticker': ticker, 'Quantity': quantity, 'Price': price, 
                    'Amount': quantity * price
                }
                add_transaction(data)
                

    # ---------------------------------------------------------------------
    # TAB 2: SIP & GOALS
    # ---------------------------------------------------------------------
    with tab2:
        st.header("SIP & Goal Planning")
        
        st.subheader("Systematic Investment Plan (SIP) Calculator")
        with st.form("sip_form_tab2"):
            sip_amount = st.number_input("Monthly SIP Amount (₹)", min_value=100.0, value=5000.0, step=100.0, key='sip_amt_tab2')
            sip_return = st.slider("Expected Annual Return (%)", min_value=5.0, max_value=25.0, value=12.0, step=0.5, key='sip_ret_tab2')
            sip_years = st.slider("Investment Duration (Years)", min_value=1, max_value=40, value=15, key='sip_yrs_tab2')
            
            if st.form_submit_button("Calculate Future Value", key='sip_btn'):
                future_value = calculate_sip_future_value(sip_amount, sip_return, sip_years)
                st.metric("Estimated Future Value", f"₹{future_value:,.0f}")
                
        st.markdown("---")
        
        st.subheader("Goal-Based Investment Suggestions")
        with st.form("goal_form_tab2"):
            goal_amount = st.number_input("Goal Amount Needed (₹)", min_value=1000.0, value=500000.0, step=1000.0, key='goal_amt_tab2')
            goal_return = st.slider("Expected Annual Return (%)", min_value=5.0, max_value=25.0, value=12.0, step=0.5, key='g_ret_tab2')
            goal_years = st.slider("Goal Timeline (Years)", min_value=1, max_value=40, value=10, key='g_years_tab2')
            
            if st.form_submit_button("Calculate Required SIP", key='goal_btn'):
                required_sip = calculate_monthly_sip_required(goal_amount, goal_return, goal_years)
                st.success(f"To reach **₹{goal_amount:,.0f}** in {goal_years} years, you need to invest a monthly SIP of:")
                st.metric("Required Monthly SIP", f"₹{required_sip:,.0f}")

    # ---------------------------------------------------------------------
    # TAB 3: EXPENSE TRACKER (DELETE-ONLY BY S.NO.)
    # ---------------------------------------------------------------------
    with tab3:
        st.header("💸 Interactive Expense Tracker")
        
        col_form, col_summary = st.columns([1, 1])

        # --- Add Expense/Income Form ---
        with col_form.form("record_expense_form"):
            col_exp1, col_exp2 = st.columns(2)
            exp_date = col_exp1.date_input("Date", date.today(), key='exp_date')
            exp_type = col_exp2.selectbox("Type", ["Expense", "Income"], key='exp_type_form')
            
            exp_category = st.selectbox("Category", TRANSACTION_CATEGORIES, key='exp_cat_form')
            exp_amount = st.number_input("Amount (₹)", min_value=0.01, key='exp_amt')
            
            if st.form_submit_button("Record Expense/Income"):
                data = {
                    'Date': exp_date, 'Type': exp_type, 'Category': exp_category, 
                    'Ticker': '', 'Quantity': 0, 'Price': 0.0, 
                    'Amount': exp_amount
                }
                add_transaction(data)

        # --- Expense Table and Actions (Delete Only) ---
        expense_df = get_expense_df()

        with col_summary:
            st.subheader("Summary by Category")
            if not expense_df.empty:
                # Calculate Net Income/Expense for Summary
                expense_df['Signed Amount'] = expense_df.apply(
                    lambda row: row['Amount (₹)'] if row['Tx Type'] == 'Income' else -row['Amount (₹)'], axis=1
                )
                expense_summary = expense_df.groupby('Category')['Signed Amount'].sum().reset_index()
                
                # FIXED: Replaced use_container_width=True with width='stretch'
                st.dataframe(
                    expense_summary.style.format({'Signed Amount': '₹{:,.2f}'}), 
                    width='stretch', 
                    hide_index=True
                )
                st.metric("Net Flow", f"₹{expense_summary['Signed Amount'].sum():,.2f}")
            else:
                st.info("No expense or income transactions recorded yet.")


        if not expense_df.empty:
            
            st.subheader("Transaction History (S.No. based)")
            
            # FIXED: Replaced use_container_width=True with width='stretch'
            st.dataframe(
                expense_df.drop(columns=['ID']).rename_axis('S.No.'), 
                width='stretch', 
            )
            
            st.markdown("---")
            
            # --- DELETE BY S.NO. CONTROL ---
            st.subheader("Delete Entry")
            col_delete_select, col_delete_btn = st.columns([1, 3])
            
            s_no_options = expense_df.index.tolist()
            
            delete_index = col_delete_select.selectbox(
                "Select S.No. to delete:",
                options=[0] + s_no_options, 
                index=0,
                key='delete_select_index',
                format_func=lambda x: "--- Select ---" if x == 0 else str(x)
            )
            
            if delete_index > 0:
                
                row_to_confirm = expense_df.loc[delete_index]
                st.warning(f"Confirm deletion of entry {delete_index}: {row_to_confirm['Category']} - ₹{row_to_confirm['Amount (₹)']:.2f} on {row_to_confirm['Date']}.")

                if col_delete_btn.button(f"Confirm Delete S.No. {delete_index}", key='confirm_delete_btn'):
                    delete_expense_entry_by_s_no(delete_index, expense_df)


    # ---------------------------------------------------------------------
    # TAB 4: TAX CALCULATIONS
    # ---------------------------------------------------------------------
    with tab4:
        st.header("⚖️ Indian Tax Implications (LTCG/STCG)")
        
        if st.button("Calculate Capital Gains", key='tax_btn'):
            investment_tx = st.session_state.transactions_df[
                st.session_state.transactions_df['Type'].isin(["Buy", "Sell"])
            ].copy()
            
            if not investment_tx.empty:
                try:
                    gains_df, tax_summary = calculate_capital_gains(investment_tx)
                    
                    st.subheader("Realized Gains Breakdown")
                    # FIXED: Replaced use_container_width=True with width='stretch'
                    st.dataframe(gains_df, width='stretch')

                    st.subheader("Tax Liability Summary (Simplified Equity Rules)")
                    
                    col_stcg, col_ltcg, col_total = st.columns(3)
                    col_stcg.metric("STCG Tax Payable (15%)", f"₹{tax_summary['STCG Tax (15%)']:,.0f}")
                    col_ltcg.metric("LTCG Tax Payable (10%)", f"₹{tax_summary['LTCG Tax (10%)']:,.0f}")
                    
                    col_total.metric("Total Tax Payable", f"₹{tax_summary['Total Tax Payable']:,.0f}")

                except Exception as e:
                    st.error(f"Error during tax calculation: {e}. Ensure you have matching Buy/Sell transactions.")
            else:
                st.warning("Please record some 'Buy' and 'Sell' transactions to calculate capital gains.")