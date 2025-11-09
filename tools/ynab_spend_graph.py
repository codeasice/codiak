import streamlit as st
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Import plotly only when needed to avoid import errors
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# Import ynab only when needed to avoid import errors
try:
    import ynab
    YNAB_AVAILABLE = True
except ImportError:
    YNAB_AVAILABLE = False

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('accounts.db')

def get_budgets_from_db() -> List[Dict[str, Any]]:
    """Get budgets from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, last_modified_on FROM ynab_budgets")
    budgets_data = cursor.fetchall()

    budgets = []
    for budget in budgets_data:
        budgets.append({
            'id': budget[0],
            'name': budget[1],
            'last_modified_on': budget[2]
        })

    conn.close()
    return budgets

def get_categories_from_db(budget_id: Optional[str] = None) -> Dict[str, Dict]:
    """Get all categories from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if budget_id:
        # Get categories for a specific budget
        query = """
            SELECT DISTINCT c.id, c.name, c.category_group_name
            FROM ynab_categories c
            WHERE c.id IN (
                SELECT DISTINCT t.category_id
                FROM ynab_transactions t
                WHERE t.category_id IS NOT NULL
                AND t.deleted = 0
                AND EXISTS (
                    SELECT 1 FROM ynab_account ya
                    WHERE ya.ynab_account_id = t.account_id
                    AND ya.budget_id = ?
                )
            )
        """
        cursor.execute(query, (budget_id,))
    else:
        # Get all categories
        query = """
            SELECT DISTINCT c.id, c.name, c.category_group_name
            FROM ynab_categories c
            WHERE c.id IN (
                SELECT DISTINCT category_id
                FROM ynab_transactions
                WHERE category_id IS NOT NULL
                AND deleted = 0
            )
        """
        cursor.execute(query)

    categories_data = cursor.fetchall()

    category_mapping = {}
    for cat in categories_data:
        category_mapping[cat[0]] = {
            'id': cat[0],
            'name': cat[1],
            'group_name': cat[2],
            'full_name': f"{cat[2]} > {cat[1]}" if cat[2] else cat[1]
        }

    conn.close()
    return category_mapping

