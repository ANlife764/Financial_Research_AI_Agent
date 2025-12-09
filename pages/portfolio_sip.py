import streamlit as st
from utils.portfolio_calc import (
    calculate_sip_future_value,
    calculate_monthly_sip_required
)

def calc_SIP():
    st.header("SIP & Goal Planning")
        
        # SIP Calculator
    st.subheader("Systematic Investment Plan (SIP) Calculator")
    with st.form("sip_form"):
            sip_amount = st.number_input("Monthly SIP Amount (₹)", min_value=100.0, value=5000.0, step=100.0)
            sip_return = st.slider("Expected Annual Return (%)", min_value=5.0, max_value=25.0, value=12.0, step=0.5)
            sip_years = st.slider("Investment Duration (Years)", min_value=1, max_value=40, value=15)
            
            if st.form_submit_button("Calculate Future Value"):
                future_value = calculate_sip_future_value(sip_amount, sip_return, sip_years)
                st.metric("Estimated Future Value", f"₹{future_value:,.0f}")
                
    st.markdown("---")
        
        # Goal-Based Investment
    st.subheader("Goal-Based Investment Suggestions")
    with st.form("goal_form"):
            goal_amount = st.number_input("Goal Amount Needed (₹)", min_value=1000.0, value=500000.0, step=1000.0)
            goal_return = st.slider("Expected Annual Return (%)", min_value=5.0, max_value=25.0, value=12.0, step=0.5, key='g_ret')
            goal_years = st.slider("Goal Timeline (Years)", min_value=1, max_value=40, value=10, key='g_years')
            
            if st.form_submit_button("Calculate Required SIP"):
                required_sip = calculate_monthly_sip_required(goal_amount, goal_return, goal_years)
                st.success(f"To reach **₹{goal_amount:,.0f}** in {goal_years} years, you need to invest a monthly SIP of:")
                st.metric("Required Monthly SIP", f"₹{required_sip:,.0f}")
    
    st.divider()
    if st.button("← Back to Portfolio"):
        st.session_state.current_page = "Portfolio"