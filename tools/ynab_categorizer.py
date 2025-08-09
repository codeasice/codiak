import streamlit as st
import ynab
import os
import json
import re
from typing import List, Dict, Optional, Tuple
from ynab.api.transactions_api import TransactionsApi
from ynab.api.budgets_api import BudgetsApi
from ynab.api.categories_api import CategoriesApi
from ynab.models.save_transaction_with_optional_fields import SaveTransactionWithOptionalFields
from ynab.models.save_transaction_with_id_or_import_id import SaveTransactionWithIdOrImportId
from ynab.models.patch_transactions_wrapper import PatchTransactionsWrapper
import time
import random
from datetime import datetime, timedelta

# Import shared LLM utilities
from .llm_utils import get_llm_suggestion, display_llm_logs, clear_llm_logs

# Import config helper
from .ynab_categorizer_config import load_rules, save_rules, format_date

def clear_transactions_cache():
    """Clear cached transactions from session state."""
    if 'ynab_transactions_cache' in st.session_state:
        del st.session_state['ynab_transactions_cache']
        st.success("🔄 Transaction cache cleared!")

def rate_limited_api_call(api_call_func, *args, max_retries=3, base_delay=1.0, **kwargs):
    """Execute an API call with rate limiting and retry logic."""
    for attempt in range(max_retries):
        try:
            return api_call_func(*args, **kwargs)
        except ynab.exceptions.UnauthorizedException as e:
            # Handle 401 Unauthorized immediately (no retry)
            print(f"❌ DEBUG: API key is invalid or expired (401 Unauthorized)")
            if hasattr(e, 'body'):
                print(f"❌ DEBUG: Error detail: {e.body}")
            raise
        except ynab.exceptions.ApiException as e:
            if e.status == 429:  # Too Many Requests
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"🔍 DEBUG: Rate limited (429), waiting {delay:.2f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(delay)
                    continue
                else:
                    print(f"❌ DEBUG: Rate limit exceeded after {max_retries} retries")
                    raise
            else:
                # Re-raise non-rate-limit errors immediately
                raise
        except Exception as e:
            # Re-raise other exceptions immediately
            raise

    return None

def check_api_key_validity():
    """Check if the YNAB API key is valid and provide helpful error messages."""
    api_key = os.getenv('YNAB_API_KEY')

    if not api_key:
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
        return False

    try:
        configuration = ynab.Configuration(access_token=api_key)
        with ynab.ApiClient(configuration) as api_client:
            from ynab.api.user_api import UserApi
            user_api = UserApi(api_client)
            user_response = rate_limited_api_call(user_api.get_user)

            # Display user info safely - check what attributes are available
            user_info = "Unknown"
            if hasattr(user_response.data.user, 'id'):
                user_info = f"User ID: {user_response.data.user.id}"
            elif hasattr(user_response.data.user, 'email'):
                user_info = f"Email: {user_response.data.user.email}"
            elif hasattr(user_response.data.user, 'username'):
                user_info = f"Username: {user_response.data.user.username}"

            st.success(f"✅ **API Key Valid** - Connected as: {user_info}")
            return True
    except ynab.exceptions.UnauthorizedException:
        st.error("❌ **Invalid YNAB API Key**")
        st.markdown("""
        Your YNAB API key is invalid or has expired. Please:

        1. **Generate a new API key** from [YNAB Developer Settings](https://app.youneedabudget.com/settings/developer)
        2. **Update your environment** with the new key
        3. **Restart the application**

        **Note**: API keys can expire or be revoked. You may need to generate a fresh one.
        """)
        return False
    except Exception as e:
        st.error(f"❌ **API Connection Error**: {str(e)}")
        st.markdown("""
        There was an error connecting to YNAB. Please check:

        1. **Your internet connection**
        2. **YNAB service status** at [status.youneedabudget.com](https://status.youneedabudget.com)
        3. **Your API key** is correctly configured
        """)
        return False

