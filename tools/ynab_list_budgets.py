import streamlit as st
import ynab
import os
from ynab.api.budgets_api import BudgetsApi

def render():
    ynab_api_key = os.getenv('YNAB_API_KEY')

    if not ynab_api_key:
        st.error("YNAB_API_KEY environment variable not set. Please set it in your .env file.")
        st.stop()

    # 2. Configure API
    configuration = ynab.Configuration(
        access_token = ynab_api_key
    )

    # 3. Fetch Budgets
    if st.button("Fetch Budgets"):
        with st.spinner("Fetching budgets..."):
            try:
                with ynab.ApiClient(configuration) as api_client:
                    api_instance = BudgetsApi(api_client)
                    response = api_instance.get_budgets()
                    budgets = response.data.budgets

                    # 4. Display Budgets
                    st.success(f"Found {len(budgets)} budgets!")
                    for budget in budgets:
                        st.write(f"- {budget.name} (ID: {budget.id})")

            except ynab.ApiException as e:
                st.error(f"Error fetching budgets: {e.reason}")