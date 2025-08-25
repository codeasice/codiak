import streamlit as st
import os
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from .ynab_categorizer_config import load_rules, save_rules, format_date
from .llm_utils import get_llm_suggestion, display_llm_logs, clear_llm_logs

# Import ynab only when needed to avoid import errors
try:
    import ynab
    YNAB_AVAILABLE = True
except ImportError:
    YNAB_AVAILABLE = False

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
        from ynab.api.budgets_api import BudgetsApi
        budgets_api = BudgetsApi(api_client)
        budgets_response = budgets_api.get_budgets()

        budgets = budgets_response.data.budgets
        budget_names = [budget.name for budget in budgets]
        selected_budget_name = st.selectbox("Select a budget", budget_names)
        selected_budget_id = [budget.id for budget in budgets if budget.name == selected_budget_name][0]
        return selected_budget_id, configuration

def get_categories(budget_id: str, configuration) -> Dict[str, Dict]:
    """Get all categories for a budget."""
    with ynab.ApiClient(configuration) as api_client:
        from ynab.api.categories_api import CategoriesApi
        categories_api = CategoriesApi(api_client)
        categories_response = categories_api.get_categories(budget_id)

        category_mapping = {}
        for group in categories_response.data.category_groups:
            for cat in group.categories:
                category_mapping[cat.id] = {
                    'name': cat.name,
                    'group_name': group.name,
                    'full_name': f"{group.name} > {cat.name}"
                }
        return category_mapping

def get_unassigned_transactions(budget_id: str, configuration, force_refresh: bool = False) -> List[Dict]:
    """Get unassigned transactions (where category_id is null) with caching."""
    cache_key = f"unassigned_transactions_{budget_id}"

    # Check if we have cached data and force_refresh is False
    if not force_refresh and 'ynab_transactions_cache' in st.session_state:
        cached_data = st.session_state['ynab_transactions_cache']
        if cache_key in cached_data:
            cached_transactions = cached_data[cache_key]
            if cached_transactions.get('timestamp'):
                # Check if cache is less than 5 minutes old
                cache_time = datetime.fromisoformat(cached_transactions['timestamp'])
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return cached_transactions['transactions']

    with ynab.ApiClient(configuration) as api_client:
        from ynab.api.transactions_api import TransactionsApi
        transactions_api = TransactionsApi(api_client)
        response = transactions_api.get_transactions(budget_id)
        transactions = response.data.transactions

        # Filter for unassigned transactions (excluding transfers)
        unassigned = []
        for txn in transactions:
            if not txn.category_id:
                # Check if this is a transfer transaction
                is_transfer = hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None
                if not is_transfer:
                    unassigned.append({
                        'id': txn.id,
                        'date': txn.var_date,
                        'payee_name': txn.payee_name or '',
                        'memo': txn.memo or '',
                        'amount': txn.amount,
                        'account_id': txn.account_id,
                        'account_name': txn.account_name or '',
                        'cleared': txn.cleared,
                        'approved': txn.approved,
                        'category_id': txn.category_id,
                        'category_name': txn.category_name or ''
                    })

        # Cache the results
        if 'ynab_transactions_cache' not in st.session_state:
            st.session_state['ynab_transactions_cache'] = {}

        st.session_state['ynab_transactions_cache'][cache_key] = {
            'transactions': unassigned,
            'timestamp': datetime.now().isoformat()
        }

        return unassigned

def match_transaction_to_rule(transaction: Dict, rules: List[Dict]) -> str:
    """Match a transaction to a rule and return category_id if found."""
    payee_name = transaction['payee_name'].lower()
    memo = transaction['memo'].lower()

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

def get_llm_category_suggestion(transaction: Dict, categories: Dict[str, Dict]) -> Tuple[str, str]:
    """Get LLM suggestion for transaction category."""
    # Build category list for context
    category_list = []
    for cat_id, cat_info in categories.items():
        category_list.append(f"- {cat_info['full_name']} (ID: {cat_id})")

    prompt = f"""
    Suggest a budget category for this transaction:

    Payee: "{transaction['payee_name']}"
    Memo: "{transaction['memo']}"
    Amount: ${transaction['amount'] / 1000.0:.2f}

    Available categories:
    {chr(10).join(category_list)}

    IMPORTANT: Respond with ONLY the category ID (the part after "ID: "), not the full category name.
    For example, if you see "Groceries (ID: abc-123)", respond with just "abc-123".

    If no existing category fits well, respond with "NEW_CATEGORY" and suggest a new category name.

    CRITICAL: Do not include the category name in your response, only the ID.
    """

    suggestion, error = get_llm_suggestion(
        prompt=prompt,
        tool_name="YNAB Map Uncategorized",
        function_name="get_llm_category_suggestion"
    )

    if error:
        return "", error

    # Check if it's a valid category ID
    if suggestion in categories:
        return suggestion, ""
    elif suggestion.startswith("NEW_CATEGORY"):
        return "NEW_CATEGORY", suggestion.replace("NEW_CATEGORY", "").strip()
    else:
        # Try to extract category ID from full category name
        for cat_id, cat_info in categories.items():
            if cat_info['full_name'] == suggestion:
                return cat_id, ""

        # Try to extract category ID from response that includes both name and ID
        import re
        id_match = re.search(r'\(ID: ([a-f0-9-]+)\)', suggestion)
        if id_match:
            category_id = id_match.group(1)
            if category_id in categories:
                return category_id, ""

        # If still not found, return error
        return "", f"Invalid suggestion: {suggestion}"