def get_ynab_client():
    """Get configured YNAB API client."""
    ynab_api_key = os.getenv('YNAB_API_KEY')
    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

    print(f"🔍 DEBUG: Using YNAB API key: {ynab_api_key[:10]}...{ynab_api_key[-4:] if len(ynab_api_key) > 14 else '***'}")

    configuration = ynab.Configuration(access_token=ynab_api_key)

    # Test API key permissions
    try:
        with ynab.ApiClient(configuration) as api_client:
            budgets_api = BudgetsApi(api_client)
            budgets_response = budgets_api.get_budgets()
            print(f"🔍 DEBUG: API key can read budgets: ✅ ({len(budgets_response.data.budgets)} budgets found)")

            # Test write permissions by checking user info (without creating test transactions)
            try:
                from ynab.api.user_api import UserApi
                user_api = UserApi(api_client)
                user_response = user_api.get_user()
                print(f"🔍 DEBUG: API key is valid and associated with user: {user_response.data.user.id}")
                print(f"🔍 DEBUG: API key has read/write permissions: ✅")
            except Exception as e:
                print(f"❌ DEBUG: API key validation failed: {e}")
    except Exception as e:
        print(f"❌ DEBUG: API key cannot read budgets: {e}")

    return configuration

def get_budget_selection():
    """Get budget selection from user."""
    configuration = ynab.Configuration(access_token=os.getenv('YNAB_API_KEY'))

    with ynab.ApiClient(configuration) as api_client:
        budgets_api = BudgetsApi(api_client)

        # Use rate limiting wrapper for API call
        budgets_response = rate_limited_api_call(budgets_api.get_budgets)

        budgets = budgets_response.data.budgets
        budget_names = [budget.name for budget in budgets]
        selected_budget_name = st.selectbox("Select a budget", budget_names)
        selected_budget_id = [budget.id for budget in budgets if budget.name == selected_budget_name][0]
        return selected_budget_id, configuration

def get_categories(budget_id: str, configuration: ynab.Configuration) -> Dict[str, Dict]:
    """Get all categories for a budget."""
    with ynab.ApiClient(configuration) as api_client:
        categories_api = CategoriesApi(api_client)

        # Use rate limiting wrapper for API call
        categories_response = rate_limited_api_call(categories_api.get_categories, budget_id)

        category_mapping = {}
        for group in categories_response.data.category_groups:
            for cat in group.categories:
                category_mapping[cat.id] = {
                    'name': cat.name,
                    'group_name': group.name,
                    'full_name': f"{group.name} > {cat.name}"
                }
        return category_mapping

def get_unassigned_transactions(budget_id: str, configuration: ynab.Configuration, force_refresh: bool = False) -> List[Dict]:
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
                    print(f"🔍 DEBUG: Using cached transactions for budget {budget_id}")
                    return cached_transactions['transactions']

    print(f"🔍 DEBUG: Fetching unassigned transactions for budget {budget_id}")

    with ynab.ApiClient(configuration) as api_client:
        transactions_api = TransactionsApi(api_client)

        # Use rate limiting wrapper for API call
        response = rate_limited_api_call(transactions_api.get_transactions, budget_id)
        transactions = response.data.transactions

        print(f"🔍 DEBUG: Total transactions fetched: {len(transactions)}")

        # Filter for unassigned transactions (excluding transfers)
        unassigned = []
        transfer_count = 0
        for txn in transactions:
            if not txn.category_id:
                # Check if this is a transfer transaction
                is_transfer = hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None
                if is_transfer:
                    transfer_count += 1
                    print(f"🔍 DEBUG: Skipping transfer transaction: {txn.id} - {txn.payee_name}")
                else:
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

        print(f"🔍 DEBUG: Found {len(unassigned)} unassigned transactions (excluded {transfer_count} transfer transactions)")
        for txn in unassigned[:3]:  # Show first 3 for debugging
            print(f"🔍 DEBUG: Unassigned transaction: {txn['id']} - {txn['payee_name']} - Category: {txn['category_id']}")

        # Cache the results
        if 'ynab_transactions_cache' not in st.session_state:
            st.session_state['ynab_transactions_cache'] = {}

        st.session_state['ynab_transactions_cache'][cache_key] = {
            'transactions': unassigned,
            'timestamp': datetime.now().isoformat()
        }

        return unassigned

