# app.py
import os
from datetime import datetime, timedelta
import yfinance as yf
import matplotlib.pyplot as plt
import streamlit as st
import google.generativeai as genai
import io
import pandas as pd
from typing import Dict, Tuple

# ==== CONFIGURE GEMINI AI ====
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

# ==== STOCK LIST ====
STOCKS = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "Bajaj Finance": "BAJFINANCE.NS"
}

# ==== FETCH STOCK DATA ====
def get_stock_data(ticker, period="1mo"):
    df = yf.download(ticker, period=period, interval="1d")
    if df.empty:
        return None, None, None, None, None
    latest_price = float(df["Close"].iloc[-1])
    change_pct = float((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100)
    max_price = float(df["Close"].max())
    min_price = float(df["Close"].min())
    return df, latest_price, change_pct, max_price, min_price

# ==== PLOT STATIC CHART ====
def plot_stock(df, ticker):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df.index, df["Close"], label=ticker, linewidth=2, color='blue')
    max_price = float(df["Close"].max())
    min_price = float(df["Close"].min())
    max_date = df["Close"].idxmax()
    min_date = df["Close"].idxmin()
    ax.scatter(max_date, max_price, color='red', s=50, label=f"Max: ₹{max_price:.2f}")
    ax.scatter(min_date, min_price, color='green', s=50, label=f"Min: ₹{min_price:.2f}")
    ax.set_title(f"{ticker} Stock Trend (Last 1 Month)", fontsize=16)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Price (₹)", fontsize=12)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()
    plt.xticks(rotation=45)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

# Add this function for financial data
def get_financial_analysis(stock_name: str, ticker: str) -> Dict:
    """Get basic financial metrics for analysis"""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        financials = {
            "market_cap": info.get('marketCap', 'N/A'),
            "pe_ratio": info.get('trailingPE', 'N/A'),
            "pb_ratio": info.get('priceToBook', 'N/A'),
            "debt_to_equity": info.get('debtToEquity', 'N/A'),
            "roe": info.get('returnOnEquity', 'N/A'),
            "roa": info.get('returnOnAssets', 'N/A'),
            "revenue_growth": info.get('revenueGrowth', 'N/A'),
            "profit_margins": info.get('profitMargins', 'N/A'),
            "dividend_yield": info.get('dividendYield', 'N/A'),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A')
        }
        
        # Format large numbers
        if financials["market_cap"] != 'N/A' and isinstance(financials["market_cap"], (int, float)):
            if financials["market_cap"] > 1e12:
                financials["market_cap"] = f"₹{financials['market_cap']/1e12:.2f} Lakh Cr"
            else:
                financials["market_cap"] = f"₹{financials['market_cap']/1e7:.2f} Cr"
        
        return financials
    except Exception as e:
        return {"error": str(e)}

# Enhanced comparison function
def compare_stocks(stock1: str, stock2: str) -> Dict:
    """Compare two stocks across multiple metrics"""
    ticker1 = STOCKS[stock1]
    ticker2 = STOCKS[stock2]
    
    # Get price data
    df1, price1, change1, max1, min1 = get_stock_data(ticker1)
    df2, price2, change2, max2, min2 = get_stock_data(ticker2)
    
    # Get financial data
    financials1 = get_financial_analysis(stock1, ticker1)
    financials2 = get_financial_analysis(stock2, ticker2)
    
    comparison_data = {
        stock1: {
            "price_data": {
                "current_price": price1,
                "change_pct": change1,
                "week_high": max1,
                "week_low": min1
            },
            "financials": financials1
        },
        stock2: {
            "price_data": {
                "current_price": price2,
                "change_pct": change2,
                "week_high": max2,
                "week_low": min2
            },
            "financials": financials2
        }
    }
    
    return comparison_data

