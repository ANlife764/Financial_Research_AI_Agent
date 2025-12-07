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
        # Use GNews API instead of NewsData.io
        self.api_key = st.secrets.get("GNEWS_API_KEY", os.environ.get("GNEWS_API_KEY"))
        self.base_url = "https://gnews.io/api/v4"
        self.cache = {}
        self.last_api_call = 0
        self.rate_limit_delay = 1  # seconds between API calls
    
    def _make_gnews_api_call(self, params: Dict) -> Dict:
        """Make API call to GNews with rate limiting"""
        # Rate limiting
        time_since_last_call = time.time() - self.last_api_call
        if time_since_last_call < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_call)
        
        try:
            params['apikey'] = self.api_key
            response = requests.get(f"{self.base_url}/search", params=params, timeout=10)
            self.last_api_call = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                st.warning("GNews API rate limit reached. Using cached data or mock data.")
                return {"error": "Rate limit exceeded"}
            else:
                st.error(f"GNews API error: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            st.error(f"Error calling GNews API: {str(e)}")
            return {"error": str(e)}
    
    def get_financial_news(self, query: str = "stock market", country: str = None, category: str = None, num_articles: int = 10) -> List[Dict]:
        """Get financial news from GNews API with Indian focus"""
        
        # If no API key, use mock data
        if not self.api_key:
            st.info("GNEWS_API_KEY not found. Using high-quality Indian financial news samples.")
            return self._get_high_quality_indian_financial_news(num_articles)
        
        # Enhance query for Indian financial news
        enhanced_query = self._enhance_query_for_india(query)
        
        try:
            # GNews API parameters
            params = {
                'q': enhanced_query,
                'lang': 'en',
                'country': 'in',  # India
                'max': num_articles * 2,  # Get more to filter
                'in': 'title,description',  # Search in title and description
                'sortby': 'relevance'
            }
            
            # Make API call
            data = self._make_gnews_api_call(params)
            
            if 'error' in data:
                st.warning(f"GNews API error: {data['error']}. Using sample data.")
                return self._get_high_quality_indian_financial_news(num_articles)
            
            if data.get('articles'):
                articles = data['articles']
                
                # Process articles
                processed_news = []
                for article in articles:
                    # Analyze sentiment
                    text_to_analyze = f"{article.get('title', '')}. {article.get('description', '')}"
                    sentiment = self.analyze_sentiment(text_to_analyze)
                    
                    processed_news.append({
                        "title": article.get('title', 'No title'),
                        "description": article.get('description', 'No description'),
                        "published_at": self._parse_gnews_date(article.get('publishedAt')),
                        "source": article.get('source', {}).get('name', 'Unknown'),
                        "url": article.get('url', '#'),
                        "sentiment": sentiment["sentiment"],
                        "sentiment_score": sentiment["combined"],
                        "confidence": sentiment["confidence"],
                        "image_url": article.get('image', None),
                        "content": article.get('content', '')
                    })
                
                # Filter for financial relevance
                filtered_news = self._filter_financial_news(processed_news, query)
                
                if filtered_news and len(filtered_news) > 0:
                    return filtered_news[:num_articles]
            
            # If no articles found
            st.info(f"No news found for '{enhanced_query}'. Using high-quality samples.")
            return self._get_high_quality_indian_financial_news(num_articles)
            
        except Exception as e:
            st.error(f"Error getting GNews data: {str(e)}")
            return self._get_high_quality_indian_financial_news(num_articles)
    
    def _parse_gnews_date(self, date_string: str) -> datetime:
        """Parse date from GNews format (e.g., '2023-12-07T10:30:00Z')"""
        try:
            if date_string:
                # GNews uses ISO format: 2023-12-07T10:30:00Z
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            pass
        return datetime.now()
    
    def _get_high_quality_indian_financial_news(self, num_articles: int) -> List[Dict]:
        """Get curated high-quality Indian financial news"""
        curated_news = [
            {
                "title": "Sensex surges 600 points to hit fresh record high of 85,200",
                "description": "Indian equity benchmarks soared to new peaks on Monday, with the Sensex crossing 85,000 for the first time ever, driven by strong foreign fund inflows and upbeat corporate earnings.",
                "published_at": datetime.now() - timedelta(hours=2),
                "source": "Economic Times",
                "url": "#",
                "sentiment": "Positive",
                "sentiment_score": 0.85,
                "confidence": 0.9,
                "category": ["markets", "stocks"]
            },
            {
                "title": "RBI keeps repo rate unchanged at 6.5%, maintains 'withdrawal of accommodation' stance",
                "description": "The Monetary Policy Committee voted 5-1 to hold rates steady, citing persistent inflation risks despite recent moderation. GDP growth forecast maintained at 7% for FY25.",
                "published_at": datetime.now() - timedelta(hours=4),
                "source": "Business Standard",
                "url": "#",
                "sentiment": "Neutral",
                "sentiment_score": 0.05,
                "confidence": 0.8,
                "category": ["banking", "economy"]
            },
            {
                "title": "TCS bags $2 billion digital transformation deal from European manufacturing giant",
                "description": "Tata Consultancy Services has secured one of its largest ever contracts to digitally transform the operations of a leading European industrial conglomerate over seven years.",
                "published_at": datetime.now() - timedelta(hours=6),
                "source": "Reuters",
                "url": "#",
                "sentiment": "Positive",
                "sentiment_score": 0.78,
                "confidence": 0.85,
                "category": ["technology", "business"]
            },
            {
                "title": "Reliance Industries Q3 net profit jumps 25% to ₹21,423 crore, beats estimates",
                "description": "Mukesh Ambani-led conglomerate reported robust quarterly results across all business segments, with Jio Platforms and Retail showing particularly strong growth amid expanding market share.",
                "published_at": datetime.now() - timedelta(hours=8),
                "source": "Moneycontrol",
                "url": "#",
                "sentiment": "Positive",
                "sentiment_score": 0.82,
                "confidence": 0.88,
                "category": ["energy", "earnings"]
            },
            {
                "title": "HDFC Bank faces RBI scrutiny over digital loan disbursal practices",
                "description": "The central bank has identified certain deficiencies in the bank's digital lending processes and has asked for corrective measures within 30 days.",
                "published_at": datetime.now() - timedelta(hours=10),
                "source": "Financial Express",
                "url": "#",
                "sentiment": "Negative",
                "sentiment_score": -0.65,
                "confidence": 0.75,
                "category": ["banking", "regulation"]
            },
            {
                "title": "Foreign portfolio investors pour ₹12,500 crore into Indian equities in December so far",
                "description": "FPIs continue to be net buyers in Indian markets, bringing total inflows for 2025 to over ₹1.8 lakh crore, signaling strong confidence in India's growth story.",
                "published_at": datetime.now() - timedelta(hours=12),
                "source": "Livemint",
                "url": "#",
                "sentiment": "Positive",
                "sentiment_score": 0.72,
                "confidence": 0.82,
                "category": ["markets", "fii"]
            },
            {
                "title": "Infosys launches new AI platform 'Topaz' for enterprise clients",
                "description": "The IT major unveiled its comprehensive AI offering that combines generative AI, data analytics, and cloud capabilities to help businesses accelerate digital transformation.",
                "published_at": datetime.now() - timedelta(hours=14),
                "source": "ET Tech",
                "url": "#",
                "sentiment": "Positive",
                "sentiment_score": 0.68,
                "confidence": 0.8,
                "category": ["technology", "ai"]
            },
            {
                "title": "ICICI Bank reports 22% rise in net profit to ₹11,872 crore in Q3",
                "description": "Strong growth in retail loans and improving asset quality helped India's second-largest private lender post better-than-expected quarterly results.",
                "published_at": datetime.now() - timedelta(hours=16),
                "source": "Business Today",
                "url": "#",
                "sentiment": "Positive",
                "sentiment_score": 0.75,
                "confidence": 0.83,
                "category": ["banking", "earnings"]
            }
        ]
        
        return curated_news[:num_articles]
    
    # Keep all other methods the same (analyze_sentiment, get_stock_specific_news, etc.)
    # Only change the news fetching methods above
    
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

    def _enhance_query_for_india(self, query: str) -> str:
        """Enhance query to get better Indian financial news"""
        query_lower = query.lower()
        
        # Map general queries to Indian financial terms
        query_mapping = {
            "stock market": "Indian stock market OR sensex OR nifty OR BSE",
            "market": "Indian stock market OR markets India",
            "banking": "RBI OR Indian banking OR banks India",
            "finance": "Indian finance OR financial India",
            "technology": "Indian technology OR IT sector India",
            "energy": "Indian energy OR oil India OR gas India",
            "business": "Indian business OR economy India"
        }
        
        # Check for mapped queries
        for key, value in query_mapping.items():
            if key in query_lower:
                return value
        
        # Add "India" to query if not already present
        if "india" not in query_lower and "indian" not in query_lower:
            return f"{query} India"
        
        return query

    def _filter_financial_news(self, news_list: List[Dict], original_query: str) -> List[Dict]:
        """Filter news to show most relevant financial content first"""
        if not news_list:
            return []
        
        scored_news = []
        
        # Keywords that indicate high-quality financial news
        high_priority_keywords = [
            'stock market', 'sensex', 'nifty', 'BSE', 'NSE', 'equity', 
            'RBI', 'bank', 'finance', 'investment', 'economy',
            'TCS', 'Infosys', 'Reliance', 'HDFC', 'ICICI', 'Wipro'
        ]
        
        medium_priority_keywords = [
            'business', 'market', 'growth', 'profit', 'revenue',
            'quarter', 'results', 'earning', 'dividend'
        ]
        
        # Keywords to filter out (non-financial)
        filter_out_keywords = [
            'horoscope', 'zodiac', 'astrology', 'recipe', 'cooking',
            'celebrity', 'gossip', 'sports', 'entertainment', 'movie',
            'tv', 'music', 'lifestyle', 'fashion', 'travel'
        ]
        
        for news in news_list:
            title = news.get('title', '').lower()
            description = news.get('description', '').lower()
            source = news.get('source', '').lower()
            
            # Skip if contains filter-out keywords
            if any(keyword in title or keyword in description for keyword in filter_out_keywords):
                continue
            
            # Calculate relevance score
            score = 0
            
            # High priority keywords
            for keyword in high_priority_keywords:
                if keyword.lower() in title:
                    score += 3
                if keyword.lower() in description:
                    score += 2
            
            # Medium priority keywords
            for keyword in medium_priority_keywords:
                if keyword.lower() in title:
                    score += 1
                if keyword.lower() in description:
                    score += 0.5
            
            # Boost score for Indian financial sources
            indian_sources = ['economic times', 'business standard', 'moneycontrol', 'livemint',
                            'financial express', 'reuters india', 'bloomberg india']
            if any(source_name in source for source_name in indian_sources):
                score += 2
            
            # Add to scored list
            scored_news.append((score, news))
        
        # Sort by score (highest first)
        scored_news.sort(key=lambda x: x[0], reverse=True)
        
        # Return only the news items
        return [news for score, news in scored_news]
    
    
    
    def _parse_date(self, date_string: str) -> datetime:
        """Parse date from newsdata.io format"""
        try:
            if date_string:
                return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except:
            pass
        return datetime.now()
    
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
        
        # Check if we got valid articles or an error
        if not news_articles or isinstance(news_articles, str) or 'error' in news_articles:
            # Return default sentiment if API fails
            return {
                "overall_sentiment": "Neutral", 
                "average_score": 0, 
                "positive_articles": 0, 
                "negative_articles": 0, 
                "neutral_articles": 0, 
                "total_articles": 0
            }
        
        # Check if news_articles is a list
        if not isinstance(news_articles, list):
            st.warning(f"Unexpected response type: {type(news_articles)}")
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
            # Make sure article is a dictionary
            if isinstance(article, dict) and "sentiment" in article:
                sentiment_counts[article["sentiment"]] += 1
                total_sentiment_score += article.get("sentiment_score", 0)
            else:
                # Skip invalid articles
                continue
        
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

# Global instance
news_analyzer = NewsSentimentAnalyzer()