def load_categorization_rules() -> List[Dict]:
    """Load categorization rules from config file or session state."""
    if 'ynab_categorization_rules' not in st.session_state:
        st.session_state.ynab_categorization_rules = load_rules()
    return st.session_state.ynab_categorization_rules

def save_categorization_rules(rules: List[Dict], changed_rule_indices: List[int] = None):
    """Save categorization rules to config file and session state."""
    st.session_state.ynab_categorization_rules = rules
    save_rules(rules, changed_rule_indices)

def match_transaction_to_rule(transaction: Dict, rules: List[Dict]) -> Optional[str]:
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
        tool_name="YNAB Categorizer",
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
        # Handle cases like "Wants > 🍽️ Dining out (ID: dc8b80e8-afa4-43b6-b976-22d3779819ad)"
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
        tool_name="YNAB Categorizer",
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

def update_transactions(budget_id: str, configuration: ynab.Configuration, updates: List[Dict]) -> bool:
    """Update transactions with new categories."""
    try:
        print(f"🔍 DEBUG: Starting update_transactions with {len(updates)} updates")
        print(f"🔍 DEBUG: Budget ID: {budget_id}")

        with ynab.ApiClient(configuration) as api_client:
            transactions_api = TransactionsApi(api_client)

            # Prepare the correct JSON payload format as per YNAB API documentation
            transactions_payload = []
            for update in updates:
                print(f"🔍 DEBUG: Preparing transaction {update['transaction_id']} with category {update['category_id']}")

                # Use the correct format: just id and category_id
                transaction_data = {
                    "id": update['transaction_id'],
                    "category_id": update['category_id']
                }
                transactions_payload.append(transaction_data)

            print(f"🔍 DEBUG: Prepared {len(transactions_payload)} transactions for update")
            print(f"🔍 DEBUG: Payload: {transactions_payload}")

            # Use PatchTransactionsWrapper (correct approach)
            from ynab.models.patch_transactions_wrapper import PatchTransactionsWrapper
            wrapper = PatchTransactionsWrapper(transactions=transactions_payload)

            # Use rate limiting wrapper for API call
            response = rate_limited_api_call(transactions_api.update_transactions, budget_id, wrapper)

            print(f"🔍 DEBUG: Response: {response}")
            print(f"🔍 DEBUG: Response type: {type(response)}")

            if response and hasattr(response, 'data'):
                print(f"🔍 DEBUG: Response data: {response.data}")
                if hasattr(response.data, 'transactions'):
                    print(f"🔍 DEBUG: Updated transactions: {len(response.data.transactions)}")
                if hasattr(response.data, 'transaction_ids'):
                    print(f"🔍 DEBUG: Transaction IDs: {response.data.transaction_ids}")

                success_count = len(response.data.transaction_ids) if hasattr(response.data, 'transaction_ids') else len(transactions_payload)
                print(f"🔍 DEBUG: Successfully updated {success_count} transactions")

                st.session_state['update_success_message'] = f"✅ Successfully updated {success_count} transactions!"
                return True
            else:
                print(f"❌ DEBUG: Response is None or invalid")
                st.session_state['update_success_message'] = f"❌ Failed to update transactions - no response from API"
                return False

    except Exception as e:
        print(f"❌ DEBUG: Error in update_transactions: {str(e)}")
        print(f"❌ DEBUG: Error type: {type(e).__name__}")
        if hasattr(e, 'reason'):
            print(f"❌ DEBUG: Reason: {e.reason}")
        if hasattr(e, 'body'):
            print(f"❌ DEBUG: Response body: {e.body}")
        st.error(f"Error updating transactions: {str(e)}")
        return False

