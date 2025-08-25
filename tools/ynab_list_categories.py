import streamlit as st
import os
from typing import Dict

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
    """Main render function for the YNAB List Categories tool."""
    st.title("📋 YNAB List Categories")
    st.write("View all categories in your YNAB budget with their IDs and structure.")

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

    st.write(f"📊 Found {len(categories)} categories in your budget")

    # Quick search for problematic category ID
    st.write("---")
    st.subheader("🔍 Quick Category ID Check")
    problematic_id = st.text_input("Enter category ID to check:", value="6d33e675", placeholder="Enter full category ID...")
    if st.button("🔍 Check This Category ID"):
        if problematic_id in categories:
            cat_info = categories[problematic_id]
            st.success(f"✅ **Category FOUND:** {cat_info['full_name']}")
            st.write(f"**ID:** `{problematic_id}`")
            st.write(f"**Name:** {cat_info['name']}")
            st.write(f"**Group:** {cat_info['group_name']}")
        else:
            st.error(f"❌ **Category NOT FOUND:** ID `{problematic_id}` doesn't exist in this budget!")
            st.write("**This explains why updates are failing!**")

            # Show similar categories
            st.write("**Similar categories that DO exist:**")
            similar_count = 0
            for cat_id, cat_info in categories.items():
                if (problematic_id[:4] in cat_id[:4] or
                    "credit" in cat_info['name'].lower() or
                    "chase" in cat_info['name'].lower()):
                    if similar_count < 5:
                        st.write(f"• `{cat_id}` → {cat_info['full_name']}")
                        similar_count += 1
                    else:
                        break

    # Search functionality
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search categories:", placeholder="Enter category name or group...")
    with col2:
        if st.button("🔍 Search"):
            st.rerun()

    # Filter categories based on search
    filtered_categories = {}
    if search_term:
        search_lower = search_term.lower()
        for cat_id, cat_info in categories.items():
            if (search_lower in cat_info['name'].lower() or
                search_lower in cat_info['group_name'].lower() or
                search_lower in cat_info['full_name'].lower()):
                filtered_categories[cat_id] = cat_info
    else:
        filtered_categories = categories

    st.write(f"📋 Showing {len(filtered_categories)} categories")

    # Group categories by group name
    groups = {}
    for cat_id, cat_info in filtered_categories.items():
        group_name = cat_info['group_name']
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append((cat_id, cat_info))

    # Display categories grouped by category group
    for group_name in sorted(groups.keys()):
        with st.expander(f"📁 {group_name} ({len(groups[group_name])} categories)", expanded=True):
            for cat_id, cat_info in groups[group_name]:
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.code(cat_id[:8] + "...", language="text")
                with col2:
                    st.write(f"**{cat_info['name']}**")
                with col3:
                    if st.button("📋 Copy ID", key=f"copy_{cat_id}"):
                        st.write(f"✅ Copied: `{cat_id}`")
                        st.code(cat_id, language="text")

    # Summary section
    st.write("---")
    st.subheader("📊 Category Summary")

    # Count by group
    group_counts = {}
    for cat_info in categories.values():
        group_name = cat_info['group_name']
        group_counts[group_name] = group_counts.get(group_name, 0) + 1

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Categories by Group:**")
        for group_name, count in sorted(group_counts.items()):
            st.write(f"• {group_name}: {count}")

    with col2:
        st.write("**Total Categories:**")
        st.write(f"• **{len(categories)}** total categories")
        st.write(f"• **{len(group_counts)}** category groups")

        if search_term:
            st.write(f"• **{len(filtered_categories)}** matching search")
