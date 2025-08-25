import streamlit as st
import os
import json
from typing import List, Dict
from datetime import datetime
from .ynab_categorizer_config import load_rules, save_rules, format_date

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

def render():
    """Main render function for the YNAB Rules tool."""
    st.title("📋 YNAB Rules Manager")
    st.write("Create and manage categorization rules for automatic transaction categorization.")

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

    # Display rule statistics
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        st.metric("Total Rules", len(rules))
    with col2:
        rules_with_categories = len([r for r in rules if r.get('category_id')])
        st.metric("With Categories", rules_with_categories)
    with col3:
        rules_without_categories = len(rules) - rules_with_categories
        st.metric("Without Categories", rules_without_categories)
    with col4:
        invalid_category_rules = len([r for r in rules if r.get('category_id') and r.get('category_id') not in categories])
        st.metric("Invalid Categories", invalid_category_rules, delta_color="inverse")

    # Show warnings for invalid category IDs
    invalid_rules = [r for r in rules if r.get('category_id') and r.get('category_id') not in categories]
    if invalid_rules:
        st.error("🚨 **Found rules with invalid category IDs!**")
        st.write("These rules will not work and need to be fixed:")
        for rule in invalid_rules:
            st.write(f"• **{rule['match']}** → Invalid ID: `{rule['category_id']}`")
        st.write("**Fix:** Update these rules with valid category IDs from the dropdown above.")
        st.markdown("---")

    # Sort options
    sort_option = st.selectbox(
        "Sort rules by:",
        ["Match Text (A-Z)", "Category Name (A-Z)", "Created Date (Newest First)", "Created Date (Oldest First)"],
        index=0
    )

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
    else:  # Created Date (Oldest First)
        sorted_rules = sorted(rules, key=lambda x: x.get('created_at', ''))

    # Display existing rules
    st.subheader("📝 Current Rules")

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
                save_rules(rules)
                st.rerun()

        # Display category ID and name for debugging
        if rule.get('category_id'):
            category_id = rule['category_id']
            if category_id in categories:
                category_info = categories[category_id]
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Category:** {category_info['full_name']}")
                with col2:
                    st.code(category_id, language="text")
                    if st.button("📋 Copy ID", key=f"copy_id_{i}"):
                        st.write(f"✅ Copied: `{category_id}`")
            else:
                st.error(f"❌ **Invalid Category ID:** `{category_id}` - Category not found in budget!")
                st.warning("⚠️ This rule will not work until the category ID is corrected.")
        else:
            st.warning("⚠️ **No category selected** - This rule will not categorize transactions.")

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

    # Add new rule section
    st.subheader("➕ Add New Rule")

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        new_match = st.text_input("Match Text", placeholder="e.g., Amazon, Starbucks, etc.")
    with col2:
        new_type = st.selectbox("Match Type", ["contains", "exact", "startsWith"], index=0)
    with col3:
        category_options = [""] + [cat_id for cat_id in categories.keys()]
        category_names = [""] + [categories[cat_id]['full_name'] for cat_id in categories.keys()]
        new_category = st.selectbox("Category", category_names, index=0)

    if st.button("➕ Add Rule"):
        if new_match and new_category:
            selected_category_id = category_options[category_names.index(new_category)]
            current_time = datetime.now().isoformat()
            new_rule = {
                "match": new_match,
                "type": new_type,
                "category_id": selected_category_id,
                "created_at": current_time,
                "updated_at": current_time
            }
            rules.append(new_rule)
            save_rules(rules)
            st.success(f"✅ Rule added: {new_match} → {new_category}")
            st.rerun()
        else:
            st.error("Please provide both match text and category.")

    # Save rules button
    if changed_rule_indices and st.button("💾 Save Changes"):
        save_rules(rules, changed_rule_indices)
        st.success("✅ Rules saved!")
        st.rerun()

    # Quick category ID lookup
    with st.expander("🔍 Quick Category ID Lookup", expanded=False):
        st.write("**Search for a category by name or ID:**")
        col1, col2 = st.columns([3, 1])
        with col1:
            search_term = st.text_input("Search categories:", placeholder="Enter category name or partial ID...")
        with col2:
            if st.button("🔍 Search"):
                st.rerun()

        if search_term:
            search_lower = search_term.lower()
            found_categories = []

            for cat_id, cat_info in categories.items():
                if (search_lower in cat_info['name'].lower() or
                    search_lower in cat_info['group_name'].lower() or
                    search_lower in cat_info['full_name'].lower() or
                    search_lower in cat_id.lower()):
                    found_categories.append((cat_id, cat_info))

            if found_categories:
                st.write(f"**Found {len(found_categories)} matching categories:**")
                for cat_id, cat_info in found_categories:
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        st.code(cat_id[:8] + "...", language="text")
                    with col2:
                        st.write(f"**{cat_info['full_name']}**")
                    with col3:
                        if st.button("📋 Copy Full ID", key=f"copy_lookup_{cat_id}"):
                            st.write(f"✅ Copied: `{cat_id}`")
            else:
                st.info("No categories found matching your search.")

    # Help section
    with st.expander("ℹ️ How to use rules"):
        st.markdown("""
        **Rule Types:**
        - **contains**: Matches if the payee name or memo contains the text (e.g., "Amazon" matches "Amazon Prime")
        - **exact**: Matches only if the payee name or memo exactly equals the text
        - **startsWith**: Matches if the payee name or memo starts with the text (e.g., "Starbucks" matches "Starbucks Downtown")

        **Tips:**
        - Use "contains" for most cases - it's the most flexible
        - Keep match text short but specific (e.g., "Amazon" not "Amazon.com Inc")
        - Rules are applied to both payee names and memos
        - **Transfer transactions are automatically excluded** (cannot be categorized)
        - Rules only apply to regular spending/income transactions
        """)
