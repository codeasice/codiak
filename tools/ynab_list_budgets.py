import streamlit as st
import os
import pandas as pd

# Import ynab only when needed to avoid import errors
try:
    import ynab
    from ynab.api.budgets_api import BudgetsApi
    from ynab.api.categories_api import CategoriesApi
    YNAB_AVAILABLE = True
except ImportError:
    YNAB_AVAILABLE = False

def render():
    if not YNAB_AVAILABLE:
        st.error("YNAB module not available. Please install it with: pip install ynab")
        st.stop()

    ynab_api_key = os.getenv('YNAB_API_KEY')

    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

    # 2. Configure API
    configuration = ynab.Configuration(
        access_token = ynab_api_key
    )

    # Initialize session state for storing data
    if 'budgets' not in st.session_state:
        st.session_state.budgets = []
    if 'selected_budget' not in st.session_state:
        st.session_state.selected_budget = None
    if 'category_groups' not in st.session_state:
        st.session_state.category_groups = []

    # 3. Fetch Budgets
    if st.button("Fetch Budgets"):
        with st.spinner("Fetching budgets and categories..."):
            try:
                with ynab.ApiClient(configuration) as api_client:
                    budgets_api = BudgetsApi(api_client)
                    categories_api = CategoriesApi(api_client)

                    response = budgets_api.get_budgets()
                    budgets = response.data.budgets
                    st.session_state.budgets = budgets

                    # 4. Display Budgets
                    st.success(f"Found {len(budgets)} budgets!")

                    # Create data for table
                    table_data = []

                    for budget in budgets:
                        # Fetch categories for this budget
                        try:
                            categories_response = categories_api.get_categories(budget.id)
                            category_groups = categories_response.data.category_groups

                            if category_groups:
                                for group in category_groups:
                                    for category in group.categories:
                                        table_data.append({
                                            'Budget': budget.name,
                                            'Category Group': group.name,
                                            'Category': category.name,
                                            'Category ID': category.id
                                        })
                            else:
                                table_data.append({
                                    'Budget': budget.name,
                                    'Category Group': 'No categories',
                                    'Category': 'N/A',
                                    'Category ID': 'N/A'
                                })

                        except ynab.ApiException as e:
                            st.error(f"Error fetching categories for {budget.name}: {e.reason}")
                            table_data.append({
                                'Budget': budget.name,
                                'Category Group': 'Error',
                                'Category': 'Error fetching categories',
                                'Category ID': 'N/A'
                            })

                    # Display as table
                    if table_data:
                        df = pd.DataFrame(table_data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No budget categories found.")

            except ynab.ApiException as e:
                st.error(f"Error fetching budgets: {e.reason}")

    # 5. Category Management Section
    st.markdown("---")
    st.subheader("Category Management")

    if st.session_state.budgets:
        # Budget selection
        budget_options = {budget.name: budget for budget in st.session_state.budgets}
        selected_budget_name = st.selectbox(
            "Select a budget:",
            options=list(budget_options.keys()),
            key="budget_selector"
        )

        if selected_budget_name:
            selected_budget = budget_options[selected_budget_name]
            st.session_state.selected_budget = selected_budget

            # Fetch category groups for selected budget
            if st.button("Load Category Groups"):
                with st.spinner("Loading category groups..."):
                    try:
                        with ynab.ApiClient(configuration) as api_client:
                            categories_api = CategoriesApi(api_client)
                            categories_response = categories_api.get_categories(selected_budget.id)
                            st.session_state.category_groups = categories_response.data.category_groups
                            st.success(f"Loaded {len(st.session_state.category_groups)} category groups!")
                    except ynab.ApiException as e:
                        st.error(f"Error loading category groups: {e.reason}")

            # Display category groups
            if st.session_state.category_groups:
                st.write("**Available Category Groups:**")
                for i, group in enumerate(st.session_state.category_groups):
                    with st.expander(f"📁 {group.name} ({len(group.categories)} categories)"):
                        st.write("**Existing Categories:**")
                        if group.categories:
                            for category in group.categories:
                                st.write(f"• {category.name} (ID: {category.id})")
                        else:
                            st.write("No categories in this group")

                        # Note about category creation
                        st.info("💡 **Note**: New categories cannot be created through the YNAB API. The API only supports reading and updating existing categories. To create new categories, please use the YNAB web interface or mobile app.")
    else:
        st.info("Please fetch budgets first to view category information.")