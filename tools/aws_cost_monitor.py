import streamlit as st
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
from datetime import datetime, timedelta
import time

def get_ce_client():
    """Get Cost Explorer client with error handling for credentials."""
    try:
        # Use the 'codiak' profile specifically
        session = boto3.Session(profile_name='codiak')
        return session.client('ce')
    except NoCredentialsError:
        st.error("AWS credentials not found for 'codiak' profile. Please configure your AWS credentials using 'aws configure --profile codiak'.")
        return None
    except Exception as e:
        st.error(f"Error creating Cost Explorer client with 'codiak' profile: {str(e)}")
        return None

def get_cost_data(ce_client, start_date, end_date, granularity='MONTHLY'):
    """Get cost data from AWS Cost Explorer."""
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'REGION'}
            ]
        )
        return response
    except ClientError as e:
        st.error(f"Error getting cost data: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def parse_cost_data(response):
    """Parse the cost data response into a more usable format."""
    if not response:
        return []

    costs = []
    for result in response.get('ResultsByTime', []):
        time_period = result['TimePeriod']
        start_date = time_period['Start']
        end_date = time_period['End']

        for group in result.get('Groups', []):
            keys = group['Keys']
            service = keys[0] if len(keys) > 0 else 'Unknown'
            region = keys[1] if len(keys) > 1 else 'Unknown'

            # Get the cost amount
            metrics = group['Metrics']
            cost_amount = float(metrics['UnblendedCost']['Amount'])
            cost_unit = metrics['UnblendedCost']['Unit']

            costs.append({
                'Service': service,
                'Region': region,
                'Cost': cost_amount,
                'Unit': cost_unit,
                'Start Date': start_date,
                'End Date': end_date
            })

    return costs

def get_current_month_costs(ce_client):
    """Get costs for the current month."""
    today = datetime.now()
    start_date = today.replace(day=1)
    end_date = today + timedelta(days=1)  # Include today

    return get_cost_data(ce_client, start_date, end_date, 'DAILY')

def get_last_30_days_costs(ce_client):
    """Get costs for the last 30 days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    return get_cost_data(ce_client, start_date, end_date, 'DAILY')

def get_custom_period_costs(ce_client, start_date, end_date):
    """Get costs for a custom period."""
    return get_cost_data(ce_client, start_date, end_date, 'DAILY')

def render():
    st.write("Monitor your AWS costs and spending patterns using AWS Cost Explorer.")

    # Initialize session state for messages
    if 'cost_message' not in st.session_state:
        st.session_state.cost_message = None
    if 'cost_message_type' not in st.session_state:
        st.session_state.cost_message_type = None

    # Get Cost Explorer client
    ce_client = get_ce_client()
    if not ce_client:
        st.stop()

    # Period selection
    st.subheader("📊 Cost Analysis Period")
    period_options = {
        "Current Month": "current_month",
        "Last 30 Days": "last_30_days",
        "Custom Period": "custom_period"
    }

    selected_period = st.selectbox(
        "Select time period:",
        list(period_options.keys()),
        key="cost_period_selector"
    )

    # Handle custom period selection
    if selected_period == "Custom Period":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now() - timedelta(days=30),
                key="cost_start_date"
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now(),
                key="cost_end_date"
            )

        if start_date >= end_date:
            st.error("Start date must be before end date.")
            return

    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh Costs", use_container_width=True):
            st.rerun()

    with col2:
        st.write("Click refresh to update the cost data")

    # Get cost data based on selection
    cost_data = None
    if selected_period == "Current Month":
        cost_data = get_current_month_costs(ce_client)
    elif selected_period == "Last 30 Days":
        cost_data = get_last_30_days_costs(ce_client)
    elif selected_period == "Custom Period":
        cost_data = get_custom_period_costs(ce_client, start_date, end_date)

    if not cost_data:
        st.info("No cost data available for the selected period or no access to Cost Explorer.")
        return

    # Parse the cost data
    costs = parse_cost_data(cost_data)

    if not costs:
        st.info("No cost data found for the selected period.")
        return

    # Convert to DataFrame for analysis
    df = pd.DataFrame(costs)

    # Calculate total cost
    total_cost = df['Cost'].sum()

    # Display summary metrics
    st.subheader("💰 Cost Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cost", f"${total_cost:.2f}")
    with col2:
        st.metric("Services", df['Service'].nunique())
    with col3:
        st.metric("Regions", df['Region'].nunique())

    # Service breakdown
    st.subheader("📈 Service Breakdown")
    service_costs = df.groupby('Service')['Cost'].sum().sort_values(ascending=False)

    # Create a bar chart for top services
    if len(service_costs) > 0:
        st.bar_chart(service_costs.head(10))

        # Show detailed service breakdown
        st.write("**Top Services by Cost:**")
        service_df = pd.DataFrame({
            'Service': service_costs.index,
            'Cost': service_costs.values
        })
        service_df['Percentage'] = (service_df['Cost'] / total_cost * 100).round(2)

        for _, row in service_df.head(10).iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['Service']}**")
            with col2:
                st.write(f"${row['Cost']:.2f}")
            with col3:
                st.write(f"{row['Percentage']}%")

    # Regional breakdown
    st.subheader("🌍 Regional Breakdown")
    region_costs = df.groupby('Region')['Cost'].sum().sort_values(ascending=False)

    if len(region_costs) > 0:
        # Show regional costs
        region_df = pd.DataFrame({
            'Region': region_costs.index,
            'Cost': region_costs.values
        })
        region_df['Percentage'] = (region_df['Cost'] / total_cost * 100).round(2)

        for _, row in region_df.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['Region']}**")
            with col2:
                st.write(f"${row['Cost']:.2f}")
            with col3:
                st.write(f"{row['Percentage']}%")

    # Detailed cost table
    st.subheader("📋 Detailed Cost Breakdown")

    # Add date range info
    if selected_period == "Current Month":
        st.caption(f"Showing costs from {datetime.now().replace(day=1).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
    elif selected_period == "Last 30 Days":
        st.caption(f"Showing costs from {(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
    elif selected_period == "Custom Period":
        st.caption(f"Showing costs from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    # Show the detailed data
    st.dataframe(
        df[['Service', 'Region', 'Cost', 'Start Date', 'End Date']].sort_values('Cost', ascending=False),
        use_container_width=True
    )

    # Export option
    st.subheader("💾 Export Data")
    if st.button("Download CSV", use_container_width=True):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Cost Data",
            data=csv,
            file_name=f"aws_costs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # Show messages
    if st.session_state.cost_message:
        if st.session_state.cost_message_type == 'success':
            st.success(st.session_state.cost_message)
        else:
            st.error(st.session_state.cost_message)

        # Clear message after showing
        if st.button("Clear Message"):
            st.session_state.cost_message = None
            st.session_state.cost_message_type = None
            st.rerun()