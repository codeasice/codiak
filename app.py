import streamlit as st

# CRITICAL: set_page_config must be the very first Streamlit command
st.set_page_config(
    page_title="Codiak",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os
from dotenv import load_dotenv
import pandas as pd

# Import tools only after page config is set
import tools
from tools.ui_tools_manager import UIToolsManager

load_dotenv()
DEFAULT_VAULT_PATH = os.getenv('OB_VAULT_PATH', './vault')

# Use the fast metadata mode for tool discovery
ui_tools_manager = UIToolsManager(use_fast_mode=True)
TOOLS_METADATA = ui_tools_manager.get_tools()

# --- Sidebar Navigation ---
st.sidebar.title("Tools")

# Set the initial tool or get it from query params
query_params = st.query_params
if 'tool' in query_params:
    st.session_state.selected_tool_id = query_params.get_all('tool')[0]

selected_tool_id = st.session_state.get('selected_tool_id')

# Add a back button to the sidebar if a tool is selected
if selected_tool_id:
    if st.sidebar.button("← Back to Tool Directory", key="back_to_directory", use_container_width=True):
        st.session_state.selected_tool_id = None
        # Remove the 'tool' query param
        st.query_params.clear()
        st.rerun()

# Group tools by category
categories = {}
for tool in TOOLS_METADATA:
    if tool['category'] not in categories:
        categories[tool['category']] = []
    categories[tool['category']].append(tool)

# --- Sidebar: Category Expanders with Buttons ---
for category, tools_in_category in sorted(categories.items()):
    expanded = any(tool['id'] == selected_tool_id for tool in tools_in_category)
    with st.sidebar.expander(category, expanded=expanded):
        for tool in tools_in_category:
            is_selected = tool['id'] == selected_tool_id
            if st.button(tool['short_title'], key=f"sidebar_btn_{tool['id']}", use_container_width=True):
                st.session_state.selected_tool_id = tool['id']
                st.query_params.update(tool=tool['id'])
                st.rerun()

# --- Main Page ---

# Show success message if present
if 'success_message' in st.session_state:
    st.success(st.session_state['success_message'])
    del st.session_state['success_message']

selected_tool_definition = next((t for t in TOOLS_METADATA if t['id'] == selected_tool_id), None)

RENDER_FUNC_MAP = {
    'MCPClient': tools.mcp_client_ui.render,
    'HtmlToMarkdown': tools.html_to_markdown.render,
    'EmojiTagRenamer': tools.emoji_tag_renamer.render,
    'FindUnupdatedLinks': tools.find_unupdated_links.render,
    'RemoveEmojiLinks': tools.remove_emoji_links.render,
    'ReplaceTag': tools.replace_tag.render,
    'Budgets': tools.ynab_list_budgets.render,
    'Transactions': tools.ynab_get_transactions.render,
    'YnabCreateTransaction': tools.ynab_create_transaction.render,
    'TagSearch': tools.tag_search.render,
    'HomeAssistantSensors': tools.home_assistant_sensors.render,
    'SmartThingsListDevices': tools.smartthings_list_devices.render,
    'SmartThingsDashboard': tools.smartthings_dashboard.render,
    'HomeAssistantDashboard': tools.home_assistant_dashboard.render,
    'ItemsToLinks': tools.items_to_links.render,
    'MarkdownStripper': tools.markdown_stripper.render,
    'ColorSwatchInjector': tools.colorswatch_injector.render,
    'NmapNetworkAnalyzer': tools.nmap_network_analyzer.render,
    'YnabUnknownCategoryTransactions': tools.ynab_unknown_category_transactions.render,

    'YnabRules': tools.ynab_rules.render,
    'YnabApplyRules': tools.ynab_apply_rules.render,
    'YnabMapUncategorized': tools.ynab_map_uncategorized.render,
    'YnabListCategories': tools.ynab_list_categories.render,
    'YnabAlluvialDiagram': tools.ynab_alluvial_diagram.render,
    'YnabExportData': tools.ynab_export_data.render,
    'YnabPayeeManager': tools.ynab_payee_manager.render,
    'HomeAutomationCategorizer': tools.home_automation_categorizer.render,
    'TableCreator': tools.table_creator.render,
    'MarkdownTableConverter': tools.markdown_table_converter.render,
    'ChangesInRange': tools.changes_in_range.render,
    'IncompleteTasksInRange': tools.incomplete_tasks_in_range.render,
    'AwsEc2Manager': tools.aws_ec2_manager.render,
    'AwsCostMonitor': tools.aws_cost_monitor.render,
    'DndCharacterEditor': tools.dnd_character_editor.render,
    'AccountDashboard': tools.account_dashboard.render,
    'AccountManager': tools.account_manager.render,
    'CreditCardInterest': tools.credit_card_interest.render,
    'AccountLinkManager': tools.account_link_manager.render,
}

def show_tool_directory():
    st.title("🛠️ Tool Directory")
    st.write("Select a tool from the sidebar or launch one below.")
    table_data = []
    for tool in TOOLS_METADATA:
        table_data.append({
            "Tool": tool["short_title"],
            "Category": tool["category"],
            "Description": tool["description"],
            "ID": tool["id"]
        })
    df = pd.DataFrame(table_data)
    for _, row in df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            st.subheader(row["Tool"])
            st.caption(f"📂 {row['Category']}")
        with col2:
            st.write(row["Description"])
        with col3:
            if st.button("Launch", key=f"launch_{row['ID']}", use_container_width=True):
                st.session_state.selected_tool_id = row['ID']
                st.query_params.update(tool=row['ID'])
                st.rerun()
        st.divider()

if selected_tool_definition:
    # Global logging for tool access
    from datetime import datetime
    timestamp = datetime.now().isoformat()
    print("=" * 100)
    print(f"🌐 GLOBAL TOOL ACCESS LOG - {timestamp}")
    print(f"🔧 Tool: {selected_tool_definition['long_title']}")
    print(f"🆔 Tool ID: {selected_tool_definition['id']}")
    print(f"📂 Category: {selected_tool_definition['category']}")
    print(f"👤 Session ID: {st.session_state.get('session_id', 'unknown')}")
    print(f"📝 Description: {selected_tool_definition['description']}")
    print("=" * 100)

    # Tool metadata is now handled by the tool's own render function
    st.divider()
    render_func = RENDER_FUNC_MAP.get(selected_tool_definition['id'])
    if render_func:
        if selected_tool_definition.get('requires_vault_path'):
            render_func(DEFAULT_VAULT_PATH)
        else:
            render_func()
    else:
        st.error("Render function not found for this tool.")
else:
    show_tool_directory()