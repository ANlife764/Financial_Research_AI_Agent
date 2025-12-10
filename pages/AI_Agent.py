# pages/AI_Agent.py
import streamlit as st
import google.generativeai as genai
import os
import matplotlib.pyplot as plt
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from utils.stock_data import get_stock_data, get_financial_metrics, INDIAN_STOCKS
from utils.news_sentiment import news_analyzer
from utils.technical_analysis import tech_analyzer
import yfinance as yf

# Configure Gemini AI
genai.configure(api_key=st.secrets.get("GOOGLE_API_KEY", os.environ.get("GOOGLE_API_KEY")))
model = genai.GenerativeModel("models/gemini-2.5-flash")

def get_current_price_yfinance(symbol):
    """Get current price using yfinance"""
    try:
        # Try with .NS suffix for NSE
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="1d")
        if not hist.empty:
            return hist["Close"].iloc[-1]
        
        # Try without suffix
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            return hist["Close"].iloc[-1]
        
        return None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

def load_portfolio_data():
    """Load portfolio from JSON files"""
    portfolio_data = {
        "holdings": [],
        "transactions": [],
        "summary": {}
    }
    
    try:
        # Load current portfolio (from portfolio.json - should only have current holdings)
        if os.path.exists("portfolio.json"):
            with open("portfolio.json", "r") as f:
                portfolio_items = json.load(f)
                # Filter only current holdings (Buy transactions that haven't been fully sold)
                portfolio_data["holdings"] = [item for item in portfolio_items if item.get('Type') == 'Buy']
        
        # Load transaction history
        if os.path.exists("transactions.json"):
            with open("transactions.json", "r") as f:
                portfolio_data["transactions"] = json.load(f)
        
        # Calculate summary with REAL current prices
        if portfolio_data["holdings"]:
            total_investment = 0
            total_current_value = 0
            
            for holding in portfolio_data["holdings"]:
                investment = holding['quantity'] * holding['price']
                total_investment += investment
                
                # Fetch current price
                current_price = get_current_price_yfinance(holding['ticker'])
                if current_price:
                    current_value = holding['quantity'] * current_price
                else:
                    current_value = investment  # Fallback to buy price
                
                total_current_value += current_value
            
            total_pnl = total_current_value - total_investment
            pnl_percentage = (total_pnl / total_investment * 100) if total_investment > 0 else 0
            
            portfolio_data["summary"] = {
                "total_investment": round(total_investment, 2),
                "current_value": round(total_current_value, 2),
                "total_pnl": round(total_pnl, 2),
                "pnl_percentage": round(pnl_percentage, 2),
                "total_holdings": len(portfolio_data["holdings"]),
                "holdings_count": len(portfolio_data["holdings"])
            }
    
    except Exception as e:
        st.error(f"Error loading portfolio: {e}")
    
    return portfolio_data

