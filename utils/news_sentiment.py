# utils/news_sentiment.py
import requests
import pandas as pd
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import streamlit as st
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple
import time

# Initialize sentiment analyzer
vader_analyzer = SentimentIntensityAnalyzer()

class NewsSentimentAnalyzer:
    def __init__(self):
        self.api_key = os.environ.get("NEWSDATA_API_KEYww")
        self.base_url = "https://newsdata.io/api/1/news"
        self.cache = {}
        self.last_api_call = 0
        self.rate_limit_delay = 1  # seconds between API calls
    
    def _make_api_call(self, params: Dict) -> Dict:
        """Make API call with rate limiting"""
        # Rate limiting
        time_since_last_call = time.time() - self.last_api_call
        if time_since_last_call < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_call)
        
        try:
            params['apikey'] = self.api_key
            response = requests.get(self.base_url, params=params, timeout=10)
            self.last_api_call = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                st.warning("API rate limit reached. Using cached data or mock data.")
                return {"status": "error", "message": "Rate limit exceeded"}
            else:
                st.error(f"News API error: {response.status_code}")
                return {"status": "error", "message": f"HTTP {response.status_code}"}
                
        except Exception as e:
            st.error(f"Error calling newsdata.io API: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment using both TextBlob and VADER"""
        if not text or len(text.strip()) < 10:
            return {"textblob": 0, "vader": 0, "combined": 0, "sentiment": "Neutral"}
        
        try:
            # TextBlob sentiment
            blob = TextBlob(text)
            tb_sentiment = blob.sentiment.polarity
            
            # VADER sentiment  
            vader_scores = vader_analyzer.polarity_scores(text)
            vader_sentiment = vader_scores['compound']
            
            # Combined sentiment (weighted average)
            combined = (tb_sentiment + vader_sentiment) / 2
            
            # Determine sentiment label
            if combined >= 0.1:
                sentiment_label = "Positive"
            elif combined <= -0.1:
                sentiment_label = "Negative"
            else:
                sentiment_label = "Neutral"
            
            return {
                "textblob": round(tb_sentiment, 3),
                "vader": round(vader_sentiment, 3),
                "combined": round(combined, 3),
                "sentiment": sentiment_label,
                "confidence": abs(combined)
            }
            
        except Exception as e:
            return {"textblob": 0, "vader": 0, "combined": 0, "sentiment": "Neutral", "error": str(e)}
    
    def get_financial_news(self, query: str = "stock market", country: str = "in", category: str = "business", num_articles: int = 10) -> List[Dict]:
        """Get real financial news from newsdata.io"""
        
        # Try to get real news first
        real_news = self._get_real_news(query, country, category, num_articles)
        if real_news:
            return real_news
        
        # Fallback to mock data if API fails
        st.info("Using sample data for demonstration. Add your newsdata.io API key for real-time news.")
        return self._get_mock_news(num_articles)
    
    def _get_real_news(self, query: str, country: str, category: str, num_articles: int) -> List[Dict]:
        """Get real news from newsdata.io API"""
        if not self.api_key:
            st.warning("NEWSDATA_API_KEY not found in environment variables.")
            return []
        
        try:
            params = {
                'q': query,
                'country': country,
                'category': category,
                'language': 'en',
                'size': num_articles
            }
            
            data = self._make_api_call(params)
            
            if data.get('status') == 'success' and data.get('results'):
                analyzed_news = []
                for article in data['results'][:num_articles]:
                    # Analyze sentiment
                    text_to_analyze = f"{article.get('title', '')}. {article.get('description', '')}"
                    sentiment = self.analyze_sentiment(text_to_analyze)
                    
                    analyzed_news.append({
                        "title": article.get('title', 'No title'),
                        "description": article.get('description', 'No description'),
                        "published_at": self._parse_date(article.get('pubDate')),
                        "source": article.get('source_id', 'Unknown'),
                        "url": article.get('link', '#'),
                        "sentiment": sentiment["sentiment"],
                        "sentiment_score": sentiment["combined"],
                        "confidence": sentiment["confidence"],
                        "image_url": article.get('image_url'),
                        "category": article.get('category', [])
                    })
                
                return analyzed_news
            else:
                st.warning(f"No news results found for query: {query}")
                return []
                
        except Exception as e:
            st.error(f"Error processing news data: {str(e)}")
            return []
    
    def _parse_date(self, date_string: str) -> datetime:
        """Parse date from newsdata.io format"""
        try:
            if date_string:
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            pass
        return datetime.now()
    
    def _get_mock_news(self, num_articles: int) -> List[Dict]:
        """Fallback mock news data"""
        mock_news = [
            {
                "title": "Reliance Industries reports strong quarterly results with 25% profit growth",
                "description": "Reliance Industries exceeded market expectations with robust performance across all business segments, driven by strong retail and digital services.",
                "published_at": datetime.now() - timedelta(hours=2),
                "source": "Economic Times",
                "url": "#",
                "image_url": None,
                "category": ["business", "energy"]
            },
            {
                "title": "TCS secures $2 billion digital transformation deal from European client",
                "description": "Tata Consultancy Services announces major contract win strengthening its European market presence and digital capabilities.",
                "published_at": datetime.now() - timedelta(hours=4),
                "source": "Business Standard",
                "url": "#",
                "image_url": None,
                "category": ["business", "technology"]
            },
            {
                "title": "RBI maintains repo rate at 6.5%, signals cautious stance on inflation",
                "description": "The Reserve Bank of India keeps interest rates unchanged amid persistent inflation concerns and global economic uncertainty.",
                "published_at": datetime.now() - timedelta(hours=6),
                "source": "Moneycontrol",
                "url": "#",
                "image_url": None,
                "category": ["business", "economics"]
            },
            {
                "title": "HDFC Bank faces regulatory scrutiny over digital lending practices",
                "description": "Regulatory authorities investigate HDFC Bank's compliance with digital lending guidelines and customer protection measures.",
                "published_at": datetime.now() - timedelta(hours=8),
                "source": "Financial Express",
                "url": "#",
                "image_url": None,
                "category": ["business", "banking"]
            },
            {
                "title": "Infosys announces major expansion in AI and machine learning capabilities",
                "description": "Infosys invests $1 billion in artificial intelligence research and development initiatives to boost digital transformation services.",
                "published_at": datetime.now() - timedelta(hours=10),
                "source": "Bloomberg Quint",
                "url": "#",
                "image_url": None,
                "category": ["business", "technology"]
            },
            {
                "title": "Indian stock markets hit record high amid strong foreign inflows",
                "description": "Benchmark indices Sensex and Nifty reach all-time highs as foreign institutional investors continue to pour money into Indian equities.",
                "published_at": datetime.now() - timedelta(hours=12),
                "source": "Reuters",
                "url": "#",
                "image_url": None,
                "category": ["business", "markets"]
            },
            {
                "title": "SEBI introduces new regulations for algorithmic trading in India",
                "description": "Securities and Exchange Board of India announces stricter norms for algo trading to ensure market stability and investor protection.",
                "published_at": datetime.now() - timedelta(hours=14),
                "source": "ET Markets",
                "url": "#",
                "image_url": None,
                "category": ["business", "regulation"]
            }
        ]
        
        # Analyze sentiment for mock news
        analyzed_news = []
        for news in mock_news[:num_articles]:
            text_to_analyze = f"{news['title']}. {news['description']}"
            sentiment = self.analyze_sentiment(text_to_analyze)
            
            analyzed_news.append({
                **news,
                "sentiment": sentiment["sentiment"],
                "sentiment_score": sentiment["combined"],
                "confidence": sentiment["confidence"]
            })
        
        return analyzed_news
    
    def get_stock_specific_news(self, stock_name: str, num_articles: int = 5) -> List[Dict]:
        """Get news specific to a particular stock"""
        # Map stock names to search queries
        stock_queries = {
            "Reliance": "Reliance Industries",
            "TCS": "Tata Consultancy Services",
            "Infosys": "Infosys",
            "HDFC Bank": "HDFC Bank",
            "ICICI Bank": "ICICI Bank",
            "Bajaj Finance": "Bajaj Finance"
        }
        
        query = stock_queries.get(stock_name, stock_name)
        return self.get_financial_news(query=query, num_articles=num_articles)
    
    def get_market_sentiment_summary(self) -> Dict:
        """Get overall market sentiment summary"""
        news_articles = self.get_financial_news("stock market India", num_articles=15)
        
        if not news_articles:
            return {
                "overall_sentiment": "Neutral", 
                "average_score": 0, 
                "positive_articles": 0, 
                "negative_articles": 0, 
                "neutral_articles": 0, 
                "total_articles": 0
            }
        
        sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        total_sentiment_score = 0
        
        for article in news_articles:
            sentiment_counts[article["sentiment"]] += 1
            total_sentiment_score += article["sentiment_score"]
        
        total_articles = len(news_articles)
        avg_sentiment = total_sentiment_score / total_articles if total_articles > 0 else 0
        
        if avg_sentiment >= 0.1:
            overall_sentiment = "Bullish"
        elif avg_sentiment <= -0.1:
            overall_sentiment = "Bearish"
        else:
            overall_sentiment = "Neutral"
        
        return {
            "overall_sentiment": overall_sentiment,
            "average_score": round(avg_sentiment, 3),
            "positive_articles": sentiment_counts["Positive"],
            "negative_articles": sentiment_counts["Negative"],
            "neutral_articles": sentiment_counts["Neutral"],
            "total_articles": total_articles
        }
    
    def get_news_categories(self) -> List[Dict]:
        """Get news by different categories"""
        categories = {
            "Market News": {"query": "stock market", "category": "business"},
            "Banking": {"query": "banking finance", "category": "business"},
            "Technology": {"query": "technology IT", "category": "technology"},
            "Economy": {"query": "economy GDP", "category": "business"},
            "Energy": {"query": "energy oil", "category": "business"}
        }
        
        categorized_news = {}
        for category_name, params in categories.items():
            news = self.get_financial_news(
                query=params["query"], 
                category=params["category"], 
                num_articles=5
            )
            categorized_news[category_name] = news
        
        return categorized_news

# Global instance
news_analyzer = NewsSentimentAnalyzer()