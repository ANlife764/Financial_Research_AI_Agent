# pages/AI_Agent.py
import streamlit as st
import google.generativeai as genai
import os
import matplotlib.pyplot as plt
import pandas as pd
import time
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
    if "process_button_prompt" not in st.session_state:
        st.session_state.process_button_prompt = None
    if "typing_speed" not in st.session_state:
        st.session_state.typing_speed = 0.01  # Default typing speed
    
    # ==== CONTROL PANEL (Collapsible) ====
    with st.expander("⚙️ **Control Panel**", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.subheader("📊 Stock Selection")
            stock_name = st.selectbox("Choose a stock:", list(INDIAN_STOCKS.keys()), key="stock_select")
            st.session_state.selected_stock = stock_name
            
            # Stock comparison
            st.subheader("⚖️ Compare")
            other_stocks = [s for s in INDIAN_STOCKS.keys() if s != stock_name]
            compare_stock = st.selectbox("Compare with:", other_stocks, key="compare_select")
            if st.button("Compare Stocks", use_container_width=True, key="btn_compare_stocks"):
                prompt = f"Compare {stock_name} with {compare_stock}"
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.process_button_prompt = prompt
                st.rerun()
        
        with col_b:
            st.subheader("💼 Portfolio")
            try:
                portfolio_summary = portfolio_manager.get_portfolio_summary()
                if portfolio_summary and portfolio_summary['total_investment'] > 0:
                    st.metric("Portfolio Value", f"₹{portfolio_summary['current_value']:,.2f}", key="metric_portfolio_value")
                    st.metric("Total P&L", f"₹{portfolio_summary['total_pnl']:,.2f}", key="metric_portfolio_pnl")
                    
                    if st.button("📋 Get Advice", use_container_width=True, key="btn_portfolio_advice_ai"):
                        prompt = "Give me advice for my current portfolio"
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        st.session_state.process_button_prompt = prompt
                        st.rerun()
                    
                    if st.button("🔄 Analyze", use_container_width=True, key="btn_portfolio_analyze_ai"):
                        prompt = "Analyze my portfolio performance and suggest improvements"
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        st.session_state.process_button_prompt = prompt
                        st.rerun()
                else:
                    st.info("No portfolio data yet")
                    if st.button("➕ Create Portfolio", use_container_width=True, key="btn_create_portfolio_ai"):
                        prompt = "How should I start building my investment portfolio?"
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        st.session_state.process_button_prompt = prompt
                        st.rerun()
            except:
                st.error("Portfolio manager not available")
        
        with col_c:
            st.subheader("💡 Try Asking:")
            st.markdown("""
            - "Price of TCS?"
            - "Compare Infosys vs TCS"
            - "News sentiment?"
            - "Market trends?"
            """)

            if st.button("🗑️ Clear", use_container_width=True, key="btn_clear_chat_quick"):
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
        USER QUESTION: {prompt}
        
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
    
    return comparison

if __name__ == "__main__":
    ai_agent_page()

if __name__ == "__main__":
    ai_agent_page()