def render_rule_management(categories: Dict[str, Dict]):
    """Render rule management interface."""
    st.subheader("📋 Categorization Rules")

    st.info("💡 **Note**: Transfer transactions (between accounts) are automatically excluded from categorization as YNAB handles them automatically.")

    rules = load_categorization_rules()

        # Display rule statistics
    total_rules = len(rules)
    rules_with_categories = len([r for r in rules if r.get('category_id')])
    rules_without_categories = total_rules - rules_with_categories

    # Sort options
    sort_option = st.selectbox(
        "Sort rules by:",
        ["Match Text (A-Z)", "Category Name (A-Z)", "Created Date (Newest First)", "Created Date (Oldest First)",
         "Modified Date (Newest First)", "Modified Date (Oldest First)"],
        index=0
    )

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        st.metric("Total Rules", total_rules)
    with col2:
        st.metric("With Categories", rules_with_categories)
    with col3:
        st.metric("Without Categories", rules_without_categories)
    with col4:
        st.caption(f"📊 Sorted by: {sort_option}")

    # Sort rules based on selection
    if sort_option == "Match Text (A-Z)":
        sorted_rules = sorted(rules, key=lambda x: x['match'].lower())
    elif sort_option == "Category Name (A-Z)":
        def get_category_name(rule):
            category_id = rule.get('category_id', '')
            if category_id and category_id in categories:
                return categories[category_id]['full_name'].lower()
            return 'zzz'  # Put rules without categories at the end
        sorted_rules = sorted(rules, key=get_category_name)
    elif sort_option == "Created Date (Newest First)":
        sorted_rules = sorted(rules, key=lambda x: x.get('created_at', ''), reverse=True)
    elif sort_option == "Created Date (Oldest First)":
        sorted_rules = sorted(rules, key=lambda x: x.get('created_at', ''))
    elif sort_option == "Modified Date (Newest First)":
        sorted_rules = sorted(rules, key=lambda x: x.get('updated_at', ''), reverse=True)
    elif sort_option == "Modified Date (Oldest First)":
        sorted_rules = sorted(rules, key=lambda x: x.get('updated_at', ''))
    else:
        sorted_rules = rules  # Default to original order

    # Display existing rules
    st.write("**Current Rules:**")

    # Track which rules have been modified
    changed_rule_indices = []

    for i, rule in enumerate(sorted_rules):
        # Find the original index of this rule in the unsorted list
        original_index = next((idx for idx, r in enumerate(rules) if r['match'] == rule['match'] and r['type'] == rule['type']), i)

        # Store original values to detect changes
        original_match = rule['match']
        original_type = rule['type']
        original_category_id = rule.get('category_id', '')

        # Rule editing section
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        with col1:
            st.text_input(f"Match Text", value=rule['match'], key=f"rule_match_{i}")
        with col2:
            match_type = st.selectbox("Type", ["contains", "exact", "startsWith"],
                                    index=["contains", "exact", "startsWith"].index(rule['type']),
                                    key=f"rule_type_{i}")
        with col3:
            category_options = [""] + [cat_id for cat_id in categories.keys()]
            category_names = [""] + [categories[cat_id]['full_name'] for cat_id in categories.keys()]
            selected_idx = category_options.index(rule.get('category_id', '')) if rule.get('category_id') in category_options else 0
            category_id = st.selectbox("Category", category_names, index=selected_idx, key=f"rule_category_{i}")
            if category_id:
                rule['category_id'] = category_options[category_names.index(category_id)]
        with col4:
            if st.button("❌", key=f"delete_rule_{i}"):
                rules.pop(original_index)
                save_categorization_rules(rules)
                st.rerun()

                        # Update rule and check for changes
        new_match = st.session_state[f"rule_match_{i}"]
        new_type = match_type

        # Check if the rule has been modified
        rule_modified = (new_match != original_match or
                        new_type != original_type or
                        rule.get('category_id', '') != original_category_id)

        if rule_modified:
            changed_rule_indices.append(original_index)

        rules[original_index]['match'] = new_match
        rules[original_index]['type'] = new_type

        # Date information section
        created_at = rule.get('created_at', 'Unknown')
        updated_at = rule.get('updated_at', 'Unknown')

        # Only show dates if they're not "Unknown"
        if created_at != 'Unknown' or updated_at != 'Unknown':
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.caption(f"📅 Created: {format_date(created_at)}")
            with col2:
                st.caption(f"🔄 Updated: {format_date(updated_at)}")
            with col3:
                if rule_modified:
                    st.caption("⚠️ **Modified**")

        # Add separator between rules
        st.markdown("---")

    # Add new rule button
    if st.button("➕ Add New Rule"):
        current_time = datetime.now().isoformat()
        rules.append({
            "match": "",
            "type": "contains",
            "category_id": "",
            "created_at": current_time,
            "updated_at": current_time
        })
        save_categorization_rules(rules)
        st.rerun()

    # Save rules
    if st.button("💾 Save Rules"):
        save_categorization_rules(rules, changed_rule_indices)
        st.success("Rules saved!")

