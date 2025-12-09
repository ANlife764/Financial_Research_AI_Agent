# app.py
import streamlit as st
import pandas as pd
import sys
import types

# Create dummy multitasking module if import fails
try:
    import multitasking
except ImportError:
    print("Creating dummy multitasking module...")
    multitasking = types.ModuleType('multitasking')
    multitasking.disable = lambda: None
    multitasking.task = lambda func: func
    sys.modules['multitasking'] = multitasking

st.set_page_config(
    page_title="AI Financial Agent",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar by default
)

# Custom CSS for top navigation
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .top-nav {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: center;
        gap: 1rem;
    }
    .nav-button {
        padding: 0.5rem 1.5rem;
        border: none;
        border-radius: 5px;
        background-color: white;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .nav-button:hover {
        background-color: #1f77b4;
        color: white;
    }
    .nav-button.active {
        background-color: #1f77b4;
        color: white;
    }
    /* Hide the default sidebar */
    section[data-testid="stSidebar"] {
        display: none;
    }
    /header[data-testid="stHeader"] {
    display: none !important;
    }


</style>
""", unsafe_allow_html=True)

def main():
    # Top Navigation Bar
    st.markdown('<div class="main-header">🤖 AI Financial Research Assistant</div>', unsafe_allow_html=True)
    
    # Navigation buttons in top bar
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        home_clicked = st.button("🏠 Home", use_container_width=True)
    with col2:
        news_clicked = st.button("📰 News", use_container_width=True)
    with col3:
        ai_clicked = st.button("🤖 AI Agent", use_container_width=True)
    with col4:
        portfolio_clicked = st.button("💼 Portfolio", use_container_width=True)
    with col5:
        analytics_clicked = st.button("📊 Analytics", use_container_width=True)
    
    # Determine current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    
    # Update page based on button clicks
    if home_clicked:
        st.session_state.current_page = "Home"
        st.rerun()
    elif news_clicked:
        st.session_state.current_page = "News"
        st.rerun()
    elif ai_clicked:
        st.session_state.current_page = "AI Agent"
        st.rerun()
    elif portfolio_clicked:
        st.session_state.current_page = "Portfolio"
        st.rerun()
    elif analytics_clicked:
        st.session_state.current_page = "Analytics"
        st.rerun()
    
    # Display current page
    if st.session_state.current_page == "Home":
        from pages.Home import home_page
        home_page()
    elif st.session_state.current_page == "News":
        from pages.News import news_page
        news_page()
    elif st.session_state.current_page == "AI Agent":
        from pages.AI_Agent import ai_agent_page
        ai_agent_page()
    elif st.session_state.current_page == "Portfolio":
        from pages.Portfolio import portfolio_page
        portfolio_page()
    elif st.session_state.current_page == "AddStock":
        from pages.portfolio_add import add_stock_page
        add_stock_page()
    elif st.session_state.current_page == "SIP":
        from pages.portfolio_sip import calc_SIP
        calc_SIP()
    elif st.session_state.current_page == "Tax":
        from pages.portfolio_tax import tax_calc
        tax_calc()
    elif st.session_state.current_page == "Extr":
        from pages.portfolio_extr import exptr
        exptr()
    elif st.session_state.current_page == "Analytics":
        from pages.Analytics import analytics_page
        analytics_page()

    def initialize_portfolio_state():
        """Initialize or load the dynamic transaction history."""
        if 'transactions_df' not in st.session_state:
        # Columns for all transactions (Buy/Sell/Expense/Income)
            st.session_state.transactions_df = pd.DataFrame(
            columns=['Date', 'Type', 'Category', 'Ticker', 'Quantity', 'Price', 'Amount']
            )
    initialize_portfolio_state()

    # Footer
    st.markdown("---")
    st.markdown("💡 **Tip**: Use the AI Agent for personalized investment insights!")

if __name__ == "__main__":
    main()