# Update the AI prompt generation to include financial data
def generate_comparison_prompt(stock1: str, stock2: str, user_question: str) -> str:
    """Generate a detailed prompt for stock comparison"""
    
    comparison_data = compare_stocks(stock1, stock2)
    
    prompt = f"""
    Stock Comparison Analysis Requested:
    
    User Question: {user_question}
    
    COMPARISON DATA:
    
    {stock1.upper()} Analysis:
    - Current Price: ₹{comparison_data[stock1]['price_data']['current_price']:.2f}
    - 1-Month Change: {comparison_data[stock1]['price_data']['change_pct']:.2f}%
    - 52-Week Range: ₹{comparison_data[stock1]['price_data']['week_low']:.2f} - ₹{comparison_data[stock1]['price_data']['week_high']:.2f}
    - Market Cap: {comparison_data[stock1]['financials'].get('market_cap', 'N/A')}
    - P/E Ratio: {comparison_data[stock1]['financials'].get('pe_ratio', 'N/A')}
    - Sector: {comparison_data[stock1]['financials'].get('sector', 'N/A')}
    
    {stock2.upper()} Analysis:
    - Current Price: ₹{comparison_data[stock2]['price_data']['current_price']:.2f}
    - 1-Month Change: {comparison_data[stock2]['price_data']['change_pct']:.2f}%
    - 52-Week Range: ₹{comparison_data[stock2]['price_data']['week_low']:.2f} - ₹{comparison_data[stock2]['price_data']['week_high']:.2f}
    - Market Cap: {comparison_data[stock2]['financials'].get('market_cap', 'N/A')}
    - P/E Ratio: {comparison_data[stock2]['financials'].get('pe_ratio', 'N/A')}
    - Sector: {comparison_data[stock2]['financials'].get('sector', 'N/A')}
    
    Please provide a comprehensive comparison covering:
    1. Price performance and momentum
    2. Valuation metrics (P/E, Market Cap)
    3. Sector differences and implications
    4. Risk assessment based on available metrics
    5. Investment considerations for each stock
    
    Be analytical but conversational. Point out key differences and what they might mean for an investor.
    """
    
    return prompt

# ==== STREAMLIT UI ====
st.set_page_config(page_title="AI Stock Chatbot", layout="wide")
st.title("💹 AI Stock Chatbot")
st.markdown("Chat with me about Indian stocks! I can show you prices, trends, and analysis.")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm your stock analysis assistant. I can help you analyze Indian stocks like Reliance, TCS, Infosys, and more. What would you like to know?"}
    ]
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = list(STOCKS.keys())[0]

# Sidebar for stock selection and financial display
with st.sidebar:
    st.header("📊 Stock Selection")
    stock_name = st.selectbox("Choose a stock:", list(STOCKS.keys()))
    st.session_state.selected_stock = stock_name
    
    # Get current stock data for sidebar display
    ticker = STOCKS[stock_name]
    df, price, change_pct, max_price, min_price = get_stock_data(ticker)
    
    if price:
        st.subheader(f"📊 {stock_name} Financial Snapshot")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Current Price", f"₹{price:.2f}")
            st.metric("1M Change", f"{change_pct:.2f}%")
        
        with col2:
            st.metric("52W High", f"₹{max_price:.2f}")
            st.metric("52W Low", f"₹{min_price:.2f}")
        
        # Show financial metrics if available
        financials = get_financial_analysis(stock_name, ticker)
        if 'error' not in financials:
            st.write("**Valuation:**")
            st.write(f"P/E Ratio: {financials.get('pe_ratio', 'N/A')}")
            st.write(f"Market Cap: {financials.get('market_cap', 'N/A')}")
            st.write(f"Sector: {financials.get('sector', 'N/A')}")
    
    st.header("💡 Quick Actions")
    if st.button("Show Current Price"):
        st.session_state.messages.append({"role": "user", "content": f"What's the current price of {stock_name}?"})
    if st.button("Show Graph"):
        st.session_state.messages.append({"role": "user", "content": f"Show me the graph for {stock_name}"})
    if st.button("Financial Analysis"):
        st.session_state.messages.append({"role": "user", "content": f"Give me financial analysis for {stock_name}"})
    
    # Comparison buttons
    other_stocks = [s for s in STOCKS.keys() if s != stock_name]
    compare_stock = st.selectbox("Compare with:", other_stocks)
    if st.button("Compare Stocks"):
        st.session_state.messages.append({"role": "user", "content": f"Compare {stock_name} with {compare_stock}"})
    
    if st.button("Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Chat cleared! How can I help you with stocks today?"}
        ]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Check if the last user message requires a graph or comparison
