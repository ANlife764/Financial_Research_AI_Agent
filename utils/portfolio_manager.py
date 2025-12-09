
# utils/portfolio_manager.py
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import Dict, List, Optional
import yfinance as yf

class PortfolioManager:
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for portfolio tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create transactions table (Source of Truth)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create watchlist table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    added_date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            st.error(f"Database initialization error: {str(e)}")
    
    def add_holding(self, symbol: str, quantity: int, buy_price: float, buy_date: str = None):
        """Add a stock to portfolio holdings (Records a BUY transaction)"""
        try:
            if buy_date is None:
                buy_date = datetime.now().strftime("%Y-%m-%d")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert transaction record (BUY)
            cursor.execute('''
                INSERT INTO transactions (type, symbol, quantity, price, date)
                VALUES (?, ?, ?, ?, ?)
            ''', ('BUY', symbol, quantity, buy_price, buy_date))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            st.error(f"Error adding holding: {str(e)}")
            return False
    
    def remove_holding(self, symbol: str, quantity: int, sell_price: float):
        """Remove/sell a stock from portfolio (Records a SELL transaction)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # FIX: Validate if sufficient total quantity is owned (Query the transactions table)
            cursor.execute('''
                SELECT SUM(CASE WHEN type = 'BUY' THEN quantity ELSE -quantity END)
                FROM transactions
                WHERE symbol = ?
            ''', (symbol,))
            
            total_quantity_owned = cursor.fetchone()[0] or 0 # Get net quantity
            
            if quantity > total_quantity_owned:
                st.error(f"Cannot sell {quantity} shares of {symbol}. You only own {total_quantity_owned} shares.")
                conn.close()
                return False
            
            # Add sell transaction
            cursor.execute('''
                INSERT INTO transactions (type, symbol, quantity, price, date)
                VALUES (?, ?, ?, ?, ?)
            ''', ('SELL', symbol, quantity, sell_price, datetime.now().strftime("%Y-%m-%d")))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error removing holding: {str(e)}")
            return False
    
    def get_portfolio_summary(self) -> Dict:
        """Get complete portfolio summary with current values calculated from transactions."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # FIX: Use transactions table to calculate net holdings and total cost
            transactions_df = pd.read_sql_query('''
                SELECT type, symbol, quantity, price, date
                FROM transactions
            ''', conn)
            
            if transactions_df.empty:
                return {
                    "total_investment": 0, "current_value": 0, "total_pnl": 0,
                    "pnl_percentage": 0, "holdings": []
                }
                
            # Prepare data for aggregation
            transactions_df['signed_quantity'] = np.where(
                transactions_df['type'] == 'BUY', 
                transactions_df['quantity'], 
                -transactions_df['quantity']
            )
            transactions_df['cost'] = transactions_df['quantity'] * transactions_df['price']
            
            holdings_summary = transactions_df.groupby('symbol').agg(
                quantity=('signed_quantity', 'sum'),
                total_cost=('cost', 'sum')
            ).reset_index()
            
            # Filter out fully sold symbols (quantity = 0) and ensure quantity is positive for display
            holdings_summary = holdings_summary[holdings_summary['quantity'] != 0].copy()
            holdings_summary['quantity'] = holdings_summary['quantity'].abs() 

            if holdings_summary.empty:
                return {
                    "total_investment": 0, "current_value": 0, "total_pnl": 0,
                    "pnl_percentage": 0, "holdings": []
                }
                
            # Calculate Avg Price 
            holdings_summary['avg_price'] = holdings_summary['total_cost'] / holdings_summary['quantity']
            
            portfolio_data = []
            total_investment = 0
            total_current_value = 0
            
            # Loop to fetch current price and calculate P&L
            for _, holding in holdings_summary.iterrows():
                symbol = holding['symbol']
                quantity = holding['quantity']
                buy_price = holding['avg_price'] # Use the calculated average price as the buy price

                # --- API CALL LOGIC ---
                try:
                    stock = yf.Ticker(symbol)
                    current_data = stock.history(period="1d")
                    current_price = current_data["Close"].iloc[-1] if not current_data.empty else buy_price
                except:
                    current_price = buy_price
                # ----------------------
                
                # Recalculate investment and P&L
                investment = quantity * buy_price
                current_value = quantity * current_price
                pnl = current_value - investment
                pnl_percentage = (pnl / investment) * 100 if investment > 0 else 0
                
                portfolio_data.append({
                    'symbol': symbol, 'quantity': quantity, 'buy_price': buy_price,
                    'current_price': round(current_price, 2), 'investment': round(investment, 2),
                    'current_value': round(current_value, 2), 'pnl': round(pnl, 2),
                    'pnl_percentage': round(pnl_percentage, 2)
                })
                
                total_investment += investment
                total_current_value += current_value
            
            total_pnl = total_current_value - total_investment
            total_pnl_percentage = (total_pnl / total_investment) * 100 if total_investment > 0 else 0
            
            conn.close()
            
            return {
                "total_investment": round(total_investment, 2),
                "current_value": round(total_current_value, 2),
                "total_pnl": round(total_pnl, 2),
                "pnl_percentage": round(total_pnl_percentage, 2),
                "holdings": portfolio_data
            }
            
        except Exception as e:
            st.error(f"Error getting portfolio summary: {str(e)}")
            return {}
    
    # --- Other functions (get_transaction_history, add_to_watchlist, get_watchlist, calculate_portfolio_metrics) remain unchanged ---
    
    def get_transaction_history(self, limit: int = 50) -> pd.DataFrame:
        """Get transaction history"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(f'''
                SELECT type, symbol, quantity, price, date, notes, created_at
                FROM transactions
                ORDER BY created_at DESC
                LIMIT {limit}
            ''', conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error getting transaction history: {str(e)}")
            return pd.DataFrame()
    
    def add_to_watchlist(self, symbol: str):
        """Add stock to watchlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if already in watchlist
            cursor.execute('SELECT id FROM watchlist WHERE symbol = ?', (symbol,))
            if cursor.fetchone():
                st.warning(f"{symbol} is already in watchlist")
                return False
            
            cursor.execute('INSERT INTO watchlist (symbol) VALUES (?)', (symbol,))
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error adding to watchlist: {str(e)}")
            return False
    
    def get_watchlist(self) -> List[str]:
        """Get current watchlist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT symbol FROM watchlist ORDER BY added_date DESC')
            watchlist = [row[0] for row in cursor.fetchall()]
            conn.close()
            return watchlist
        except Exception as e:
            st.error(f"Error getting watchlist: {str(e)}")
            return []
    
    def calculate_portfolio_metrics(self) -> Dict:
        """Calculate advanced portfolio metrics"""
        try:
            portfolio = self.get_portfolio_summary()
            
            if not portfolio.get('holdings'):
                return {}
            
            # Calculate diversification metrics
            holdings = portfolio['holdings']
            total_value = portfolio['current_value']
            
            sector_allocation = {}
            for holding in holdings:
                # Extract sector from symbol (simplified)
                symbol = holding['symbol']
                sector = "Unknown"
                if '.NS' in symbol:
                    sector = "Indian Equity"
                elif '.BO' in symbol:
                    sector = "BSE Equity"
                else:
                    sector = "Other"
                
                if sector not in sector_allocation:
                    sector_allocation[sector] = 0
                sector_allocation[sector] += holding['current_value']
            
            # Calculate allocation percentages
            for sector in sector_allocation:
                sector_allocation[sector] = round((sector_allocation[sector] / total_value) * 100, 2)
            
            # Risk metrics (simplified)
            total_pnl_percentage = portfolio['pnl_percentage']
            
            if total_pnl_percentage > 20:
                risk_level = "High"
            elif total_pnl_percentage > 10:
                risk_level = "Medium-High"
            elif total_pnl_percentage > 0:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            return {
                "sector_allocation": sector_allocation,
                "risk_level": risk_level,
                "diversification_score": min(100, len(holdings) * 10),  # Simple score
                "total_holdings": len(holdings),
                "best_performer": max(holdings, key=lambda x: x['pnl_percentage']) if holdings else None,
                "worst_performer": min(holdings, key=lambda x: x['pnl_percentage']) if holdings else None
            }
            
        except Exception as e:
            st.error(f"Error calculating portfolio metrics: {str(e)}")
            return {}

# Global instance
portfolio_manager = PortfolioManager()