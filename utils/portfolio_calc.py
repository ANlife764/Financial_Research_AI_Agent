# utils/portfolio_calc.py

import numpy as np
import numpy_financial as npf
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. SIP and Goal Calculation ---

def calculate_sip_future_value(monthly_sip, annual_return_percent, years):
    """Calculates the future value of a Systematic Investment Plan (SIP)."""
    # Convert annual return to monthly rate
    rate = (annual_return_percent / 100) / 12
    # Total number of periods (months)
    nper = years * 12
    # PMT (payment) is negative because it's cash outflow
    pmt = -monthly_sip
    
    # Calculate Future Value (FV)
    # 'when="end"' assumes payments at the end of the month
    fv = npf.fv(rate, nper, pmt, pv=0, when='end')
    return round(fv, 2)

def calculate_monthly_sip_required(goal_amount, annual_return_percent, years):
    """Calculates the monthly SIP required to reach a specific goal."""
    # Convert annual return to monthly rate
    rate = (annual_return_percent / 100) / 12
    # Total number of periods (months)
    nper = years * 12
    # FV (Future Value) is negative because it's cash inflow/goal
    fv = -goal_amount
    
    # Calculate Payment (PMT)
    pmt = npf.pmt(rate, nper, pv=0, fv=fv, when='end')
    return round(pmt, 2)

# --- 2. Tax Calculation (LTCG/STCG) ---

def calculate_capital_gains(transactions_df):

    # Ensure numeric fields
    for col in ['price', 'quantity']:
        transactions_df[col] = pd.to_numeric(transactions_df[col], errors='coerce')

    transactions_df.dropna(subset=['price', 'quantity'], inplace=True)

    gains = []

    buys = transactions_df[transactions_df['Type'] == 'Buy'].sort_values('date').reset_index(drop=True)
    sells = transactions_df[transactions_df['Type'] == 'Sell'].sort_values('date').reset_index(drop=True)

    # Convert buy pool to list of dicts
    buy_pool = buys.to_dict('records')

    # --- FIXED FIFO MATCHING ---
    for idx, sell in sells.iterrows():

        sold_qty = sell['quantity']

        # Only consider buys of SAME ticker
        ticker_pool = [b for b in buy_pool if b['ticker'] == sell['ticker']]

        if not ticker_pool:
            continue  # no matching buys

        while sold_qty > 0 and ticker_pool:

            buy_tx = ticker_pool[0]

            match_qty = min(sold_qty, buy_tx['quantity'])

            buy_date = pd.to_datetime(buy_tx['date'])
            sell_date = pd.to_datetime(sell['date'])
            holding_days = (sell_date - buy_date).days

            gain_per_share = sell['price'] - buy_tx['price']
            realized_gain = gain_per_share * match_qty

            gain_type = "LTCG" if holding_days > 365 else "STCG"

            gains.append({
                "Sell Date": sell['date'],
                "Buy Date": buy_tx['date'],
                "Ticker": sell['ticker'],
                "Quantity": match_qty,
                "Holding Days": holding_days,
                "Gain/Loss": round(realized_gain, 2),
                "Type": gain_type
            })

            # Update quantities
            sold_qty -= match_qty
            buy_tx['quantity'] -= match_qty

            # Remove buy entry once fully consumed
            if buy_tx['quantity'] == 0:
                buy_pool.remove(buy_tx)
                ticker_pool.remove(buy_tx)

    # ---- TAX Calculation ----
    total_stcg = sum(g['Gain/Loss'] for g in gains if g['Type'] == 'STCG')
    total_ltcg = sum(g['Gain/Loss'] for g in gains if g['Type'] == 'LTCG')

    stcg_tax = total_stcg * 0.15 if total_stcg > 0 else 0
    ltcg_taxable = max(0, total_ltcg - 100000)
    ltcg_tax = ltcg_taxable * 0.10

    tax_summary = {
        "Total STCG": round(total_stcg, 2),
        "STCG Tax (15%)": round(stcg_tax, 2),
        "Total LTCG": round(total_ltcg, 2),
        "LTCG Taxable (over ₹1L)": round(ltcg_taxable, 2),
        "LTCG Tax (10%)": round(ltcg_tax, 2),
        "Total Tax Payable": round(stcg_tax + ltcg_tax, 2),
    }

    return pd.DataFrame(gains), tax_summary
