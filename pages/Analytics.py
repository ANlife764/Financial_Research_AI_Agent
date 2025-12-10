# pages/analytics.py - ENHANCED VERSION
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.technical_analysis import tech_analyzer
from utils.stock_data import get_stock_data, get_financial_metrics, INDIAN_STOCKS
from utils.news_sentiment import news_analyzer

def analytics_page():
    st.header("📊 Advanced Analytics Dashboard")
    
    # Stock selection and timeframe
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        stock_name = st.selectbox("Select Stock", list(INDIAN_STOCKS.keys()))
        ticker = INDIAN_STOCKS[stock_name]["ticker"]
    with col2:
        timeframe = st.selectbox("Timeframe", ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"])
    with col3:
        analysis_type = st.selectbox("Analysis Type", 
            ["Technical", "Fundamental", "Comparison", "Risk", "Sentiment"])
    
    # Get stock data
    df, price, change_pct, max_price, min_price = get_stock_data(ticker, timeframe)
    
    if df is None or df.empty:
        st.error("Could not fetch stock data. Please try again.")
        return
    
    # Calculate technical indicators
    with st.spinner("Calculating technical indicators..."):
        indicators = tech_analyzer.calculate_technical_indicators(df)
    
    # Get financial metrics
    financials = get_financial_metrics(stock_name, ticker)
    
    # Display in tabs based on analysis type
    if analysis_type == "Technical":
        show_technical_analysis(df, stock_name, timeframe, indicators)
    elif analysis_type == "Fundamental":
        show_fundamental_analysis(stock_name, financials)
    elif analysis_type == "Comparison":
        show_comparison_analysis(stock_name, ticker, timeframe)
    elif analysis_type == "Risk":
        show_risk_analysis(df, stock_name, financials)
    elif analysis_type == "Sentiment":
        show_sentiment_analysis(stock_name)

def show_technical_analysis(df, stock_name, timeframe, indicators):
    """Display comprehensive technical analysis"""
    st.subheader(f"📈 Technical Analysis - {stock_name}")
    
    # Create tabs for different technical views
    tab1, tab2, tab3, tab4 = st.tabs(["Price Chart", "Indicators", "Oscillators", "Signals"])
    
    with tab1:
        # Enhanced candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC'
        )])
        
        # Calculate and add moving averages
        if len(df) >= 20:
            sma_20 = df['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=sma_20,
                mode='lines',
                name='SMA 20',
                line=dict(color='orange', width=2)
            ))
        
        if len(df) >= 50:
            sma_50 = df['Close'].rolling(window=50).mean()
            fig.add_trace(go.Scatter(
                x=df.index,
                y=sma_50,
                mode='lines',
                name='SMA 50',
                line=dict(color='red', width=1, dash='dash')
            ))
        
        fig.update_layout(
            title=f"{stock_name} Price Chart ({timeframe})",
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            height=500,
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Technical Indicators")
        
        # Calculate indicators directly (fallback if tech_analyzer fails)
        try:
            # Current price
            current_price = df['Close'].iloc[-1] if not df.empty else 0
            
            # 1. RSI Calculation
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            current_rsi = rsi_series.iloc[-1] if not rsi_series.empty else 50
            
            # 2. Moving Averages
            sma_20_value = df['Close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else current_price
            sma_50_value = df['Close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else current_price
            
            # 3. MACD Calculation
            ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_histogram = macd_line - signal_line
            current_macd = macd_histogram.iloc[-1] if not macd_histogram.empty else 0
            
            # 4. Volume Analysis
            volume_avg = df['Volume'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else df['Volume'].mean()
            current_volume = df['Volume'].iloc[-1] if not df['Volume'].empty else 0
            volume_ratio = current_volume / volume_avg if volume_avg > 0 else 1
            
            # 5. Bollinger Bands
            bb_middle = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            bb_width_pct = ((bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1]) * 100 if not bb_middle.empty else 0
            
            # 6. ATR (Average True Range)
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(window=14).mean().iloc[-1] if not true_range.empty else 0
            
            # 7. Volatility (Beta approximation)
            returns = df['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
        except Exception as e:
            st.error(f"Error calculating indicators: {e}")
            # Default values
            current_price = df['Close'].iloc[-1] if not df.empty else 0
            current_rsi = 50
            sma_20_value = current_price
            current_macd = 0
            volume_ratio = 1
            bb_width_pct = 0
            atr = 0
            volatility = 0
        
        # Display indicators in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # RSI - use "inverse" for overbought/oversold
            rsi_color = "inverse" if current_rsi > 70 or current_rsi < 30 else "normal"
            st.metric("RSI (14)", f"{current_rsi:.2f}", delta_color=rsi_color)
            rsi_status = "Overbought (>70)" if current_rsi > 70 else "Oversold (<30)" if current_rsi < 30 else "Neutral"
            st.caption(rsi_status)
        
        with col2:
            # MACD - use normal for positive, inverse for negative
            macd_color = "normal" if current_macd > 0 else "inverse"
            macd_status = "Bullish" if current_macd > 0 else "Bearish"
            macd_delta = f"+{current_macd:.4f}" if current_macd > 0 else f"{current_macd:.4f}"
            st.metric("MACD", f"{current_macd:.4f}", 
                     delta=macd_delta,
                     delta_color=macd_color)
            st.caption(macd_status)
        
        with col3:
            # Price vs SMA - use normal if above, inverse if below
            price_vs_sma = "Above" if current_price > sma_20_value else "Below"
            price_delta_color = "normal" if current_price > sma_20_value else "inverse"
            price_difference = ((current_price - sma_20_value) / sma_20_value) * 100
            price_delta = f"+{price_difference:.2f}%" if price_difference > 0 else f"{price_difference:.2f}%"
            
            st.metric("SMA 20", f"₹{sma_20_value:.2f}", 
                     delta=price_delta,
                     delta_color=price_delta_color)
            st.caption(f"Price is {price_vs_sma} SMA")
        
        with col4:
            # Volume - use normal for high volume, inverse for low
            volume_status = "High" if volume_ratio > 1.5 else "Normal" if volume_ratio > 0.7 else "Low"
            volume_color = "normal" if volume_ratio > 1.2 else "inverse" if volume_ratio < 0.8 else "off"
            volume_delta = f"+{(volume_ratio-1)*100:.0f}%" if volume_ratio > 1 else f"{(volume_ratio-1)*100:.0f}%"
            
            st.metric("Volume", f"{volume_ratio:.2f}x", 
                     delta=volume_delta if volume_ratio != 1 else None,
                     delta_color=volume_color)
            st.caption(f"{volume_status} volume")
        
        # Additional indicators
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # Bollinger Width
            bb_status = "High Vol" if bb_width_pct > 10 else "Normal" if bb_width_pct > 5 else "Low Vol"
            bb_color = "normal" if bb_width_pct > 8 else "inverse" if bb_width_pct < 4 else "off"
            st.metric("BB Width", f"{bb_width_pct:.2f}%", delta_color=bb_color)
            st.caption(bb_status)
        
        with col6:
            # ATR
            st.metric("ATR", f"₹{atr:.2f}")
            st.caption("Avg True Range")
        
        with col7:
            # Volatility
            vol_status = "High" if volatility > 0.3 else "Medium" if volatility > 0.2 else "Low"
            vol_color = "normal" if volatility > 0.25 else "inverse" if volatility < 0.15 else "off"
            st.metric("Volatility", f"{volatility*100:.2f}%", delta_color=vol_color)
            st.caption(f"{vol_status} risk")
        
        with col8:
            # Period Return
            price_change = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100 if len(df) > 1 else 0
            return_color = "normal" if price_change > 0 else "inverse" if price_change < 0 else "off"
            st.metric("Period Return", f"{price_change:.2f}%", delta_color=return_color)
            st.caption(f"{timeframe} performance")
    
    with tab3:
        st.subheader("Technical Oscillators")
        
        # RSI Chart
        try:
            # Recalculate RSI series for chart
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_series = 100 - (100 / (1 + rs))
            
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=df.index,
                y=rsi_series,
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", 
                            annotation_text="Overbought", annotation_position="bottom right")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", 
                            annotation_text="Oversold", annotation_position="top right")
            fig_rsi.update_layout(
                title="RSI Oscillator (14 periods)",
                height=300,
                yaxis_range=[0, 100],
                xaxis_title="Date",
                yaxis_title="RSI Value"
            )
            st.plotly_chart(fig_rsi, use_container_width=True)
            
        except Exception as e:
            st.error(f"Could not generate RSI chart: {e}")
        
        # MACD Chart
        try:
            ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            macd_histogram = macd_line - signal_line
            
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(
                x=df.index,
                y=macd_line,
                mode='lines',
                name='MACD Line',
                line=dict(color='blue', width=2)
            ))
            fig_macd.add_trace(go.Scatter(
                x=df.index,
                y=signal_line,
                mode='lines',
                name='Signal Line',
                line=dict(color='red', width=1)
            ))
            fig_macd.add_trace(go.Bar(
                x=df.index,
                y=macd_histogram,
                name='MACD Histogram',
                marker_color=['green' if x >= 0 else 'red' for x in macd_histogram],
                opacity=0.6
            ))
            fig_macd.update_layout(
                title="MACD Oscillator (12,26,9)",
                height=300,
                xaxis_title="Date",
                yaxis_title="MACD Value"
            )
            st.plotly_chart(fig_macd, use_container_width=True)
            
        except Exception as e:
            st.error(f"Could not generate MACD chart: {e}")
    
    with tab4:
        st.subheader("Trading Signals")
        
        try:
            # Generate signals based on calculated values
            current_price = df['Close'].iloc[-1] if not df.empty else 0
            
            # Calculate required values
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi_value = (100 - (100 / (1 + rs))).iloc[-1] if not rs.empty else 50
            
            # SMA
            sma_20 = df['Close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else current_price
            
            # MACD
            ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
            macd_line_val = (ema_12 - ema_26).iloc[-1] if not ema_12.empty else 0
            
            # Volume
            volume_avg_20 = df['Volume'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else df['Volume'].mean()
            current_volume = df['Volume'].iloc[-1] if not df['Volume'].empty else 0
            volume_ratio_signal = current_volume / volume_avg_20 if volume_avg_20 > 0 else 1
            
            # Generate signals
            buy_signals = 0
            sell_signals = 0
            signal_details = []
            
            # 1. Price vs SMA Signal
            if current_price > sma_20 * 1.02:  # 2% above SMA
                buy_signals += 1
                signal_details.append(("📈", "Price > SMA 20", "BULLISH"))
            elif current_price < sma_20 * 0.98:  # 2% below SMA
                sell_signals += 1
                signal_details.append(("📉", "Price < SMA 20", "BEARISH"))
            else:
                signal_details.append(("➡️", "Price near SMA 20", "NEUTRAL"))
            
            # 2. RSI Signal
            if rsi_value < 30:
                buy_signals += 1
                signal_details.append(("🟢", f"RSI {rsi_value:.1f} (Oversold)", "BULLISH"))
            elif rsi_value > 70:
                sell_signals += 1
                signal_details.append(("🔴", f"RSI {rsi_value:.1f} (Overbought)", "BEARISH"))
            else:
                signal_details.append(("🟡", f"RSI {rsi_value:.1f} (Neutral)", "NEUTRAL"))
            
            # 3. MACD Signal
            if macd_line_val > 0:
                buy_signals += 1
                signal_details.append(("📊", "MACD > 0", "BULLISH"))
            else:
                sell_signals += 1
                signal_details.append(("📊", "MACD < 0", "BEARISH"))
            
            # 4. Volume Signal
            if volume_ratio_signal > 1.5:
                buy_signals += 0.5  # Half weight for volume
                signal_details.append(("📢", "High Volume", "BULLISH"))
            elif volume_ratio_signal < 0.5:
                sell_signals += 0.5
                signal_details.append(("🔇", "Low Volume", "CAUTION"))
            else:
                signal_details.append(("📊", "Normal Volume", "NEUTRAL"))
            
            # Determine overall signal
            if buy_signals > sell_signals + 1:
                overall_signal = "STRONG BUY"
                signal_color = "darkgreen"
            elif buy_signals > sell_signals:
                overall_signal = "BUY"
                signal_color = "green"
            elif sell_signals > buy_signals + 1:
                overall_signal = "STRONG SELL"
                signal_color = "darkred"
            elif sell_signals > buy_signals:
                overall_signal = "SELL"
                signal_color = "red"
            else:
                overall_signal = "HOLD"
                signal_color = "orange"
            
            # Display overall signal
            st.markdown(
                f"""
                <div style="
                    background-color: {signal_color}20;
                    border: 2px solid {signal_color};
                    border-radius: 10px;
                    padding: 20px;
                    text-align: center;
                    margin: 20px 0;
                ">
                    <h2 style="color: {signal_color}; margin: 0;">🎯 {overall_signal}</h2>
                    <p style="color: #666; margin: 5px 0 0 0;">
                        {buy_signals:.1f} Buy vs {sell_signals:.1f} Sell signals
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Display signal details
            st.write("#### 📋 Signal Breakdown")
            
            cols = st.columns(2)
            for i, (emoji, text, strength) in enumerate(signal_details):
                with cols[i % 2]:
                    strength_color = "green" if "BULLISH" in strength else "red" if "BEARISH" in strength else "orange"
                    st.markdown(f"{emoji} **{text}** <span style='color:{strength_color};font-size:0.9em'>{strength}</span>", 
                               unsafe_allow_html=True)
            
            # Trading recommendation
            st.write("#### 💡 Trading Recommendation")
            
            if overall_signal in ["STRONG BUY", "BUY"]:
                st.success("""
                **Consider BUYING or ADDING to position:**
                - Multiple bullish signals aligned
                - Consider entering with stop-loss 5-10% below current price
                - Target: 15-20% upside potential
                """)
            elif overall_signal in ["STRONG SELL", "SELL"]:
                st.error("""
                **Consider SELLING or REDUCING position:**
                - Multiple bearish signals aligned
                - Consider taking profits or cutting losses
                - Wait for reversal signals before re-entering
                """)
            else:
                st.info("""
                **HOLD or WAIT for clearer signals:**
                - Mixed signals suggest indecision
                - Monitor key support/resistance levels
                - Wait for confirmation before taking action
                """)
                
        except Exception as e:
            st.error(f"Could not generate trading signals: {e}")
            st.info("Try selecting a longer timeframe (like 3mo or 1y) for better signal generation.")

def show_fundamental_analysis(stock_name, financials):
    """Display fundamental analysis"""
    st.subheader(f"📊 Fundamental Analysis - {stock_name}")
    
    if 'error' in financials:
        st.error("Could not fetch fundamental data")
        return
    
    # Valuation metrics
    st.write("### 💰 Valuation Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("P/E Ratio", financials.get('pe_ratio', 'N/A'))
        st.caption("Lower is better")
    
    with col2:
        st.metric("P/B Ratio", financials.get('pb_ratio', 'N/A'))
        st.caption("< 1 is undervalued")
    
    with col3:
        st.metric("Market Cap", financials.get('market_cap', 'N/A'))
    
    with col4:
        st.metric("Dividend Yield", f"{financials.get('dividend_yield', 'N/A')}%")
    
    # Profitability metrics
    st.write("### 📈 Profitability")
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("ROE", f"{financials.get('roe', 'N/A')}%")
        st.caption("Return on Equity")
    
    with col6:
        st.metric("ROA", f"{financials.get('roa', 'N/A')}%")
        st.caption("Return on Assets")
    
    with col7:
        st.metric("Profit Margin", f"{financials.get('profit_margins', 'N/A')}%")
    
    with col8:
        st.metric("Revenue Growth", f"{financials.get('revenue_growth', 'N/A')}%")
    
    # Financial health
    st.write("### 🏥 Financial Health")
    col9, col10, col11, col12 = st.columns(4)
    
    with col9:
        debt_equity = financials.get('debt_to_equity', 'N/A')
        st.metric("Debt/Equity", debt_equity)
        st.caption("✓ Good" if isinstance(debt_equity, (int, float)) and debt_equity < 1 else "⚠️ High")
    
    with col10:
        current_ratio = financials.get('current_ratio', 'N/A')
        st.metric("Current Ratio", current_ratio)
        st.caption("✓ Good" if isinstance(current_ratio, (int, float)) and current_ratio > 1.5 else "⚠️ Low")
    
    with col11:
        st.metric("Operating Margin", f"{financials.get('operating_margins', 'N/A')}%")
    
    with col12:
        st.metric("Free Cash Flow", financials.get('free_cashflow', 'N/A'))

def show_comparison_analysis(stock_name, ticker, selected_timeframe):
    """Display stock comparison"""
    st.subheader("⚖️ Stock Comparison")
    
    # Select stocks to compare
    other_stocks = [s for s in INDIAN_STOCKS.keys() if s != stock_name]
    compare_with = st.multiselect("Select stocks to compare:", other_stocks, max_selections=3)
    
    if compare_with:
        # Use a fixed timeframe for comparison to ensure consistency
        comparison_timeframe = "1y"  # Fixed 1-year timeframe for comparison
        
        comparison_data = []
        price_data_for_chart = []
        
        # Get data for selected stocks
        for comp_stock in [stock_name] + compare_with:
            comp_ticker = INDIAN_STOCKS[comp_stock]["ticker"]
            df_comp, price_comp, change_comp, max_comp, min_comp = get_stock_data(comp_ticker, comparison_timeframe)
            financials_comp = get_financial_metrics(comp_stock, comp_ticker)
            
            if df_comp is not None and not df_comp.empty:
                # Store for table
                comparison_data.append({
                    'Stock': comp_stock,
                    'Current Price': f"₹{price_comp:.2f}",
                    f'1-Year Return': f"{change_comp:.2f}%",
                    'P/E Ratio': financials_comp.get('pe_ratio', 'N/A'),
                    'Market Cap': financials_comp.get('market_cap', 'N/A'),
                    'Sector': financials_comp.get('sector', 'N/A')
                })
                
                # Store for chart
                price_data_for_chart.append({
                    'stock': comp_stock,
                    'data': df_comp,
                    'price': price_comp
                })
            else:
                st.warning(f"Could not fetch data for {comp_stock}")
        
        if not comparison_data:
            st.error("No comparison data available. Please try different stocks.")
            return
            
        # Create comparison table
        comparison_df = pd.DataFrame(comparison_data)
        st.write("#### 📊 Comparison Table")
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        # Visual comparison - Normalized Price chart
        if price_data_for_chart:
            st.write(f"#### 📈 Price Comparison (1-Year Normalized)")
            fig = go.Figure()
            colors = ['blue', 'red', 'green', 'orange', 'purple']
            
            for idx, stock_data in enumerate(price_data_for_chart):
                df_comp = stock_data['data']
                stock_name_comp = stock_data['stock']
                
                # Normalize prices for comparison (start all at 100)
                if not df_comp.empty and len(df_comp) > 0:
                    normalized_price = (df_comp['Close'] / df_comp['Close'].iloc[0]) * 100
                    
                    fig.add_trace(go.Scatter(
                        x=df_comp.index,
                        y=normalized_price,
                        mode='lines',
                        name=f"{stock_name_comp}",
                        line=dict(color=colors[idx % len(colors)], width=2),
                        hovertemplate=(
                            f"<b>{stock_name_comp}</b><br>" +
                            "Date: %{x|%d %b %Y}<br>" +
                            "Normalized: %{y:.1f} (Base=100)<br>" +
                            "Actual: ₹%{customdata:.2f}<br>" +
                            "<extra></extra>"
                        ),
                        customdata=df_comp['Close']
                    ))
            
            fig.update_layout(
                title="1-Year Normalized Price Comparison (Base=100)",
                xaxis_title="Date",
                yaxis_title="Normalized Price (% from start)",
                height=400,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Add comparison insights
            st.write("#### 📊 Comparison Insights")
            
            # Find best and worst performers
            performance_data = []
            for data in comparison_data:
                try:
                    # Extract percentage from string like "15.25%"
                    change_str = str(data['1-Year Return'])
                    change_pct = float(change_str.replace('%', '').strip())
                    performance_data.append((data['Stock'], change_pct))
                except:
                    continue
            
            if performance_data:
                performance_data.sort(key=lambda x: x[1], reverse=True)
                best_performer = performance_data[0]
                worst_performer = performance_data[-1]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"**🏆 Best 1-Year Performer:** {best_performer[0]} ({best_performer[1]:+.2f}%)")
                with col2:
                    st.error(f"**📉 Worst 1-Year Performer:** {worst_performer[0]} ({worst_performer[1]:+.2f}%)")
        else:
            st.info("No price data available for chart comparison.")
    else:
        st.info("Select stocks to compare from the dropdown above.")

def show_risk_analysis(df, stock_name, financials):
    """Display risk metrics"""
    st.subheader("⚠️ Risk Analysis")
    
    # Calculate volatility (standard deviation of returns)
    returns = df['Close'].pct_change().dropna()
    volatility = returns.std() * np.sqrt(252)  # Annualized volatility
    
    # Calculate Value at Risk (VaR)
    var_95 = np.percentile(returns.dropna(), 5) * 100
    
    # Get debt ratio and ensure it's a float
    debt_ratio_str = financials.get('debt_to_equity', '0')
    try:
        # Handle different string formats
        if isinstance(debt_ratio_str, str):
            # Remove any non-numeric characters except decimal point
            debt_ratio_str = ''.join(c for c in debt_ratio_str if c.isdigit() or c == '.')
            if debt_ratio_str == '':
                debt_ratio = 0
            else:
                debt_ratio = float(debt_ratio_str)
        else:
            debt_ratio = float(debt_ratio_str)
    except (ValueError, TypeError):
        debt_ratio = 0
    
    # Display risk metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Annual Volatility", f"{volatility*100:.2f}%")
        st.caption("Higher = More risk")
    
    with col2:
        st.metric("Daily VaR (95%)", f"{var_95:.2f}%")
        st.caption("Max daily loss with 95% confidence")
    
    with col3:
        st.metric("Max Drawdown", f"{calculate_max_drawdown(df):.2f}%")
        st.caption("Peak to trough decline")
    
    with col4:
        # Safe comparison with float value
        risk_score = "Low" if debt_ratio < 0.5 else "Medium" if debt_ratio < 1 else "High"
        st.metric("Credit Risk", risk_score)
    
    # Risk assessment summary
    st.write("### 📋 Risk Assessment")
    
    risk_factors = []
    
    # Evaluate different risk factors
    if volatility > 0.3:
        risk_factors.append("High price volatility detected")
    
    if debt_ratio > 1:
        risk_factors.append("High debt levels")
    
    current_ratio = financials.get('current_ratio', 2)
    try:
        if isinstance(current_ratio, str):
            current_ratio = float(''.join(c for c in current_ratio if c.isdigit() or c == '.'))
    except (ValueError, TypeError):
        current_ratio = 2
    
    if current_ratio < 1:
        risk_factors.append("Low liquidity (current ratio < 1)")
    
    if len(risk_factors) == 0:
        st.success("✅ Overall Risk: Low - Stock appears relatively stable")
    elif len(risk_factors) <= 2:
        st.warning(f"⚠️ Overall Risk: Moderate - {len(risk_factors)} risk factors identified")
        for factor in risk_factors:
            st.write(f"• {factor}")
    else:
        st.error(f"🔴 Overall Risk: High - {len(risk_factors)} risk factors identified")
        for factor in risk_factors:
            st.write(f"• {factor}")

def show_sentiment_analysis(stock_name):
    """Display news sentiment analysis"""
    st.subheader("📰 Market Sentiment Analysis")
    
    # Get news sentiment
    with st.spinner("Analyzing market sentiment..."):
        try:
            news_data = news_analyzer.get_news_multi_source(query=f"{stock_name} stock", num_articles=5)
            
            if news_data and len(news_data) > 0:
                # Calculate sentiment distribution
                sentiments = [news.get('sentiment', 'Neutral') for news in news_data]
                positive = sentiments.count('Positive')
                negative = sentiments.count('Negative')
                neutral = sentiments.count('Neutral')
                
                # Sentiment chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Positive', 'Negative', 'Neutral'],
                    values=[positive, negative, neutral],
                    hole=.3,
                    marker_colors=['green', 'red', 'gray']
                )])
                fig.update_layout(title="Sentiment Distribution")
                st.plotly_chart(fig, use_container_width=True)
                
                # Display top news
                st.write("### 📰 Recent News Headlines")
                for i, news in enumerate(news_data[:3], 1):
                    sentiment_color = '🟢' if news.get('sentiment') == 'Positive' else '🔴' if news.get('sentiment') == 'Negative' else '🟡'
                    st.write(f"{i}. **{news.get('title', 'No title')}**")
                    st.write(f"   {sentiment_color} {news.get('sentiment', 'Neutral')} | {news.get('source', 'Unknown')}")
                    st.write(f"   {news.get('description', '')[:100]}...")
                    st.divider()
                
                # Overall sentiment summary
                if positive > negative:
                    st.success(f"✅ Overall sentiment is **Positive** ({positive} positive, {negative} negative articles)")
                elif negative > positive:
                    st.error(f"⚠️ Overall sentiment is **Negative** ({negative} negative, {positive} positive articles)")
                else:
                    st.info(f"📊 Overall sentiment is **Neutral** ({neutral} neutral articles)")
            else:
                st.info("No recent news found for this stock")
        except Exception as e:
            st.error(f"Could not fetch sentiment data: {str(e)}")

def calculate_max_drawdown(df):
    """Calculate maximum drawdown"""
    try:
        if df is None or df.empty or 'Close' not in df.columns:
            return 0
        
        # Ensure we have enough data
        if len(df) < 2:
            return 0
        
        # Calculate cumulative returns
        returns = df['Close'].pct_change()
        
        # Handle any NaN values
        if returns.isna().all():
            return 0
            
        cumulative = (1 + returns.fillna(0)).cumprod()
        
        # Calculate running maximum
        running_max = cumulative.expanding().max()
        
        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max
        
        # Find maximum drawdown
        max_drawdown = drawdown.min()
        
        # Return as percentage
        if pd.isna(max_drawdown):
            return 0
        return abs(max_drawdown * 100)
    except Exception as e:
        # Log error and return 0
        print(f"Error calculating max drawdown: {e}")
        return 0