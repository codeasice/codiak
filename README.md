# Codiak

> **Note:** Codiak is a work-in-progress (WIP) project that houses a growing suite of personal utilities for managing notes, automations, and integrations.

Codiak is a Streamlit-based app that provides a unified interface for managing and updating your Obsidian vault notes, automating workflows, and integrating with external services like YNAB, Home Assistant, SmartThings, and AWS. It offers a collection of tools for:

- Batch-renaming and retagging notes
- Fixing and updating internal links
- Converting and cleaning up Markdown and HTML
- Integrating with home automation, finance, and cloud APIs
- Network analysis and D&D character management
- And more!

## Features & Tools

### Note Taking & Markdown Utilities
- **HTML to Markdown Converter**: Convert rich HTML content to Markdown for easy import into Obsidian.
- **Items to Links**: Convert a list of items (one per line) into Obsidian-style links (`[[item]]`).
- **Markdown Stripper**: Remove selected Markdown formatting (headings, lists, bold, etc.) from pasted text.
- **Color Swatch Injector**: Augment Markdown color lists with color swatches next to each color name.
- **Table Creator**: Create markdown tables from lists or join two tables (append or align columns).
- **Table Converter**: Convert markdown tables to formats compatible with Microsoft Teams (HTML), Excel (CSV), and Confluence (HTML).

### Obsidian Vault Management
- **Emoji Tag Renamer**: Find notes with a given tag (including YAML frontmatter) that do **not** start with a specified emoji, and batch-rename them.
- **Find Unupdated Links**: Identify and optionally fix links in your vault that do not use the emoji-based filename convention.
- **Remove Emoji Links**: Remove links from your notes that contain emojis in the link text or destination.
- **Replace Tag**: Perform a find-and-replace operation for a specific tag across all notes in your vault.
- **Tag Search**: Search notes in your vault that contain any of the specified tags (YAML or body).
- **Incomplete Tasks in Range**: Find incomplete tasks in notes with titles or sections starting with dates in the specified range.
- **Changes in Range**: Find all Obsidian notes and completed tasks within a date or week range. Compile selected notes into a single text area.
- **Structure Analyzer**: Scan your vault's folder tree to a set depth and get cleanup recommendations.
- **Vault Manager**: Scan your Obsidian vault structure and get AI-powered recommendations for organizing notes and finding relevant information.

### Home Automation
- **Home Assistant Sensors**: Connect to Home Assistant and list all sensor entities.
- **Home Assistant Dashboard**: Dashboard for Home Assistant entities grouped by type, with toggling for lights and switches.
- **SmartThings Devices**: Connect to SmartThings and list all devices.
- **SmartThings Dashboard**: Dashboard for SmartThings devices grouped by type.
- **Home Automation Categorizer**: Categorizes a list of home automation items by their type based on line suffix.

### Finance (YNAB)
- **Budgets**: View your YNAB budgets and categories from the database. See budget information, category structure, and financial details.
- **Transactions**: View your YNAB transactions from the database. See transaction details, summary metrics, and filtering options.
- **YNAB Create Transaction**: Create a new transaction in a selected budget and account via the YNAB API.
- **YNAB Rules Manager**: Create and manage categorization rules for automatic transaction categorization.
- **YNAB Auto-Categorize**: Find transactions that match your categorization rules and apply them automatically.
- **YNAB AI Categorizer**: Use AI assistance to categorize transactions that don't match your rules.
- **YNAB Unknown Category Transactions**: Show transactions from a YNAB budget where the category is unknown (category_id not found).
- **YNAB List Categories**: View all categories in your YNAB budget with their IDs and structure.
- **YNAB Money Flow**: Visualize money flow from payees to categories for a selected month using an interactive alluvial diagram.
- **YNAB Export Data**: Export all YNAB data (budgets, categories, transactions, accounts) to a JSON file for offline analysis.
- **YNAB Payee Manager**: Browse and analyze payees with filtering capabilities. View transaction history and category breakdowns for each payee.
- **YNAB Spend Graph**: Display a graph of daily YNAB transaction spend for select categories across a selected date range.
- **Account Dashboard**: View your financial accounts organized by type and hierarchy. See account balances, totals, and account structure.
- **Account Manager**: List, edit, and manage your financial accounts. Update account details, hierarchy, and financial information.
- **Credit Card Interest**: Calculate daily interest costs for credit card balances based on APRs. See how much interest you're paying each day.
- **Account Link Manager**: Manage links between your local accounts and YNAB accounts. View, add, and delete account connections for data synchronization.

### AWS Cloud Management
- **AWS EC2 Manager**: List and manage your AWS EC2 instances. View instance status and toggle them on/off.
- **AWS Cost Monitor**: Monitor your AWS costs and spending patterns using AWS Cost Explorer. View costs by service and region.

### Network Analysis
- **Network Analyzer (nmap)**: Analyze the current network using nmap. Scan for live hosts and open ports.

