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
    """
    Calculates LTCG and STCG based on buy/sell dates using FIFO logic.
    Requires a DataFrame with 'Date', 'Type' (Buy/Sell), 'Ticker', 'Price', 'Quantity'.
    """
    
    # 🛑 CRITICAL FIX: Ensure Price, Quantity, and Amount columns are numeric 
    # This prevents the 'Gain/Loss: 0' error from occurring due to string comparison.
    for col in ['Price', 'Quantity', 'Amount']:
        transactions_df[col] = pd.to_numeric(transactions_df[col], errors='coerce')
        
    # Drop any rows that failed conversion (optional, but safer)
    transactions_df.dropna(subset=['Price', 'Quantity', 'Amount'], inplace=True)
        
    gains = []
    
    # 1. Separate Buy and Sell Transactions
    buys = transactions_df[transactions_df['Type'] == 'Buy'].sort_values('Date', ascending=True).reset_index(drop=True)
    sells = transactions_df[transactions_df['Type'] == 'Sell'].sort_values('Date', ascending=True).reset_index(drop=True)
    
    # 2. Track available shares for matching
    buy_pool = buys.to_dict('records')

    # 3. Process Sales (simplified FIFO logic)
    for index, sell_row in sells.iterrows():
        sold_qty = sell_row['Quantity']
        
        while sold_qty > 0 and buy_pool:
            buy_tx = buy_pool[0]
            
            if buy_tx['Ticker'] != sell_row['Ticker']:
                # Skip transactions for different stocks
                buy_pool.pop(0) 
                continue
                
            # If the buy transaction is for a different ticker, it's irrelevant. Pop it.
            if buy_tx['Ticker'] != sell_row['Ticker']:
                buy_pool.pop(0) 
                continue

            match_qty = min(sold_qty, buy_tx['Quantity'])
            
            # Determine Holding Period
            buy_date = pd.to_datetime(buy_tx['Date'])
            sell_date = pd.to_datetime(sell_row['Date'])
            holding_period = (sell_date - buy_date).days

            # Calculate Gain/Loss (This should now work with numeric values)
            gain_per_share = sell_row['Price'] - buy_tx['Price']
            realized_gain = match_qty * gain_per_share
            
            # Classify Gain
            # Indian Equity Tax Rule: > 365 days is Long-Term (LTCG)
            gain_type = 'LTCG' if holding_period > 365 else 'STCG'
            
            gains.append({
                'Sell Date': sell_row['Date'],
                'Buy Date': buy_tx['Date'],
                'Ticker': sell_row['Ticker'],
                'Quantity': match_qty,
                'Holding Days': holding_period,
                'Gain/Loss': round(realized_gain, 2),
                'Type': gain_type
            })

            # Update remaining quantities
            sold_qty -= match_qty
            buy_pool[0]['Quantity'] -= match_qty
            
            # Remove depleted buy transaction
            if buy_pool[0]['Quantity'] == 0:
                buy_pool.pop(0)

    # 4. Calculate Final Tax Liability (Simplified)
    total_stcg = sum(g['Gain/Loss'] for g in gains if g['Type'] == 'STCG')
    total_ltcg = sum(g['Gain/Loss'] for g in gains if g['Type'] == 'LTCG')
    
    # STCG Tax: 15% flat rate
    stcg_tax = total_stcg * 0.15 if total_stcg > 0 else 0
    
    # LTCG Tax: 10% on gains over ₹1,00,000 (Simplified)
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

    return pd.DataFrame(gains), tax_summary