def render_matched_transactions(unassigned_transactions: List[Dict], categories: Dict[str, Dict],
                              rules: List[Dict], budget_id: str, configuration: ynab.Configuration):
    """Render transactions matched by rules."""
    st.subheader("✅ Matched by Rules")

    matched_transactions = []
    for txn in unassigned_transactions:
        category_id = match_transaction_to_rule(txn, rules)
        if category_id:
            matched_transactions.append({
                'transaction': txn,
                'suggested_category_id': category_id,
                'suggested_category_name': categories[category_id]['full_name']
            })

    if not matched_transactions:
        st.info("No transactions matched by rules.")
        return

    st.write(f"Found {len(matched_transactions)} transactions that match rules:")

    # Select all option
    col1, col2 = st.columns([1, 3])
    with col1:
        select_all = st.checkbox("✅ Select All", key="select_all_matched")
    with col2:
        if select_all:
            st.success("All transactions selected for approval")
        else:
            st.info("Select individual transactions or use 'Select All'")

    # Checkboxes for approval
    approved_updates = []
    for i, match in enumerate(matched_transactions):
        txn = match['transaction']
        category_name = match['suggested_category_name']

        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{txn['payee_name']}**")
            st.caption(f"Memo: {txn['memo']} | Amount: ${txn['amount'] / 1000.0:.2f}")
        with col2:
            st.write(f"→ {category_name}")
        with col3:
            # Use select_all to control individual checkboxes
            checkbox_value = select_all or st.checkbox("Approve", key=f"approve_matched_{i}")
            if checkbox_value:
                approved_updates.append({
                    'transaction_id': txn['id'],
                    'category_id': match['suggested_category_id']
                })

    # Apply updates
    if approved_updates and st.button("🚀 Apply Selected Updates"):
        if update_transactions(budget_id, configuration, approved_updates):
            # Clear cache to refresh transactions after categorization
            clear_transactions_cache()
            st.session_state['update_success_message'] = f"Successfully updated {len(approved_updates)} transactions!"
            st.rerun()