### Game Development
- **D&D Character Editor**: Edit primary properties of D&D characters (hero.json, npc.json) and monsters (monster.json) with a comprehensive UI.

### Developer & Integration Tools
- **MCP Client**: An interactive client to send requests to MCP servers.

## Setup

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   This will install all required packages, including:
   - `streamlit` (web app framework)
   - `python-dotenv` (for .env support)
   - `markdownify` (convert HTML to Markdown)
   - `ynab` (YNAB API client)
   - `boto3` (AWS SDK)
   - `python-nmap` (network scanning)
   - `pandas` (data manipulation)
   - And many more dependencies (see requirements.txt for full list)
3. **(Optional) Set your Obsidian vault path with a .env file:**
   - Create a file named `.env` in the project root with the following content:
     ```env
     OB_VAULT_PATH=C:\Users\live\Documents\ObsidianVault
     ```
   - If not set, the app will default to `./vault`.
4. **Run the app:**
   ```sh
   streamlit run app.py
   # Or, to ensure using the right Python:
   python -m streamlit run app.py
   ```

## Usage
- Use the sidebar to select a tool by category.
- For Obsidian tools, set your vault path and any required options.
- Use automation and finance tools by providing the necessary API credentials (see tool UI for details).
- Always back up your vault before running batch operations that modify files or links.

## Available Tools

### MCP
| Tool                   | Description |
|------------------------|-------------|
| MCP Client             | Interactive client for MCP servers |

### Note Taking
| Tool                   | Description |
|------------------------|-------------|
| HTML to Markdown       | Convert HTML content to Markdown |
| Items to Links         | Convert list items to Obsidian links |
| Markdown Stripper      | Remove Markdown formatting |
| Color Swatch Injector  | Add color swatches to Markdown lists |
| Table Creator          | Create markdown tables from lists or join two tables |
| Table Converter        | Convert markdown tables to Teams/Excel/Confluence formats |

### Obsidian
| Tool                   | Description |
|------------------------|-------------|
| Emoji Tag Renamer      | Rename tags with emojis for Obsidian compatibility |
| Find Unupdated Links   | Find and fix outdated internal links |
| Remove Emoji Links     | Remove links with emojis from notes |
| Replace Tag            | Find-and-replace tags across notes |
| Tag Search             | Search notes by tags (YAML/body) |
| Incomplete Tasks in Range | Find incomplete tasks in notes with date-based titles or sections |
| Changes in Range       | Find notes and completed tasks within a date range |
| Structure Analyzer     | Scan vault folder tree and get cleanup recommendations |
| Vault Manager          | Get AI-powered recommendations for organizing notes |

### Financial/YNAB
| Tool                   | Description |
|------------------------|-------------|
| Budgets                | View YNAB budgets and categories from database |
| Transactions           | View YNAB transactions from database with filtering |
| YNAB Create Transaction| Create a new YNAB transaction via API |
| YNAB Rules Manager     | Create and manage categorization rules |
| YNAB Auto-Categorize   | Apply categorization rules to matching transactions |
| YNAB AI Categorizer    | Use AI to categorize transactions without rules |
| YNAB Unknown Category Txns | Show transactions with unknown categories |
| YNAB List Categories   | View all categories with IDs and structure |
| YNAB Money Flow        | Visualize money flow from payees to categories |
| YNAB Export Data       | Export all YNAB data to JSON |
| YNAB Payee Manager     | Browse and analyze payees with transaction history |
| YNAB Spend Graph       | Display daily spend graph for selected categories |
| Account Dashboard      | View financial accounts organized by type and hierarchy |
| Account Manager        | List, edit, and manage financial accounts |
| Credit Card Interest   | Calculate daily interest costs for credit card balances |
| Account Link Manager   | Manage links between local and YNAB accounts |

### Home Automation
| Tool                   | Description |
|------------------------|-------------|
| Home Assistant Sensors | List all Home Assistant sensor entities |
| Home Assistant Dashboard| Dashboard for Home Assistant entities with toggling |
| SmartThings Devices    | List all SmartThings devices |
| SmartThings Dashboard  | Dashboard for SmartThings devices grouped by type |
| Home Automation Categorizer | Categorize home automation items by type |

### AWS
| Tool                   | Description |
|------------------------|-------------|
| AWS EC2 Manager        | List and manage AWS EC2 instances |
| AWS Cost Monitor       | Monitor AWS costs and spending patterns |

### Network Analysis
| Tool                   | Description |
|------------------------|-------------|
| Network Analyzer       | Analyze network using nmap (scan hosts and ports) |

### Game Development
| Tool                   | Description |
|------------------------|-------------|
| D&D Character Editor   | Edit D&D characters and monsters with comprehensive UI |

## Notes
- The app works with standard Obsidian markdown vaults.
- Always back up your vault before running batch rename or link-fix operations.
- The app does not modify note content unless you explicitly enable fixing links or batch operations.

---
MIT License