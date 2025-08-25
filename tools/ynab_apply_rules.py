import streamlit as st
import os
import time
from typing import List, Dict
from datetime import datetime, timedelta
from .ynab_categorizer_config import load_rules, format_date

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
        transfer_count = 0
        for txn in transactions:
            if not txn.category_id:
                # Check if this is a transfer transaction
                is_transfer = hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None
                if is_transfer:
                    transfer_count += 1
                    continue  # Skip transfer transactions

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

        # Log transfer filtering
        if transfer_count > 0:
            st.write(f"ℹ️ **Filtered out {transfer_count} transfer transactions** (cannot be categorized)")

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

def update_transactions(budget_id: str, configuration, updates: List[Dict]) -> bool:
    """Update transactions with new categories."""
    try:
        with ynab.ApiClient(configuration) as api_client:
            from ynab.api.transactions_api import TransactionsApi
            transactions_api = TransactionsApi(api_client)

            # Prepare the payload
            transactions_payload = []
            for update in updates:
                transaction_data = {
                    "id": update['transaction_id'],
                    "category_id": update['category_id']
                }
                transactions_payload.append(transaction_data)

            # Use individual transaction updates for better reliability
            success_count = 0
            failed_updates = []

            for txn_data in transactions_payload:
                try:
                    from ynab.models.put_transaction_wrapper import PutTransactionWrapper
                    from ynab.models.existing_transaction import ExistingTransaction

                    individual_txn = ExistingTransaction(
                        id=txn_data['id'],
                        category_id=txn_data['category_id']
                    )
                    wrapper = PutTransactionWrapper(transaction=individual_txn)

                    st.write(f"🔄 **Attempting to update transaction {txn_data['id'][:8]}...**")

                    response = transactions_api.update_transaction(budget_id, txn_data['id'], wrapper)

                    # Better response validation
                    if response and hasattr(response, 'data') and response.data:
                        if hasattr(response.data, 'transaction'):
                            # Check if the transaction actually has the category we set
                            updated_txn = response.data.transaction
                            if updated_txn.category_id == txn_data['category_id']:
                                st.success(f"✅ **SUCCESS** - Transaction {txn_data['id'][:8]} updated with category {txn_data['category_id'][:8]}")
                                success_count += 1
                            else:
                                st.error(f"❌ **FAILED** - Transaction {txn_data['id'][:8]} returned with wrong category: {updated_txn.category_id}")
                                failed_updates.append({
                                    'id': txn_data['id'],
                                    'expected': txn_data['category_id'],
                                    'actual': updated_txn.category_id,
                                    'reason': 'Wrong category returned'
                                })
                        else:
                            st.error(f"❌ **FAILED** - Transaction {txn_data['id'][:8]} response missing transaction data")
                            failed_updates.append({
                                'id': txn_data['id'],
                                'expected': txn_data['category_id'],
                                'actual': 'No transaction data',
                                'reason': 'Missing transaction data in response'
                            })
                    else:
                        st.error(f"❌ **FAILED** - Transaction {txn_data['id'][:8]} response invalid: {response}")
                        failed_updates.append({
                            'id': txn_data['id'],
                            'expected': txn_data['category_id'],
                            'actual': 'Invalid response',
                            'reason': 'Response validation failed'
                        })

                except Exception as e:
                    st.error(f"❌ **EXCEPTION** - Failed to update transaction {txn_data['id'][:8]}: {e}")
                    failed_updates.append({
                        'id': txn_data['id'],
                        'expected': txn_data['category_id'],
                        'actual': 'Exception',
                        'reason': str(e)
                    })

            # Store detailed results
            if success_count > 0:
                st.session_state['update_success_message'] = f"✅ Successfully updated {success_count} transactions!"
                updated_ids = [update['transaction_id'] for update in updates if update['transaction_id'] not in [f['id'] for f in failed_updates]]
                st.session_state['last_updated_transaction_ids'] = updated_ids
                st.session_state['last_update_time'] = datetime.now().isoformat()

                # Store failed updates for debugging
                if failed_updates:
                    st.session_state['failed_updates'] = failed_updates
                    st.warning(f"⚠️ **{len(failed_updates)} transactions failed to update**")

                return True
            else:
                st.error("❌ Failed to update any transactions")
                if failed_updates:
                    st.write("**Failed updates details:**")
                    for failure in failed_updates:
                        st.write(f"• {failure['id'][:8]} → Expected: {failure['expected'][:8]}, Actual: {failure['actual']}, Reason: {failure['reason']}")
                return False

    except Exception as e:
        st.error(f"Error updating transactions: {str(e)}")
        return False

