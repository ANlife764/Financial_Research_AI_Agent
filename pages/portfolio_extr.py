import streamlit as st
import json
import os
import pandas as pd
from datetime import date


TRANSACTION_CATEGORIES = ["Investment", "Income", "Rent", "Food", "Utilities", "Travel", "Misc"]
JSON_FILE = "expenses.json"


def save_json(df):
    df.to_json(JSON_FILE, orient="records", date_format="iso")


def load_transactions():
    if os.path.exists(JSON_FILE):
        return pd.read_json(JSON_FILE, convert_dates=["Date"])
    return pd.DataFrame(columns=['Date','Type','Category','Quantity','Price','Amount'])


def add_transaction(data):
    new_tx = pd.DataFrame([data])

    st.session_state.transactions_df = pd.concat(
        [st.session_state.transactions_df, new_tx], ignore_index=True
    )

    save_json(st.session_state.transactions_df)
    st.success("Transaction recorded successfully!")
    st.rerun()


def exptr():
    if "transactions_df" not in st.session_state:
        st.session_state.transactions_df = load_transactions()

    st.header("💸 Expense Tracking with Categories")

    # --- FORM ---
    st.subheader("➕ Record Expense or Income")
    with st.form("record_expense_form"):
        col1, col2 = st.columns(2)
        exp_date = col1.date_input("Date", date.today())
        exp_type = col2.selectbox("Type", ["Expense", "Income"])

        col3, col4 = st.columns(2)
        exp_category = col3.selectbox("Category", TRANSACTION_CATEGORIES)
        exp_amount = col4.number_input("Amount (₹)", min_value=0.01)

        if st.form_submit_button("Record Expense/Income"):
            data = {
                'Date': pd.to_datetime(exp_date),   # <<< FIX IS HERE
                'Type': exp_type,
                'Category': exp_category,
                'Quantity': 0,
                'Price': 0.0,
                'Amount': exp_amount
            }
            add_transaction(data)

    st.markdown("---")

    # --- SUMMARY ---
    # Always load JSON into session state if not already done
    transactions = st.session_state.transactions_df

    expense_df = transactions[
        transactions['Type'].isin(["Expense", "Income"])
    ].copy()

    st.subheader("Summary by Category")

    if not expense_df.empty:
        expense_df['SignedAmount'] = expense_df.apply(
            lambda row: row['Amount'] if row['Type'] == 'Income' else -row['Amount'],
            axis=1
        )

        summary = (
            expense_df.groupby('Category')['SignedAmount']
            .sum()
            .reset_index()
            .rename(columns={'SignedAmount': 'Net Amount'})
        )

        st.dataframe(summary.style.format({'Net Amount': '₹{:,.2f}'}))

    else:
        st.info("No expense or income transactions recorded yet.")

    st.divider()
    if st.button("← Back to Portfolio"):
        st.session_state.current_page = "Portfolio"
        st.rerun()
