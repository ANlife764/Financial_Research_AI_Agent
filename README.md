# 🤖 AI Financial Research Assistant

A comprehensive, AI-powered financial analysis platform designed for Indian markets that provides real-time portfolio tracking, stock analysis, news sentiment analysis, and personalized investment insights using Google's Gemini AI.

## 🌟 Key Features

### 📊 **Portfolio Management**
- Real-time tracking of investments with live price updates (e.g., RELIANCE.NS, TCS.NS, HDFCBANK.NS)
- Buy/Sell transaction recording with detailed history
- Portfolio performance metrics (P/L, ROI, diversification)
- Expense tracking with categorization
- Capital gains tax calculation (LTCG/STCG) - Indian tax rules compliant
- SIP calculator and goal-based investment planning

### 🤖 **AI Financial Agent**
- Chat-based interface with Google Gemini AI
- Personalized portfolio advice based on your holdings
- Stock comparison and analysis (e.g., "Compare INFOSYS with TCS")
- Technical and fundamental analysis integration
- Market sentiment analysis
- PDF portfolio report generation

### 📈 **Analytics Dashboard**
- Technical analysis with 20+ indicators (RSI, MACD, Bollinger Bands, etc.)
- Fundamental analysis (P/E, P/B, ROE, Debt/Equity ratios) for Indian stocks
- Stock comparison tools
- Risk assessment and volatility analysis
- Sector performance tracking (Nifty Bank, Nifty IT, etc.)

### 📰 **Market Intelligence**
- Real-time news aggregation with sentiment analysis
- Market status monitoring (NSE/BSE trading hours: 9:15 AM - 3:30 PM IST)
- Live Nifty 50 (^NSEI) and Sensex (^BSESN) tracking
- Sector-wise performance analysis
- News sentiment dashboard

