# pages/News.py
import streamlit as st
from datetime import datetime, timedelta
from utils.news_sentiment import news_analyzer

def news_page():
    st.header("📰 Market News Dashboard")
    
    # Introduction
    st.markdown("""
    Get real-time Indian market news with AI-powered sentiment analysis.
    Our system analyzes financial news to provide market sentiment insights.
    """)
    
    # Simple search
    col1, col2 = st.columns([4, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search market news...",
            placeholder="e.g., sensex, nifty, RBI, TCS, Reliance",
            value="Indian stock market"
        )
    
    with col2:
        st.write("")
        st.write("")
        search_clicked = st.button("Search", use_container_width=True)
    
    # Get news
    with st.spinner("📡 Fetching market news..."):
        news_items = news_analyzer.get_news_multi_source(
            query=search_query,
            num_articles=8
        )
    
    # Display sentiment statistics
    if news_items:
        # Calculate sentiment summary
        sentiments = [item.get('sentiment', 'Neutral') for item in news_items]
        positive = sentiments.count('Positive')
        negative = sentiments.count('Negative')
        neutral = sentiments.count('Neutral')
        
        # Overall sentiment
        total = len(news_items)
        if positive > negative and positive > neutral:
            overall = "📈 Bullish"
            overall_color = "green"
        elif negative > positive and negative > neutral:
            overall = "📉 Bearish" 
            overall_color = "red"
        else:
            overall = "📊 Neutral"
            overall_color = "gray"
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Articles", total)
        with col2:
            st.metric("Positive", positive)
        with col3:
            st.metric("Negative", negative)
        with col4:
            st.metric("Overall", overall)
        
        # Display all articles
        st.subheader(f"📰 Latest Market News ({len(news_items)} articles)")
        
        for i, news in enumerate(news_items, 1):
            display_market_news_card(news, i)
        
        # Source info
        st.caption("ℹ️ Data sources: Market news APIs and financial publications")
        
    else:
        st.warning("No market news found. Please try a different search term.")
        
        # Show sample articles
        st.subheader("💡 Sample Market News")
        sample_news = news_analyzer._get_high_quality_indian_financial_news(5)
        for i, news in enumerate(sample_news, 1):
            display_market_news_card(news, i)

def display_market_news_card(news, index):
    """Display a market news article with proper sentiment score"""
    with st.container():
        # Create columns: 70% for content, 30% for sentiment
        content_col, sentiment_col = st.columns([7, 3])
        
        with content_col:
            # Title
            title = news.get('title', 'No title')
            st.markdown(f"**{index}. {title}**")
            
            # Source and time
            source = news.get('source', 'Unknown')
            time_ago = get_time_ago(news.get('published_at'))
            
            st.caption(f"📅 {time_ago} | 📰 {source}")
            
            # Description (truncated)
            description = news.get('description', '')
            if description:
                short_desc = description[:120] + "..." if len(description) > 120 else description
                st.write(short_desc)
            
            # URL if available
            url = news.get('url', '#')
            if url and url != '#':
                st.markdown(f"[Read full article →]({url})")
        
        with sentiment_col:
            # Get sentiment data
            sentiment = news.get('sentiment', 'Neutral')
            score = news.get('sentiment_score', 0)
            confidence = abs(score)  # Confidence is absolute value of score
            
            # Determine color and emoji based on sentiment
            if sentiment == 'Positive':
                color = '#22c55e'  # Green
                emoji = '📈'
                sentiment_text = 'Bullish'
            elif sentiment == 'Negative':
                color = '#ef4444'  # Red
                emoji = '📉'
                sentiment_text = 'Bearish'
            else:
                color = '#f59e0b'  # Orange
                emoji = '📊'
                sentiment_text = 'Neutral'
            
            # Create a styled sentiment box
            st.markdown(f"""
            <div style="
                background-color: {color}15;
                border: 1px solid {color}30;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                margin: 5px 0;
            ">
                <div style="font-size: 24px; margin-bottom: 5px;">{emoji}</div>
                <div style="font-weight: bold; color: {color}; font-size: 16px; margin-bottom: 5px;">
                    {sentiment_text}
                </div>
                <div style="font-size: 20px; font-weight: bold; color: {color}; margin-bottom: 5px;">
                    {score:.2f}
                </div>
                <div style="font-size: 12px; color: #666;">
                    Sentiment Score
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Confidence indicator
            st.progress(confidence, text=f"Confidence: {confidence:.0%}")
        
        # Divider between articles
        st.divider()

def get_time_ago(published_at):
    """Convert datetime to readable time format"""
    try:
        if isinstance(published_at, str):
            # Try to parse if it's a string
            try:
                published_at = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except:
                return published_at
        
        if isinstance(published_at, datetime):
            now = datetime.now()
            diff = now - published_at
            
            minutes = int(diff.total_seconds() // 60)
            hours = int(diff.total_seconds() // 3600)
            
            if minutes < 60:
                return f"{minutes}m ago" if minutes > 1 else "Just now"
            elif hours < 24:
                return f"{hours}h ago"
            else:
                days = hours // 24
                return f"{days}d ago" if days == 1 else f"{days}d ago"
    except:
        pass
    
    return "Recent"

if __name__ == "__main__":
    news_page()
