import streamlit as st
import os
from dotenv import load_dotenv

import tools
from tools.mcp_client_tool import MCPClientTool
import asyncio

load_dotenv()
DEFAULT_VAULT_PATH = os.getenv('OB_VAULT_PATH', './vault')

# A list of all available tools in a structured format
AVAILABLE_TOOLS = [
    {
        "id": "MCPClient",
        "short_title": "MCP Client",
        "long_title": "MCP Client",
        "category": "MCP",
        "description": "An interactive client to send requests to MCP servers.",
        "render_func": tools.mcp_client_ui.render,
        "requires_vault_path": False
    },
    {
        "id": "HtmlToMarkdown",
        "short_title": "HTML to Markdown",
        "long_title": "HTML to Markdown Converter",
        "category": "Note Taking",
        "description": "A simple utility to convert HTML content into Markdown format.",
        "render_func": tools.html_to_markdown.render,
        "requires_vault_path": False
    },
    {
        "id": "EmojiTagRenamer",
        "short_title": "Emoji Tag Renamer",
        "long_title": "Rename Emoji Tags in Obsidian",
        "category": "Obsidian",
        "description": "Scans your Obsidian vault to find and rename tags containing emojis to be compatible with Obsidian's tagging system.",
        "render_func": tools.emoji_tag_renamer.render,
        "requires_vault_path": True
    },
    {
        "id": "FindUnupdatedLinks",
        "short_title": "Find Unupdated Links",
        "long_title": "Find Un-updated Internal Links in Obsidian",
        "category": "Obsidian",
        "description": "Finds internal links in your Obsidian vault that are using an older format and may need to be updated.",
        "render_func": tools.find_unupdated_links.render,
        "requires_vault_path": True
    },
    {
        "id": "RemoveEmojiLinks",
        "short_title": "Remove Emoji Links",
        "long_title": "Remove Emoji Links from Obsidian Notes",
        "category": "Obsidian",
        "description": "Removes links from your Obsidian notes that contain emojis in the link text or destination.",
        "render_func": tools.remove_emoji_links.render,
        "requires_vault_path": True
    },
    {
        "id": "ReplaceTag",
        "short_title": "Replace Tag",
        "long_title": "Replace a Tag in Obsidian",
        "category": "Obsidian",
        "description": "Performs a find-and-replace operation for a specific tag across all notes in your Obsidian vault.",
        "render_func": tools.replace_tag.render,
        "requires_vault_path": True
    },
    {
        "id": "YnabListBudgets",
        "short_title": "YNAB List Budgets",
        "long_title": "List YNAB Budgets",
        "category": "YNAB",
        "description": "Fetches and displays a list of all your available budgets from the YNAB API.",
        "render_func": tools.ynab_list_budgets.render,
        "requires_vault_path": False
    },
    {
        "id": "YnabGetTransactions",
        "short_title": "YNAB Get Transactions",
        "long_title": "Get Transactions from a YNAB Budget",
        "category": "YNAB",
        "description": "Select a budget and fetch a list of its recent transactions from the YNAB API.",
        "render_func": tools.ynab_get_transactions.render,
        "requires_vault_path": False
    },
    {
        "id": "YnabCreateTransaction",
        "short_title": "YNAB Create Transaction",
        "long_title": "Create a New YNAB Transaction",
        "category": "YNAB",
        "description": "Create a new transaction in a selected budget and account via the YNAB API.",
        "render_func": tools.ynab_create_transaction.render,
        "requires_vault_path": False
    },
]

st.set_page_config(
    page_title="Codiak",
    page_icon="favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar Navigation ---
st.sidebar.title("Tools")

# Use query params for navigation. This allows for link-based navigation.
query_params = st.query_params

# Set the initial tool or get it from query params
if 'tool' in query_params:
    st.session_state.selected_tool_id = query_params.get_all('tool')[0]
else:
    if 'selected_tool_id' not in st.session_state:
        st.session_state.selected_tool_id = AVAILABLE_TOOLS[0]['id']
    st.query_params.update(tool=st.session_state.selected_tool_id)

# Create a dictionary to hold tools by category for the sidebar
categories = {}
for tool in AVAILABLE_TOOLS:
    if tool['category'] not in categories:
        categories[tool['category']] = []
    categories[tool['category']].append(tool)

# Display categories and links
for category, tools_in_category in sorted(categories.items()):
    st.sidebar.subheader(category)
    for tool in tools_in_category:
        st.sidebar.markdown(f"[{tool['short_title']}](?tool={tool['id']})")

# --- Main Page ---

# Show success message if present
if 'success_message' in st.session_state:
    st.success(st.session_state['success_message'])
    del st.session_state['success_message']

# Find the selected tool's definition
selected_tool_definition = next((t for t in AVAILABLE_TOOLS if t['id'] == st.session_state.selected_tool_id), None)

# Render the selected tool
if selected_tool_definition:
    # Display the tool's title and description from the metadata
    st.title(selected_tool_definition['long_title'])
    st.write(selected_tool_definition['description'])
    st.divider()

    # Call the tool's render function
    render_func = selected_tool_definition['render_func']
    if selected_tool_definition['requires_vault_path']:
        render_func(DEFAULT_VAULT_PATH)
    else:
        render_func()
else:
    st.error("Tool not found. Please select a tool from the sidebar.")
    st.stop()