def get_portfolio_summary():
    """Get portfolio summary for AI context"""
    portfolio_data = load_portfolio_data()
    
    if not portfolio_data["holdings"]:
        return {
            "total_investment": 0,
            "current_value": 0,
            "total_pnl": 0,
            "pnl_percentage": 0,
            "holdings": [],
            "has_portfolio": False
        }
    
    # Get holdings with current prices
    holdings_list = []
    for holding in portfolio_data["holdings"]:
        current_price = get_current_price_yfinance(holding['ticker'])
        if not current_price:
            current_price = holding['price']
        
        current_value = holding['quantity'] * current_price
        investment = holding['quantity'] * holding['price']
        pnl = current_value - investment
        pnl_percentage = (pnl / investment * 100) if investment > 0 else 0
        
        holdings_list.append({
            'symbol': holding['ticker'],
            'name': holding.get('name', holding['ticker']),
            'quantity': holding['quantity'],
            'buy_price': holding['price'],
            'current_price': round(current_price, 2),
            'current_value': round(current_value, 2),
            'pnl': round(pnl, 2),
            'pnl_percentage': round(pnl_percentage, 2)
        })
    
    return {
        "total_investment": portfolio_data["summary"]["total_investment"],
        "current_value": portfolio_data["summary"]["current_value"],
        "total_pnl": portfolio_data["summary"]["total_pnl"],
        "pnl_percentage": portfolio_data["summary"]["pnl_percentage"],
        "holdings": holdings_list,
        "has_portfolio": True
    }

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
    if "process_button_prompt" not in st.session_state:
        st.session_state.process_button_prompt = None
    if "typing_speed" not in st.session_state:
        st.session_state.typing_speed = 0.01  # Default typing speed
    
    # ==== CONTROL PANEL (Collapsible) ====
    with st.expander("⚙️ **Control Panel**", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.subheader("📊 Stock Selection")
            stock_name = st.selectbox("Choose a stock:", list(INDIAN_STOCKS.keys()))
            st.session_state.selected_stock = stock_name
            
            # Stock comparison
            st.subheader("⚖️ Compare")
            other_stocks = [s for s in INDIAN_STOCKS.keys() if s != stock_name]
            compare_stock = st.selectbox("Compare with:", other_stocks)
            if st.button("Compare Stocks", use_container_width=True):
                prompt = f"Compare {stock_name} with {compare_stock}"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.process_button_prompt = prompt
                st.rerun()
        
        with col_b:
            st.subheader("💼 Portfolio")
            
            portfolio_summary = get_portfolio_summary()
            
            if portfolio_summary["has_portfolio"]:
                # FIXED: No 'key=' parameter
                st.metric("Portfolio Value", 
                        f"₹{portfolio_summary['current_value']:,.2f}")
                
                # Show simplified P&L
                pnl_display = f"₹{portfolio_summary['total_pnl']:,.2f}"
                if portfolio_summary['total_pnl'] > 0:
                    st.metric("Total P&L", pnl_display, delta=f"{portfolio_summary['pnl_percentage']:.2f}%")
                else:
                    st.metric("Total P&L", pnl_display)
                
                # Portfolio advice buttons
                if st.button("📋 Get Portfolio Advice", use_container_width=True):
                    prompt = f"Analyze my current portfolio and give me personalized advice. I hold {len(portfolio_summary['holdings'])} stocks including {', '.join([h['symbol'] for h in portfolio_summary['holdings'][:3]])}."
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.session_state.process_button_prompt = prompt
                    st.rerun()
                
                if st.button("🔄 Analyze Portfolio", use_container_width=True):
                    prompt = "Analyze my portfolio performance, diversification, and suggest improvements based on current market conditions."
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.session_state.process_button_prompt = prompt
                    st.rerun()
            else:
                st.info("No portfolio data yet")
                if st.button("➕ Create Portfolio", use_container_width=True):
                    prompt = "How should I start building my investment portfolio for Indian markets?"
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.session_state.process_button_prompt = prompt
                    st.rerun()
        
        with col_c:
            # Portfolio Quick Actions
            st.subheader("📈 Portfolio Quick Actions")
            
            quick_col1, quick_col2 = st.columns(2)
            with quick_col1:
                if st.button("Check Diversification", use_container_width=True):
                    prompt = "Analyze my portfolio diversification and suggest improvements"
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.session_state.process_button_prompt = prompt
                    st.rerun()
            
            with quick_col2:
                if st.button("Risk Assessment", use_container_width=True):
                    prompt = "Assess the risk level of my current portfolio"
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    st.session_state.process_button_prompt = prompt
                    st.rerun()
            
            st.subheader("💡 Try Asking:")
            st.markdown("""
            - "Price of TCS?"
            - "Compare Infosys vs TCS"
            - "News sentiment?"
            - "Market trends?"
            """)
            
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = [
                    {"role": "assistant", "content": "Chat cleared! How can I help you with stocks today?"}
                ]
                st.session_state.show_graph = False
                st.session_state.process_button_prompt = None
                st.rerun()
    
    st.markdown("---")
    
    # ==== MAIN CHAT AREA ====
    
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

    # ====== HYBRID RESPONSE HANDLING ======
    
    def display_typewriter_text(text, placeholder):
        """Display text with typewriter effect"""
        displayed_text = ""
        
        # Start with cursor
        placeholder.markdown("▌")
        time.sleep(st.session_state.typing_speed * 10)
        
        # Split into words for more natural typing
        words = str(text).split(' ')
        
        for i, word in enumerate(words):
            if i > 0:
                displayed_text += " "
            
            # Type word character by character
            for char in word:
                displayed_text += char
                placeholder.markdown(displayed_text + " ▌")
                time.sleep(st.session_state.typing_speed)
            
            # Small pause after words (longer after punctuation)
            if word.endswith(('.', '!', '?')):
                time.sleep(st.session_state.typing_speed * 20)
            else:
                time.sleep(st.session_state.typing_speed * 3)
        
        # Remove cursor at the end
        placeholder.markdown(displayed_text)
    
    def generate_enhanced_ai_prompt(prompt: str, selected_stock: str) -> str:
        """Generate the prompt for AI without calling the API"""
        prompt_lower = prompt.lower()
        ticker = INDIAN_STOCKS[selected_stock]["ticker"]

        # Get portfolio summary
        portfolio_summary = get_portfolio_summary()
        
        # Build portfolio context string
        portfolio_context = ""
        if portfolio_summary["has_portfolio"]:
            portfolio_context = f"""
            USER'S PORTFOLIO:
            - Total Holdings: {len(portfolio_summary['holdings'])} stocks
            - Total Investment: ₹{portfolio_summary['total_investment']:,.2f}
            - Current Value: ₹{portfolio_summary['current_value']:,.2f}
            - P&L: ₹{portfolio_summary['total_pnl']:,.2f} ({portfolio_summary['pnl_percentage']:.2f}%)
            
            Holdings:"""
            
            for holding in portfolio_summary['holdings']:
                portfolio_context += f"\n  - {holding['symbol']}: {holding['quantity']} shares @ ₹{holding['buy_price']}"
            
            # Check if selected stock is in portfolio
            in_portfolio = any(h['symbol'] == ticker for h in portfolio_summary['holdings'])
            if in_portfolio:
                portfolio_context += f"\n\nNOTE: {selected_stock} is ALREADY in the user's portfolio!"
        else:
            portfolio_context = "\nUSER'S PORTFOLIO: No portfolio data available yet."
        
        # Get chat history (last 10 messages for context)
        chat_history = ""
        if len(st.session_state.messages) > 1:  # More than just the initial message
            # Get last N messages (excluding current prompt)
            history_messages = st.session_state.messages[:-1] if st.session_state.messages[-1]["role"] == "user" else st.session_state.messages
            
            # Limit to last 10 messages to avoid token limits
            for msg in history_messages[-10:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                chat_history += f"{role}: {msg['content']}\n"
        
        # Get comprehensive data
        df, price, change_pct, max_price, min_price = get_stock_data(ticker)
        financials = get_financial_metrics(selected_stock, ticker)
        technical_data = tech_analyzer.calculate_technical_indicators(df) if df is not None else {}
        
        # Get news sentiment
        try:
            news_data = news_analyzer.get_news_multi_source(query=f"{selected_stock} stock", num_articles=3)
        except AttributeError:
            news_data = news_analyzer.get_news_multi_source(query="Indian stock market", num_articles=3)
        
        # Build comprehensive context
        context = f"""
        CHAT HISTORY:
        {chat_history if chat_history else "This is the first message in the conversation."}
        
        CURRENT USER QUESTION: {prompt}
        
        CURRENT STOCK ANALYSIS FOR {selected_stock.upper()}: (Ticker: {ticker})
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
        if news_data and isinstance(news_data, list) and len(news_data) > 0:
            sentiment_scores = []
            for news in news_data:
                if isinstance(news, dict):
                    score = news.get('sentiment_score', news.get('combined', news.get('score', 0)))
                    if isinstance(score, (int, float)):
                        sentiment_scores.append(score)
            
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                sentiment_label = "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"
                
                context += f"""
        NEWS SENTIMENT:
        - Overall Sentiment: {sentiment_label} (Score: {avg_sentiment:.2f})
        - Recent News: {len(news_data)} articles analyzed
        """
                # Add top news headlines
                context += "    - Top Headlines:\n"
                for i, news in enumerate(news_data[:2], 1):
                    if isinstance(news, dict):
                        title = news.get('title', 'No title')
                        sentiment = news.get('sentiment', 'Neutral')
                        context += f"      {i}. {title} [{sentiment}]\n"
        
        # Add market sentiment if available
        try:
            market_sentiment = news_analyzer.get_market_sentiment_summary()
            if market_sentiment:
                context += f"""
        MARKET SENTIMENT OVERVIEW:
        - Overall Market: {market_sentiment.get('overall_sentiment', 'Neutral')}
        - Positive Articles: {market_sentiment.get('positive_articles', 0)}
        - Negative Articles: {market_sentiment.get('negative_articles', 0)}
        """
        except Exception:
            pass
        
        # Add portfolio context to the main context
        context += f"""
        {portfolio_context}
        """
        
        # Handle specific query types
        if "compare" in prompt_lower:
            stocks_to_compare = []
            for stock in INDIAN_STOCKS.keys():
                if stock.lower() in prompt_lower:
                    stocks_to_compare.append(stock)
            
            if len(stocks_to_compare) >= 2:
                comparison_context = generate_comparison_context(stocks_to_compare[0], stocks_to_compare[1])
                context += f"\n{comparison_context}"
        
        if any(word in prompt_lower for word in ["graph", "chart", "plot", "visual"]):
            context += "\nCHART NOTE: I've displayed the price chart for visual analysis."
        
        # Generate final AI prompt
        ai_prompt = f"""
        {context}
        
        You are a knowledgeable, friendly financial advisor specializing in Indian stocks. 
        You have access to the user's portfolio information above. Use it to:
        1. Provide personalized advice based on their current holdings
        2. Suggest diversification if needed
        3. Consider portfolio concentration when recommending new stocks
        4. Reference their existing investments when discussing related companies
        
        When analyzing {selected_stock}:
        - If it's already in their portfolio, discuss performance and holding strategy
        - If it's not in their portfolio, consider how it would complement existing holdings
        - Mention sector diversification based on their current portfolio
        
        Provide comprehensive, accurate analysis that considers:
        - Current market conditions
        - Technical indicators
        - Fundamental metrics  
        - News sentiment
        - Risk assessment
        - PORTFOLIO CONTEXT (especially important!)
        - Previous conversation context
        
        Now respond to the user's query: "{prompt}"
        
        Response:
        """
        
        return ai_prompt
    
    def generate_ai_response_with_streaming(prompt_text: str, selected_stock: str):
        """Generate AI response with streaming if available, fallback to regular"""
        ai_prompt = generate_enhanced_ai_prompt(prompt_text, selected_stock)
        
        try:
            # Try streaming first
            response = model.generate_content(ai_prompt, stream=True)
            return response  # Return stream object
        except Exception as stream_error:
            # Fallback to regular generation
            try:
                response = model.generate_content(ai_prompt)
                return response.text  # Return text
            except Exception as e:
                # Ultimate fallback
                return f"""**Analysis for {selected_stock}** (Ticker: {INDIAN_STOCKS[selected_stock]['ticker']})

**📊 Current Status:** Based on available data, here's my analysis.

**💡 Insights:** 
{('The stock shows positive momentum' if 'positive' in prompt_text.lower() else 'Consider reviewing fundamentals' if 'fundamental' in prompt_text.lower() else 'Monitor market conditions closely')}.

**🎯 Recommendation:** 
Consult with a financial advisor for personalized investment advice.

*Note: Unable to generate full AI analysis at this moment.*"""
    
    def handle_ai_response(prompt_text: str, selected_stock: str):
        """Handle AI response with hybrid approach"""
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            with st.spinner("🔍 Analyzing markets..."):
                try:
                    response = generate_ai_response_with_streaming(prompt_text, selected_stock)
                    
                    if hasattr(response, '__iter__'):  # It's a stream
                        accumulated_response = ""
                        
                        # Show initial thinking indicator
                        response_placeholder.markdown("🤔 *Analyzing data...*")
                        time.sleep(0.5)
                        
                        for chunk in response:
                            if chunk.text:
                                accumulated_response += chunk.text
                                # Display with slight delay for natural feel
                                response_placeholder.markdown(accumulated_response + " ▌")
                                time.sleep(st.session_state.typing_speed * 2)
                        
                        # Remove cursor
                        response_placeholder.markdown(accumulated_response)
                        final_response = accumulated_response
                        
                    else:  # It's regular text
                        # Use typewriter effect
                        display_typewriter_text(response, response_placeholder)
                        final_response = response
                    
                    return final_response
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    display_typewriter_text(error_msg, response_placeholder)
                    return error_msg
    
    # Handle button-triggered prompts
    if st.session_state.process_button_prompt:
        prompt = st.session_state.process_button_prompt
        # Clear the flag
        st.session_state.process_button_prompt = None
        
        # Generate response
        response_text = handle_ai_response(prompt, st.session_state.selected_stock)
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()  # Refresh to show in chat history
    
    # Chat input (original functionality)
    if prompt := st.chat_input("Ask me about stocks, analysis, or investment advice..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display AI response
        response_text = handle_ai_response(prompt, st.session_state.selected_stock)
        st.session_state.messages.append({"role": "assistant", "content": response_text})

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
    
    # Get news for both stocks
    news1 = news_analyzer.get_news_multi_source(query=f"{stock1} stock", num_articles=2)
    news2 = news_analyzer.get_news_multi_source(query=f"{stock2} stock", num_articles=2)
    
    comparison = f"""
    STOCK COMPARISON: {stock1.upper()} (Ticker: {ticker1}) vs {stock2.upper()} (Ticker: {ticker2})
    
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
    
    # Add sentiment comparison
    if news1 and news2:
        sentiment1 = sum([n.get('sentiment_score', 0) for n in news1 if isinstance(n, dict)]) / len(news1) if len(news1) > 0 else 0
        sentiment2 = sum([n.get('sentiment_score', 0) for n in news2 if isinstance(n, dict)]) / len(news2) if len(news2) > 0 else 0
        
        comparison += f"""
    SENTIMENT COMPARISON:
    - {stock1}: {'Positive' if sentiment1 > 0.1 else 'Negative' if sentiment1 < -0.1 else 'Neutral'} ({sentiment1:.2f})
    - {stock2}: {'Positive' if sentiment2 > 0.1 else 'Negative' if sentiment2 < -0.1 else 'Neutral'} ({sentiment2:.2f})
    """
    
    # Add portfolio relevance
    portfolio_summary = get_portfolio_summary()
    if portfolio_summary["has_portfolio"]:
        comparison += f"""
    PORTFOLIO RELEVANCE:
    """
        for stock in [stock1, stock2]:
            ticker = INDIAN_STOCKS[stock]["ticker"]
            in_portfolio = any(h['symbol'] == ticker for h in portfolio_summary['holdings'])
            comparison += f"    - {stock}: {'IN PORTFOLIO' if in_portfolio else 'NOT in portfolio'}\n"
    
    return comparison

if __name__ == "__main__":
    ai_agent_page()