# pages/home.py
import streamlit as st
import pandas as pd
from utils.stock_data import get_stock_data, get_financial_metrics, get_market_status, INDIAN_STOCKS
from utils.news_sentiment import news_analyzer
from utils.technical_analysis import tech_analyzer

def home_page():
    st.header("🏠 Market Dashboard")
    
    # Get market status
    market_status = get_market_status()
    
    # Quick Overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Nifty 50", "22,415.80", "+1.2%")
    with col2:
        st.metric("Sensex", "73,805.50", "+0.8%")
    with col3:
        status_color = "green" if market_status.get('is_open') else "red"
        status_text = "🟢 Open" if market_status.get('is_open') else "🔴 Closed"
        st.metric("Market Status", status_text)
    with col4:
        st.metric("Active Stocks", "2,450", "15 new")
    
    # Market Overview and News Side by Side
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Top Performers")
        
        # Get real stock data for top performers
        top_performers = []
        for stock_name in list(INDIAN_STOCKS.keys())[:5]:  # Show top 5 stocks
            ticker = INDIAN_STOCKS[stock_name]["ticker"]
            df, price, change_pct, max_price, min_price = get_stock_data(ticker, "1d")
            
            if price > 0:
                top_performers.append({
                    'Stock': stock_name,
                    'Price': f"₹{price:.2f}",
                    'Change %': f"{change_pct:+.2f}%"
                })
        
        if top_performers:
            performers_df = pd.DataFrame(top_performers)
            st.dataframe(performers_df, use_container_width=True)
        else:
            # Fallback to mock data if API fails
            performers_data = {
                'Stock': ['RELIANCE', 'TCS', 'INFY', 'HDFC Bank', 'ICICI Bank'],
                'Price': ['₹2,845.50', '₹3,812.75', '₹1,645.20', '₹1,542.30', '₹1,085.45'],
                'Change %': ['+2.5%', '+1.8%', '+3.2%', '+1.1%', '+2.8%']
            }
            st.dataframe(pd.DataFrame(performers_data), use_container_width=True)
    
    with col2:
        st.subheader("🚨 Market Alerts")
        
        # Dynamic alerts based on market status
        if not market_status.get('is_open', False):
            st.warning(f"• Markets closed. Opens {market_status.get('next_open', 'tomorrow')}")
        else:
            st.success("• Markets currently open")
            
        st.info("• RBI policy meeting tomorrow")
        st.warning("• Tech sector showing volatility")
        st.success("• Banking stocks gaining momentum")
        
        # Add sentiment alert
        sentiment_summary = news_analyzer.get_market_sentiment_summary()
        if sentiment_summary['overall_sentiment'] == 'Bearish':
            st.error(f"• Market sentiment: {sentiment_summary['overall_sentiment']}")
        else:
            st.success(f"• Market sentiment: {sentiment_summary['overall_sentiment']}")
    
    # Recent News Preview
    st.subheader("📰 Latest Market News")
    
    # Get real news data
    news_data = news_analyzer.get_financial_news(
        query="stock OR market",  # Simple query for free plan
        num_articles=3
    )
    
    if news_data:
        news_col1, news_col2, news_col3 = st.columns(3)
        
        for i, news in enumerate(news_data):
            if i == 0:
                with news_col1:
                    display_news_card(news)
            elif i == 1:
                with news_col2:
                    display_news_card(news)
            elif i == 2:
                with news_col3:
                    display_news_card(news)
    else:
        # Fallback news display
        news_col1, news_col2, news_col3 = st.columns(3)
        
        with news_col1:
            st.write("**Reliance expands renewable energy**")
            st.caption("2 hours ago • Positive")
            st.progress(70)
            
        with news_col2:
            st.write("**TCS wins $2B deal**")
            st.caption("4 hours ago • Very Positive")
            st.progress(85)
            
        with news_col3:
            st.write("**Inflation concerns rise**")
            st.caption("6 hours ago • Negative")
            st.progress(30)
    
    # Portfolio Snapshot (if available)
    try:
        from utils.portfolio_manager import portfolio_manager
        portfolio_summary = portfolio_manager.get_portfolio_summary()
        
        if portfolio_summary and portfolio_summary['total_investment'] > 0:
            st.subheader("💼 Portfolio Snapshot")
            
            p_col1, p_col2, p_col3, p_col4 = st.columns(4)
            
            with p_col1:
                st.metric("Total Value", f"₹{portfolio_summary['current_value']:,.2f}")
            with p_col2:
                st.metric("Total P&L", f"₹{portfolio_summary['total_pnl']:,.2f}")
            with p_col3:
                pnl_color = "green" if portfolio_summary['total_pnl'] >= 0 else "red"
                st.metric("P&L %", f"{portfolio_summary['pnl_percentage']:.2f}%")
            with p_col4:
                st.metric("Holdings", len(portfolio_summary['holdings']))
    except:
        pass  # Portfolio not set up yet
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    
    with quick_col1:
        if st.button("📊 Check Analytics", use_container_width=True, help="View detailed technical analysis"):
            st.switch_page("pages/Analytics.py")
    with quick_col2:
        if st.button("🤖 Ask AI Agent", use_container_width=True, help="Chat with AI financial advisor"):
            st.switch_page("pages/AI_Agent.py")
    with quick_col3:
        if st.button("📰 Read News", use_container_width=True, help="Browse financial news"):
            st.switch_page("pages/News.py")
    with quick_col4:
        if st.button("💼 My Portfolio", use_container_width=True, help="Manage your investments"):
            st.switch_page("pages/Portfolio.py")
    
    # Market Insights Section
    st.subheader("💡 Today's Insights")
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.info("""
        **Sector Performance:**
        - Technology: ↗️ +2.3%
        - Banking: ↗️ +1.8% 
        - Energy: ↗️ +1.5%
        - Pharma: ↘️ -0.8%
        """)
    
    with insight_col2:
        # Get some technical insight
        sample_stock = list(INDIAN_STOCKS.keys())[0]
        sample_ticker = INDIAN_STOCKS[sample_stock]["ticker"]
        df, _, _, _, _ = get_stock_data(sample_ticker, "1mo")
        
        if df is not None and not df.empty:
            indicators = tech_analyzer.calculate_technical_indicators(df)
            if indicators and 'signals' in indicators:
                signal = indicators['signals'].get('overall', 'HOLD')
                signal_color = "green" if signal == 'BUY' else "red" if signal == 'SELL' else "orange"
                
                st.info(f"""
                **Technical Outlook:**
                - Overall Signal: :{signal_color}[{signal}]
                - RSI: {indicators.get('rsi', 'N/A'):.1f}
                - Trend: {indicators['signals'].get('trend', 'N/A')}
                """)
            else:
                st.info("""
                **Technical Outlook:**
                - Market in consolidation
                - Wait for clear signals
                - Monitor volume patterns
                """)
        else:
            st.info("""
            **Market Tips:**
            - Diversify across sectors
            - Monitor global cues
            - Set stop losses
            """)
    
    # Footer with last updated
    st.markdown("---")
    st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

def display_news_card(news):
    """Display a news article in a card format"""
    sentiment = news['sentiment']
    sentiment_color = {
        'Positive': '🟢',
        'Negative': '🔴', 
        'Neutral': '🟡'
    }.get(sentiment, '⚪')
    
    # Calculate time ago
    time_ago = (pd.Timestamp.now() - pd.Timestamp(news['published_at']))
    hours_ago = int(time_ago.total_seconds() // 3600)
    
    st.write(f"**{news['title']}**")
    st.caption(f"{hours_ago}h ago • {sentiment_color} {sentiment}")
    
    # Show sentiment score as progress bar
    sentiment_score = abs(news['sentiment_score'])
    st.progress(sentiment_score)
    
    # Brief description (truncated)
    description = news['description'][:100] + "..." if len(news['description']) > 100 else news['description']
    st.write(description)

if __name__ == "__main__":
    home_page()