def get_llm_rule_suggestion(transaction: Dict, categories: Dict[str, Dict]) -> Optional[Dict]:
    """Get LLM suggestion for a categorization rule."""
    # Build category list for context
    category_list = []
    for cat_id, cat_info in categories.items():
        category_list.append(f"- {cat_info['full_name']} (ID: {cat_id})")

    prompt = f"""
    Suggest a categorization rule for this transaction:

    Payee: "{transaction['payee_name']}"
    Memo: "{transaction['memo']}"
    Amount: ${transaction['amount'] / 1000.0:.2f}

    Available categories:
    {chr(10).join(category_list)}

    Create a rule that would match this transaction and similar ones. Consider:
    1. What part of the payee name would be most reliable for matching?
    2. Should it be an exact match, contains, or starts with?
    3. Which category best fits this transaction?

    Respond in this exact format:
    MATCH_TEXT|MATCH_TYPE|CATEGORY_ID

    For example: "Amazon"|contains|abc-123-def
    """

    suggestion, error = get_llm_suggestion(
        prompt=prompt,
        tool_name="YNAB Map Uncategorized",
        function_name="get_llm_rule_suggestion"
    )

    if error:
        return None

    # Parse the response
    if '|' in suggestion:
        parts = suggestion.split('|')
        if len(parts) == 3:
            match_text, match_type, category_id = parts
            if category_id in categories:
                return {
                    'match': match_text.strip(),
                    'type': match_type.strip(),
                    'category_id': category_id.strip(),
                    'category_name': categories[category_id]['full_name']
                }

    return None

def update_transactions(budget_id: str, configuration, updates: List[Dict]) -> bool:
    """Update transactions with new categories."""
    try:
        with ynab.ApiClient(configuration) as api_client:
            from ynab.api.transactions_api import TransactionsApi
            transactions_api = TransactionsApi(api_client)

            # Use individual transaction updates for better reliability
            success_count = 0
            for update in updates:
                try:
                    from ynab.models.put_transaction_wrapper import PutTransactionWrapper
                    from ynab.models.existing_transaction import ExistingTransaction

                    individual_txn = ExistingTransaction(
                        id=update['transaction_id'],
                        category_id=update['category_id']
                    )
                    wrapper = PutTransactionWrapper(transaction=individual_txn)

                    response = transactions_api.update_transaction(budget_id, update['transaction_id'], wrapper)
                    if response and hasattr(response, 'data'):
                        success_count += 1
                except Exception as e:
                    st.error(f"Failed to update transaction {update['transaction_id'][:8]}: {e}")

            if success_count > 0:
                st.session_state['update_success_message'] = f"✅ Successfully updated {success_count} transactions!"
                return True
            else:
                st.error("❌ Failed to update any transactions")
                return False

    except Exception as e:
        st.error(f"Error updating transactions: {str(e)}")
        return False

def clear_transactions_cache():
    """Clear cached transactions from session state."""
    if 'ynab_transactions_cache' in st.session_state:
        del st.session_state['ynab_transactions_cache']