show_graph = False
graph_stock = None
needs_comparison = False
comparison_stocks = []

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    last_user_message = st.session_state.messages[-1]["content"].lower()
    
    # Check for graph request
    if any(word in last_user_message for word in ["graph", "chart", "plot", "visual"]):
        show_graph = True
        graph_stock = st.session_state.selected_stock
    
    # Check for comparison request
    if "compare" in last_user_message:
        needs_comparison = True
        # Extract stock names from comparison request
        words = last_user_message.split()
        for stock in STOCKS.keys():
            if stock.lower() in last_user_message:
                comparison_stocks.append(stock)

# Chat input
if prompt := st.chat_input("Ask me about stocks..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing stocks..."):
            try:
                # Handle comparison requests
                if "compare" in prompt.lower():
                    stocks_to_compare = []
                    for stock in STOCKS.keys():
                        if stock.lower() in prompt.lower():
                            stocks_to_compare.append(stock)
                    
                    if len(stocks_to_compare) >= 2:
                        comparison_prompt = generate_comparison_prompt(
                            stocks_to_compare[0], 
                            stocks_to_compare[1], 
                            prompt
                        )
                        response = model.generate_content(comparison_prompt, stream=True)
                        full_response = ""
                        for chunk in response:
                            if chunk.text:
                                full_response += chunk.text
                        st.write(full_response)
                    else:
                        full_response = "I'd be happy to compare stocks! Please mention which two stocks you'd like me to compare, for example: 'Compare Reliance and TCS'."
                
                else:
                    # Get current stock data
                    ticker = STOCKS[st.session_state.selected_stock]
                    df, price, change_pct, max_price, min_price = get_stock_data(ticker)
                    financials = get_financial_analysis(st.session_state.selected_stock, ticker)
                    
                    # Prepare context for AI
                    stock_context = f"""
                    Current Stock Analysis for {st.session_state.selected_stock} ({ticker}):
                    - Current Price: ₹{price:.2f}
                    - 1-Month Change: {change_pct:.2f}%
                    - 52-Week High: ₹{max_price:.2f}
                    - 52-Week Low: ₹{min_price:.2f}
                    """
                    
                    # Add financial data if available
                    if 'error' not in financials:
                        stock_context += f"""
                    - Market Cap: {financials.get('market_cap', 'N/A')}
                    - P/E Ratio: {financials.get('pe_ratio', 'N/A')}
                    - Sector: {financials.get('sector', 'N/A')}
                    - Profit Margin: {financials.get('profit_margins', 'N/A')}
                        """
                    
                    stock_context += "\nConversation History:\n"
                    
                    # Add recent conversation context
                    for msg in st.session_state.messages[-6:]:
                        stock_context += f"{msg['role'].capitalize()}: {msg['content']}\n"
                    
                    ai_prompt = f"""
                    {stock_context}
                    
                    You are a friendly, knowledgeable stock market assistant specializing in Indian stocks. 
                    Provide helpful, accurate information about stock prices, trends, and analysis.
                    Be conversational but professional. If the user asks for a graph or chart, mention that one will be displayed.
                    
                    Current user question: {prompt}
                    
                    Assistant:
                    """
                    
                    response = model.generate_content(ai_prompt, stream=True)
                    full_response = ""               
                    for chunk in response:
                        if chunk.text:
                            full_response += chunk.text
                
                # Display response
                st.markdown(full_response)
                
                # Add to conversation history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                error_msg = f"Sorry, I encountered an error while processing your request: {str(e)}"
                st.markdown(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Display graph if requested
if show_graph and graph_stock:
    ticker = STOCKS[graph_stock]
    df, _, _, _, _ = get_stock_data(ticker)
    if df is not None:
        st.subheader(f"📈 {graph_stock} Price Chart (Last 1 Month)")
        fig_buf = plot_stock(df, graph_stock)
        st.image(fig_buf, use_container_width=True)
        
        # Add graph info to chat
        graph_info = f"I've displayed the price chart for {graph_stock}. The chart shows the closing prices over the last month with high and low points marked."
        st.session_state.messages.append({"role": "assistant", "content": graph_info})
        with st.chat_message("assistant"):
            st.markdown(graph_info)

# Add some helpful suggestions
st.sidebar.header("🎯 Try Asking:")
st.sidebar.markdown("""
- "What's the current price of TCS?"
- "Show me Reliance's performance graph"
- "Compare Infosys and TCS"
- "Is this a good time to buy HDFC Bank?"
- "Financial analysis for ICICI Bank"
- "Compare Reliance with TCS financials"
""")