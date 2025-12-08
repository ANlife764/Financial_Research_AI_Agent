# utils/portfolio_calc.py - FINAL CORRECTED VERSION

import numpy as np
import numpy_financial as npf
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- 1. SIP and Goal Calculation (Unchanged) ---

def calculate_sip_future_value(monthly_sip, annual_return_percent, years):
    """Calculates the future value of a Systematic Investment Plan (SIP)."""
    rate = (annual_return_percent / 100) / 12
    nper = years * 12
    pmt = -monthly_sip
    fv = npf.fv(rate, nper, pmt, pv=0, when='end')
    return round(fv, 2)

def calculate_monthly_sip_required(goal_amount, annual_return_percent, years):
    """Calculates the monthly SIP required to reach a specific goal."""
    rate = (annual_return_percent / 100) / 12
    nper = years * 12
    fv = -goal_amount
    pmt = npf.pmt(rate, nper, pv=0, fv=fv, when='end')
    return round(pmt, 2)

# --- 2. Tax Calculation (LTCG/STCG) ---

def calculate_capital_gains(transactions_df):
    """
    Calculates LTCG and STCG based on buy/sell dates using FIFO logic.
    Requires a DataFrame with 'Date', 'Type' (Buy/Sell), 'Ticker', 'Price', 'Quantity'.
    """
    
    # 1. Clean and Prepare Data
    for col in ['Price', 'Quantity', 'Amount']:
        transactions_df[col] = pd.to_numeric(transactions_df[col], errors='coerce')
        
    transactions_df['Date'] = pd.to_datetime(transactions_df['Date'])
    transactions_df.dropna(subset=['Price', 'Quantity', 'Amount'], inplace=True)
        
    gains = []
    
    # Separate Buy and Sell Transactions, ensuring Buys are sorted by Date (FIFO)
    buys = transactions_df[transactions_df['Type'] == 'Buy'].sort_values('Date', ascending=True).reset_index(drop=True)
    sells = transactions_df[transactions_df['Type'] == 'Sell'].sort_values('Date', ascending=True).reset_index(drop=True)
    
    # Ensure Buy quantities are absolute for matching logic
    buys['Quantity'] = buys['Quantity'].abs()
    sells['Quantity'] = sells['Quantity'].abs()
    
    # 2. Process Sales (FIFO Matching)
    buy_pool = buys.to_dict('records')

    for index, sell_row in sells.iterrows():
        sold_qty = sell_row['Quantity']
        
        while sold_qty > 0 and buy_pool:
            
            # Find the oldest remaining buy transaction for the same Ticker
            match_index = next((i for i, tx in enumerate(buy_pool) if tx['Ticker'] == sell_row['Ticker'] and tx['Quantity'] > 0), None)

            if match_index is None:
                # No matching buy transaction found for this Ticker in the pool
                break

            buy_tx = buy_pool[match_index]
            
            match_qty = min(sold_qty, buy_tx['Quantity'])
            
            # Determine Holding Period
            buy_date = buy_tx['Date']
            sell_date = sell_row['Date']
            holding_period = (sell_date - buy_date).days

            # Calculate Gain/Loss
            gain_per_share = sell_row['Price'] - buy_tx['Price']
            realized_gain = match_qty * gain_per_share
            
            # Classify Gain (Indian Equity Rule: > 365 days is LTCG)
            gain_type = 'LTCG' if holding_period > 365 else 'STCG'
            
            gains.append({
                'Sell Date': sell_date.date(),
                'Buy Date': buy_date.date(),
                'Ticker': sell_row['Ticker'],
                'Quantity': match_qty,
                'Holding Days': holding_period,
                'Gain/Loss': round(realized_gain, 2),
                'Type': gain_type
            })

            # Update remaining quantities
            sold_qty -= match_qty
            buy_pool[match_index]['Quantity'] -= match_qty
            
            # If the buy transaction is depleted, remove it from the pool
            if buy_pool[match_index]['Quantity'] <= 0.001: # Use small tolerance for float comparison
                buy_pool.pop(match_index)

    # 3. Calculate Final Tax Liability (Simplified Rules)
    
    # Ensure gains is not empty before summarizing
    if not gains:
         return pd.DataFrame(columns=['Sell Date', 'Buy Date', 'Ticker', 'Quantity', 'Holding Days', 'Gain/Loss', 'Type']), {
            'Total STCG': 0, 'STCG Tax (15%)': 0, 'Total LTCG': 0, 
            'LTCG Taxable (over ₹1L)': 0, 'LTCG Tax (10%)': 0, 'Total Tax Payable': 0
        }

    gains_df = pd.DataFrame(gains)
    
    total_stcg = gains_df[gains_df['Type'] == 'STCG']['Gain/Loss'].sum()
    total_ltcg = gains_df[gains_df['Type'] == 'LTCG']['Gain/Loss'].sum()
    
    # STCG Tax: 15% flat rate on positive gains
    stcg_tax = total_stcg * 0.15 if total_stcg > 0 else 0
    
    # LTCG Tax: 10% on gains over ₹1,00,000 
    ltcg_taxable_gain = max(0, total_ltcg - 100000)
    ltcg_tax = ltcg_taxable_gain * 0.10
    
    tax_summary = {
        'Total STCG': round(total_stcg, 2),
        'STCG Tax (15%)': round(stcg_tax, 2),
        'Total LTCG': round(total_ltcg, 2),
        'LTCG Taxable (over ₹1L)': round(ltcg_taxable_gain, 2),
        'LTCG Tax (10%)': round(ltcg_tax, 2),
        'Total Tax Payable': round(stcg_tax + ltcg_tax, 2)
    }

    return gains_df, tax_summary