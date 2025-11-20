# pages/news.py
import streamlit as st
from utils.news_sentiment import news_analyzer
from datetime import datetime

def news_page():
    st.header("📰 News & Market Sentiment")
    
    # Get real sentiment data
    sentiment_summary = news_analyzer.get_market_sentiment_summary()
    
    # Sentiment Overview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Sentiment", sentiment_summary["overall_sentiment"])
    with col2:
        st.metric("Positive News", f"{sentiment_summary['positive_articles']} articles")
    with col3:
        st.metric("Sentiment Score", f"{sentiment_summary['average_score']:.2f}")
    
    # News Search
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("🔍 Search news...")
    with search_col2:
        st.write("")
        st.write("")
        if st.button("Search"):
            st.rerun()
    
    # News Categories
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Market News", "🏦 Banking", "💻 Technology", "🛢️ Energy"])
    
    with tab1:
        display_news_category("market")
    with tab2:
        display_news_category("banking")
    with tab3:
        display_news_category("technology")
    with tab4:
        display_news_category("energy")

def display_news_category(category):
    # Mock data - replace with actual news API
    news_items = [
        {"title": f"Major development in {category} sector", "sentiment": 0.8, "time": "2h ago", "impact": "High"},
        {"title": f"Regulatory changes affecting {category}", "sentiment": -0.3, "time": "4h ago", "impact": "Medium"},
        {"title": f"New investments in {category} industry", "sentiment": 0.6, "time": "6h ago", "impact": "High"},
    ]
    
    for news in news_items:
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{news['title']}**")
                st.caption(f"{news['time']} • Impact: {news['impact']}")
            with col2:
                sentiment_color = "🟢" if news['sentiment'] > 0.3 else "🔴" if news['sentiment'] < -0.3 else "🟡"
                st.write(f"{sentiment_color} {news['sentiment']:.2f}")
            st.divider()