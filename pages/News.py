# pages/news.py
import streamlit as st
from utils.news_sentiment import news_analyzer
from datetime import datetime

def news_page():
    st.header("📰 News & Market Sentiment")
    
    # DEBUG: Test the API directly
    if st.sidebar.button("🔍 Debug API"):
        import requests
        test_url = "https://newsdata.io/api/1/latest"
        params = {
            'apikey': st.secrets.get("NEWSDATA_API_KEY", ""),
            'q': 'stock market',
            'language': 'en',
            'size': 3
        }
        
        response = requests.get(test_url, params=params)
        st.write("### API Test Results:")
        st.write(f"**Status Code:** {response.status_code}")
        st.write(f"**Response:**")
        st.json(response.json())
        
        # Check what we actually got
        data = response.json()
        if data.get('status') == 'success':
            st.success(f"✅ API Success! Found {data.get('totalResults', 0)} articles")
            if data.get('results'):
                st.write("**Sample Article:**")
                st.write(data['results'][0])
        else:
            st.error(f"❌ API Error: {data.get('message', 'Unknown error')}")
        
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

    # News Categories
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Market News", "🏦 Banking", "💻 Technology", "🛢️ Energy"])

    with tab1:
        display_news_category("market")  # This will use "stock market OR sensex OR nifty"

    with tab2:
        display_news_category("banking")  # This will use "banking OR RBI OR finance"

    with tab3:
        display_news_category("technology")  # This will use "technology OR IT OR startup"

    with tab4:
        display_news_category("energy")  # This will use "energy OR oil OR gas"

def display_news_category(category):
    """Display news for a specific category with better filtering"""
    
    # Better queries for each category
    query_map = {
        "market": "Indian stock market OR sensex OR nifty",
        "banking": "RBI OR Indian banking OR HDFC Bank OR ICICI Bank", 
        "technology": "Indian technology OR TCS OR Infosys OR tech startup India",
        "energy": "Indian energy OR Reliance OR oil India OR gas India"
    }
    
    search_query = query_map.get(category.lower(), category)
    
    # Get news
    news_items = news_analyzer.get_financial_news(
        query=search_query,
        num_articles=6  # Get more to allow filtering
    )
    
    if news_items:
        # Show the most relevant news first
        relevant_count = 0
        for news in news_items:
            title = news.get('title', '').lower()
            
            # Check if it's actually relevant to the category
            if _is_relevant_to_category(news, category):
                display_news_item(news)
                relevant_count += 1
                
                # Stop after showing 3 relevant items
                if relevant_count >= 3:
                    break
        
        # If no relevant news found, show sample
        if relevant_count == 0:
            st.info(f"No relevant {category} news found. Showing general financial news.")
            for news in news_items[:3]:
                display_news_item(news)
    else:
        # Show sample data
        display_sample_financial_news(category)


def get_time_ago(published_at):
    """Convert datetime to 'X hours ago' format"""
    from datetime import datetime, timezone, timedelta
    
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
                # Clean up description (remove MENAFN tags, etc.)
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

def _clean_description(description):
    """Clean up news description"""
    # Remove MENAFN tags and other noise
    import re
    
    # Remove (MENAFN - ...) patterns
    description = re.sub(r'\(MENAFN[^)]*\)', '', description)
    
    # Remove (IANS) patterns
    description = re.sub(r'\(IANS[^)]*\)', '', description)
    
    # Remove extra whitespace
    description = ' '.join(description.split())
    
    return description.strip()


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

# Add a button to run this test
if st.sidebar.button("Test Better Queries"):
    test_better_queries()
