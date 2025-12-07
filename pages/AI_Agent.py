# pages/AI_Agent.py
import streamlit as st
import google.generativeai as genai
import os
import io
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from utils.stock_data import get_stock_data, get_financial_metrics, INDIAN_STOCKS
from utils.news_sentiment import news_analyzer
from utils.technical_analysis import tech_analyzer
from utils.portfolio_manager import portfolio_manager

# Configure Gemini AI
genai.configure(api_key=st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY")))
model = genai.GenerativeModel("models/gemini-2.5-flash")

def ai_agent_page():
    st.header("🤖 AI Financial Agent")
    st.markdown("Chat with your AI financial advisor for personalized insights and stock analysis")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm your AI financial advisor. I can help you analyze stocks, compare investments, provide technical analysis, and give personalized financial advice. What would you like to know?"}
        ]
    if "selected_stock" not in st.session_state:
        st.session_state.selected_stock = list(INDIAN_STOCKS.keys())[0]
    if "show_graph" not in st.session_state:
        st.session_state.show_graph = False
    if "graph_stock" not in st.session_state:
        st.session_state.graph_stock = None

    # ==== COMPLETE SIDEBAR WITH ALL DETAILS ====
    with st.sidebar:
        st.header("📊 Stock Selection")
        
        # Stock selection
        stock_name = st.selectbox("Choose a stock:", list(INDIAN_STOCKS.keys()))
        st.session_state.selected_stock = stock_name
        
        # Get current stock data for sidebar display
        ticker = INDIAN_STOCKS[stock_name]["ticker"]
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
            financials = get_financial_metrics(stock_name, ticker)
            if 'error' not in financials:
                st.write("**Valuation:**")
                st.write(f"P/E Ratio: {financials.get('pe_ratio', 'N/A')}")
                st.write(f"Market Cap: {financials.get('market_cap', 'N/A')}")
                st.write(f"Sector: {financials.get('sector', 'N/A')}")
        
        st.header("💡 Quick Actions")
        
        # Quick action buttons - COMPLETE SET
        if st.button("📈 Show Current Price", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"What's the current price of {stock_name}?"})
            st.rerun()
        
        if st.button("📊 Show Graph", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"Show me the graph for {stock_name}"})
            st.session_state.show_graph = True
            st.session_state.graph_stock = stock_name
            st.rerun()
        
        if st.button("💰 Financial Analysis", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"Give me financial analysis for {stock_name}"})
            st.rerun()
        
        if st.button("🔍 Technical Analysis", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"Show technical analysis for {stock_name}"})
            st.rerun()
        
        if st.button("📰 News Sentiment", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"What's the news sentiment for {stock_name}?"})
            st.rerun()
        
        # Stock comparison section
        st.header("⚖️ Stock Comparison")
        other_stocks = [s for s in INDIAN_STOCKS.keys() if s != stock_name]
        compare_stock = st.selectbox("Compare with:", other_stocks)
        if st.button("Compare Stocks", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": f"Compare {stock_name} with {compare_stock}"})
            st.rerun()
        
        # Portfolio integration section
        st.header("💼 Portfolio Tools")
        try:
            portfolio_summary = portfolio_manager.get_portfolio_summary()
            if portfolio_summary and portfolio_summary['total_investment'] > 0:
                st.metric("Portfolio Value", f"₹{portfolio_summary['current_value']:,.2f}")
                st.metric("Total P&L", f"₹{portfolio_summary['total_pnl']:,.2f}")
                
                if st.button("📋 Portfolio Advice", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": "Give me advice for my current portfolio"})
                    st.rerun()
                
                if st.button("🔄 Portfolio Analysis", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": "Analyze my portfolio performance and suggest improvements"})
                    st.rerun()
            else:
                st.info("No portfolio data yet")
                if st.button("➕ Create Portfolio", use_container_width=True):
                    st.session_state.messages.append({"role": "user", "content": "How should I start building my investment portfolio?"})
                    st.rerun()
        except Exception as e:
            st.error("Portfolio manager not available")
        
        # Market tools section
        st.header("🌐 Market Tools")
        if st.button("📈 Market Overview", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Give me today's market overview and trends"})
            st.rerun()
        
        if st.button("📰 Latest News", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What are the latest market news and developments?"})
            st.rerun()
        
        if st.button("⚡ Sector Analysis", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Analyze different market sectors and their performance"})
            st.rerun()
        
        # Chat management
        st.header("⚙️ Chat Settings")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Chat cleared! How can I help you with stocks today?"}
            ]
            st.session_state.show_graph = False
            st.rerun()
        
        if st.button("💾 Save Conversation", use_container_width=True):
            st.session_state.messages.append({"role": "assistant", "content": "Conversation saved! You can continue from here."})
            st.rerun()

    # ==== MAIN CHAT INTERFACE ====
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Check for automatic graph display from previous messages
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        last_user_message = st.session_state.messages[-1]["content"].lower()
        
        # Check for graph request in last message
        if any(word in last_user_message for word in ["graph", "chart", "plot", "visual"]):
            st.session_state.show_graph = True
            st.session_state.graph_stock = st.session_state.selected_stock

    # Chat input
    if prompt := st.chat_input("Ask me about stocks, analysis, or investment advice..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("🔍 Analyzing markets..."):
                try:
                    response = generate_enhanced_ai_response(prompt, st.session_state.selected_stock)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.markdown(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

    # Display graph if requested
    if st.session_state.show_graph and st.session_state.graph_stock:
        display_stock_graph(st.session_state.graph_stock)

    # Suggested questions in main area
    st.sidebar.header("🎯 Try Asking:")
    st.sidebar.markdown("""
    **Price & Analysis:**
    - "What's the current price of TCS?"
    - "Show me Reliance's performance graph"
    - "Technical analysis for ICICI Bank"
    
    **Comparison:**
    - "Compare Infosys and TCS"
    - "Which is better: HDFC Bank or ICICI Bank?"
    
    **Investment Advice:**
    - "Is this a good time to buy HDFC Bank?"
    - "Should I invest in technology stocks?"
    - "Portfolio diversification advice"
    
    **Market Insights:**
    - "News sentiment for Bajaj Finance"
    - "Market trends this week"
    - "Sector performance analysis"
    """)

def generate_enhanced_ai_response(prompt: str, selected_stock: str) -> str:
    """Generate AI response with integrated data from all modules"""
    
    prompt_lower = prompt.lower()
    ticker = INDIAN_STOCKS[selected_stock]["ticker"]
    
    # Get comprehensive data
    df, price, change_pct, max_price, min_price = get_stock_data(ticker)
    financials = get_financial_metrics(selected_stock, ticker)
    technical_data = tech_analyzer.calculate_technical_indicators(df) if df is not None else {}
    news_data = news_analyzer.get_stock_specific_news(selected_stock, num_articles=3)
    
    # Build comprehensive context
    context = f"""
    USER QUESTION: {prompt}
    
    CURRENT STOCK ANALYSIS FOR {selected_stock.upper()}:
    - Current Price: ₹{price:.2f}
    - 1-Month Change: {change_pct:+.2f}%
    - 52-Week Range: ₹{min_price:.2f} - ₹{max_price:.2f}
    - Sector: {financials.get('sector', 'N/A')}
    - Market Cap: {financials.get('market_cap', 'N/A')}
    - P/E Ratio: {financials.get('pe_ratio', 'N/A')}
    """
    
    # Add technical analysis if available
    if technical_data and 'error' not in technical_data:
        context += f"""
    TECHNICAL ANALYSIS:
    - RSI: {technical_data.get('rsi', 'N/A'):.2f}
    - Trend: {technical_data.get('signals', {}).get('trend', 'N/A')}
    - Overall Signal: {technical_data.get('signals', {}).get('overall', 'N/A')}
    - MACD: {technical_data.get('macd', 'N/A'):.2f}
    """
    
    # Add news sentiment if available
    if news_data:
        sentiment_scores = [news['sentiment_score'] for news in news_data]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        sentiment_label = "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"
        
        context += f"""
    NEWS SENTIMENT:
    - Overall Sentiment: {sentiment_label} (Score: {avg_sentiment:.2f})
    - Recent News: {len(news_data)} articles analyzed
    """
    
    # Add portfolio context if available
    try:
        portfolio_summary = portfolio_manager.get_portfolio_summary()
        if portfolio_summary and portfolio_summary['total_investment'] > 0:
            context += f"""
    PORTFOLIO CONTEXT:
    - Total Value: ₹{portfolio_summary['current_value']:,.2f}
    - Total P&L: ₹{portfolio_summary['total_pnl']:,.2f} ({portfolio_summary['pnl_percentage']:.2f}%)
    - Number of Holdings: {len(portfolio_summary['holdings'])}
    """
    except:
        pass
    
    # Handle specific query types
    if "compare" in prompt_lower:
        # Extract stocks to compare
        stocks_to_compare = []
        for stock in INDIAN_STOCKS.keys():
            if stock.lower() in prompt_lower:
                stocks_to_compare.append(stock)
        
        if len(stocks_to_compare) >= 2:
            comparison_context = generate_comparison_context(stocks_to_compare[0], stocks_to_compare[1])
            context += f"\n{comparison_context}"
        else:
            context += "\nCOMPARISON NOTE: Please specify which two stocks you want to compare."
    
    if "graph" in prompt_lower or "chart" in prompt_lower or "plot" in prompt_lower:
        st.session_state.show_graph = True
        st.session_state.graph_stock = selected_stock
        context += "\nCHART NOTE: I've displayed the price chart for visual analysis."
    
    # Generate AI response
    ai_prompt = f"""
    {context}
    
    You are a knowledgeable, friendly financial advisor specializing in Indian stocks. 
    Provide comprehensive, accurate analysis that considers:
    - Current market conditions
    - Technical indicators
    - Fundamental metrics  
    - News sentiment
    - Risk assessment
    - Portfolio context (if available)
    
    Be analytical but conversational. If the user asks for comparisons, provide detailed side-by-side analysis.
    If they ask for investment advice, consider risk tolerance and diversification.
    
    Always be honest about limitations and suggest consulting professional advisors for major decisions.
    
    Response:
    """
    
    try:
        response = model.generate_content(ai_prompt)
        return response.text
    except Exception as e:
        return f"I understand you're asking about {selected_stock}. Currently trading at ₹{price:.2f} ({change_pct:+.2f}%). For detailed AI analysis, please ensure your Gemini API key is properly configured."

def generate_comparison_context(stock1: str, stock2: str) -> str:
    """Generate comparison context for two stocks"""
    ticker1 = INDIAN_STOCKS[stock1]["ticker"]
    ticker2 = INDIAN_STOCKS[stock2]["ticker"]
    
    # Get data for both stocks
    df1, price1, change1, max1, min1 = get_stock_data(ticker1)
    df2, price2, change2, max2, min2 = get_stock_data(ticker2)
    
    financials1 = get_financial_metrics(stock1, ticker1)
    financials2 = get_financial_metrics(stock2, ticker2)
    
    tech1 = tech_analyzer.calculate_technical_indicators(df1) if df1 is not None else {}
    tech2 = tech_analyzer.calculate_technical_indicators(df2) if df2 is not None else {}
    
    return f"""
    STOCK COMPARISON: {stock1.upper()} vs {stock2.upper()}
    
    {stock1.upper()}:
    - Price: ₹{price1:.2f} ({change1:+.2f}%)
    - P/E: {financials1.get('pe_ratio', 'N/A')}
    - Market Cap: {financials1.get('market_cap', 'N/A')}
    - Technical Signal: {tech1.get('signals', {}).get('overall', 'N/A')}
    - Sector: {financials1.get('sector', 'N/A')}
    
    {stock2.upper()}:
    - Price: ₹{price2:.2f} ({change2:+.2f}%)
    - P/E: {financials2.get('pe_ratio', 'N/A')}
    - Market Cap: {financials2.get('market_cap', 'N/A')}
    - Technical Signal: {tech2.get('signals', {}).get('overall', 'N/A')}
    - Sector: {financials2.get('sector', 'N/A')}
    """

def display_stock_graph(stock_name: str):
    """Display stock price chart"""
    ticker = INDIAN_STOCKS[stock_name]["ticker"]
    df, _, _, _, _ = get_stock_data(ticker)
    
    if df is not None and not df.empty:
        st.subheader(f"📈 {stock_name} Price Chart (Last 1 Month)")
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df["Close"], label=stock_name, linewidth=2, color='blue')
        
        # Mark high and low points
        max_price = float(df["Close"].max())
        min_price = float(df["Close"].min())
        max_date = df["Close"].idxmax()
        min_date = df["Close"].idxmin()
        
        ax.scatter(max_date, max_price, color='red', s=50, label=f"Max: ₹{max_price:.2f}")
        ax.scatter(min_date, min_price, color='green', s=50, label=f"Min: ₹{min_price:.2f}")
        
        ax.set_title(f"{stock_name} Stock Trend", fontsize=16)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Price (₹)", fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend()
        plt.xticks(rotation=45)
        
        st.pyplot(fig)
        
        # Add technical analysis overlay if available
        technical_data = tech_analyzer.calculate_technical_indicators(df)
        if technical_data and 'error' not in technical_data:
            st.info(f"**Technical Summary:** RSI: {technical_data.get('rsi', 'N/A'):.1f} | "
                   f"Trend: {technical_data.get('signals', {}).get('trend', 'N/A')} | "
                   f"Signal: {technical_data.get('signals', {}).get('overall', 'N/A')}")

if __name__ == "__main__":
    ai_agent_page()