def clear_transactions_cache():
    """Clear all YNAB-related caches from session state."""
    # Clear the main transactions cache
    if 'ynab_transactions_cache' in st.session_state:
        del st.session_state['ynab_transactions_cache']

    # Clear the unknown category transactions cache
    if 'ynab_cache' in st.session_state:
        del st.session_state['ynab_cache']

    # Clear any other YNAB-related session state
    ynab_keys = [key for key in st.session_state.keys() if key.startswith('ynab_')]
    for key in ynab_keys:
        del st.session_state[key]

def render():
    """Main render function for the YNAB Apply Rules tool."""
    st.title("✅ YNAB Apply Rules")
    st.write("Find transactions that match your categorization rules and apply them automatically.")

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

    if not rules:
        st.warning("⚠️ No categorization rules found. Please create rules in the YNAB Rules tool first.")
        return

    # Debug: Show raw rules data
    with st.expander("🔍 Debug: Raw Rules Data", expanded=False):
        st.write("**Raw rules loaded from file:**")
        for i, rule in enumerate(rules):
            st.write(f"**Rule {i+1}:**")
            st.write(f"• Match: `{rule['match']}`")
            st.write(f"• Type: `{rule['type']}`")
            st.write(f"• Category ID: `{rule['category_id']}`")
            st.write(f"• Category ID Length: {len(rule['category_id']) if rule.get('category_id') else 0}")
            st.write("---")

    # Add refresh controls
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Refresh"):
            clear_transactions_cache()
            st.rerun()
    with col2:
        if st.button("🗑️ Force Clear All Caches"):
            # Clear all possible caches
            clear_transactions_cache()
            # Also clear any other session state that might be related
            for key in list(st.session_state.keys()):
                if 'ynab' in key.lower() or 'cache' in key.lower():
                    del st.session_state[key]
            st.success("🧹 All caches cleared!")
            st.rerun()

    # Nuclear option: Complete session reset
    with st.expander("⚠️ Nuclear Options", expanded=False):
        if st.button("💥 Complete Session Reset"):
            # Clear ALL session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("💥 Complete session reset! All data cleared.")
            st.rerun()
    with col3:
        st.info("💡 Use 'Refresh' for normal reload, 'Force Clear' for complete cache reset")

    # Get unassigned transactions
    try:
        unassigned_transactions = get_unassigned_transactions(budget_id, configuration)
    except Exception as e:
        st.error(f"❌ **Error loading transactions**: {str(e)}")
        return

    # Show transaction summary
    st.write(f"📊 Found {len(unassigned_transactions)} unassigned transactions (transfer transactions excluded)")

    # Debug: Show cache status
    with st.expander("🔍 Debug: Cache Status", expanded=False):
        cache_keys = [key for key in st.session_state.keys() if 'ynab' in key.lower() or 'cache' in key.lower()]
        if cache_keys:
            st.write("**Active Cache Keys:**")
            for key in cache_keys:
                st.write(f"• {key}")
        else:
            st.write("**No active caches found**")

        st.write(f"**Total unassigned transactions:** {len(unassigned_transactions)}")
        if unassigned_transactions:
            st.write("**Sample transactions (transfers excluded):**")
            for i, txn in enumerate(unassigned_transactions[:3]):  # Show first 3
                st.write(f"• {txn['payee_name']} | Category ID: {txn['category_id']}")

    # Debug: Force fresh data from YNAB
    with st.expander("🔍 Debug: Force Fresh Data", expanded=False):
        if st.button("🔄 Force Fresh API Call (No Cache)"):
            # Force a fresh API call without any caching
            with ynab.ApiClient(configuration) as api_client:
                from ynab.api.transactions_api import TransactionsApi
                transactions_api = TransactionsApi(api_client)
                response = transactions_api.get_transactions(budget_id)
                raw_transactions = response.data.transactions

                st.write(f"**Raw transactions from YNAB API: {len(raw_transactions)}**")

                # Show transactions with null category_id
                null_category_txns = [t for t in raw_transactions if not t.category_id]
                st.write(f"**Transactions with null category_id: {len(null_category_txns)}**")

                if null_category_txns:
                    st.write("**Sample null category transactions:**")
                    for i, txn in enumerate(null_category_txns[:5]):
                        st.write(f"• {txn.payee_name} | Category ID: {txn.category_id} | Transfer: {hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None}")

                # Show transactions that were supposedly updated
                st.write("**Looking for transactions that should have been updated:**")
                # This would need the transaction IDs from the previous update
                if 'last_updated_transaction_ids' in st.session_state:
                    updated_ids = st.session_state['last_updated_transaction_ids']
                    st.write(f"**Last updated transaction IDs: {updated_ids}**")

                    for txn in raw_transactions:
                        if txn.id in updated_ids:
                            st.write(f"• {txn.payee_name} | Category ID: {txn.category_id} | Should be categorized!")
                else:
                    st.write("**No record of last updated transactions**")

        # Debug: Test filtering logic
        if st.button("🔍 Test Filtering Logic"):
            # Test the exact filtering logic used in get_unassigned_transactions
            with ynab.ApiClient(configuration) as api_client:
                from ynab.api.transactions_api import TransactionsApi
                transactions_api = TransactionsApi(api_client)
                response = transactions_api.get_transactions(budget_id)
                raw_transactions = response.data.transactions

                st.write("**🔍 Testing Transaction Filtering Logic:**")

                # Step 1: Count raw transactions
                st.write(f"1. **Raw transactions:** {len(raw_transactions)}")

                # Step 2: Count null category_id
                null_category_count = len([t for t in raw_transactions if not t.category_id])
                st.write(f"2. **With null category_id:** {null_category_count}")

                # Step 3: Count transfers
                transfer_count = 0
                non_transfer_null_count = 0

                for txn in raw_transactions:
                    if not txn.category_id:  # Only look at null category transactions
                        is_transfer = hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None
                        if is_transfer:
                            transfer_count += 1
                        else:
                            non_transfer_null_count += 1

                st.write(f"3. **Transfer transactions (excluded):** {transfer_count}")
                st.write(f"4. **Non-transfer, null category (should be shown):** {non_transfer_null_count}")

                # Step 4: Show sample of what should be shown
                if non_transfer_null_count > 0:
                    st.write("**Sample transactions that should appear in the tool:**")
                    sample_count = 0
                    for txn in raw_transactions:
                        if not txn.category_id and not (hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None):
                            if sample_count < 5:
                                st.write(f"• {txn.payee_name} | {txn.memo} | ${txn.amount/1000.0:.2f}")
                                sample_count += 1
                            else:
                                break

                # Step 5: Test rule matching
                st.write("**5. Testing Rule Matching:**")
                rules = load_rules()
                if rules:
                    st.write(f"**Loaded {len(rules)} rules**")

                    # Test first few null category transactions against rules
                    test_count = 0
                    matched_count = 0

                    for txn in raw_transactions:
                        if not txn.category_id and not (hasattr(txn, 'transfer_account_id') and txn.transfer_account_id is not None):
                            if test_count < 10:  # Test first 10
                                # Convert to dict format for rule matching
                                txn_dict = {
                                    'payee_name': txn.payee_name or '',
                                    'memo': txn.memo or ''
                                }

                                category_id = match_transaction_to_rule(txn_dict, rules)
                                if category_id:
                                    matched_count += 1
                                    st.write(f"✅ **{txn.payee_name}** → Rule matched!")
                                else:
                                    st.write(f"❌ **{txn.payee_name}** → No rule match")

                                test_count += 1
                            else:
                                break

                    st.write(f"**Rule matching results:** {matched_count}/{test_count} transactions matched rules")
                else:
                    st.write("**No rules loaded**")

    if len(unassigned_transactions) == 0:
        st.success("🎉 All categorizable transactions are already categorized!")
        return

    # Find transactions that match rules
    matched_transactions = []
    for txn in unassigned_transactions:
        category_id = match_transaction_to_rule(txn, rules)
        if category_id:
            # Debug: Log the category ID being used
            st.write(f"🔍 **DEBUG**: Transaction '{txn['payee_name']}' matched rule with category ID: `{category_id}` (length: {len(category_id)})")

            matched_transactions.append({
                'transaction': txn,
                'suggested_category_id': category_id,
                'suggested_category_name': categories[category_id]['full_name']
            })

    st.subheader(f"🎯 Transactions Matching Rules ({len(matched_transactions)})")

    if not matched_transactions:
        st.info("No transactions match your current rules. Try creating more specific rules in the YNAB Rules tool.")
        return

    # Select all option
    col1, col2 = st.columns([1, 3])
    with col1:
        select_all = st.checkbox("✅ Select All", key="select_all_matched")
    with col2:
        if select_all:
            st.success("✅ All transactions automatically selected for approval")
        else:
            st.info("Select individual transactions or use 'Select All' to approve all at once")

    # Display matched transactions
    approved_updates = []
    for i, match in enumerate(matched_transactions):
        txn = match['transaction']
        category_name = match['suggested_category_name']

        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        with col1:
            st.write(f"**{txn['payee_name']}**")
            st.caption(f"Memo: {txn['memo']} | Amount: ${txn['amount'] / 1000.0:.2f}")
        with col2:
            st.write(f"→ {category_name}")
            st.caption(f"ID: `{match['suggested_category_id']}`")
        with col3:
            st.caption(f"📅 {txn['date']}")
        with col4:
            # Always render the checkbox, but control its value with select_all
            if select_all:
                st.checkbox("Approve", value=True, key=f"approve_matched_{i}", disabled=True)
                checkbox_value = True
            else:
                checkbox_value = st.checkbox("Approve", key=f"approve_matched_{i}")

            if checkbox_value:
                approved_updates.append({
                    'transaction_id': txn['id'],
                    'category_id': match['suggested_category_id']
                })

    # Apply updates
    if approved_updates and st.button("🚀 Apply Selected Updates"):
        with st.spinner("Applying updates..."):
            st.write(f"🔄 Attempting to update {len(approved_updates)} transactions...")

            # Log what we're trying to update
            for update in approved_updates:
                st.write(f"• Transaction {update['transaction_id'][:8]} → Category {update['category_id'][:8]}")

            if update_transactions(budget_id, configuration, approved_updates):
                # Clear cache to refresh transactions after categorization
                clear_transactions_cache()

                # Force a complete cache clear and wait for YNAB to sync
                st.success(f"✅ Successfully updated {len(approved_updates)} transactions!")
                st.info("🔄 Waiting for YNAB to sync changes...")
                time.sleep(3)  # Wait longer for YNAB to sync

                # Force clear ALL possible caches
                for key in list(st.session_state.keys()):
                    if 'ynab' in key.lower() or 'cache' in key.lower():
                        del st.session_state[key]

                st.info("🧹 All caches cleared! Refreshing...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to update transactions. Please check the console for errors.")

    # Show success message if present
    if 'update_success_message' in st.session_state:
        st.success(st.session_state['update_success_message'])
        del st.session_state['update_success_message']

    # Debug: Show what was last updated
    with st.expander("🔍 Debug: Last Update Info", expanded=False):
        if 'last_updated_transaction_ids' in st.session_state:
            updated_ids = st.session_state['last_updated_transaction_ids']
            update_time = st.session_state.get('last_update_time', 'Unknown')

            st.write(f"**Last Update Time:** {update_time}")
            st.write(f"**Transactions Updated:** {len(updated_ids)}")
            st.write(f"**Transaction IDs:** {updated_ids[:5]}...")  # Show first 5

            # Check if these transactions still appear in the current list
            if unassigned_transactions:
                still_showing = []
                for txn in unassigned_transactions:
                    if txn['id'] in updated_ids:
                        still_showing.append(txn['payee_name'])

                if still_showing:
                    st.warning(f"⚠️ **{len(still_showing)} updated transactions still showing:**")
                    for name in still_showing[:3]:  # Show first 3
                        st.write(f"• {name}")

                    # Add a force refresh button specifically for updated transactions
                    st.write("---")
                    if st.button("🔄 Force Refresh (Wait for YNAB Sync)", key="force_refresh_updated"):
                        st.info("⏳ Waiting 30 seconds for YNAB to sync changes...")
                        time.sleep(30)  # Wait much longer for YNAB to sync

                        # Clear all caches
                        for key in list(st.session_state.keys()):
                            if 'ynab' in key.lower() or 'cache' in key.lower():
                                del st.session_state[key]

                        st.success("🧹 All caches cleared after waiting for YNAB sync!")
                        st.rerun()

                    # Debug: Check if transactions were actually updated in YNAB
                    st.write("---")
                    if st.button("🔍 Verify YNAB Updates", key="verify_updates"):
                        st.write("**🔍 Verifying if transactions were actually updated in YNAB...**")

                        # Make a fresh API call to check the current state
                        with ynab.ApiClient(configuration) as api_client:
                            from ynab.api.transactions_api import TransactionsApi
                            transactions_api = TransactionsApi(api_client)

                            # Get ALL transactions and find the ones we updated
                            try:
                                response = transactions_api.get_transactions(budget_id)
                                if response and hasattr(response, 'data') and response.data.transactions:
                                    raw_transactions = response.data.transactions

                                    # Find the specific transactions that were supposed to be updated
                                    for txn_id in updated_ids:
                                        found = False
                                        for raw_txn in raw_transactions:
                                            if raw_txn.id == txn_id:
                                                found = True
                                                st.write(f"**Transaction {txn_id[:8]}:**")
                                                st.write(f"• Payee: {raw_txn.payee_name}")
                                                st.write(f"• Category ID: {raw_txn.category_id}")
                                                st.write(f"• Category Name: {raw_txn.category_name}")

                                                if raw_txn.category_id:
                                                    st.success(f"✅ **UPDATED** - Has category: {raw_txn.category_name}")
                                                else:
                                                    st.error(f"❌ **NOT UPDATED** - Still has no category")
                                                break

                                        if not found:
                                            st.warning(f"⚠️ **Transaction {txn_id[:8]} not found in YNAB** - may have been deleted")

                                    # Summary
                                    st.write("---")
                                    updated_count = 0
                                    not_updated_count = 0
                                    for txn_id in updated_ids:
                                        for raw_txn in raw_transactions:
                                            if raw_txn.id == txn_id:
                                                if raw_txn.category_id:
                                                    updated_count += 1
                                                else:
                                                    not_updated_count += 1
                                                break

                                    st.write(f"**📊 Summary:** {updated_count} updated, {not_updated_count} not updated")

                                    if not_updated_count > 0:
                                        st.error("❌ **Some transactions were NOT updated in YNAB!**")
                                        st.write("**This means the API calls are failing silently.**")
                                    elif updated_count > 0:
                                        st.success("✅ **All transactions were updated in YNAB!**")
                                        st.write("**If they still show in the list, there's a filtering bug.**")

                                else:
                                    st.error("❌ **Failed to get transactions from YNAB**")

                            except Exception as e:
                                st.error(f"❌ **Error getting transactions from YNAB**: {e}")

                        st.write("---")
                        st.write("**If transactions show as UPDATED above but still appear in the list, there's a filtering bug.**")
                        st.write("**If transactions show as NOT UPDATED above, the API calls are failing silently.**")

                        # Also check if there's a filtering logic issue
                        st.write("---")
                        if st.button("🔍 Debug Filtering Logic", key="debug_filtering"):
                            st.write("**🔍 Checking filtering logic for updated transactions...**")

                            # Get fresh data from YNAB
                            response = transactions_api.get_transactions(budget_id)
                            raw_transactions = response.data.transactions

                            # Find the specific transactions that were updated
                            for txn_id in updated_ids:
                                for raw_txn in raw_transactions:
                                    if raw_txn.id == txn_id:
                                        st.write(f"**Transaction {txn_id[:8]} in raw data:**")
                                        st.write(f"• Payee: {raw_txn.payee_name}")
                                        st.write(f"• Category ID: {raw_txn.category_id}")
                                        st.write(f"• Transfer Account ID: {getattr(raw_txn, 'transfer_account_id', 'None')}")

                                        # Check why it's being filtered
                                        if not raw_txn.category_id:
                                            if hasattr(raw_txn, 'transfer_account_id') and raw_txn.transfer_account_id is not None:
                                                st.warning(f"⚠️ **Filtered as TRANSFER** - transfer_account_id: {raw_txn.transfer_account_id}")
                                            else:
                                                st.error(f"❌ **Should be shown** - null category_id, not a transfer")
                                        else:
                                            st.success(f"✅ **Should NOT be shown** - has category_id: {raw_txn.category_id}")
                                        break

                        # Add category verification
                        st.write("---")
                        if st.button("🔍 Verify Category & Permissions", key="verify_category"):
                            st.write("**🔍 Verifying category and transaction permissions...**")

                            # Check if the category exists
                            try:
                                from ynab.api.categories_api import CategoriesApi
                                categories_api = CategoriesApi(api_client)
                                categories_response = categories_api.get_categories(budget_id)
                                category_found = False
                                for group in categories_response.data.category_groups:
                                    for cat in group.categories:
                                        if cat.id == "2f166614":  # The category we're trying to set
                                            category_found = True
                                            st.success(f"✅ **Category FOUND:** {group.name} > {cat.name}")
                                            break
                                    if category_found:
                                        break

                                if not category_found:
                                    st.error(f"❌ **Category NOT FOUND:** ID 2f166614 doesn't exist in this budget!")
                                    st.write("**This explains why updates are failing!**")

                            except Exception as e:
                                st.error(f"❌ **Error checking categories:** {e}")

                            # Check transaction details for restrictions
                            st.write("---")
                            st.write("**🔍 Checking transaction details for restrictions...**")

                            for txn_id in updated_ids:
                                for raw_txn in raw_transactions:
                                    if raw_txn.id == txn_id:
                                        st.write(f"**Transaction {txn_id[:8]} details:**")
                                        st.write(f"• Payee: {raw_txn.payee_name}")
                                        st.write(f"• Date: {raw_txn.var_date}")
                                        st.write(f"• Cleared: {raw_txn.cleared}")
                                        st.write(f"• Approved: {raw_txn.approved}")
                                        st.write(f"• Import ID: {getattr(raw_txn, 'import_id', 'None')}")
                                        st.write(f"• Subtransactions: {len(getattr(raw_txn, 'subtransactions', []))}")

                                        # Check for common restrictions
                                        if hasattr(raw_txn, 'import_id') and raw_txn.import_id:
                                            st.warning(f"⚠️ **IMPORTED TRANSACTION** - May have editing restrictions")
                                        if len(getattr(raw_txn, 'subtransactions', [])) > 0:
                                            st.warning(f"⚠️ **HAS SUBTRANSACTIONS** - May require different update method")
                                        if raw_txn.cleared == 'reconciled':
                                            st.warning(f"⚠️ **RECONCILED TRANSACTION** - May be locked from editing")

                                        break
                else:
                    st.success("✅ All updated transactions have disappeared from the list!")
        else:
            st.info("No previous update attempts found. Try updating some transactions first.")

        # Always show category verification button
        st.write("---")
        st.write("**🔍 Category & Permission Verification**")
        if st.button("🔍 Verify Category & Permissions", key="verify_category_always"):
            st.write("**🔍 Verifying category and transaction permissions...**")

            # Check if the category exists
            try:
                with ynab.ApiClient(configuration) as api_client:
                    from ynab.api.categories_api import CategoriesApi
                    categories_api = CategoriesApi(api_client)
                    categories_response = categories_api.get_categories(budget_id)
                    category_found = False
                    for group in categories_response.data.category_groups:
                        for cat in group.categories:
                            if cat.id == "6d33e675":  # The category from your failed update
                                category_found = True
                                st.success(f"✅ **Category FOUND:** {group.name} > {cat.name}")
                                break
                        if category_found:
                            break

                    if not category_found:
                        st.error(f"❌ **Category NOT FOUND:** ID 6d33e675 doesn't exist in this budget!")
                        st.write("**This explains why updates are failing!**")
                    else:
                        st.info("✅ Category exists. Let's check transaction details...")

            except Exception as e:
                st.error(f"❌ **Error checking categories:** {e}")
