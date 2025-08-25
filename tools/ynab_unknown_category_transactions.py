import streamlit as st
import os
import json
import time
from datetime import datetime

# Import ynab only when needed to avoid import errors
try:
    import ynab
    from ynab.api.transactions_api import TransactionsApi
    from ynab.api.budgets_api import BudgetsApi
    from ynab.api.categories_api import CategoriesApi
    YNAB_AVAILABLE = True
except ImportError:
    YNAB_AVAILABLE = False
from collections import defaultdict

def load_rules() -> list:
    """Load existing categorization rules."""
    config_file = "ynab_categorizer_rules.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []

def save_rules(rules: list):
    """Save categorization rules."""
    config_file = "ynab_categorizer_rules.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(rules, f, indent=2)
        return True
    except IOError:
        return False

def match_transaction_to_rule(transaction: dict, rules: list) -> str:
    """Match a transaction to a rule and return category_id if found."""
    payee_name = transaction.get('payee_name', '').lower()
    memo = transaction.get('memo', '').lower()

    for rule in rules:
        if not rule.get('category_id'):  # Skip rules without category_id
            continue

        match_text = rule['match'].lower()
        match_type = rule['type']

        # Check payee_name and memo
        for field in [payee_name, memo]:
            if match_type == 'exact' and field == match_text:
                return rule['category_id']
            elif match_type == 'contains' and match_text in field:
                return rule['category_id']
            elif match_type == 'startsWith' and field.startswith(match_text):
                return rule['category_id']

    return None

