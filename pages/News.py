# pages/news.py
import streamlit as st
import re
from datetime import datetime, timezone, timedelta
from utils.news_sentiment import news_analyzer

def _clean_description(description):
    """Clean up news description"""
    # Remove MENAFN tags and other noise
    
    # Remove (MENAFN - ...) patterns
    description = re.sub(r'\(MENAFN[^)]*\)', '', description)
    
    # Remove (IANS) patterns
    description = re.sub(r'\(IANS[^)]*\)', '', description)
    
    # Remove extra whitespace
    description = ' '.join(description.split())
    
    return description.strip()

def get_time_ago(published_at):
    """Convert datetime to 'X hours ago' format"""
    
    # If published_at is already a string in a nice format, return it
    if isinstance(published_at, str):
        # Check if it's already a time string like "2h ago"
        if 'ago' in published_at.lower():
            return published_at
        
        # Try to parse it
        try:
            # Remove timezone info for simplicity
            if 'T' in published_at or '+' in published_at or 'Z' in published_at:
                # It's an ISO format string with timezone
                if 'Z' in published_at:
                    published_at = published_at.replace('Z', '+00:00')
                
                # Parse with timezone
                dt = datetime.fromisoformat(published_at)
                # Convert to UTC for consistency
                if dt.tzinfo:
                    dt = dt.astimezone(timezone.utc)
                    published_at = dt.replace(tzinfo=None)  # Make naive
                else:
                    published_at = dt
            else:
                # Try other formats
                try:
                    published_at = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")
                except:
                    # If we can't parse it, return as is
                    return published_at
        except:
            # If parsing fails, return as is
            return str(published_at)
    
    # If it's already a datetime object
    if isinstance(published_at, datetime):
        # Make sure both datetimes are naive (no timezone) or both aware
        now = datetime.now()
        
        # If published_at is timezone-aware, convert now to the same timezone
        if published_at.tzinfo:
            # Make now aware with UTC
            now = datetime.now(timezone.utc)
            # Convert published_at to UTC for comparison
            published_at = published_at.astimezone(timezone.utc)
        
        diff = now - published_at
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        
        if hours < 1:
            if minutes < 1:
                return "Just now"
            elif minutes == 1:
                return "1 minute ago"
            else:
                return f"{minutes} minutes ago"
        elif hours == 1:
            return "1 hour ago"
        elif hours < 24:
            return f"{hours} hours ago"
        else:
            days = hours // 24
            if days == 1:
                return "1 day ago"
            elif days < 7:
                return f"{days} days ago"
            elif days < 30:
                weeks = days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                months = days // 30
                return f"{months} month{'s' if months > 1 else ''} ago"
    
    # If it's not a datetime, return as string
    return str(published_at)

def display_news_item(news):
    """Display a single news item with source quality indicator"""
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Title with optional link
            title = news.get('title', 'No title')
            url = news.get('url', '#')
            
            if url and url != '#':
                st.markdown(f"**[{title}]({url})**", unsafe_allow_html=True)
            else:
                st.write(f"**{title}**")
            
            # Source and time with quality indicator
            source = news.get('source', 'Unknown')
            time_display = get_time_ago(news.get('published_at', 'Recent'))
            
            # Add quality indicator for sources
            quality_sources = ['Economic Times', 'Business Standard', 'Reuters', 'Bloomberg', 
                             'Moneycontrol', 'Livemint', 'Financial Express']
            
            source_display = source
            if source in quality_sources:
                source_display = f"✅ {source}"
            
            st.caption(f"{time_display} • Source: {source_display}")
            
            # Description
            description = news.get('description', '')
            if description:
                # Clean up description
                clean_desc = _clean_description(description)
                short_desc = clean_desc[:150] + "..." if len(clean_desc) > 150 else clean_desc
                st.write(short_desc)
        
        with col2:
            # Sentiment with color
            sentiment = news.get('sentiment', 'Neutral')
            score = news.get('sentiment_score', 0)
            
            sentiment_emoji = {
                'Positive': '🟢',
                'Negative': '🔴',
                'Neutral': '🟡'
            }.get(sentiment, '⚪')
            
            st.write(f"{sentiment_emoji} {score:.2f}")
            st.caption(sentiment)
        
        with col3:
            # Relevance indicator
            title_lower = title.lower()
            if any(word in title_lower for word in ['stock', 'market', 'sensex', 'nifty', 'rbi', 'bank']):
                st.metric("Relevance", "High", delta="📈")
            else:
                st.metric("Relevance", "Medium", delta="📊")
        
        st.divider()

def _is_relevant_to_category(news, category):
    """Check if news is relevant to the category"""
    title = news.get('title', '').lower()
    description = news.get('description', '').lower()
    
    category_keywords = {
        "market": ['stock', 'market', 'sensex', 'nifty', 'bse', 'nse', 'equity', 'invest', 'trading'],
        "banking": ['bank', 'rbi', 'finance', 'loan', 'interest', 'credit', 'hdfc', 'icici', 'sbi'],
        "technology": ['tech', 'software', 'it', 'digital', 'tcs', 'infosys', 'wipro', 'startup', 'ai'],
        "energy": ['energy', 'oil', 'gas', 'power', 'reliance', 'adani', 'renewable', 'coal', 'petroleum']
    }
    
    keywords = category_keywords.get(category.lower(), [])
    
    # Check if any keyword is in title or description
    for keyword in keywords:
        if keyword in title or keyword in description:
            return True
    
    return False

