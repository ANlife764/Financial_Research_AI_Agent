import streamlit as st
import pandas as pd
import os
JSON_FILE = "transactions.json"

from utils.portfolio_calc import (
    calculate_sip_future_value,
    calculate_monthly_sip_required,
    calculate_capital_gains
)

def load_transactions_from_json():
    """Load all transactions from the JSON file."""
    if not JSON_FILE or not os.path.exists(JSON_FILE):
        return pd.DataFrame(columns=['date','type','ticker','quantity','price','name'])
    return pd.read_json(JSON_FILE, convert_dates=["date"])


def tax_calc():
    st.header("⚖️ Indian Tax Implications (LTCG/STCG)")

    # Load JSON instead of session_state
    transactions_df = load_transactions_from_json()

    if st.button("Calculate Capital Gains"):

        # Filter only Buy/Sell
        investment_tx = transactions_df[
            transactions_df['Type'].isin(["Buy", "Sell"])
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
    st.divider()
    if st.button("← Back to Portfolio"):
        st.session_state.current_page = "Portfolio"
        st.rerun()