def render():
    st.title("🔍 YNAB Unknown Category Transactions")
    st.write("Find transactions with unknown categories and create categorization rules to prevent future issues.")

    if not YNAB_AVAILABLE:
        st.error("YNAB module not available. Please install it with: pip install ynab")
        st.stop()

    ynab_api_key = os.getenv('YNAB_API_KEY')

    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

    configuration = ynab.Configuration(
        access_token = ynab_api_key
    )

    try:
        with ynab.ApiClient(configuration) as api_client:
            budgets_api = BudgetsApi(api_client)
            budgets_response = budgets_api.get_budgets()
            budgets = budgets_response.data.budgets
            budget_names = [budget.name for budget in budgets]
            selected_budget_name = st.selectbox("Select a budget", budget_names)
            selected_budget_id = [budget.id for budget in budgets if budget.name == selected_budget_name][0]

        if selected_budget_id:
            # Use session state to store unknown transactions and grouped data with caching
            cache_key = f"ynab_unknown_txns_{selected_budget_id}"

            if 'ynab_cache' not in st.session_state:
                st.session_state['ynab_cache'] = {}

            # Check if we have cached data and if it's still valid (5 minutes)
            cached_data = st.session_state['ynab_cache'].get(cache_key)
            cache_valid = False

            if cached_data and 'timestamp' in cached_data:
                try:
                    timestamp = cached_data['timestamp']
                    if isinstance(timestamp, str):
                        cache_age = datetime.now() - datetime.fromisoformat(timestamp)
                    else:
                        cache_age = datetime.now() - timestamp
                    cache_valid = cache_age.total_seconds() < 300  # 5 minutes = 300 seconds
                except (ValueError, TypeError):
                    # If timestamp parsing fails, consider cache invalid
                    cache_valid = False

            # Cache management controls
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                fetch_clicked = st.button("🔄 Refresh Data")
            with col2:
                if st.button("🗑️ Clear Cache"):
                    if cache_key in st.session_state['ynab_cache']:
                        del st.session_state['ynab_cache'][cache_key]
                    st.rerun()
            with col3:
                if st.button("🚫 Force Clear Transfer Cache"):
                    # Clear all YNAB-related caches to force fresh data
                    for key in list(st.session_state.keys()):
                        if 'ynab' in key.lower():
                            del st.session_state[key]
                    # Set a flag to force refresh on next render
                    st.session_state['force_refresh_ynab'] = True
                    st.success("🧹 All YNAB caches cleared! Refreshing...")
                    st.rerun()

            # Check if we should force refresh (after cache clearing)
            force_refresh = st.session_state.get('force_refresh_ynab', False)
            if force_refresh:
                # Clear the flag and force fresh data
                del st.session_state['force_refresh_ynab']
                cached_data = None
                cache_valid = False

            should_fetch = (
                fetch_clicked or
                not cached_data or
                not cache_valid
            )
            if should_fetch:
                with st.spinner("Fetching transactions and categories..."):
                    api_instance = TransactionsApi(api_client)
                    categories_api = CategoriesApi(api_client)

                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Fetch categories and build mapping
                    status_text.text("Loading categories...")
                    progress_bar.progress(25)
                    categories_response = categories_api.get_categories(selected_budget_id)
                    category_mapping = {}
                    for group in categories_response.data.category_groups:
                        for cat in group.categories:
                            category_mapping[cat.id] = cat.name

                    # Fetch transactions
                    status_text.text("Loading transactions...")
                    progress_bar.progress(50)
                    response = api_instance.get_transactions(selected_budget_id)
                    transactions = response.data.transactions

                    # Process unknown transactions
                    status_text.text("Processing unknown transactions...")
                    progress_bar.progress(75)
                    # Filter for truly unassigned transactions (null category_id) and exclude transfers
                    unknown_transactions = []
                    transfer_count = 0
                    for t in transactions:
                        if not t.category_id:  # Only transactions with null category_id
                            # Check if this is a transfer transaction
                            is_transfer = hasattr(t, 'transfer_account_id') and t.transfer_account_id is not None

                            # Also check payee name patterns that indicate transfers
                            payee_name = (t.payee_name or '').lower()
                            memo = (t.memo or '').lower()
                            is_transfer_pattern = (
                                'transfer' in payee_name or
                                'transfer' in memo or
                                payee_name.startswith('transfer ') or
                                memo.startswith('transfer ')
                            )

                            if is_transfer or is_transfer_pattern:
                                transfer_count += 1
                                continue  # Skip transfer transactions
                            unknown_transactions.append(t)

                    # Convert YNAB API objects to dictionaries for rule matching
                    from collections import defaultdict
                    grouped = defaultdict(list)
                    for t in unknown_transactions:
                        # Convert to dictionary format that match_transaction_to_rule expects
                        txn_dict = {
                            'id': t.id,
                            'date': t.var_date,
                            'payee_name': t.payee_name or '',
                            'memo': t.memo or '',
                            'amount': t.amount,
                            'account_id': t.account_id,
                            'account_name': t.account_name or '',
                            'cleared': t.cleared,
                            'approved': t.approved,
                            'category_id': t.category_id,
                            'category_name': t.category_name or ''
                        }
                        name = t.payee_name or t.memo or "(No Name)"
                        grouped[name].append(txn_dict)

                    # Complete
                    status_text.text("Complete!")
                    progress_bar.progress(100)

                    # Log transfer filtering
                    if transfer_count > 0:
                        st.info(f"ℹ️ **Filtered out {transfer_count} transfer transactions** (cannot be categorized)")

                        # Show some examples of what was filtered
                        filtered_examples = []
                        for t in transactions:
                            if not t.category_id:
                                payee_name = (t.payee_name or '').lower()
                                memo = (t.memo or '').lower()
                                is_transfer = hasattr(t, 'transfer_account_id') and t.transfer_account_id is not None
                                is_transfer_pattern = (
                                    'transfer' in payee_name or
                                    'transfer' in memo or
                                    payee_name.startswith('transfer ') or
                                    memo.startswith('transfer ')
                                )
                                if is_transfer or is_transfer_pattern:
                                    filtered_examples.append(f"• {t.payee_name or 'No Payee'} | {t.memo or 'No Memo'}")
                                    if len(filtered_examples) >= 3:  # Show max 3 examples
                                        break

                        if filtered_examples:
                            st.write("**Examples of filtered transfers:**")
                            for example in filtered_examples:
                                st.write(example)

                                        # Store in cache with timestamp
                    st.session_state['ynab_cache'][cache_key] = {
                        'unknown_transactions': unknown_transactions,
                        'grouped': grouped,
                        'timestamp': datetime.now().isoformat()
                    }

                    # Clear progress indicators
                    time.sleep(0.5)
                    progress_bar.empty()
                    status_text.empty()
            else:
                # Use cached data
                unknown_transactions = cached_data['unknown_transactions']
                grouped = cached_data['grouped']

                # Show cache status
                try:
                    timestamp = cached_data['timestamp']
                    if isinstance(timestamp, str):
                        cache_age = datetime.now() - datetime.fromisoformat(timestamp)
                    else:
                        cache_age = datetime.now() - timestamp
                    cache_minutes = int(cache_age.total_seconds() / 60)
                    st.info(f"📋 Using cached data from {cache_minutes} minutes ago. Click 'Refresh Data' to get latest.")
                except (ValueError, TypeError):
                    st.warning("⚠️ Cache timestamp error. Click 'Refresh Data' to reload.")

            if unknown_transactions is not None:
                st.success(f"Found {len(unknown_transactions)} transactions with unknown category (transfer transactions excluded)!")

                # Explain the relationship with YNAB Apply Rules
                st.info("💡 **Note:** These are transactions with no category assigned (transfer transactions cannot be categorized). After creating rules here, use the 'YNAB Apply Rules' tool to automatically apply them to matching transactions.")

                # Debug: Show transaction filtering info
                with st.expander("🔍 Debug: Transaction Filtering", expanded=False):
                    if 'transactions' in locals():
                        st.write(f"**Total transactions fetched:** {len(transactions)}")
                        st.write(f"**Transactions with null category_id:** {len([t for t in transactions if not t.category_id])}")
                        st.write(f"**Transfer transactions excluded:** {len([t for t in transactions if hasattr(t, 'transfer_account_id') and t.transfer_account_id is not None])}")
                    else:
                        st.write("**Using cached data - raw transaction details not available**")
                    st.write(f"**Final unknown transactions:** {len(unknown_transactions)}")

                    if len(unknown_transactions) > 0:
                        st.write("**Sample unknown transactions:**")
                        for i, txn in enumerate(unknown_transactions[:5]):  # Show first 5
                            st.write(f"• **{txn.payee_name or 'No Payee'}** | {txn.memo or 'No Memo'} | **ID:** `{txn.id[:8]}...` | Category ID: {txn.category_id}")

                # Load existing rules
                existing_rules = load_rules()

                # Show existing rules info
                if existing_rules:
                    with st.expander(f"📋 Existing Rules ({len(existing_rules)})", expanded=False):
                        st.write("**Current Categorization Rules:**")
                        for rule in existing_rules:
                            match_text = rule['match']
                            rule_type = rule['type']
                            category_id = rule.get('category_id', 'Not set')

                            # Create a more descriptive rule explanation
                            if rule_type == 'contains':
                                rule_desc = f"**Contains** '{match_text}' anywhere in payee name or memo"
                            elif rule_type == 'startsWith':
                                rule_desc = f"**Starts with** '{match_text}'"
                            elif rule_type == 'exact':
                                rule_desc = f"**Exactly matches** '{match_text}'"
                            else:
                                rule_desc = f"**{rule_type}** '{match_text}'"

                            st.write(f"• {rule_desc} → Category: {category_id}")
                else:
                    st.info("💡 No categorization rules found. Create rules below to automatically categorize future transactions.")

                                # Debug: Show which transactions would match existing rules
                if existing_rules and unknown_transactions:
                    with st.expander("🔍 Debug: Rule Matching", expanded=False):
                        st.write("**Transactions that would match existing rules:**")
                        matched_count = 0
                        for txn in unknown_transactions:
                            if isinstance(txn, dict):  # Ensure it's a dictionary
                                category_id = match_transaction_to_rule(txn, existing_rules)
                                if category_id:
                                    matched_count += 1
                                    # Find which rule matched
                                    matched_rule = None
                                    for rule in existing_rules:
                                        if rule.get('category_id') == category_id:
                                            matched_rule = rule
                                            break

                                    if matched_rule:
                                        rule_desc = f"'{matched_rule['match']}' ({matched_rule['type']})"
                                        st.write(f"✅ **{txn.get('payee_name', 'Unknown')}** (ID: `{txn.get('id', 'Unknown')[:8]}...`) → Matches rule: {rule_desc}")
                                    else:
                                        st.write(f"✅ **{txn.get('payee_name', 'Unknown')}** (ID: `{txn.get('id', 'Unknown')[:8]}...`) → Rule: {category_id}")

                        if matched_count == 0:
                            st.info("💡 No transactions match existing rules. This is why they appear in 'Needs Review'.")
                        else:
                            st.success(f"🎯 {matched_count} transactions would be auto-categorized with existing rules!")

                # Performance controls
                col1, col2 = st.columns([1, 1])
                with col1:
                    sort_option = st.selectbox(
                        "Sort groups by:",
                        ["Payee/Description (A-Z)", "# of Transactions (Most First)"]
                    )
                with col2:
                    max_groups = st.selectbox(
                        "Show max groups:",
                        [5, 10, 20, 50, 100, "All"],
                        index=1,  # Default to 10
                        help="Limit results for faster loading"
                    )

                # Sort groups
                if sort_option == "Payee/Description (A-Z)":
                    group_keys = sorted(grouped.keys(), key=lambda n: n.lower())
                else:
                    group_keys = sorted(grouped.keys(), key=lambda n: len(grouped[n]), reverse=True)

                # Limit results
                if max_groups != "All":
                    group_keys = group_keys[:max_groups]
                    if len(grouped) > max_groups:
                        st.info(f"📊 Showing {len(group_keys)} of {len(grouped)} total groups. Use the dropdown above to see more.")

                for name in group_keys:
                    txns = grouped[name]
                    with st.expander(f"{name} ({len(txns)})", expanded=False):
                        # Show transaction details
                        st.write("**Transactions:**")
                        for transaction in sorted(txns, key=lambda t: t['date']):
                            st.write(f"• **{transaction['date']}** | **${transaction['amount'] / 1000.0:.2f}** | **ID:** `{transaction['id'][:8]}...`")

                        st.divider()

                        # Rule creation section for this payee
                        st.subheader("📝 Create Categorization Rule")
                        st.write(f"Create a rule to automatically categorize future transactions from **{name}**")

                        # Get categories for rule creation
                        try:
                            with ynab.ApiClient(configuration) as api_client:
                                categories_api = CategoriesApi(api_client)
                                categories_response = categories_api.get_categories(selected_budget_id)

                                # Build category options
                                category_options = [""]
                                category_names = [""]
                                for group in categories_response.data.category_groups:
                                    for cat in group.categories:
                                        # Ensure we have valid data types
                                        if hasattr(cat, 'id') and hasattr(cat, 'name') and hasattr(group, 'name'):
                                            category_options.append(str(cat.id))
                                            category_names.append(f"{group.name} > {cat.name}")
                                        else:
                                            st.warning(f"⚠️ Skipping invalid category: {cat}")

                                # Rule creation form
                                col1, col2, col3 = st.columns([2, 1, 2])
                                with col1:
                                    match_text = st.text_input(
                                        "Match Text",
                                        value=name,
                                        key=f"rule_match_{name}",
                                        help="Text to match in payee name or memo"
                                    )
                                with col2:
                                    match_type = st.selectbox(
                                        "Match Type",
                                        ["contains", "exact", "startsWith"],
                                        index=0,
                                        key=f"rule_type_{name}"
                                    )
                                with col3:
                                    if category_names and len(category_names) > 1:
                                        selected_category_idx = st.selectbox(
                                            "Category",
                                            category_names,
                                            index=0,
                                            key=f"rule_category_{name}"
                                        )
                                    else:
                                        st.warning("⚠️ No categories available")
                                        selected_category_idx = ""

                                # Create rule button
                                if st.button("➕ Create Rule", key=f"create_rule_{name}"):
                                    if match_text and selected_category_idx and selected_category_idx != "":
                                        try:
                                            # selected_category_idx is the category name string, not an index
                                            # Find the index of the selected category name
                                            if selected_category_idx in category_names:
                                                category_index = category_names.index(selected_category_idx)
                                                selected_category_id = category_options[category_index]
                                                selected_category_name = selected_category_idx
                                            else:
                                                st.error(f"Selected category not found: {selected_category_idx}")
                                                continue
                                        except (ValueError, IndexError, TypeError) as e:
                                            st.error(f"Invalid category selection: {str(e)}")
                                            continue

                                        # Check if rule already exists
                                        rule_exists = any(
                                            rule.get('match') == match_text and
                                            rule.get('type') == match_type
                                            for rule in existing_rules
                                        )

                                        if rule_exists:
                                            st.warning("⚠️ A rule with this match text and type already exists!")
                                            st.info(f"💡 Rule already exists: **{match_text}** ({match_type}) → Check the 'YNAB Apply Rules' tool to see if transactions are being auto-categorized.")
                                        else:
                                            # Create new rule
                                            new_rule = {
                                                "match": match_text,
                                                "type": match_type,
                                                "category_id": selected_category_id,
                                                "created_at": datetime.now().isoformat(),
                                                "updated_at": datetime.now().isoformat()
                                            }

                                            existing_rules.append(new_rule)
                                            if save_rules(existing_rules):
                                                st.success(f"✅ Rule created: **{match_text}** ({match_type}) → **{selected_category_name}**")
                                                st.balloons()

                                                # Refresh rules
                                                existing_rules = load_rules()

                                                # Show next steps
                                                st.info("💡 **Next step:** Use the 'YNAB Apply Rules' tool to automatically categorize matching transactions!")
                                            else:
                                                st.error("❌ Failed to save rule. Please try again.")
                                    else:
                                        st.error("Please provide both match text and category.")

                        except Exception as e:
                            st.error(f"Error loading categories: {str(e)}")

    except ynab.ApiException as e:
        st.error(f"Error: {e.reason}")

    # Help section
    with st.expander("ℹ️ About this tool", expanded=False):
        st.markdown("""
        **What this tool shows:**
        - Transactions with **no category assigned** (category_id is null)
        - **Transfer transactions are automatically excluded** (cannot be categorized)
        - Only regular spending/income transactions that need categorization

        **Why transfer transactions are excluded:**
        - Transfer transactions move money between accounts
        - They cannot be assigned to spending/income categories
        - YNAB automatically handles these internally

        **After creating rules here:**
        - Use the **YNAB Apply Rules** tool to automatically categorize matching transactions
        - Rules will apply to future transactions with similar payee names or memos
        """)