def display_news_category(category):
    """Display news for a specific category using GNews"""
    
    # Map categories to GNews optimized queries
    query_map = {
        "stock market": "Indian stock market OR sensex OR nifty OR BSE",
        "market": "Indian stock market OR markets India",
        "rbi or indian banking": "RBI OR Indian banking OR banks India",
        "indian technology or it sector india": "Indian technology OR IT sector India",
        "indian energy or oil india or gas india": "Indian energy OR oil India OR gas India"
    }
    
    # Use mapped query or the category itself
    search_query = query_map.get(category.lower(), category)
    
    # Get news from GNews
    news_items = news_analyzer.get_financial_news(
        query=search_query,
        num_articles=8  # Get more to allow filtering
    )
    
    if news_items and isinstance(news_items, list) and len(news_items) > 0:
        st.write(f"Found {len(news_items)} articles for '{search_query}'")
        
        for i, news in enumerate(news_items[:4]):  # Show max 4
            display_news_item(news)
    else:
        st.info(f"No news found for '{search_query}'. Showing sample data.")
        # Show sample data from the analyzer
        sample_news = news_analyzer._get_high_quality_indian_financial_news(4)
        for news in sample_news:
            display_news_item(news)

def get_indian_financial_news_specific():
    """Try specific Indian financial queries"""
    
    specific_queries = [
        "sensex nifty stock market India",
        "RBI Reserve Bank of India",
        "TCS Infosys Wipro Indian IT",
        "Reliance Industries Adani",
        "HDFC Bank ICICI Bank SBI"
    ]
    
    all_news = []
    
    for query in specific_queries:
        try:
            news = news_analyzer.get_financial_news(query=query, num_articles=2)
            if news:
                all_news.extend(news)
        except:
            continue
    
    # Remove duplicates by title
    seen_titles = set()
    unique_news = []
    
    for news in all_news:
        title = news.get('title', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(news)
    
    return unique_news[:5]  # Return top 5

def test_better_queries():
    """Test different queries to see what works best"""
    
    test_queries = [
        "sensex OR nifty",
        "Indian stock market",
        "RBI interest rates",
        "TCS OR Infosys earnings",
        "Reliance Q3 results"
    ]
    
    for query in test_queries:
        st.write(f"**Testing: '{query}'**")
        
        # Direct API test
        import requests
        
        params = {
            'apikey': st.secrets.get("NEWSDATA_API_KEY", ""),
            'q': query,
            'language': 'en',
            'size': 2
        }
        
        response = requests.get("https://newsdata.io/api/1/latest", params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                st.success(f"Found {data.get('totalResults', 0)} results")
                if data.get('results'):
                    for article in data['results']:
                        st.write(f"- {article.get('title')[:80]}...")
            else:
                st.error(f"API error: {data.get('message')}")
        
        st.divider()

def news_page():
    st.header("📰 News & Market Sentiment")
    
    # DEBUG: Test GNews API directly
    if st.sidebar.button("🔍 Debug GNews API"):
        import requests
        from utils.news_sentiment import NewsSentimentAnalyzer
        
        # Create analyzer instance
        analyzer = NewsSentimentAnalyzer()
        
        st.write("### GNews API Test Results:")
        
        # Test the actual method
        test_news = analyzer.get_financial_news(
            query="Indian stock market", 
            num_articles=3
        )
        
        st.write(f"**Got {len(test_news) if test_news else 0} articles**")
        
        if test_news:
            st.write("**First Article:**")
            st.json(test_news[0])
        
        # Direct API test
        st.write("### Direct API Test:")
        test_url = "https://gnews.io/api/v4/search"
        params = {
            'apikey': st.secrets.get("GNEWS_API_KEY", ""),
            'q': 'Indian stock market',
            'lang': 'en',
            'country': 'in',
            'max': 3
        }
        
        response = requests.get(test_url, params=params, timeout=10)
        st.write(f"**Status Code:** {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            st.write(f"**Articles Found:** {len(data.get('articles', []))}")
            if data.get('articles'):
                st.write("**Sample Article:**")
                st.write(data['articles'][0])
        else:
            st.error(f"❌ API Error: {response.status_code} - {response.text}")
    
    # News Search
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("🔍 Search news...", value="stock market")
    with search_col2:
        st.write("")
        st.write("")
        search_clicked = st.button("Search")
    
    # If search button clicked, show results
    if search_clicked and search_query:
        st.subheader(f"🔍 Search Results for: '{search_query}'")
        display_news_category(search_query)
    
    # News Categories with GNews optimized queries
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Market News", "🏦 Banking", "💻 Technology", "🛢️ Energy"])

    with tab1:
        # Use more specific query for market news
        display_news_category("stock market OR sensex OR nifty")

    with tab2:
        # More comprehensive banking query
        display_news_category("banking OR RBI OR HDFC OR ICICI OR SBI")

    with tab3:
        # Tech sector focused query
        display_news_category("technology OR IT OR TCS OR Infosys OR Wipro")

    with tab4:
        # Energy sector query
        display_news_category("energy OR oil OR gas OR Reliance OR Adani")
# Add a button to run this test
if st.sidebar.button("Test Better Queries"):
    test_better_queries()