def render_llm_assisted_transactions(unassigned_transactions: List[Dict], categories: Dict[str, Dict],
                                   rules: List[Dict], budget_id: str, configuration: ynab.Configuration):
    """Render transactions that need LLM assistance."""
    st.subheader("🤖 Needs Review (LLM Assist)")

    # Filter out transactions that match rules
    unmatched_transactions = []
    for txn in unassigned_transactions:
        if not match_transaction_to_rule(txn, rules):
            unmatched_transactions.append(txn)

    if not unmatched_transactions:
        st.info("All transactions matched by rules!")
        return

    # Group transactions by payee name (like the unknown category tool)
    from collections import defaultdict
    grouped_transactions = defaultdict(list)
    for txn in unmatched_transactions:
        payee_name = txn['payee_name'] or txn['memo'] or "(No Name)"
        grouped_transactions[payee_name].append(txn)

    # Sort options
    sort_option = st.selectbox(
        "Sort transactions by:",
        ["# of Occurrences (Most First)", "Most Recent", "Payee Name (A-Z)"],
        index=0  # Default to number of occurrences
    )

    # Sort grouped transactions based on selection
    if sort_option == "# of Occurrences (Most First)":
        sorted_groups = sorted(grouped_transactions.items(), key=lambda x: len(x[1]), reverse=True)
    elif sort_option == "Most Recent":
        # Sort by most recent transaction in each group
        sorted_groups = sorted(grouped_transactions.items(),
                             key=lambda x: max(txn['date'] for txn in x[1]), reverse=True)
    else:  # Payee Name (A-Z)
        sorted_groups = sorted(grouped_transactions.items(), key=lambda x: x[0].lower())

    # Limit to first 10 groups to avoid overwhelming LLM
    batch_size = 10
    current_batch_groups = sorted_groups[:batch_size]

    total_transactions = sum(len(group) for group in current_batch_groups)
    st.write(f"Showing {total_transactions} transactions from {len(current_batch_groups)} groups (of {len(grouped_transactions)} total groups):")

    # Add rule creation section
    st.subheader("📝 Create New Rules")
    st.write("Create rules for these transactions to automatically categorize similar ones in the future.")

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
    group_index = 0  # Global index for groups

    for group_name, group_transactions in current_batch_groups:
        # Create a unique identifier for this group to prevent form conflicts
        group_id = f"{group_index}_{hash(group_name) % 10000}"

        # Show group header with count
        st.markdown(f"### 📊 {group_name} ({len(group_transactions)} transactions)")

        # Get a representative transaction (first one in the group)
        representative_txn = group_transactions[0]

        # Create a container for the representative transaction
        with st.container():
            st.markdown("---")

            # Transaction details section
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{representative_txn['payee_name']}**")
                st.caption(f"Memo: {representative_txn['memo']} | Amount: ${representative_txn['amount'] / 1000.0:.2f} | Date: {representative_txn['date']}")
                if len(group_transactions) > 1:
                    st.caption(f"📊 **{len(group_transactions)} identical transactions**")

            with col2:
                if st.button("🤖 Suggest Existing Category", key=f"llm_suggest_{group_id}"):
                    with st.spinner("Getting LLM suggestion..."):
                        category_id, error = get_llm_category_suggestion(representative_txn, categories)

                        if error:
                            st.error(error)
                        elif category_id == "NEW_CATEGORY":
                            st.warning("LLM suggests creating a new category")
                            # Store suggestion in session state
                            st.session_state[f"llm_suggestion_{group_id}"] = category_id
                            st.session_state[f"llm_suggestion_text_{group_id}"] = error  # This contains the new category name
                        else:
                            st.success(f"Suggested: {categories[category_id]['full_name']}")
                            st.session_state[f"llm_suggestion_{group_id}"] = category_id

            # Show suggestion if available
            if f"llm_suggestion_{group_id}" in st.session_state:
                suggestion = st.session_state[f"llm_suggestion_{group_id}"]

                if suggestion == "NEW_CATEGORY":
                    new_category_name = st.session_state.get(f"llm_suggestion_text_{group_id}", "")
                    st.warning(f"LLM suggests new category: {new_category_name}")
                    # For now, we'll skip new category creation
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

            # Rule creation section for the representative transaction
            st.write("**Create Rule for This Transaction Group:**")

            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            with col1:
                # Auto-fill match text with transaction payee name or suggested rule
                default_match_text = representative_txn['payee_name']
                if f"rule_suggestion_match_{group_id}" in st.session_state:
                    default_match_text = st.session_state[f"rule_suggestion_match_{group_id}"]
                match_text = st.text_input(f"Match Text", value=default_match_text, key=f"rule_match_{group_id}")
            with col2:
                # Default to "contains" for better matching, or use suggested type
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
                selected_index = 0  # Default to empty
                if f"llm_suggestion_{group_id}" in st.session_state:
                    suggestion = st.session_state[f"llm_suggestion_{group_id}"]
                    if suggestion != "NEW_CATEGORY" and suggestion in categories:
                        category_name = categories[suggestion]['full_name']
                        if category_name in category_names:
                            selected_index = category_names.index(category_name)
                elif f"rule_suggestion_category_{group_id}" in st.session_state:
                    suggested_category = st.session_state[f"rule_suggestion_category_{group_id}"]
                    if suggested_category in category_names:
                        selected_index = category_names.index(suggested_category)

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
                        save_categorization_rules(rules)
                        st.success(f"Rule added: {match_text} → {selected_category}")
                    else:
                        st.error("Please provide both match text and category.")

            # Show auto-fill notification if LLM suggestion is available
            if f"llm_suggestion_{group_id}" in st.session_state:
                suggestion = st.session_state[f"llm_suggestion_{group_id}"]
                if suggestion != "NEW_CATEGORY" and suggestion in categories:
                    category_name = categories[suggestion]['full_name']
                    st.info(f"💡 **Auto-filled**: Category set to '{category_name}' based on LLM suggestion")

            # Show auto-fill notification if rule suggestion is available
            if f"rule_suggestion_match_{group_id}" in st.session_state:
                suggested_match = st.session_state[f"rule_suggestion_match_{group_id}"]
                suggested_type = st.session_state.get(f"rule_suggestion_type_{group_id}", "contains")
                suggested_category = st.session_state.get(f"rule_suggestion_category_{group_id}", "")
                st.info(f"💡 **Auto-filled**: Rule suggestion applied - '{suggested_match}' ({suggested_type}) → '{suggested_category}'")

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

    # Apply updates
    if approved_updates and st.button("🚀 Apply Selected LLM Updates"):
        if update_transactions(budget_id, configuration, approved_updates):
            # Clear cache to refresh transactions after categorization
            clear_transactions_cache()
            st.session_state['update_success_message'] = f"Successfully updated {len(approved_updates)} transactions!"
            st.rerun()

