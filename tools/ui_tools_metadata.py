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
    {
        "id": "YnabUnknownCategoryTransactions",
        "short_title": "YNAB Unknown Category Txns",
        "long_title": "YNAB Transactions with Unknown Category",
        "category": "YNAB",
        "description": "Show transactions from a YNAB budget where the category is unknown (category_id not found).",
        "requires_vault_path": False
    },
    {
        "id": "TagSearch",
        "short_title": "Tag Search",
        "long_title": "Tag Search in Obsidian Notes",
        "category": "Obsidian",
        "description": "Search notes in your Obsidian vault that contain any of the specified tags (YAML or body).",
        "requires_vault_path": True
    },
    {
        "id": "HomeAssistantSensors",
        "short_title": "HA Sensors",
        "long_title": "Home Assistant Sensors",
        "category": "Home Automation",
        "description": "Connects to Home Assistant and lists all sensor entities.",
        "requires_vault_path": False
    },
    {
        "id": "SmartThingsListDevices",
        "short_title": "ST Devices",
        "long_title": "SmartThings Devices",
        "category": "Home Automation",
        "description": "Connects to SmartThings and lists all devices.",
        "requires_vault_path": False
    },
    {
        "id": "SmartThingsDashboard",
        "short_title": "ST Dashboard",
        "long_title": "SmartThings Dashboard",
        "category": "Home Automation",
        "description": "Dashboard for SmartThings devices grouped by type.",
        "requires_vault_path": False
    },
    {
        "id": "HomeAssistantDashboard",
        "short_title": "HA Dashboard",
        "long_title": "Home Assistant Dashboard",
        "category": "Home Automation",
        "description": "Dashboard for Home Assistant entities grouped by type, with toggling for lights and switches.",
        "requires_vault_path": False
    },
    {
        "id": "ItemsToLinks",
        "short_title": "Items to Links",
        "long_title": "Convert List Items to Obsidian Links",
        "category": "Note Taking",
        "description": "Converts a list of items (one per line) into Obsidian-style links ([[item]]).",
        "requires_vault_path": False
    },
    {
        "id": "MarkdownStripper",
        "short_title": "Markdown Stripper",
        "long_title": "Remove Markdown Formatting Elements",
        "category": "Note Taking",
        "description": "Remove selected markdown formatting (headings, lists, bold, etc.) from pasted text.",
        "requires_vault_path": False
    },
    {
        "id": "ColorSwatchInjector",
        "short_title": "Color Swatch Injector",
        "long_title": "Inject Color Swatches into Markdown Lists",
        "category": "Note Taking",
        "description": "Augments markdown color lists with color swatches next to each color name.",
        "requires_vault_path": False
    },
    {
        "id": "NmapNetworkAnalyzer",
        "short_title": "Network Analyzer",
        "long_title": "Network Analyzer (nmap)",
        "category": "Network Analysis",
        "description": "Analyze the current network using nmap. Scan for live hosts and open ports.",
        "requires_vault_path": False
    },
    {
        "id": "HomeAutomationCategorizer",
        "short_title": "HA Categorizer",
        "long_title": "Home Automation List Categorizer",
        "category": "Home Automation",
        "description": "Categorizes a list of home automation items by their type based on line suffix.",
        "requires_vault_path": False
    },
    {
        "id": "MarkdownTableStripper",
        "short_title": "Table Stripper",
        "long_title": "Markdown Table Stripper",
        "category": "Note Taking",
        "description": "Strips markdown table formatting, outputting just the cell contents as plain lines.",
        "requires_vault_path": False
    },
    {
        "id": "TableCreator",
        "short_title": "Table Creator",
        "long_title": "Markdown Table Creator/Joiner",
        "category": "Note Taking",
        "description": "Create a markdown table from a list or join two tables (append or align columns).",
        "requires_vault_path": False
    },
    {
        "id": "ChangesInRange",
        "short_title": "Changes in Range",
        "long_title": "Find Notes and Tasks Changed in Date Range",
        "category": "Obsidian",
        "description": "Find all Obsidian notes and completed tasks within a date or week range. Compile selected notes into a single text area.",
        "requires_vault_path": True
    },
    {
        "id": "IncompleteTasksInRange",
        "short_title": "Incomplete Tasks in Range",
        "long_title": "Find Incomplete Tasks in Date Range",
        "category": "Obsidian",
        "description": "Find incomplete tasks in notes with titles or sections starting with dates in the specified range.",
        "requires_vault_path": True
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