def render():
    """Main render function for the YNAB Map Uncategorized tool."""
    st.title("🤖 YNAB Map Uncategorized")
    st.write("Use AI assistance to categorize transactions that don't match your rules.")

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
    except Exception as e:
        st.error(f"❌ **Error loading budgets**: {str(e)}")
        return

    # Get categories
    try:
        categories = get_categories(budget_id, configuration)
    except Exception as e:
        st.error(f"❌ **Error loading categories**: {str(e)}")
        return

    # Load rules
    rules = load_rules()

    # Add refresh controls
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🔄 Refresh"):
            clear_transactions_cache()
            st.rerun()
    with col2:
        st.info("💡 Click refresh to reload transactions from YNAB")

    # Get unassigned transactions
    try:
        unassigned_transactions = get_unassigned_transactions(budget_id, configuration)
    except Exception as e:
        st.error(f"❌ **Error loading transactions**: {str(e)}")
        return

    # Show transaction summary
    st.write(f"📊 Found {len(unassigned_transactions)} unassigned transactions")

    if len(unassigned_transactions) == 0:
        st.success("🎉 All categorizable transactions are already categorized!")
        return

    # Filter out transactions that match rules
    unmatched_transactions = []
    for txn in unassigned_transactions:
        if not match_transaction_to_rule(txn, rules):
            unmatched_transactions.append(txn)

    if not unmatched_transactions:
        st.success("🎉 All transactions are matched by rules! Use the YNAB Apply Rules tool to apply them.")
        return

    st.subheader(f"🤖 Transactions Needing Review ({len(unmatched_transactions)})")

    # Group transactions by payee name
    grouped_transactions = defaultdict(list)
    for txn in unmatched_transactions:
        payee_name = txn['payee_name'] or txn['memo'] or "(No Name)"
        grouped_transactions[payee_name].append(txn)

    # Sort options
    sort_option = st.selectbox(
        "Sort transactions by:",
        ["# of Occurrences (Most First)", "Most Recent", "Payee Name (A-Z)"],
        index=0
    )

    # Sort grouped transactions based on selection
    if sort_option == "# of Occurrences (Most First)":
        sorted_groups = sorted(grouped_transactions.items(), key=lambda x: len(x[1]), reverse=True)
    elif sort_option == "Most Recent":
        sorted_groups = sorted(grouped_transactions.items(),
                             key=lambda x: max(txn['date'] for txn in x[1]), reverse=True)
    else:  # Payee Name (A-Z)
        sorted_groups = sorted(grouped_transactions.items(), key=lambda x: x[0].lower())

    # Limit to first 10 groups to avoid overwhelming LLM
    batch_size = 10
    current_batch_groups = sorted_groups[:batch_size]

    total_transactions = sum(len(group) for group in current_batch_groups)
    st.write(f"Showing {total_transactions} transactions from {len(current_batch_groups)} groups (of {len(grouped_transactions)} total groups):")

    # Select all option for LLM suggestions
    col1, col2 = st.columns([1, 3])
    with col1:
        select_all_llm = st.checkbox("✅ Select All LLM Suggestions", key="select_all_llm")
    with col2:
        if select_all_llm:
            st.success("All LLM suggestions selected for approval")
        else:
            st.info("Select individual LLM suggestions or use 'Select All LLM Suggestions'")

    # Process each group of transactions
    approved_updates = []
    group_index = 0

    for group_name, group_transactions in current_batch_groups:
        group_id = f"{group_index}_{hash(group_name) % 10000}"

        # Show group header with count
        st.markdown(f"### 📊 {group_name} ({len(group_transactions)} transactions)")

        # Get a representative transaction (first one in the group)
        representative_txn = group_transactions[0]

        # Transaction details section
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{representative_txn['payee_name']}**")
            st.caption(f"Memo: {representative_txn['memo']} | Amount: ${representative_txn['amount'] / 1000.0:.2f} | Date: {representative_txn['date']}")
            if len(group_transactions) > 1:
                st.caption(f"📊 **{len(group_transactions)} identical transactions**")

        with col2:
            if st.button("🤖 Suggest Category", key=f"llm_suggest_{group_id}"):
                with st.spinner("Getting LLM suggestion..."):
                    category_id, error = get_llm_category_suggestion(representative_txn, categories)

                    if error:
                        st.error(error)
                    elif category_id == "NEW_CATEGORY":
                        st.warning("LLM suggests creating a new category")
                        st.session_state[f"llm_suggestion_{group_id}"] = category_id
                        st.session_state[f"llm_suggestion_text_{group_id}"] = error
                    else:
                        st.success(f"Suggested: {categories[category_id]['full_name']}")
                        st.session_state[f"llm_suggestion_{group_id}"] = category_id

        # Show suggestion if available
        if f"llm_suggestion_{group_id}" in st.session_state:
            suggestion = st.session_state[f"llm_suggestion_{group_id}"]

            if suggestion == "NEW_CATEGORY":
                new_category_name = st.session_state.get(f"llm_suggestion_text_{group_id}", "")
                st.warning(f"LLM suggests new category: {new_category_name}")
                st.info("New category creation not implemented yet")
            else:
                category_name = categories[suggestion]['full_name']
                st.success(f"LLM suggests: {category_name}")

                # Use select_all_llm to control individual checkboxes
                checkbox_value = select_all_llm or st.checkbox("Approve this suggestion", key=f"approve_llm_{group_id}")
                if checkbox_value:
                    # Add all transactions in this group to approved updates
                    for txn in group_transactions:
                        approved_updates.append({
                            'transaction_id': txn['id'],
                            'category_id': suggestion
                        })

        # Rule creation section
        st.write("**Create Rule for This Transaction Group:**")

        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        with col1:
            default_match_text = representative_txn['payee_name']
            if f"rule_suggestion_match_{group_id}" in st.session_state:
                default_match_text = st.session_state[f"rule_suggestion_match_{group_id}"]
            match_text = st.text_input(f"Match Text", value=default_match_text, key=f"rule_match_{group_id}")
        with col2:
            default_type_index = 0  # "contains"
            if f"rule_suggestion_type_{group_id}" in st.session_state:
                suggested_type = st.session_state[f"rule_suggestion_type_{group_id}"]
                if suggested_type in ["contains", "exact", "startsWith"]:
                    default_type_index = ["contains", "exact", "startsWith"].index(suggested_type)
            match_type = st.selectbox("Type", ["contains", "exact", "startsWith"], index=default_type_index, key=f"rule_type_{group_id}")
        with col3:
            category_options = [""] + [cat_id for cat_id in categories.keys()]
            category_names = [""] + [categories[cat_id]['full_name'] for cat_id in categories.keys()]

            # Determine the selected index for auto-filling
            selected_index = 0
            if f"llm_suggestion_{group_id}" in st.session_state:
                suggestion = st.session_state[f"llm_suggestion_{group_id}"]
                if suggestion != "NEW_CATEGORY" and suggestion in categories:
                    category_name = categories[suggestion]['full_name']
                    if category_name in category_names:
                        selected_index = category_names.index(category_name)

            selected_category = st.selectbox("Category", category_names, index=selected_index, key=f"rule_category_{group_id}")
        with col4:
            if st.button("➕ Add Rule", key=f"add_rule_{group_id}"):
                if match_text and selected_category:
                    selected_category_id = category_options[category_names.index(selected_category)]
                    current_time = datetime.now().isoformat()
                    new_rule = {
                        "match": match_text,
                        "type": match_type,
                        "category_id": selected_category_id,
                        "created_at": current_time,
                        "updated_at": current_time
                    }
                    rules.append(new_rule)
                    save_rules(rules)
                    st.success(f"Rule added: {match_text} → {selected_category}")
                else:
                    st.error("Please provide both match text and category.")

        # LLM rule suggestion
        if st.button("🤖 Suggest Rule", key=f"suggest_rule_{group_id}"):
            with st.spinner("Getting LLM rule suggestion..."):
                rule_suggestion = get_llm_rule_suggestion(representative_txn, categories)
                if rule_suggestion:
                    st.success(f"LLM suggests rule: {rule_suggestion['match']} ({rule_suggestion['type']}) → {rule_suggestion['category_name']}")
                    # Store the suggestion for next render cycle
                    st.session_state[f"rule_suggestion_match_{group_id}"] = rule_suggestion['match']
                    st.session_state[f"rule_suggestion_type_{group_id}"] = rule_suggestion['type']
                    st.session_state[f"rule_suggestion_category_{group_id}"] = rule_suggestion['category_name']
                else:
                    st.error("Could not generate rule suggestion.")

        # Option to expand and see all transactions in the group
        if len(group_transactions) > 1:
            with st.expander(f"📋 Show all {len(group_transactions)} transactions in this group"):
                for i, txn in enumerate(group_transactions):
                    st.write(f"**{txn['payee_name']}** - ${txn['amount'] / 1000.0:.2f} - {txn['date']}")
                    if txn['memo']:
                        st.caption(f"Memo: {txn['memo']}")
                    if i < len(group_transactions) - 1:
                        st.markdown("---")

        group_index += 1
        st.markdown("---")

    # Apply updates
    if approved_updates and st.button("🚀 Apply Selected LLM Updates"):
        with st.spinner("Applying updates..."):
            if update_transactions(budget_id, configuration, approved_updates):
                # Clear cache to refresh transactions after categorization
                clear_transactions_cache()
                st.success(f"✅ Successfully updated {len(approved_updates)} transactions!")
                st.info("🔄 Refreshing...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to update transactions. Please check the console for errors.")

    # Show success message if present
    if 'update_success_message' in st.session_state:
        st.success(st.session_state['update_success_message'])
        del st.session_state['update_success_message']

    # LLM Logs section
    st.subheader("📋 LLM Logs")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🗑️ Clear Logs"):
            clear_llm_logs()
            st.rerun()
    with col2:
        st.write("View all LLM interactions and their responses")

    display_llm_logs()