def render():
    """Main render function for the YNAB Categorizer tool."""

    # Show success message if present
    if 'update_success_message' in st.session_state:
        st.success(st.session_state['update_success_message'])
        del st.session_state['update_success_message']

    # Show debug info if present
    if 'update_debug_info' in st.session_state:
        st.info(st.session_state['update_debug_info'])
        del st.session_state['update_debug_info']

    # Check API key validity first
    if not check_api_key_validity():
        return

    # Get budget selection
    try:
        budget_id, configuration = get_budget_selection()
    except ynab.exceptions.UnauthorizedException:
        st.error("❌ **Authentication Failed** - Please check your API key")
        return
    except Exception as e:
        st.error(f"❌ **Error loading budgets**: {str(e)}")
        return

    # Add small delay to prevent rate limiting
    time.sleep(0.5)

    # Get categories and transactions
    try:
        categories = get_categories(budget_id, configuration)
    except Exception as e:
        st.error(f"❌ **Error loading categories**: {str(e)}")
        return

    # Add small delay between API calls
    time.sleep(0.5)

    # Add refresh controls
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 Refresh Transactions"):
            clear_transactions_cache()
            st.rerun()
    with col2:
        if st.button("📊 Show Cache Info"):
            if 'ynab_transactions_cache' in st.session_state:
                cache_data = st.session_state['ynab_transactions_cache']
                cache_key = f"unassigned_transactions_{budget_id}"
                if cache_key in cache_data:
                    cached_info = cache_data[cache_key]
                    cache_time = datetime.fromisoformat(cached_info['timestamp'])
                    st.info(f"Cache timestamp: {format_date(cached_info['timestamp'])}")
                else:
                    st.info("No cached data for this budget")
            else:
                st.info("No cache data available")
    with col3:
        st.caption("💡 Cache expires after 5 minutes")

    try:
        unassigned_transactions = get_unassigned_transactions(budget_id, configuration)
    except Exception as e:
        st.error(f"❌ **Error loading transactions**: {str(e)}")
        return

    # Show transaction summary with cache status
    cache_key = f"unassigned_transactions_{budget_id}"
    is_cached = ('ynab_transactions_cache' in st.session_state and
                 cache_key in st.session_state['ynab_transactions_cache'])

    if is_cached:
        st.success(f"📊 Found {len(unassigned_transactions)} unassigned transactions (🔄 from cache)")
    else:
        st.info(f"📊 Found {len(unassigned_transactions)} unassigned transactions (transfer transactions are automatically excluded)")

    if len(unassigned_transactions) == 0:
        st.success("🎉 All categorizable transactions are already categorized!")
        return

    # Load rules
    rules = load_categorization_rules()

    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Rules", "✅ Matched by Rules", "🤖 Needs Review (LLM Assist)", "📋 LLM Logs"])

    with tab1:
        render_rule_management(categories)

    with tab2:
        render_matched_transactions(unassigned_transactions, categories, rules, budget_id, configuration)

    with tab3:
        render_llm_assisted_transactions(unassigned_transactions, categories, rules, budget_id, configuration)

    with tab4:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Clear Logs"):
                clear_llm_logs()
                st.rerun()
        with col2:
            st.write("View all LLM interactions and their responses")

        display_llm_logs()