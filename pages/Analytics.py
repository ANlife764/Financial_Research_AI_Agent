# pages/analytics.py - CORRECTED
import streamlit as st
import plotly.graph_objects as go
from utils.technical_analysis import tech_analyzer
from utils.stock_data import get_stock_data, INDIAN_STOCKS

def analytics_page():
    st.header("📊 Advanced Analytics")
    
    # Stock selection and timeframe
    col1, col2, col3 = st.columns(3)
    with col1:
        stock_name = st.selectbox("Select Stock", list(INDIAN_STOCKS.keys()))
        ticker = INDIAN_STOCKS[stock_name]["ticker"]
    with col2:
        timeframe = st.selectbox("Timeframe", ["1mo", "3mo", "6mo", "1y"])
    with col3:
        st.write("")
        st.write("")
        analyze_clicked = st.button("Generate Analysis")
    
    if analyze_clicked or 'analytics_generated' in st.session_state:
        st.session_state.analytics_generated = True
        
        # Get stock data
        df, price, change_pct, max_price, min_price = get_stock_data(ticker, timeframe)
        
        if df is None or df.empty:
            st.error("Could not fetch stock data. Please try again.")
            return
        
        # Calculate technical indicators
        indicators = tech_analyzer.calculate_technical_indicators(df)
        
        # Display in tabs
        tab1, tab2, tab3 = st.tabs(["Price Chart", "Technical Indicators", "Signals"])
        
        with tab1:
            # Simple line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['Close'],
                mode='lines',
                name='Close Price',
                line=dict(color='blue', width=2)
            ))
            fig.update_layout(
                title=f"{stock_name} Price Chart ({timeframe})",
                xaxis_title="Date",
                yaxis_title="Price (₹)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            if indicators and 'error' not in indicators:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("RSI", f"{indicators.get('rsi', 'N/A'):.2f}")
                    st.metric("MACD", f"{indicators.get('macd', 'N/A'):.2f}")
                with col2:
                    st.metric("SMA 20", f"{indicators.get('sma_20', 'N/A'):.2f}")
                    st.metric("Volume Ratio", f"{indicators.get('volume_ratio', 'N/A'):.2f}")
            else:
                st.warning("Could not calculate technical indicators")
        
        with tab3:
            if indicators and 'signals' in indicators:
                signals = indicators['signals']
                st.subheader("Trading Signals")
                
                if 'overall' in signals:
                    signal_color = "green" if signals['overall'] == 'BUY' else "red" if signals['overall'] == 'SELL' else "orange"
                    st.markdown(f"<h3 style='color: {signal_color};'>Overall Signal: {signals['overall']}</h3>", unsafe_allow_html=True)