def get_transactions_for_date_range(
    budget_id: str,
    category_ids: List[str],
    start_date: str,
    end_date: str
) -> List[Dict[str, Any]]:
    """Get transactions from database for specified categories and date range."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if not category_ids:
        return []

    # Build query with category and date filters
    placeholders = ','.join(['?' for _ in category_ids])
    query = f"""
        SELECT t.id, t.date, t.amount, t.category_id, t.category_name,
               c.name as category_name_from_cat, c.category_group_name
        FROM ynab_transactions t
        LEFT JOIN ynab_categories c ON t.category_id = c.id
        WHERE t.category_id IN ({placeholders})
        AND t.date >= ?
        AND t.date <= ?
        AND t.deleted = 0
        AND EXISTS (
            SELECT 1 FROM ynab_account ya
            WHERE ya.ynab_account_id = t.account_id
            AND ya.budget_id = ?
        )
        ORDER BY t.date ASC
    """

    params = list(category_ids) + [start_date, end_date, budget_id]
    cursor.execute(query, params)
    transactions_data = cursor.fetchall()

    transactions = []
    for txn in transactions_data:
        # Use joined category name if available, fallback to stored name
        category_name = txn[5] if txn[5] else (txn[4] if txn[4] else 'Unknown')
        category_group_name = txn[6] if txn[6] else None

        # Build full category name to match UI format (Group > Category)
        # Match the logic from get_categories_from_db: f"{group} > {name}" if group else name
        if category_group_name:
            full_category_name = f"{category_group_name} > {category_name}"
        else:
            full_category_name = category_name

        transactions.append({
            'id': txn[0],
            'date': txn[1],
            'amount': txn[2],  # Amount in milliunits
            'category_id': txn[3],
            'category_name': full_category_name,  # Use full name to match UI
            'category_group_name': category_group_name
        })

    conn.close()
    return transactions

def aggregate_daily_spend(transactions: List[Dict[str, Any]]) -> pd.DataFrame:
    """Aggregate transactions by day and category."""
    if not transactions:
        return pd.DataFrame(columns=['date', 'category_name', 'amount'])

    # Group by date and category
    daily_totals = defaultdict(lambda: defaultdict(float))

    for txn in transactions:
        # Parse date (handle both ISO format and YYYY-MM-DD)
        try:
            if 'T' in txn['date']:
                date_obj = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(txn['date'], '%Y-%m-%d')
        except:
            continue

        date_str = date_obj.strftime('%Y-%m-%d')
        category_name = txn['category_name']
        # Convert milliunits to dollars (negative for spending)
        amount = txn['amount'] / 1000.0

        # Only count negative amounts (spending)
        if amount < 0:
            daily_totals[date_str][category_name] += abs(amount)

    # Convert to DataFrame
    data = []
    for date_str, categories in daily_totals.items():
        for category_name, amount in categories.items():
            data.append({
                'date': date_str,
                'category_name': category_name,
                'amount': amount
            })

    df = pd.DataFrame(data)
    if df.empty:
        return df

    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    return df

def create_spend_graph(df: pd.DataFrame, selected_categories: List[str]) -> go.Figure:
    """Create a line graph of daily spend by category."""
    if df.empty or selected_categories is None:
        fig = go.Figure()
        fig.add_annotation(
            text="No data to display. Select categories and a date range.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig

    # Filter to only selected categories
    df_filtered = df[df['category_name'].isin(selected_categories)].copy()

    if df_filtered.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No transactions found for selected categories in date range.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig

    # Create pivot table for easy plotting
    pivot_df = df_filtered.pivot_table(
        index='date',
        columns='category_name',
        values='amount',
        aggfunc='sum',
        fill_value=0
    )

    # Create figure
    fig = go.Figure()

    # Add a line for each category
    for category in selected_categories:
        if category in pivot_df.columns:
            fig.add_trace(go.Scatter(
                x=pivot_df.index,
                y=pivot_df[category],
                mode='lines+markers',
                name=category,
                line=dict(width=2),
                marker=dict(size=4)
            ))

    # Update layout
    fig.update_layout(
        title='Daily YNAB Transaction Spend by Category',
        xaxis_title='Date',
        yaxis_title='Amount Spent ($)',
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01
        ),
        height=600,
        margin=dict(l=50, r=150, t=50, b=50)
    )

    # Format x-axis
    fig.update_xaxes(
        tickformat='%Y-%m-%d',
        tickangle=45
    )

    # Format y-axis as currency
    fig.update_yaxes(
        tickformat='$,.2f'
    )

    return fig

def render():
    """Main render function for the YNAB Spend Graph tool."""
    # Check if database exists
    if not os.path.exists('accounts.db'):
        st.error("❌ **Database not found**")
        st.markdown("""
        The accounts.db file doesn't exist. Please:

        1. **Create the database** using the account management tools
        2. **Import YNAB data** using the YNAB Export Data tool
        """)
        return

    # Check if YNAB tables exist
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'ynab_%'")
    ynab_tables = cursor.fetchall()
    conn.close()

    if not ynab_tables:
        st.error("❌ **No YNAB tables found in database**")
        st.markdown("""
        No YNAB tables found in the database. Please:

        1. **Import YNAB data** using the YNAB Export Data tool
        2. **Or use the live API** version of this tool
        """)
        return

    # Get budgets for selection
    budgets = get_budgets_from_db()

    if not budgets:
        st.warning("No budgets found in database. Please import YNAB data first.")
        return

    # Budget selection
    budget_options = {budget['name']: budget['id'] for budget in budgets}
    selected_budget_name = st.selectbox(
        "Select a budget:",
        options=list(budget_options.keys()),
        help="Choose which budget's transactions to analyze"
    )

    selected_budget_id = budget_options[selected_budget_name]

    # Get categories for this budget
    categories = get_categories_from_db(selected_budget_id)

    if not categories:
        st.warning("No categories found for this budget. Please ensure transactions are categorized.")
        return

    # Category selection (multi-select)
    st.subheader("📊 Select Categories")
    category_options = sorted([cat['full_name'] for cat in categories.values()])
    selected_category_names = st.multiselect(
        "Choose categories to graph:",
        options=category_options,
        default=category_options[:5] if len(category_options) >= 5 else category_options,
        help="Select one or more categories to display on the graph"
    )

    if not selected_category_names:
        st.info("Please select at least one category to display on the graph.")
        return

    # Map full names back to category IDs
    category_name_to_id = {
        cat['full_name']: cat['id']
        for cat in categories.values()
    }
    selected_category_ids = [
        category_name_to_id[name] for name in selected_category_names
        if name in category_name_to_id
    ]

    # Date range selection
    st.subheader("📅 Select Date Range")
    col1, col2 = st.columns(2)

    with col1:
        # Default to last 30 days
        default_start = datetime.now() - timedelta(days=30)
        start_date = st.date_input(
            "Start Date:",
            value=default_start,
            help="Start date for the analysis period"
        )

    with col2:
        end_date = st.date_input(
            "End Date:",
            value=datetime.now(),
            help="End date for the analysis period"
        )

    if start_date > end_date:
        st.error("Start date must be before end date.")
        return

    # Load and display graph
    if st.button("📈 Generate Graph", type="primary"):
        with st.spinner("Loading transactions and generating graph..."):
            # Get transactions
            transactions = get_transactions_for_date_range(
                selected_budget_id,
                selected_category_ids,
                start_date.isoformat(),
                end_date.isoformat()
            )

            if not transactions:
                st.warning("No transactions found for the selected categories and date range.")
                return

            st.success(f"✅ Found {len(transactions)} transactions")

            # Aggregate by day
            df = aggregate_daily_spend(transactions)

            if df.empty:
                st.warning("No spending transactions found (all amounts were positive).")
                return

            # Display summary statistics
            st.subheader("📊 Summary Statistics")
            col1, col2, col3 = st.columns(3)

            total_spend = df['amount'].sum()
            avg_daily_spend = df.groupby('date')['amount'].sum().mean()
            max_daily_spend = df.groupby('date')['amount'].sum().max()

            with col1:
                st.metric("Total Spend", f"${total_spend:,.2f}")
            with col2:
                st.metric("Average Daily Spend", f"${avg_daily_spend:,.2f}")
            with col3:
                st.metric("Max Daily Spend", f"${max_daily_spend:,.2f}")

            # Create and display graph
            st.subheader("📈 Daily Spend Graph")

            if not PLOTLY_AVAILABLE:
                st.error("Plotly is not available. Please install it with: pip install plotly")
                return

            fig = create_spend_graph(df, selected_category_names)

            st.plotly_chart(fig, use_container_width=True)

            # Show category breakdown table
            st.subheader("📋 Category Breakdown")
            category_totals = df.groupby('category_name')['amount'].sum().sort_values(ascending=False)
            category_df = pd.DataFrame({
                'Category': category_totals.index,
                'Total Spend': category_totals.values
            })
            category_df['Total Spend'] = category_df['Total Spend'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(category_df, use_container_width=True, hide_index=True)

    # Data source information
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        **What this tool does:**
        - Displays a graph of daily YNAB transaction spend for selected categories
        - Shows spending trends over a selected date range
        - Provides summary statistics and category breakdowns
        - Aggregates transactions by day and category

        **Data Source:**
        - **SQLite Database**: Reads from ynab_transactions and ynab_categories tables
        - **No API calls**: Faster loading and no rate limits
        - **Offline capable**: Works without internet connection

        **Requirements:**
        - Database must contain YNAB data (imported via YNAB Export Data tool)
        - YNAB tables must exist in the database
        - Transactions must be categorized

        **Note:**
        - Only negative transaction amounts (spending) are included in the graph
        - Positive amounts (income/transfers) are excluded
        - Amounts are displayed in dollars (converted from milliunits)
        """)

