"""Pure metadata definitions for UI tools - no imports, instant access."""

# Pure metadata without any class imports for fast CLI access
UI_TOOLS_METADATA = [
    {
        "id": "MCPClient",
        "short_title": "MCP Client",
        "long_title": "MCP Client",
        "category": "MCP",
        "description": "An interactive client to send requests to MCP servers.",
        "requires_vault_path": False
    },
    {
        "id": "HtmlToMarkdown",
        "short_title": "HTML to Markdown",
        "long_title": "HTML to Markdown Converter",
        "category": "Note Taking",
        "description": "A simple utility to convert HTML content into Markdown format.",
        "requires_vault_path": False
    },
    {
        "id": "EmojiTagRenamer",
        "short_title": "Emoji Tag Renamer",
        "long_title": "Rename Emoji Tags in Obsidian",
        "category": "Obsidian",
        "description": "Scans your Obsidian vault to find and rename tags containing emojis to be compatible with Obsidian's tagging system.",
        "requires_vault_path": True
    },
    {
        "id": "FindUnupdatedLinks",
        "short_title": "Find Unupdated Links",
        "long_title": "Find Un-updated Internal Links in Obsidian",
        "category": "Obsidian",
        "description": "Finds internal links in your Obsidian vault that are using an older format and may need to be updated.",
        "requires_vault_path": True
    },
    {
        "id": "RemoveEmojiLinks",
        "short_title": "Remove Emoji Links",
        "long_title": "Remove Emoji Links from Obsidian Notes",
        "category": "Obsidian",
        "description": "Removes links from your Obsidian notes that contain emojis in the link text or destination.",
        "requires_vault_path": True
    },
    {
        "id": "ReplaceTag",
        "short_title": "Replace Tag",
        "long_title": "Replace a Tag in Obsidian",
        "category": "Obsidian",
        "description": "Performs a find-and-replace operation for a specific tag across all notes in your Obsidian vault.",
        "requires_vault_path": True
    },
    {
        "id": "YnabListBudgets",
        "short_title": "YNAB List Budgets",
        "long_title": "List YNAB Budgets",
        "category": "YNAB",
        "description": "Fetches and displays a list of all your available budgets from the YNAB API.",
        "requires_vault_path": False
    },
    {
        "id": "YnabGetTransactions",
        "short_title": "YNAB Get Transactions",
        "long_title": "Get Transactions from a YNAB Budget",
        "category": "YNAB",
        "description": "Select a budget and fetch a list of its recent transactions from the YNAB API.",
        "requires_vault_path": False
    },
    {
        "id": "YnabCreateTransaction",
        "short_title": "YNAB Create Transaction",
        "long_title": "Create a New YNAB Transaction",
        "category": "YNAB",
        "description": "Create a new transaction in a selected budget and account via the YNAB API.",
        "requires_vault_path": False
    },
]

def get_tools_metadata_fast():
    """
    Get tool metadata instantly without any imports.
    This is the fastest possible way to get tool information.

    Returns:
        List: List of tool dictionaries with metadata only
    """
    return UI_TOOLS_METADATA