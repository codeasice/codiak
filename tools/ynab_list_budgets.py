import streamlit as st
import os
import pandas as pd
import sqlite3
from datetime import datetime

def get_db_connection():
    """Get database connection."""
    return sqlite3.connect('accounts.db')

def get_ynab_data_from_db():
    """Get YNAB budgets and categories from SQLite database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get budgets
    cursor.execute("SELECT * FROM ynab_budgets")
    budgets_data = cursor.fetchall()
    budgets = []
    for budget in budgets_data:
        budgets.append({
            'id': budget[0],
            'name': budget[1],
            'last_modified_on': budget[2],
            'first_month': budget[3],
            'last_month': budget[4],
            'date_format': {'format': budget[5]} if budget[5] else None,
            'currency_format': {
                'iso_code': budget[6],
                'example_format': budget[7],
                'decimal_digits': budget[8],
                'decimal_separator': budget[9],
                'symbol_first': budget[10],
                'group_separator': budget[11],
                'currency_symbol': budget[12],
                'display_symbol': budget[13]
            } if budget[6] else None
        })

    # Get categories
    cursor.execute("SELECT * FROM ynab_categories")
    categories_data = cursor.fetchall()
    categories = []
    for cat in categories_data:
        categories.append({
            'id': cat[0],
            'name': cat[1],
            'category_group_id': cat[2],
            'category_group_name': cat[3],
            'full_name': cat[4],
            'hidden': bool(cat[5]),
            'original_category_group_id': cat[6],
            'note': cat[7],
            'budgeted': cat[8],
            'activity': cat[9],
            'balance': cat[10],
            'goal_type': cat[11],
            'goal_creation_month': cat[12],
            'goal_target': cat[13],
            'goal_target_month': cat[14],
            'goal_percentage_complete': cat[15],
            'deleted': bool(cat[16])
        })

    # Get category groups
    cursor.execute("SELECT * FROM ynab_category_groups")
    category_groups_data = cursor.fetchall()
    category_groups = []
    for group in category_groups_data:
        category_groups.append({
            'id': group[0],
            'name': group[1],
            'updated_at': group[2]
        })

    conn.close()

    return budgets, categories, category_groups

def render():
    st.title("📊 YNAB Budgets & Categories")
    st.write("View your YNAB budgets and categories from the database.")

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

    st.success(f"✅ **Found YNAB tables in database** ({len(ynab_tables)} tables)")

    # Load data button
    if st.button("📊 Load Budgets & Categories from Database"):
        with st.spinner("Loading data from database..."):
            try:
                budgets, categories, category_groups = get_ynab_data_from_db()

                if not budgets:
                    st.warning("No budgets found in database. Please import YNAB data first.")
                    return

                st.success(f"✅ **Loaded {len(budgets)} budgets and {len(categories)} categories!**")

                # Display budgets summary
                st.subheader("📋 Budgets Summary")
                budget_df = pd.DataFrame(budgets)
                st.dataframe(budget_df[['name', 'last_modified_on', 'first_month', 'last_month']],
                           use_container_width=True, hide_index=True)

                # Display categories by budget
                st.subheader("📂 Categories by Budget")

                # Group categories by budget (assuming all categories belong to the same budget for now)
                if categories:
                    # Create table data
                    table_data = []
                    for category in categories:
                        table_data.append({
                            'Budget': budgets[0]['name'] if budgets else 'Unknown',
                            'Category Group': category['category_group_name'],
                            'Category': category['name'],
                            'Category ID': category['id'],
                            'Budgeted': f"${category['budgeted']/1000:.2f}" if category['budgeted'] else '$0.00',
                            'Activity': f"${category['activity']/1000:.2f}" if category['activity'] else '$0.00',
                            'Balance': f"${category['balance']/1000:.2f}" if category['balance'] else '$0.00',
                            'Hidden': 'Yes' if category['hidden'] else 'No',
                            'Deleted': 'Yes' if category['deleted'] else 'No'
                        })

                    if table_data:
                        df = pd.DataFrame(table_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No categories found.")

                # Category groups summary
                if category_groups:
                    st.subheader("📁 Category Groups")
                    group_df = pd.DataFrame(category_groups)
                    st.dataframe(group_df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"❌ **Error loading data**: {str(e)}")

    # Data source information
    with st.expander("ℹ️ About this tool"):
        st.markdown("""
        **What this tool does:**
        - Loads YNAB budgets and categories from the SQLite database
        - Shows budget information and category structure
        - Displays category groups and their organization
        - Provides financial details for each category

        **Data Source:**
        - **SQLite Database**: Reads from ynab_budgets, ynab_categories, and ynab_category_groups tables
        - **No API calls**: Faster loading and no rate limits
        - **Offline capable**: Works without internet connection

        **Requirements:**
        - Database must contain YNAB data (imported via YNAB Export Data tool)
        - YNAB tables must exist in the database

        **Category Information Displayed:**
        - Category name and ID
        - Category group assignment
        - Budgeted amounts
        - Activity (spending)
        - Current balance
        - Hidden/deleted status
        """)