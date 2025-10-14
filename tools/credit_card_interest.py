import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('accounts.db')

def get_credit_card_balances() -> List[Dict[str, Any]]:
    """Get credit card accounts with their balances and APR information."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get credit card accounts with balances
    cursor.execute("""
        SELECT a.id, a.name, a.apr_bps, a.credit_limit_cents,
               bs.amount_cents, bs.as_of_date, bs.source
        FROM account a
        LEFT JOIN balance_snapshot bs ON a.id = bs.account_id
        WHERE a.type = 'LIABILITY'
        AND a.apr_bps IS NOT NULL
        AND bs.as_of_date = (
            SELECT MAX(as_of_date)
            FROM balance_snapshot bs2
            WHERE bs2.account_id = a.id
        )
        ORDER BY a.name
    """)

    credit_cards = []
    for row in cursor.fetchall():
        account_id, name, apr_bps, credit_limit_cents, amount_cents, as_of_date, source = row

        if amount_cents is not None:  # Only include cards with balances
            credit_cards.append({
                'account_id': account_id,
                'name': name,
                'apr_bps': apr_bps,
                'credit_limit_cents': credit_limit_cents,
                'balance_cents': amount_cents,
                'as_of_date': as_of_date,
                'source': source
            })

    conn.close()
    return credit_cards

def calculate_daily_interest(apr_bps: int, balance_cents: int) -> float:
    """Calculate daily interest cost based on APR and balance."""
    if apr_bps is None or balance_cents is None:
        return 0.0

    # Convert APR from basis points to decimal
    apr_decimal = apr_bps / 10000.0

    # Calculate daily rate (APR / 365)
    daily_rate = apr_decimal / 365.0

    # Calculate daily interest cost
    daily_interest_cents = balance_cents * daily_rate

    return daily_interest_cents / 100.0  # Convert to dollars

def format_amount(amount_cents: int) -> str:
    """Format amount in cents to currency string."""
    amount = amount_cents / 100.0
    return f"${amount:,.2f}"

def format_apr(apr_bps: int) -> str:
    """Format APR from basis points to percentage."""
    return f"{apr_bps / 100:.2f}%"

def render():
    st.title("💳 Daily Interest Calculator")
    st.markdown("Calculate daily interest costs for your credit card balances based on APRs.")

    # Check if database exists
    import os
    if not os.path.exists('accounts.db'):
        st.error("accounts.db not found! Please ensure the database file exists.")
        st.stop()

    # Get credit card data
    credit_cards = get_credit_card_balances()

    if not credit_cards:
        st.info("No credit card balances found with APR information.")
        st.markdown("""
        **To see daily interest calculations:**
        1. Make sure your credit cards have APR values set
        2. Add current balance snapshots for your credit cards
        3. Refresh this page
        """)
        return

    # Calculate daily interest for each card
    total_daily_interest = 0.0
    total_balance = 0
    total_credit_limit = 0

    table_data = []

    for card in credit_cards:
        daily_interest = calculate_daily_interest(card['apr_bps'], card['balance_cents'])
        total_daily_interest += daily_interest
        total_balance += card['balance_cents']

        if card['credit_limit_cents']:
            total_credit_limit += card['credit_limit_cents']

        # Calculate utilization percentage
        utilization = 0.0
        if card['credit_limit_cents'] and card['credit_limit_cents'] > 0:
            utilization = (card['balance_cents'] / card['credit_limit_cents']) * 100

        table_data.append({
            'Credit Card': card['name'],
            'APR': format_apr(card['apr_bps']),
            'Balance': format_amount(card['balance_cents']),
            'Credit Limit': format_amount(card['credit_limit_cents']) if card['credit_limit_cents'] else 'N/A',
            'Utilization': f"{utilization:.1f}%" if card['credit_limit_cents'] else 'N/A',
            'Daily Interest': f"${daily_interest:.2f}",
            'Monthly Interest': f"${daily_interest * 30:.2f}",
            'Annual Interest': f"${daily_interest * 365:.2f}"
        })

    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Daily Interest", f"${total_daily_interest:.2f}")

    with col2:
        st.metric("Total Monthly Interest", f"${total_daily_interest * 30:.2f}")

    with col3:
        st.metric("Total Annual Interest", f"${total_daily_interest * 365:.2f}")

    with col4:
        utilization_total = 0.0
        if total_credit_limit > 0:
            utilization_total = (total_balance / total_credit_limit) * 100
        st.metric("Overall Utilization", f"{utilization_total:.1f}%")

    st.markdown("---")

    # Display detailed table
    st.subheader("📊 Credit Card Interest Analysis")

    df = pd.DataFrame(table_data)
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Credit Card": st.column_config.TextColumn("Credit Card", width="medium"),
            "APR": st.column_config.TextColumn("APR", width="small"),
            "Balance": st.column_config.TextColumn("Balance", width="medium"),
            "Credit Limit": st.column_config.TextColumn("Credit Limit", width="medium"),
            "Utilization": st.column_config.TextColumn("Utilization", width="small"),
            "Daily Interest": st.column_config.TextColumn("Daily", width="small"),
            "Monthly Interest": st.column_config.TextColumn("Monthly", width="small"),
            "Annual Interest": st.column_config.TextColumn("Annual", width="small")
        }
    )

    # Download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Interest Analysis as CSV",
        data=csv,
        file_name=f"credit_card_interest_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

    # Additional insights
    st.markdown("---")
    st.subheader("💡 Interest Insights")

    if total_daily_interest > 0:
        # Find highest interest card
        highest_interest_card = max(credit_cards,
                                  key=lambda x: calculate_daily_interest(x['apr_bps'], x['balance_cents']))
        highest_daily = calculate_daily_interest(highest_interest_card['apr_bps'], highest_interest_card['balance_cents'])

        # Find highest APR card
        highest_apr_card = max(credit_cards, key=lambda x: x['apr_bps'])

        col1, col2 = st.columns(2)

        with col1:
            st.info(f"""
            **Highest Daily Interest Cost:**
            {highest_interest_card['name']}
            ${highest_daily:.2f} per day
            """)

        with col2:
            st.info(f"""
            **Highest APR:**
            {highest_apr_card['name']}
            {format_apr(highest_apr_card['apr_bps'])}
            """)

        # Payment recommendations
        st.markdown("### 💰 Payment Recommendations")

        if total_daily_interest > 5.0:  # More than $5/day
            st.warning("""
            **High Interest Alert!** You're paying more than $5 per day in interest.
            Consider prioritizing payments to reduce this cost.
            """)
        elif total_daily_interest > 2.0:  # More than $2/day
            st.info("""
            **Moderate Interest Cost** - You're paying more than $2 per day in interest.
            Consider making extra payments when possible.
            """)
        else:
            st.success("""
            **Good Interest Management** - Your daily interest costs are relatively low.
            Keep up the good work!
            """)

        # Calculate payoff scenarios
        st.markdown("### 📈 Payoff Scenarios")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Pay $100/month", f"${total_daily_interest * 30 - 100:.2f}",
                     "Monthly interest reduction")

        with col2:
            st.metric("Pay $200/month", f"${total_daily_interest * 30 - 200:.2f}",
                     "Monthly interest reduction")

        with col3:
            st.metric("Pay $500/month", f"${total_daily_interest * 30 - 500:.2f}",
                     "Monthly interest reduction")

    else:
        st.success("🎉 **No Interest Charges!** All your credit cards are paid off.")

    # Payment Calculator Section
    st.markdown("---")
    st.subheader("🧮 Payment Calculator")
    st.markdown("Calculate how much interest would be added to a payment amount using your highest APR.")

    # Get highest APR for calculation
    if credit_cards:
        highest_apr_card = max(credit_cards, key=lambda x: x['apr_bps'])
        highest_apr = highest_apr_card['apr_bps']
        highest_apr_name = highest_apr_card['name']

        col1, col2 = st.columns([2, 1])

        with col1:
            payment_amount = st.number_input(
                "Payment Amount ($)",
                min_value=0.0,
                value=100.0,
                step=10.0,
                help="Enter the payment amount you want to calculate interest for"
            )

        with col2:
            is_monthly = st.checkbox(
                "Monthly Payment",
                help="Check if this is a monthly payment (will multiply by 12 for annual calculation)"
            )

        if payment_amount > 0:
            # Calculate interest
            if is_monthly:
                annual_payment = payment_amount * 12
                st.info(f"**Monthly Payment**: ${payment_amount:.2f} × 12 = **${annual_payment:.2f} annually**")
            else:
                annual_payment = payment_amount
                st.info(f"**One-time Payment**: ${payment_amount:.2f}")

            # Calculate daily interest rate
            daily_rate = (highest_apr / 10000.0) / 365.0

            # Calculate interest for different time periods
            daily_interest = annual_payment * daily_rate
            monthly_interest = daily_interest * 30
            annual_interest = daily_interest * 365

            # Display results
            st.markdown("### 💰 Interest Calculation Results")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Daily Interest",
                    f"${daily_interest:.2f}",
                    help=f"Interest added per day at {highest_apr/100:.2f}% APR"
                )

            with col2:
                st.metric(
                    "Monthly Interest",
                    f"${monthly_interest:.2f}",
                    help=f"Interest added per month at {highest_apr/100:.2f}% APR"
                )

            with col3:
                st.metric(
                    "Annual Interest",
                    f"${annual_interest:.2f}",
                    help=f"Interest added per year at {highest_apr/100:.2f}% APR"
                )

            # Show total cost
            total_cost = annual_payment + annual_interest
            interest_percentage = (annual_interest / annual_payment) * 100 if annual_payment > 0 else 0

            st.markdown("### 📊 Total Cost Breakdown")

            col1, col2 = st.columns(2)

            with col1:
                st.success(f"""
                **Total Annual Cost**: ${total_cost:.2f}
                - Principal: ${annual_payment:.2f}
                - Interest: ${annual_interest:.2f}
                """)

            with col2:
                st.warning(f"""
                **Interest Rate Impact**: {interest_percentage:.1f}%
                - APR Used: {highest_apr/100:.2f}%
                - Card: {highest_apr_name}
                """)

            # Payment scenarios
            st.markdown("### 🎯 Payment Scenarios")

            scenarios = [
                ("Minimum Payment", annual_payment * 0.02),  # 2% minimum
                ("Moderate Payment", annual_payment * 0.05),  # 5% payment
                ("Aggressive Payment", annual_payment * 0.10),  # 10% payment
            ]

            scenario_data = []
            for scenario_name, scenario_amount in scenarios:
                scenario_interest = scenario_amount * daily_rate * 365
                scenario_total = scenario_amount + scenario_interest
                scenario_percentage = (scenario_interest / scenario_amount) * 100 if scenario_amount > 0 else 0

                scenario_data.append({
                    "Scenario": scenario_name,
                    "Payment": f"${scenario_amount:.2f}",
                    "Interest": f"${scenario_interest:.2f}",
                    "Total": f"${scenario_total:.2f}",
                    "Interest %": f"{scenario_percentage:.1f}%"
                })

            scenario_df = pd.DataFrame(scenario_data)
            st.dataframe(
                scenario_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Scenario": st.column_config.TextColumn("Payment Scenario", width="medium"),
                    "Payment": st.column_config.TextColumn("Annual Payment", width="small"),
                    "Interest": st.column_config.TextColumn("Annual Interest", width="small"),
                    "Total": st.column_config.TextColumn("Total Cost", width="small"),
                    "Interest %": st.column_config.TextColumn("Interest %", width="small")
                }
            )

            # Download calculator results
            calculator_csv = scenario_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Calculator Results",
                data=calculator_csv,
                file_name=f"payment_calculator_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    else:
        st.info("No credit cards with APR information found. Add credit cards with APR values to use the calculator.")

if __name__ == "__main__":
    render()
