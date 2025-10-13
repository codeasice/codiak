import streamlit as st
import os
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
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

def load_data_from_json(filename: str) -> Optional[Dict]:
    """Load YNAB data from JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading JSON file: {e}")
        return None

def get_available_json_files() -> List[str]:
    """Get list of available YNAB JSON export files."""
    json_files = [f for f in os.listdir('.') if f.startswith('ynab_data_') and f.endswith('.json')]
    return sorted(json_files, reverse=True)  # Newest first

def get_ynab_client():
    """Get configured YNAB API client."""
    if not YNAB_AVAILABLE:
        st.error("YNAB module not available. Please install it with: pip install ynab")
        st.stop()

    ynab_api_key = os.getenv('YNAB_API_KEY')
    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

    configuration = ynab.Configuration(access_token=ynab_api_key)
    return configuration

def get_budget_selection():
    """Get budget selection from user."""
    configuration = get_ynab_client()

    with ynab.ApiClient(configuration) as api_client:
        budgets_api = ynab.api.budgets_api.BudgetsApi(api_client)
        budgets_response = budgets_api.get_budgets()

        budgets = budgets_response.data.budgets
        budget_names = [budget.name for budget in budgets]
        selected_budget_name = st.selectbox("Select a budget", budget_names)
        selected_budget_id = [budget.id for budget in budgets if budget.name == selected_budget_name][0]
        return selected_budget_id, configuration

def get_categories_from_json(json_data: Dict) -> Dict[str, Dict]:
    """Get all categories from JSON data."""
    category_mapping = {}
    for cat in json_data.get('categories', []):
        category_mapping[cat['id']] = {
            'name': cat['name'],
            'group_name': cat['category_group_name'],
            'full_name': f"{cat['category_group_name']} > {cat['name']}",  # Build full_name for compatibility
            'id': cat['id']
        }
    return category_mapping

def get_categories(budget_id: str, configuration) -> Dict[str, Dict]:
    """Get all categories for a budget."""
    with ynab.ApiClient(configuration) as api_client:
        categories_api = ynab.api.categories_api.CategoriesApi(api_client)
        categories_response = categories_api.get_categories(budget_id)

        category_mapping = {}
        for group in categories_response.data.category_groups:
            for cat in group.categories:
                category_mapping[cat.id] = {
                    'name': cat.name,
                    'group_name': group.name,
                    'full_name': f"{group.name} > {cat.name}",
                    'id': cat.id
                }
        return category_mapping

def get_transactions_for_month_from_json(json_data: Dict, year: int, month: int) -> List[Dict]:
    """Get all transactions for a specific month from JSON data."""
    month_transactions = []

    for txn in json_data.get('transactions', []):
        try:
            # Handle different date formats
            date_str = txn['date']
            if isinstance(date_str, str):
                if date_str.endswith('Z'):
                    date_str = date_str[:-1] + '+00:00'
                elif '+' not in date_str and 'T' in date_str:
                    date_str = date_str + '+00:00'
                txn_date = datetime.fromisoformat(date_str)
            else:
                # Handle date object format
                txn_date = datetime.combine(datetime.fromisoformat(date_str), datetime.min.time())

            if txn_date.year == year and txn_date.month == month:
                # Include all transactions except transfers (amount != 0)
                if txn['amount'] != 0:
                    # Check if this is a transfer transaction
                    is_transfer = txn.get('transfer_account_id') is not None
                    if not is_transfer:
                        month_transactions.append({
                            'id': txn['id'],
                            'date': txn['date'],
                            'payee_name': txn.get('payee_name') or 'Unknown Payee',
                            'memo': txn.get('memo') or '',
                            'amount': txn['amount'],
                            'category_id': txn.get('category_id') or 'uncategorized',
                            'category_name': txn.get('category_name') or '❓ Uncategorized',
                            'account_id': txn.get('account_id'),
                            'account_name': txn.get('account_name') or 'Unknown Account',
                            'cleared': txn.get('cleared'),
                            'approved': txn.get('approved')
                        })
        except (ValueError, AttributeError, TypeError) as e:
            # Skip transactions with invalid dates
            continue

    return month_transactions

def get_transactions_for_month(budget_id: str, configuration, year: int, month: int) -> List[Dict]:
    """Get all transactions for a specific month."""
    with ynab.ApiClient(configuration) as api_client:
        transactions_api = ynab.api.transactions_api.TransactionsApi(api_client)
        response = transactions_api.get_transactions(budget_id)
        transactions = response.data.transactions

        # Filter transactions for the specified month
        month_transactions = []
        for txn in transactions:
            try:
                # Handle both string and date object formats
                if isinstance(txn.var_date, str):
                    # Handle string date formats
                    date_str = txn.var_date
                    if date_str.endswith('Z'):
                        date_str = date_str[:-1] + '+00:00'
                    elif '+' not in date_str and 'T' in date_str:
                        date_str = date_str + '+00:00'
                    txn_date = datetime.fromisoformat(date_str)
                else:
                    # Handle date object format
                    txn_date = datetime.combine(txn.var_date, datetime.min.time())

                if txn_date.year == year and txn_date.month == month:
                    # Include all transactions except transfers (amount != 0)
                    if txn.amount != 0:
                        # Check if this is a transfer transaction
                        is_transfer = hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None
                        if not is_transfer:
                            month_transactions.append({
                                'id': txn.id,
                                'date': txn.var_date,
                                'payee_name': txn.payee_name or 'Unknown Payee',
                                'memo': txn.memo or '',
                                'amount': txn.amount,
                                'category_id': txn.category_id or 'uncategorized',
                                'category_name': txn.category_name or '❓ Uncategorized',
                                'account_id': txn.account_id,
                                'account_name': txn.account_name or 'Unknown Account',
                                'cleared': txn.cleared,
                                'approved': txn.approved
                            })
            except (ValueError, AttributeError, TypeError) as e:
                # Skip transactions with invalid dates
                continue

        return month_transactions

def is_expense_transaction(txn, account, category):
    """Check if a transaction is an expense (not income/deposit/transfer)."""
    # Skip if it's income (positive amount)
    if txn['amount'] > 0:
        print(f"🚫 SKIPPED (Income): {txn['payee_name']} - ${abs(txn['amount'])/1000:,.2f} (positive amount)")
        return False

    # Skip if it's a transfer
    if txn.get('transfer_account_id') is not None:
        print(f"🚫 SKIPPED (Transfer): {txn['payee_name']} - ${abs(txn['amount'])/1000:,.2f} (transfer between accounts)")
        return False

    # Skip if it's from a credit card account
    if account and account.get('type') == 'creditCard':
        print(f"🚫 SKIPPED (Credit Card): {txn['payee_name']} - ${abs(txn['amount'])/1000:,.2f} (credit card account)")
        return False

    # Skip if it's an income category
    if category and category.get('group_name') in ['Income', 'Ready to Assign', 'Inflow: Ready to Assign']:
        print(f"🚫 SKIPPED (Income Category): {txn['payee_name']} - ${abs(txn['amount'])/1000:,.2f} (category: {category.get('group_name')})")
        return False

    # Skip common income payee patterns
    income_keywords = ['payroll', 'direct deposit', 'salary', 'dividend', 'interest', 'refund', 'ach deposit', 'paycheck', 'wages']
    payee_lower = txn['payee_name'].lower()
    for keyword in income_keywords:
        if keyword in payee_lower:
            print(f"🚫 SKIPPED (Income Payee): {txn['payee_name']} - ${abs(txn['amount'])/1000:,.2f} (contains '{keyword}')")
            return False

    return True  # This is an expense transaction

def prepare_alluvial_data(transactions: List[Dict], categories: Dict[str, Dict]) -> Tuple[List[Dict], List[str], List[str], List[str]]:
    """Prepare data for alluvial diagram with Group → Category → Payee flow."""
    # Group transactions by payee, category, and group
    payee_category_flows = defaultdict(lambda: defaultdict(float))  # pylint: disable=unnecessary-lambda
    category_group_flows = defaultdict(lambda: defaultdict(float))  # pylint: disable=unnecessary-lambda
    payee_totals = defaultdict(float)
    category_totals = defaultdict(float)
    group_totals = defaultdict(float)

    print("🔍 DETAILED TRANSACTION PROCESSING:")
    print("=" * 80)
    print("🚨 DEBUG: This is the NEW version with fixes applied!")
    print("🚨 DEBUG: VERSION 2.0 - Flow filtering added!")
    print("🚨 DEBUG: VERSION 3.0 - Income/Deposit filtering added!")
    print("=" * 80)

    # Apply expense filtering
    filtered_transactions = []
    skipped_count = 0

    for txn in transactions:
        # Get category info for filtering
        category = categories.get(txn['category_id']) if txn.get('category_id') else None

        # Apply expense filter (we don't have account info here, so skip that check)
        if is_expense_transaction(txn, None, category):
            filtered_transactions.append(txn)
        else:
            skipped_count += 1

    print("=" * 80)
    print(f"📊 EXPENSE FILTERING RESULTS:")
    print(f"  • Total transactions: {len(transactions)}")
    print(f"  • Expense transactions (included): {len(filtered_transactions)}")
    print(f"  • Income/Transfer transactions (skipped): {skipped_count}")
    print("=" * 80)

    for i, txn in enumerate(filtered_transactions):
        category_id = txn['category_id']
        amount = abs(txn['amount']) / 1000.0  # Convert from milliunits to dollars

        # Ensure we have valid payee name
        payee = txn['payee_name'] or 'No Payee'

        # Get category and group names - ensure we always have both
        if category_id == 'uncategorized' or not category_id:
            category_name = 'No Category'
            group_name = 'No Group'
            reason = "uncategorized or no category_id"
        elif category_id in categories:
            category_name = categories[category_id]['name']
            group_name = categories[category_id]['group_name']
            reason = f"found in categories dict"
        else:
            # Fallback to placeholders - never use payee names as category names
            category_name = 'No Category'
            group_name = 'No Group'
            reason = f"category_id '{category_id}' not found in categories dict"

        # Debug specific transaction if it's the problematic one
        if payee == 'Onetimepayment':
            print(f"🎯 ONETIMEPAYMENT TRANSACTION #{i+1}:")
            print(f"   Raw category_id: '{category_id}'")
            print(f"   Raw payee_name: '{txn['payee_name']}'")
            print(f"   Raw category_name: '{txn.get('category_name', 'N/A')}'")
            print(f"   Final category_name: '{category_name}'")
            print(f"   Final group_name: '{group_name}'")
            print(f"   Final payee: '{payee}'")
            print(f"   Reason: {reason}")
            print(f"   Amount: ${amount:,.2f}")
            print("-" * 40)

        payee_category_flows[payee][category_name] += amount
        category_group_flows[category_name][group_name] += amount
        payee_totals[payee] += amount
        category_totals[category_name] += amount
        group_totals[group_name] += amount

    print("=" * 80)

    # Create the flow data
    flows = []
    payee_names = sorted(payee_totals.keys(), key=lambda x: payee_totals[x], reverse=True)

    # Debug: Check for payee names in categories
    print("🔍 DEBUGGING CATEGORY/PAYEE SEPARATION:")
    print(f"Payee names: {payee_names}")
    print(f"Category totals keys: {list(category_totals.keys())}")

    # Remove any payee names that accidentally got into categories
    payee_set = set(payee_names)
    clean_category_totals = {}
    for cat_name, amount in category_totals.items():
        if cat_name not in payee_set:
            clean_category_totals[cat_name] = amount
        else:
            print(f"⚠️  Removing '{cat_name}' from categories (it's a payee)")

    category_names = sorted(clean_category_totals.keys(), key=lambda x: clean_category_totals[x], reverse=True)
    group_names = sorted(group_totals.keys(), key=lambda x: group_totals[x], reverse=True)
    print(f"Cleaned category names: {category_names}")
    print("-" * 80)

    # Create flows between payees and categories
    print("🔄 FLOW CREATION DEBUG:")
    for payee in payee_names:
        if payee == 'Onetimepayment':
            print(f"🎯 Creating flows for payee: '{payee}'")
            print(f"   payee_category_flows['{payee}']: {dict(payee_category_flows[payee])}")

        for category, amount in payee_category_flows[payee].items():
            if amount > 0 and category in clean_category_totals:  # Only include valid categories
                # Find the group for this category
                group_name = None
                for cat_group, cat_amount in category_group_flows[category].items():
                    if cat_amount > 0:
                        group_name = cat_group
                        break

                # Ensure we have a valid group name
                if not group_name:
                    group_name = 'No Group'

                if payee == 'Onetimepayment':
                    print(f"   ✅ Creating flow: {group_name} → {category} → {payee} (${amount:,.2f})")

                flows.append({
                    'payee': payee,
                    'category': category,
                    'group': group_name,
                    'amount': amount,
                    'payee_total': payee_totals[payee],
                    'category_total': clean_category_totals[category],
                    'group_total': group_totals[group_name]
                })
            elif payee == 'Onetimepayment':
                print(f"   ❌ Skipping flow: {category} → {payee} (${amount:,.2f}) - category not in clean_category_totals")

    print("-" * 80)

    return flows, group_names, category_names, payee_names

def create_simple_diagram(flows: List[Dict], group_names: List[str], category_names: List[str], payee_names: List[str]):
    """Create a simple diagram with proper 3-column layout."""
    if not flows:
        return go.Figure()

    # CRITICAL FIX: Only use categories and payees that are actually in the flows
    used_groups = set()
    used_categories = set()
    used_payees = set()

    for flow in flows:
        used_groups.add(flow['group'])
        used_categories.add(flow['category'])
        used_payees.add(flow['payee'])

    # Create filtered lists with only used items
    filtered_group_names = [g for g in group_names if g in used_groups]
    filtered_category_names = [c for c in category_names if c in used_categories]
    filtered_payee_names = [p for p in payee_names if p in used_payees]

    # Create node labels and positioning
    node_labels = filtered_group_names + filtered_category_names + filtered_payee_names
    node_x = []
    node_y = []

    # Group nodes (left column) - position 0
    for i in range(len(filtered_group_names)):
        node_x.append(0)
        node_y.append(i / max(1, len(filtered_group_names) - 1))

    # Category nodes (middle column) - position 0.5
    for i in range(len(filtered_category_names)):
        node_x.append(0.5)
        node_y.append(i / max(1, len(filtered_category_names) - 1))

    # Payee nodes (right column) - position 1.0 with better spacing
    for i in range(len(filtered_payee_names)):
        node_x.append(1.0)
        # Add more spacing between payee nodes to prevent overlap
        spacing = 1.2 if len(filtered_payee_names) > 3 else 1.0
        node_y.append((i * spacing) / max(1, (len(filtered_payee_names) - 1) * spacing))

    # Create flows
    source = []
    target = []
    value = []

    for flow in flows:
        group = flow['group']
        category = flow['category']
        payee = flow['payee']
        amount = flow['amount']

        # Only create flows if category is in the filtered category names
        if category in filtered_category_names:
            # Find indices
            group_idx = node_labels.index(group) if group in node_labels else -1
            category_idx = node_labels.index(category) if category in node_labels else -1
            payee_idx = node_labels.index(payee) if payee in node_labels else -1

            # Add Group → Category flow
            if group_idx >= 0 and category_idx >= 0:
                source.append(group_idx)
                target.append(category_idx)
                value.append(amount)

            # Add Category → Payee flow
            if category_idx >= 0 and payee_idx >= 0:
                source.append(category_idx)
                target.append(payee_idx)
                value.append(amount)

    # Create the diagram with better spacing
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=30,  # Increased padding to reduce overlap
            thickness=20,  # Slightly thinner nodes for better spacing
            line=dict(color="black", width=1),
            label=node_labels,
            x=node_x,
            y=node_y
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color="rgba(255,255,255,0.4)",  # Semi-transparent links
            line=dict(color="rgba(0,0,0,0.2)", width=1)
        )
    )])

    # Update layout for better spacing
    fig.update_layout(
        height=600,  # Increased height for better spacing
        margin=dict(l=50, r=50, t=50, b=50)  # More margins
    )

    return fig

def create_alluvial_diagram(flows: List[Dict], group_names: List[str], category_names: List[str], payee_names: List[str],
                          min_amount: float = 0):
    """Create an alluvial diagram using plotly with Group → Category → Payee flow."""

    # DEBUG: Show what we received as parameters
    print("🔍 FUNCTION PARAMETERS DEBUG:")
    print(f"Received category_names: {category_names}")
    print(f"Received payee_names: {payee_names}")
    print("=" * 80)

    if not PLOTLY_AVAILABLE:
        st.error("Plotly is not available. Please install it with: pip install plotly")
        return None

    # Filter flows by minimum amount
    filtered_flows = [f for f in flows if f['amount'] >= min_amount]

    if not filtered_flows:
        # Create empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No data to display. Try lowering the minimum amount filter.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig

    # Validate that we have all required data
    if not group_names or not category_names or not payee_names:
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for visualization. Missing groups, categories, or payees.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16)
        )
        return fig

    # Create node positions for 3-column layout: Group → Category → Payee
    group_nodes = {group: i for i, group in enumerate(group_names)}
    category_nodes = {category: i + len(group_names) for i, category in enumerate(category_names)}
    payee_nodes = {payee: i + len(group_names) + len(category_names) for i, payee in enumerate(payee_names)}

    # DEBUG: Show exactly what nodes are being created
    print("🔍 NODE CREATION DEBUG:")
    print(f"Group nodes: {group_nodes}")
    print(f"Category nodes: {category_nodes}")
    print(f"Payee nodes: {payee_nodes}")
    print("=" * 80)

    # Prepare data for sankey diagram
    source = []
    target = []
    value = []

    # DEBUG: Show what we're using for node_labels
    print("🔍 NODE_LABELS CREATION DEBUG:")
    print(f"group_names: {group_names}")
    print(f"category_names: {category_names}")
    print(f"payee_names: {payee_names}")

    node_labels = group_names + category_names + payee_names
    node_colors = []

    # Create simple, direct flows: Group → Category → Payee
    print("📋 CREATING SIMPLE FLOWS:")
    print("Group | Category | Payee")
    print("-" * 80)

    # Create flows directly from the filtered_flows data
    for flow in filtered_flows:
        group = flow['group']
        category = flow['category']
        payee = flow['payee']
        amount = flow['amount']

        print(f"{group} | {category} | {payee} (${amount:,.2f})")

        # Add Group → Category flow
        if group in group_nodes and category in category_nodes:
            source.append(group_nodes[group])
            target.append(category_nodes[category])
            value.append(amount)

        # Add Category → Payee flow
        if category in category_nodes and payee in payee_nodes:
            source.append(category_nodes[category])
            target.append(payee_nodes[payee])
            value.append(amount)

    print("-" * 80)
    print(f"📊 Created {len(source)} flows total")

    # DEBUG: Show the actual source, target, value arrays being passed to Plotly
    print("🔍 PLOTLY SANKEY DATA DEBUG:")
    print(f"source: {source}")
    print(f"target: {target}")
    print(f"value: {value}")
    print(f"node_labels: {node_labels}")
    print("=" * 80)

    # Create color mapping
    group_colors = px.colors.qualitative.Set1[:len(group_names)]
    category_colors = px.colors.qualitative.Set3[:len(category_names)]
    payee_colors = px.colors.qualitative.Pastel[:len(payee_names)]
    node_colors = group_colors + category_colors + payee_colors

    # Create node positions for 3-column layout with better spacing
    node_x = []
    node_y = []

    # Group nodes (left column) - position 0
    for i in range(len(group_names)):
        node_x.append(0)
        if len(group_names) > 1:
            node_y.append(i / (len(group_names) - 1))
        else:
            node_y.append(0.5)

    # Category nodes (middle column) - position 0.5
    for i in range(len(category_names)):
        node_x.append(0.5)
        if len(category_names) > 1:
            node_y.append(i / (len(category_names) - 1))
        else:
            node_y.append(0.5)

    # Payee nodes (right column) - position 1.0
    for i in range(len(payee_names)):
        node_x.append(1.0)
        if len(payee_names) > 1:
            node_y.append(i / (len(payee_names) - 1))
        else:
            node_y.append(0.5)

    # DEBUG: Show node positioning
    print("🔍 NODE POSITIONING DEBUG:")
    print(f"node_x: {node_x}")
    print(f"node_y: {node_y}")
    print(f"Total nodes: {len(node_labels)}")
    print("=" * 80)

    # Create the sankey diagram
    print("🚨 CREATING PLOTLY SANKEY WITH CORRECT DATA!")
    print(f"🚨 node_labels: {node_labels}")
    print(f"🚨 source: {source}")
    print(f"🚨 target: {target}")

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,  # Increased padding to reduce overlap
            thickness=25,  # Increased thickness for better visibility
            line=dict(color="black", width=1),
            label=node_labels,
            color=node_colors,
            x=node_x,
            y=node_y
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color="rgba(255,255,255,0.4)",  # Semi-transparent white for cleaner look
            line=dict(color="rgba(0,0,0,0.3)", width=1)  # Subtle border
        )
    )])

    fig.update_layout(
        title="Money Flow: Group → Category → Payee",
        font_size=11,  # Slightly smaller font to reduce crowding
        height=900,  # Increased height for better spacing
        margin=dict(l=80, r=80, t=60, b=60)  # More margin space
    )

    return fig

def create_summary_statistics(flows: List[Dict], group_names: List[str], category_names: List[str], payee_names: List[str]):
    """Create summary statistics for the data."""
    total_amount = sum(f['amount'] for f in flows)
    total_transactions = len(flows)

    # Top payees
    payee_totals = defaultdict(float)
    for flow in flows:
        payee_totals[flow['payee']] += flow['amount']
    top_payees = sorted(payee_totals.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top categories
    category_totals = defaultdict(float)
    for flow in flows:
        category_totals[flow['category']] += flow['amount']
    top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top groups
    group_totals = defaultdict(float)
    for flow in flows:
        group_totals[flow['group']] += flow['amount']
    top_groups = sorted(group_totals.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'total_amount': total_amount,
        'total_transactions': total_transactions,
        'unique_payees': len(payee_names),
        'unique_categories': len(category_names),
        'unique_groups': len(group_names),
        'top_payees': top_payees,
        'top_categories': top_categories,
        'top_groups': top_groups
    }

def render():
    """Main render function for the YNAB Alluvial Diagram tool."""
    st.title("🌊 YNAB Alluvial Diagram")
    st.write("Visualize money flow from payees to categories for a selected month.")

    # Data source selection
    st.subheader("📊 Data Source")
    data_source = st.radio(
        "Choose data source:",
        ["🔄 Live YNAB API", "📁 Cached JSON File"],
        index=0,
        help="Use live API data or load from a previously exported JSON file"
    )

    json_data = None
    categories = {}
    budget_id = None

    if data_source == "📁 Cached JSON File":
        # Load from JSON file
        json_files = get_available_json_files()

        if not json_files:
            st.warning("⚠️ No YNAB JSON export files found.")
            st.info("💡 **To use cached data:**")
            st.info("1. Use the **YNAB Data Export** tool to create a JSON file")
            st.info("2. Then return here and select 'Cached JSON File'")
            return

        selected_file = st.selectbox(
            "Select JSON file:",
            json_files,
            format_func=lambda x: f"{x} ({datetime.fromisoformat(load_data_from_json(x).get('metadata', {}).get('export_timestamp', 'Unknown')).strftime('%Y-%m-%d %H:%M') if load_data_from_json(x) else 'Unknown'})"
        )

        if selected_file:
            json_data = load_data_from_json(selected_file)
            if json_data:
                categories = get_categories_from_json(json_data)
                budget_id = json_data.get('metadata', {}).get('budget_id')

                # Show file info
                metadata = json_data.get('metadata', {})
                st.success(f"✅ **Loaded JSON file:** {selected_file}")
                st.write(f"📊 **Data Summary:**")
                st.write(f"• **Categories:** {len(categories)}")
                st.write(f"• **Transactions:** {metadata.get('total_transactions', 0)}")
                st.write(f"• **Export Time:** {metadata.get('export_timestamp', 'Unknown')}")
            else:
                st.error("❌ **Failed to load JSON file**")
                return
    else:
        # Use live API
        # Check API key
        if not os.getenv('YNAB_API_KEY'):
            st.error("❌ **YNAB API Key Missing**")
            st.markdown("""
            Your YNAB API key is not configured. Please:

            1. **Get your API key** from [YNAB Developer Settings](https://app.youneedabudget.com/settings/developer)
            2. **Add it to your environment** or create a `.env` file with:
               ```
               YNAB_API_KEY=your_api_key_here
               ```
            3. **Restart the application**
            """)
            return

        # Get budget selection
        try:
            budget_id, configuration = get_budget_selection()
        except (ynab.ApiException, ConnectionError, TimeoutError) as e:
            st.error(f"❌ **Error loading budgets**: {str(e)}")
            return

        # Get categories
        try:
            categories = get_categories(budget_id, configuration)
        except (ynab.ApiException, ConnectionError, TimeoutError) as e:
            st.error(f"❌ **Error loading categories**: {str(e)}")
            return

        st.write(f"📊 Found {len(categories)} categories in your budget")

    # Month selection
    st.subheader("📅 Select Month")
    col1, col2 = st.columns(2)

    with col1:
        current_year = datetime.now().year

        # Check if user clicked a suggested month
        if 'suggested_year' in st.session_state:
            suggested_year = st.session_state['suggested_year']
            # Find the index for the suggested year
            year_range = list(range(current_year - 2, current_year + 1))  # 3 years range
            if suggested_year in year_range:
                default_year_index = year_range.index(suggested_year)
            else:
                default_year_index = 3  # fallback to 2024
            # Clear the suggestion after using it
            del st.session_state['suggested_year']
        else:
            # Default to current year (2025) since user confirmed they have data there
            default_year_index = 2  # current year (2025)

        year = st.selectbox(
            "Year",
            range(current_year - 2, current_year + 1),  # 3 years range
            index=default_year_index,
            format_func=lambda x: str(x)
        )

    with col2:
        # Check if user clicked a suggested month
        if 'suggested_month' in st.session_state:
            suggested_month = st.session_state['suggested_month']
            default_month_index = suggested_month - 1  # Convert to 0-based index
            # Clear the suggestion after using it
            del st.session_state['suggested_month']
        else:
            # Default to previous month to ensure we have data
            if datetime.now().month == 1:
                default_month_index = 11  # December (index 11)
            else:
                default_month_index = datetime.now().month - 2  # Previous month (index is 0-based)

        month = st.selectbox(
            "Month",
            range(1, 13),
            index=default_month_index,
            format_func=lambda x: datetime(2024, x, 1).strftime("%B")
        )

    # Display selected month
    selected_date = datetime(year, month, 1)
    st.info(f"📅 Analyzing transactions for **{selected_date.strftime('%B %Y')}**")

    # Get transactions for the selected month
    try:
        with st.spinner("Loading transactions..."):
            if data_source == "📁 Cached JSON File" and json_data:
                transactions = get_transactions_for_month_from_json(json_data, year, month)
            else:
                transactions = get_transactions_for_month(budget_id, configuration, year, month)

        if not transactions:
            st.warning(f"⚠️ No transactions found for {selected_date.strftime('%B %Y')}")

            # Add debugging information
            with st.expander("🔍 Debug Information", expanded=True):
                st.write("**Debug Details:**")
                st.write(f"• Selected Year: {year}")
                st.write(f"• Selected Month: {month}")
                st.write(f"• Budget ID: {budget_id}")
                st.write(f"• Date Range: {selected_date.strftime('%Y-%m-%d')} to {(selected_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)}")

                # Try to get ALL transactions to see what's available
                st.write("**Checking all transactions in budget...**")
                try:
                    if data_source == "📁 Cached JSON File" and json_data:
                        all_transactions = json_data.get('transactions', [])
                    else:
                        with ynab.ApiClient(configuration) as api_client:
                            transactions_api = ynab.api.transactions_api.TransactionsApi(api_client)
                            all_response = transactions_api.get_transactions(budget_id)
                            all_transactions = all_response.data.transactions

                    st.write(f"• Total transactions in budget: {len(all_transactions)}")

                    # Check transactions by month
                    monthly_counts = defaultdict(int)
                    categorized_counts = defaultdict(int)
                    uncategorized_counts = defaultdict(int)
                    date_parse_errors = 0

                    for txn in all_transactions:
                        try:
                            # Handle both JSON and API data formats
                            if data_source == "📁 Cached JSON File":
                                # JSON data format
                                date_str = txn['date']
                                amount = txn['amount']
                                category_id = txn.get('category_id')
                                transfer_account_id = txn.get('transfer_account_id')
                            else:
                                # API data format
                                if isinstance(txn.var_date, str):
                                    date_str = txn.var_date
                                    if date_str.endswith('Z'):
                                        date_str = date_str[:-1] + '+00:00'
                                    elif '+' not in date_str and 'T' in date_str:
                                        date_str = date_str + '+00:00'
                                else:
                                    date_str = txn.var_date.isoformat() if hasattr(txn.var_date, 'isoformat') else str(txn.var_date)
                                amount = txn.amount
                                category_id = txn.category_id
                                transfer_account_id = getattr(txn, 'transfer_account_id', None)

                            txn_date = datetime.fromisoformat(date_str)
                            month_key = f"{txn_date.year}-{txn_date.month:02d}"
                            monthly_counts[month_key] += 1

                            if amount != 0:
                                # Check if this is a transfer transaction
                                is_transfer = transfer_account_id is not None
                                if not is_transfer:
                                    if category_id:
                                        categorized_counts[month_key] += 1
                                    else:
                                        uncategorized_counts[month_key] += 1
                        except Exception as e:
                            date_parse_errors += 1
                            if date_parse_errors <= 3:  # Show first few errors
                                txn_date_str = txn.get('date', 'Unknown') if data_source == "📁 Cached JSON File" else getattr(txn, 'var_date', 'Unknown')
                                st.write(f"Date parse error for '{txn_date_str}' (type: {type(txn_date_str)}): {e}")

                    if date_parse_errors > 0:
                        st.write(f"**Date parsing errors:** {date_parse_errors} transactions had unparseable dates")

                    st.write("**Transactions by month:**")
                    for month_key in sorted(monthly_counts.keys(), reverse=True):
                        total = monthly_counts[month_key]
                        categorized = categorized_counts[month_key]
                        uncategorized = uncategorized_counts.get(month_key, 0)
                        transfers = total - categorized - uncategorized
                        st.write(f"• {month_key}: {total} total, {categorized} categorized, {uncategorized} uncategorized, {transfers} transfers")

                    # Check specifically for the selected month
                    target_month_key = f"{year}-{month:02d}"
                    if target_month_key in monthly_counts:
                        st.write(f"**Selected month ({target_month_key}):**")
                        st.write(f"• Total transactions: {monthly_counts[target_month_key]}")
                        st.write(f"• Categorized transactions: {categorized_counts[target_month_key]}")
                        uncategorized = uncategorized_counts.get(target_month_key, 0)
                        transfers = monthly_counts[target_month_key] - categorized_counts[target_month_key] - uncategorized
                        st.write(f"• Uncategorized transactions: {uncategorized}")
                        st.write(f"• Transfer transactions: {transfers}")

                        # Show sample transactions for debugging
                        st.write("**Sample transactions for selected month:**")
                        sample_count = 0
                        for txn in all_transactions:
                            try:
                                # Handle both JSON and API data formats
                                if data_source == "📁 Cached JSON File":
                                    date_str = txn['date']
                                    payee_name = txn.get('payee_name', 'Unknown')
                                    amount = txn['amount']
                                    category_id = txn.get('category_id', 'None')
                                else:
                                    if isinstance(txn.var_date, str):
                                        date_str = txn.var_date
                                        if date_str.endswith('Z'):
                                            date_str = date_str[:-1] + '+00:00'
                                        elif '+' not in date_str and 'T' in date_str:
                                            date_str = date_str + '+00:00'
                                    else:
                                        date_str = txn.var_date.isoformat() if hasattr(txn.var_date, 'isoformat') else str(txn.var_date)
                                    payee_name = txn.payee_name or 'Unknown'
                                    amount = txn.amount
                                    category_id = txn.category_id or 'None'

                                txn_date = datetime.fromisoformat(date_str)
                                if txn_date.year == year and txn_date.month == month and sample_count < 5:
                                    st.write(f"• {date_str} | {payee_name} | ${amount/1000:.2f} | Category: {category_id}")
                                    sample_count += 1
                            except Exception as e:
                                if sample_count < 2:  # Show first few errors
                                    txn_date_str = txn.get('date', 'Unknown') if data_source == "📁 Cached JSON File" else getattr(txn, 'var_date', 'Unknown')
                                    st.write(f"Sample parse error for '{txn_date_str}' (type: {type(txn_date_str)}): {e}")
                                pass
                    else:
                        st.write(f"**No transactions found for {target_month_key}**")

                except Exception as debug_error:
                    st.error(f"Debug error: {debug_error}")

            st.info("💡 **Suggestions:**")
            st.info("• Try selecting a different month (previous months are more likely to have data)")
            st.info("• Make sure you have categorized transactions in YNAB")
            st.info("• Check that your budget has transactions for the selected period")

            # Show available months with data
            st.subheader("🔍 Quick Month Suggestions")
            st.write("Try these months that are more likely to have data:")

            # Suggest recent months that typically have data
            common_months = [
                (2025, 9),   # September 2025
                (2025, 8),   # August 2025
                (2025, 7),   # July 2025
                (2025, 6),   # June 2025
                (2025, 5),   # May 2025
                (2024, 12),  # December 2024
            ]

            for i, (suggested_year, suggested_month) in enumerate(common_months):
                suggested_date = datetime(suggested_year, suggested_month, 1)
                if st.button(f"📅 Try {suggested_date.strftime('%B %Y')}", key=f"suggest_{i}"):
                    st.session_state.suggested_year = suggested_year
                    st.session_state.suggested_month = suggested_month
                    st.rerun()

            return

        st.success(f"✅ Found {len(transactions)} transactions for {selected_date.strftime('%B %Y')}")

    except (ynab.ApiException, ConnectionError, TimeoutError) as e:
        st.error(f"❌ **Error loading transactions**: {str(e)}")
        return

    # Prepare data for visualization
    with st.spinner("Preparing data for visualization..."):
        flows, group_names, category_names, payee_names = prepare_alluvial_data(transactions, categories)

    if not flows:
        st.warning("⚠️ No valid flows found for visualization")

        # Debug information
        with st.expander("🔍 Debug: Flow Creation", expanded=True):
            st.write("**Debug Information:**")
            st.write(f"• Total transactions processed: {len(transactions)}")
            st.write(f"• Categories available: {len(categories)}")

            if transactions:
                st.write("**Sample transactions:**")
                for i, txn in enumerate(transactions[:3]):
                    st.write(f"{i+1}. Payee: '{txn.get('payee_name', 'None')}', Category ID: '{txn.get('category_id', 'None')}', Amount: {txn.get('amount', 0)}")

            if categories:
                st.write("**Sample categories:**")
                for i, (cat_id, cat_info) in enumerate(list(categories.items())[:3]):
                    st.write(f"{i+1}. ID: '{cat_id}', Name: '{cat_info.get('name', 'None')}', Group: '{cat_info.get('group_name', 'None')}'")

        return

    # Filters and controls
    st.subheader("🎛️ Filters & Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        min_amount = st.number_input(
            "Minimum Amount ($)",
            min_value=0.0,
            max_value=10000.0,
            value=0.0,
            step=1.0,
            help="Filter out flows below this amount"
        )

    with col2:
        max_groups = st.number_input(
            "Max Groups to Show",
            min_value=3,
            max_value=20,
            value=10,
            step=2,
            help="Limit the number of groups shown"
        )

    with col3:
        max_categories = st.number_input(
            "Max Categories to Show",
            min_value=5,
            max_value=50,
            value=15,
            step=5,
            help="Limit the number of categories shown"
        )

    col4 = st.columns(1)[0]
    with col4:
        max_payees = st.number_input(
            "Max Payees to Show",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            help="Limit the number of payees shown"
        )

    # Filter data based on controls
    filtered_flows = [f for f in flows if f['amount'] >= min_amount]

    # Limit groups, categories, and payees
    group_totals = defaultdict(float)
    payee_totals = defaultdict(float)
    category_totals = defaultdict(float)

    for flow in filtered_flows:
        group_totals[flow['group']] += flow['amount']
        payee_totals[flow['payee']] += flow['amount']
        category_totals[flow['category']] += flow['amount']

    # Clean categories - remove any payee names that got into categories
    payee_set = set(payee_names)
    clean_category_totals = {}
    print(f"🔍 CLEANING DEBUG: payee_set contains {len(payee_set)} payees")
    print(f"🔍 CLEANING DEBUG: category_totals contains: {list(category_totals.keys())}")

    for cat_name, amount in category_totals.items():
        if cat_name not in payee_set:
            clean_category_totals[cat_name] = amount
        else:
            print(f"⚠️  Removing '{cat_name}' from categories in diagram (it's a payee)")

    print(f"🔍 CLEANING DEBUG: clean_category_totals contains: {list(clean_category_totals.keys())}")

    top_groups = sorted(group_totals.items(), key=lambda x: x[1], reverse=True)[:max_groups]
    top_payees = sorted(payee_totals.items(), key=lambda x: x[1], reverse=True)[:max_payees]
    top_categories = sorted(clean_category_totals.items(), key=lambda x: x[1], reverse=True)[:max_categories]

    top_group_names = [g[0] for g in top_groups]
    top_payee_names = [p[0] for p in top_payees]
    top_category_names = [c[0] for c in top_categories]

    # Filter flows to only include top groups, categories, and payees
    final_flows = [f for f in filtered_flows
                   if f['group'] in top_group_names and f['payee'] in top_payee_names and f['category'] in top_category_names]

    # Create summary statistics
    stats = create_summary_statistics(final_flows, top_group_names, top_category_names, top_payee_names)

    # Display summary statistics
    st.subheader("📊 Summary Statistics")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Amount", f"${stats['total_amount']:,.2f}")
    with col2:
        st.metric("Total Flows", f"{stats['total_transactions']:,}")
    with col3:
        st.metric("Unique Groups", f"{stats['unique_groups']:,}")
    with col4:
        st.metric("Unique Categories", f"{stats['unique_categories']:,}")
    with col5:
        st.metric("Unique Payees", f"{stats['unique_payees']:,}")

    # Create and display the alluvial diagram
    st.subheader("🌊 Alluvial Diagram")

    # Add a refresh button to force diagram update
    if st.button("🔄 Force Refresh Diagram", help="Click to force refresh the diagram"):
        st.rerun()

    if final_flows:
        # Create the main alluvial diagram using the working simple logic
        main_fig = create_simple_diagram(final_flows, group_names, category_names, payee_names)
        st.plotly_chart(main_fig, use_container_width=True, key="main_alluvial_diagram")
    else:
        st.warning("⚠️ No flows to display with current filters")

    # Display top groups, categories, and payees
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📁 Top Groups")
        for i, (group, amount) in enumerate(stats['top_groups'][:10], 1):
            percentage = (amount / stats['total_amount']) * 100
            st.write(f"{i}. **{group}** - ${amount:,.2f} ({percentage:.1f}%)")

    with col2:
        st.subheader("📂 Top Categories")
        for i, (category, amount) in enumerate(stats['top_categories'][:10], 1):
            percentage = (amount / stats['total_amount']) * 100
            st.write(f"{i}. **{category}** - ${amount:,.2f} ({percentage:.1f}%)")

    with col3:
        st.subheader("🏪 Top Payees")
        for i, (payee, amount) in enumerate(stats['top_payees'][:10], 1):
            percentage = (amount / stats['total_amount']) * 100
            st.write(f"{i}. **{payee}** - ${amount:,.2f} ({percentage:.1f}%)")

    # Data export
    st.subheader("📥 Export Data")

    if st.button("📊 Export Flow Data"):
        df = pd.DataFrame(final_flows)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"ynab_flows_{year}_{month:02d}.csv",
            mime="text/csv"
        )

    # Help section
    with st.expander("ℹ️ How to use this tool"):
        st.markdown("""
        **What this tool shows:**
        - Money flow from Groups (left) to Categories (middle) to Payees (right)
        - Flow thickness represents the amount of money
        - Shows all transactions including uncategorized ones (in "❓ Uncategorized" category)
        - Excludes only transfer transactions

        **How to interpret the diagram:**
        - **Left side**: Groups (Bills, Wants, Needs, etc.)
        - **Middle**: Categories (Electricity, Dining out, Groceries, etc.)
        - **Right side**: Payees (individual transactions)
        - **Flow lines**: Show the path and amount of money
        - **Thicker lines**: Represent larger amounts
        - **Flow direction**: Groups → Categories → Payees

        **Filters:**
        - **Minimum Amount**: Hide small flows to focus on major spending
        - **Max Groups/Categories/Payees**: Limit the diagram complexity
        - Use these to focus on your most significant spending patterns

        **Tips:**
        - Start with a higher minimum amount to see major patterns
        - Adjust the max groups/categories/payees to balance detail vs. clarity
        - Use the summary statistics to understand your spending distribution
        - Groups show your main spending areas (Bills, Wants, Needs)
        - Categories show specific spending types within each group
        - Payees show individual merchants and transactions
        """)

if __name__ == "__main__":
    render()