### 🏠 **Real-Time Dashboard**
- Live market indices (Nifty 50, Sensex)
- Active stocks tracker (1,000+ Indian stocks)
- Top gainers/losers
- Market alerts and insights
- Auto-refresh capabilities

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Gemini API key
- Basic knowledge of Indian stock market (NSE/BSE)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/financial-research-ai.git
cd financial-research-ai
```

2. **Set up virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure API keys:**
Create `.streamlit/secrets.toml`:
```toml
GOOGLE_API_KEY = "your-gemini-api-key"
GNEWS_API_KEY = "your-gnews-api-key"
NEWSDATA_API_KEY = "your-newsdata-ai-key"
```

5. **Prepare stock data:**
- Place your `EQUITY_L.csv` file in the project root
- This file should contain Indian stock symbols (e.g., `RELIANCE`, `TCS`, `HDFCBANK`)
- Format: CSV with `SYMBOL` and `NAME` columns

6. **Run the application:**
```bash
streamlit run app.py
```

## 📁 Project Structure

```
financial-research-ai/
├── app.py                    # Main Streamlit application
├── pages/                    # Application pages
│   ├── Home.py              # Market dashboard
│   ├── AI_Agent.py          # AI chat interface
│   ├── Analytics.py         # Technical analysis
│   ├── News.py              # News sentiment dashboard
│   ├── Portfolio.py         # Portfolio management
│   ├── portfolio_add.py     # Add stock to portfolio
│   ├── portfolio_extr.py    # Expense tracker
│   ├── portfolio_sip.py     # SIP calculator
│   └── portfolio_tax.py     # Tax calculator
├── utils/                   # Core modules
│   ├── stock_data.py        # Stock data fetching
│   ├── news_sentiment.py    # News sentiment analysis
│   ├── technical_analysis.py # Technical indicators
│   ├── portfolio_manager.py # Portfolio database
│   └── portfolio_calc.py    # Financial calculations  
├── portfolio.json       # Portfolio holdings
├── transactions.json    # Transaction history
├── expenses.json        # Expense records
├── EQUITY_L.csv         # Stock database (Indian stocks)
└── requirements.txt         # Python dependencies
```

## 🔧 Core Technologies

- **Frontend**: Streamlit (Python web framework)
- **AI Engine**: Google Gemini AI (Gemini 2.5 Flash)
- **Data Sources**: Yahoo Finance (yfinance) for Indian stocks (`.NS` suffix)
- **Database**: SQLite for portfolio, JSON for transactions
- **Visualization**: Plotly, Matplotlib
- **Technical Analysis**: pandas-ta, TA-Lib
- **Sentiment Analysis**: TextBlob, VADER
- **PDF Generation**: FPDF

## 📊 Key Modules Explained

### 1. **Portfolio Manager (`portfolio_manager.py`)**
- SQLite-based transaction tracking for Indian stocks
- FIFO (First-In-First-Out) accounting for capital gains (Indian tax compliant)
- Real-time valuation with yfinance integration (e.g., `RELIANCE.NS`)
- Sector allocation and diversification analysis

### 2. **Stock Data Fetcher (`stock_data.py`)**
- Real-time Indian stock data from Yahoo Finance (`.NS` suffix for NSE)
- Fundamental metrics (P/E, P/B, Market Cap, etc.)
- Sector and industry classification
- Market status detection (NSE/BSE trading hours: 9:15 AM - 3:30 PM IST)
- **Example tickers**: `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`, `INFY.NS`, `ICICIBANK.NS`

### 3. **Technical Analyzer (`technical_analysis.py`)**
- 20+ technical indicators (RSI, MACD, Bollinger Bands)
- Automated signal generation (Buy/Sell/Hold)
- Support/Resistance level calculation
- Trend analysis and pattern recognition

### 4. **News Sentiment Analyzer (`news_sentiment.py`)**
- Multi-source news aggregation focused on Indian markets
- AI-powered sentiment analysis using VADER + TextBlob
- Market sentiment scoring (Bullish/Bearish/Neutral)
- Real-time news filtering and categorization

### 5. **Financial Calculator (`portfolio_calc.py`)**
- SIP future value calculations (₹)
- Goal-based investment planning
- Capital gains tax computation (Indian tax rules)
- LTCG/STCG tax liability estimation (₹1 lakh exemption for LTCG)

## 🎯 Use Cases

### For Indian Retail Investors
- Track personal stock portfolio in real-time (e.g., holdings in RELIANCE, TCS, HDFC)
- Get AI-powered investment recommendations for Indian stocks
- Calculate tax liabilities on capital gains (Indian tax rules)
- Plan SIP investments for financial goals (₹)

### For Indian Traders
- Technical analysis with automated signals for NSE stocks
- Market sentiment analysis for Indian markets
- Stock comparison and screening (e.g., compare banking stocks)
- Risk assessment and volatility tracking

### For Financial Analysts
- Comprehensive fundamental analysis of Indian companies
- Sector performance comparison (Nifty sectors)
- News sentiment correlation with stock performance
- Portfolio diversification analysis

## 📱 User Interface

### Navigation
- Top navigation bar with 5 main sections
- Collapsible sidebar (hidden by default)
- Responsive design for desktop use

### Pages Layout
1. **Home**: Market overview dashboard (Nifty 50, Sensex)
2. **News**: Sentiment-analyzed financial news (Indian markets focus)
3. **AI Agent**: Chat-based financial advisor for Indian stocks
4. **Portfolio**: Investment tracking and management (₹)
5. **Analytics**: Advanced stock analysis tools

### Sample Stock Symbols Supported
```
RELIANCE.NS      - Reliance Industries
TCS.NS           - Tata Consultancy Services
HDFCBANK.NS      - HDFC Bank
ICICIBANK.NS     - ICICI Bank
```

## 🔒 Data Security

- All portfolio data stored locally (SQLite + JSON)
- No sensitive data sent to external servers (except API calls)
- API keys managed through Streamlit secrets
- Transaction history encrypted in database

## 🚀 Future Enhancements

- [ ] Multi-user support with authentication
- [ ] Mobile app version
- [ ] Real-time stock alerts via notifications
- [ ] Integration with Indian broker APIs (Zerodha, Upstox, etc.)
- [ ] Advanced backtesting engine
- [ ] Machine learning price prediction models
- [ ] Cryptocurrency portfolio tracking
- [ ] International market support

## 📈 Performance Metrics

- Real-time data updates (60-second refresh)
- Supports 1,000+ Indian stocks
- PDF report generation in under 10 seconds
- AI response time: 2-5 seconds
- Concurrent user support: 10+ (Streamlit Cloud)

## 🛠️ Configuration Options

### API Keys (Optional but Recommended)
```toml
# .streamlit/secrets.toml
GOOGLE_API_KEY = "your-google-ai-key"      # Required for AI Agent
GNEWS_API_KEY = "your-gnews-key"           # For live Indian market news
NEWSDATA_API_KEY = "your-newsdata-ai-key"
```

### Stock Database
- Default: `EQUITY_L.csv` with NSE symbols (e.g., `RELIANCE`, `TCS`, `HDFCBANK`)
- Format: CSV with `SYMBOL` and `NAME` columns
- Can be replaced with custom Indian stock list
- BSE stocks can use `.BO` suffix instead of `.NS`


