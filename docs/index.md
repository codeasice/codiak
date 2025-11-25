# Codiak Project Documentation

**Last Updated:** 2025-01-27  
**Project Type:** Streamlit Web Application  
**Language:** Python 3.x  
**Status:** Work in Progress (WIP)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tool System](#tool-system)
4. [External Integrations](#external-integrations)
5. [Development Setup](#development-setup)
6. [Configuration](#configuration)
7. [Code Patterns](#code-patterns)
8. [Project Structure](#project-structure)

---

## Project Overview

Codiak is a modular Streamlit-based web application that provides a unified interface for managing personal productivity tools, including:

- **Obsidian Vault Management**: Batch operations, link fixing, tag management, and vault analysis
- **Financial Management (YNAB)**: Transaction categorization, budgeting, account management, and data visualization
- **Home Automation**: Integration with Home Assistant and SmartThings for device management
- **Note Taking Utilities**: Markdown/HTML conversion, formatting tools, and content manipulation
- **AWS Management**: EC2 instance management and cost monitoring
- **Developer Tools**: MCP client, network analysis, and various utility tools

### Key Characteristics

- **Modular Architecture**: Each tool is a self-contained module in the `tools/` directory
- **Registry-Based Navigation**: Tools are registered in metadata and discovered dynamically
- **URL-Based Routing**: Deep linking to specific tools via query parameters
- **Category Organization**: Tools grouped by functional category (Obsidian, YNAB, Home Automation, etc.)
- **Fast Metadata Mode**: Tool discovery uses lightweight metadata for performance

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    app.py (Main Entry)                   │
│  - Page configuration                                    │
│  - Navigation & routing                                  │
│  - Tool registry management                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ├─────────────────┐
                   │                 │
┌──────────────────▼──────────┐  ┌───▼──────────────────────┐
│  UIToolsManager             │  │  ui_tools_metadata.py    │
│  - Fast mode (metadata)    │  │  - Pure metadata         │
│  - Full mode (instantiated) │  │  - No imports           │
└──────────────────┬──────────┘  └─────────────────────────┘
                   │
                   │
┌──────────────────▼──────────────────────────────────────┐
│              tools/ Directory                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Tool Module  │  │ Tool Module  │  │ Tool Module  │ │
│  │ (render())   │  │ (render())   │  │ (render())   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Main Application (`app.py`)

**Responsibilities:**
- Streamlit page configuration
- Sidebar navigation with category-based organization
- Query parameter-based routing
- Tool selection and rendering
- Session state management

**Key Patterns:**
- **Registry Pattern**: Tools defined in `TOOLS_METADATA` from `UIToolsManager`
- **Render Function Map**: Maps tool IDs to their render functions
- **Query Parameter Routing**: Uses `st.query_params` for deep linking

**Code Structure:**
```python
# Tool discovery via UIToolsManager
ui_tools_manager = UIToolsManager(use_fast_mode=True)
TOOLS_METADATA = ui_tools_manager.get_tools()

# Category grouping
categories = {}
for tool in TOOLS_METADATA:
    categories.setdefault(tool['category'], []).append(tool)

# Tool rendering
render_func = RENDER_FUNC_MAP.get(selected_tool_definition['id'])
render_func()  # or render_func(vault_path) for vault-requiring tools
```

#### 2. Tool System (`tools/`)

**Architecture Pattern:** Modular Tool Pattern

Each tool is:
- A self-contained Python module
- Exports a `render()` function
- Optionally requires vault path as parameter
- Registered in `ui_tools_metadata.py`

**Tool Module Structure:**
```python
# tools/example_tool.py
def render(vault_path: str = ""):
    """Main render function for the tool."""
    st.title("Tool Title")
    st.write("Tool description")
    # Tool implementation
```

**Tool Registration:**
- Metadata defined in `tools/ui_tools_metadata.py`
- Each tool has: `id`, `short_title`, `long_title`, `category`, `description`, `requires_vault_path`
- Render function mapped in `app.py` `RENDER_FUNC_MAP`

#### 3. Tool Manager (`tools/ui_tools_manager.py`)

**Modes:**
- **Fast Mode** (default): Uses `ui_tools_metadata.py` for instant access without imports
- **Full Mode**: Instantiates tools with full class imports (requires AIPMan instance)

**Benefits:**
- Fast startup time
- Lazy loading of tool implementations
- Fallback mechanism if full mode fails

---

## Tool System

### Tool Categories

The application organizes tools into the following categories:

1. **MCP** (1 tool)
   - MCP Client: Interactive client for MCP servers

2. **Note Taking** (5 tools)
   - HTML to Markdown Converter
   - Items to Links
   - Markdown Stripper
   - Color Swatch Injector
   - Markdown Table Converter

3. **Obsidian** (9 tools)
   - Emoji Tag Renamer
   - Find Unupdated Links
   - Remove Emoji Links
   - Replace Tag
   - Tag Search
   - Structure Analyzer
   - Vault Manager
   - Note Placement
   - Changes in Range
   - Incomplete Tasks in Range

4. **Financial/YNAB** (13 tools)
   - Budgets & Categories
   - Transactions
   - Create Transaction
   - Rules Manager
   - Auto-Categorize
   - AI Categorizer
   - List Categories
   - Money Flow Visualization
   - Data Export
   - Payee Manager
   - Spend Graph
   - Account Dashboard
   - Account Manager
   - Credit Card Interest Calculator
   - Account Link Manager

5. **Home Automation** (4 tools)
   - Home Assistant Sensors
   - Home Assistant Dashboard
   - SmartThings Devices
   - SmartThings Dashboard
   - Home Automation Categorizer

6. **AWS** (2 tools)
   - EC2 Manager
   - Cost Monitor

7. **Network Analysis** (1 tool)
   - Network Analyzer (nmap)

8. **Game Development** (1 tool)
   - D&D Character Editor

**Total: 36+ tools**

### Tool Metadata Structure

```python
{
    "id": "ToolId",                    # Unique identifier
    "short_title": "Short Name",       # Sidebar display name
    "long_title": "Full Tool Name",    # Main page title
    "category": "Category Name",       # Grouping category
    "description": "Tool description", # What the tool does
    "requires_vault_path": False       # Whether tool needs Obsidian vault
}
```

### Adding a New Tool

1. **Create tool module** in `tools/` directory:
   ```python
   # tools/my_new_tool.py
   import streamlit as st
   
   def render(vault_path: str = ""):
       st.title("My New Tool")
       # Implementation
   ```

2. **Register in metadata** (`tools/ui_tools_metadata.py`):
   ```python
   {
       "id": "MyNewTool",
       "short_title": "New Tool",
       "long_title": "My New Tool",
       "category": "Category",
       "description": "Description",
       "requires_vault_path": False
   }
   ```

3. **Add to imports** (`tools/__init__.py`):
   ```python
   from . import my_new_tool
   ```

4. **Map render function** (`app.py`):
   ```python
   RENDER_FUNC_MAP = {
       # ... existing tools
       'MyNewTool': tools.my_new_tool.render,
   }
   ```

---

## External Integrations

### 1. YNAB (You Need A Budget) API

**Purpose:** Financial transaction management, budgeting, and categorization

**Key Tools:**
- Transaction fetching and creation
- Category management
- Rule-based auto-categorization
- AI-assisted categorization
- Data export and visualization

**Configuration:**
- API key via `YNAB_API_KEY` environment variable
- Budget selection via UI
- Local database (`accounts.db`) for account management

**Key Files:**
- `tools/ynab_*.py` - YNAB-related tools
- `tools/ynab_rules.py` - Categorization rules engine
- `tools/ynab_categorizer.py` - AI categorization logic

### 2. Home Assistant

**Purpose:** Home automation device management

**Key Tools:**
- Sensor listing
- Entity dashboard with controls
- Device toggling (lights, switches)

**Configuration:**
- Home Assistant URL and API token via environment variables or UI input

**Key Files:**
- `tools/home_assistant_sensors.py`
- `tools/home_assistant_dashboard.py`

### 3. SmartThings

**Purpose:** SmartThings device management

**Key Tools:**
- Device listing
- Device dashboard

**Configuration:**
- SmartThings API token via environment variables or UI input

**Key Files:**
- `tools/smartthings_list_devices.py`
- `tools/smartthings_dashboard.py`

### 4. AWS Services

**Purpose:** Cloud resource management

**Key Tools:**
- EC2 instance management (start/stop)
- Cost monitoring via Cost Explorer

**Configuration:**
- AWS credentials via `codiak` profile (see `.cursor-rules.yaml`)
- Pattern: `boto3.Session(profile_name='codiak')`

**Key Files:**
- `tools/aws_ec2_manager.py`
- `tools/aws_cost_monitor.py`

### 5. MCP (Model Context Protocol)

**Purpose:** Interactive client for MCP servers

**Key Features:**
- Server connection management
- Tool discovery and execution
- Agent-based interactions

**Key Files:**
- `tools/mcp_client_tool.py`
- `tools/mcp_client_ui.py`

### 6. LLM Integration

**Purpose:** AI-assisted features

**Usage:**
- Transaction categorization
- Vault structure analysis
- Note placement recommendations

**Key Files:**
- `tools/llm_utils.py` - LLM client wrapper
- Used by: `ynab_map_uncategorized.py`, `obsidian_vault_manager.py`, `note_placement.py`

---

## Development Setup

### Prerequisites

- Python 3.x
- pip package manager
- (Optional) Virtual environment

### Installation Steps

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd codiak
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv env
   # Windows:
   env\Scripts\activate
   # Linux/Mac:
   source env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create `.env` file in project root:
   ```env
   OB_VAULT_PATH=C:\Users\YourName\Documents\ObsidianVault
   YNAB_API_KEY=your_ynab_api_key
   # Add other API keys as needed
   ```

5. **Run application:**
   ```bash
   streamlit run app.py
   # Or:
   python -m streamlit run app.py
   ```

### Key Dependencies

**Core Framework:**
- `streamlit==1.49.1` - Web application framework
- `python-dotenv==1.1.1` - Environment variable management

**Data Processing:**
- `pandas==2.3.2` - Data manipulation
- `numpy==2.3.2` - Numerical operations

**API Clients:**
- `ynab==1.8.0` - YNAB API client
- `boto3==1.40.21` - AWS SDK
- `requests==2.32.5` - HTTP requests
- `httpx==0.28.1` - Async HTTP client

**Markdown/HTML:**
- `markdownify==1.2.0` - HTML to Markdown conversion
- `beautifulsoup4==4.13.5` - HTML parsing
- `PyYAML==6.0.2` - YAML parsing

**AI/LLM:**
- `anthropic==0.64.0` - Anthropic Claude API
- `openai==1.102.0` - OpenAI API
- `langchain-core==0.3.75` - LangChain framework

**Visualization:**
- `altair==5.5.0` - Statistical visualization
- `pydeck==0.9.1` - 3D visualization

**Other:**
- `python-nmap==0.7.1` - Network scanning
- `GitPython==3.1.45` - Git operations
- `mcp==1.13.1` - Model Context Protocol

---

## Configuration

### Environment Variables

**Obsidian:**
- `OB_VAULT_PATH` - Path to Obsidian vault (defaults to `./vault`)

**YNAB:**
- `YNAB_API_KEY` - YNAB API key from developer settings

**Home Assistant:**
- Configured via UI or environment variables (tool-specific)

**SmartThings:**
- Configured via UI or environment variables (tool-specific)

**AWS:**
- Uses AWS profile: `codiak`
- Configure via: `aws configure --profile codiak`

### Configuration Files

**`.env`** - Environment variables (not committed to git)

**`.cursor-rules.yaml`** - Cursor IDE rules:
- Python style configuration
- AWS connection patterns
- File ignore patterns

**`config.json`** - MCP client configuration (if used)

**`ynab_categorizer_rules.json`** - YNAB categorization rules

**`accounts.db`** - SQLite database for account management (YNAB tools)

---

## Code Patterns

### 1. Modular Tool Pattern

**Problem Solved:** Avoid monolithic `if/elif` blocks for tool selection

**Solution:**
- Each tool is a separate module
- Tools registered in metadata
- Render functions mapped by ID
- URL-based navigation

**Benefits:**
- Scalable: Easy to add new tools
- Maintainable: Isolated tool code
- Deep linking: Direct URLs to tools

### 2. Fast Metadata Mode

**Problem Solved:** Slow startup when importing all tools

**Solution:**
- Pure metadata file (`ui_tools_metadata.py`) with no imports
- Fast tool discovery without instantiation
- Lazy loading of actual tool implementations

**Benefits:**
- Fast application startup
- Reduced memory footprint
- Better user experience

### 3. Vault Path Pattern

**Pattern:**
```python
DEFAULT_VAULT_PATH = os.getenv('OB_VAULT_PATH', './vault')

# Tools that need vault path
if selected_tool_definition.get('requires_vault_path'):
    render_func(DEFAULT_VAULT_PATH)
else:
    render_func()
```

**Usage:**
- Obsidian tools receive vault path as parameter
- Other tools don't need it
- Configurable via environment variable

### 4. Session State Management

**Pattern:**
- Use `st.session_state` for tool state
- Query parameters for navigation
- Success messages via session state

**Example:**
```python
if 'success_message' in st.session_state:
    st.success(st.session_state['success_message'])
    del st.session_state['success_message']
```

### 5. Error Handling Pattern

**Common Pattern:**
```python
try:
    # API call or operation
    result = api_call()
except Exception as e:
    st.error(f"❌ **Error**: {str(e)}")
    return
```

### 6. AWS Connection Pattern

**From `.cursor-rules.yaml`:**
```python
session = boto3.Session(profile_name='codiak')
client = session.client('service_name')
```

**Error Handling:**
- Handle `NoCredentialsError`
- Handle `ClientError`
- Provide clear error messages

---

## Project Structure

```
codiak/
├── app.py                          # Main application entry point
├── requirements.txt                 # Python dependencies
├── README.md                       # User-facing documentation
├── .env                            # Environment variables (not committed)
├── .cursor-rules.yaml              # Cursor IDE configuration
│
├── tools/                          # Tool modules directory
│   ├── __init__.py                # Tool imports
│   ├── ui_tools_manager.py        # Tool discovery and management
│   ├── ui_tools_metadata.py       # Pure metadata (no imports)
│   ├── ui_tools_definitions.py    # Full tool definitions (if used)
│   ├── llm_utils.py              # LLM client wrapper
│   │
│   ├── # Obsidian tools
│   ├── emoji_tag_renamer.py
│   ├── find_unupdated_links.py
│   ├── remove_emoji_links.py
│   ├── replace_tag.py
│   ├── tag_search.py
│   ├── obsidian_structure_analyzer.py
│   ├── obsidian_vault_manager.py
│   ├── note_placement.py
│   ├── changes_in_range.py
│   └── incomplete_tasks_in_range.py
│   │
│   ├── # YNAB tools
│   ├── ynab_list_budgets.py
│   ├── ynab_get_transactions.py
│   ├── ynab_create_transaction.py
│   ├── ynab_rules.py
│   ├── ynab_apply_rules.py
│   ├── ynab_map_uncategorized.py
│   ├── ynab_list_categories.py
│   ├── ynab_alluvial_diagram.py
│   ├── ynab_export_data.py
│   ├── ynab_payee_manager.py
│   ├── ynab_spend_graph.py
│   ├── ynab_unknown_category_transactions.py
│   ├── account_dashboard.py
│   ├── account_manager.py
│   ├── credit_card_interest.py
│   └── account_link_manager.py
│   │
│   ├── # Home Automation tools
│   ├── home_assistant_sensors.py
│   ├── home_assistant_dashboard.py
│   ├── smartthings_list_devices.py
│   ├── smartthings_dashboard.py
│   └── home_automation_categorizer.py
│   │
│   ├── # AWS tools
│   ├── aws_ec2_manager.py
│   └── aws_cost_monitor.py
│   │
│   ├── # Note Taking tools
│   ├── html_to_markdown.py
│   ├── items_to_links.py
│   ├── markdown_stripper.py
│   ├── colorswatch_injector.py
│   ├── table_creator.py
│   └── markdown_table_converter.py
│   │
│   ├── # Other tools
│   ├── mcp_client_tool.py
│   ├── mcp_client_ui.py
│   ├── nmap_network_analyzer.py
│   └── dnd_character_editor.py
│
├── docs/                           # Documentation
│   ├── index.md                   # This file
│   └── technical/                 # Technical documentation
│
├── cli/                            # CLI utilities
│   ├── list_ui_tools.py
│   └── search-tags.py
│
├── mcp_tools/                     # MCP-related tools
│   ├── search_tags.py
│   └── ui_tools_mcp.py
│
├── aipman/                         # AI Procurement Manager (experiments)
│   └── experiments/
│       └── mcp_client.py
│
├── env/                            # Virtual environment (not committed)
│
└── # Data files (not committed to git)
    ├── accounts.db                 # SQLite database for accounts
    ├── config.json                # MCP configuration
    ├── ynab_categorizer_rules.json # YNAB rules
    ├── hero.json                  # D&D character data
    ├── npc.json                   # D&D NPC data
    └── monster.json               # D&D monster data
```

---

## Development Guidelines

### Adding New Tools

1. Follow the modular tool pattern
2. Create `render()` function with optional `vault_path` parameter
3. Register in `ui_tools_metadata.py`
4. Add import to `tools/__init__.py`
5. Map render function in `app.py` `RENDER_FUNC_MAP`

### Code Style

- Follow PEP 8
- Max line length: 100 characters
- Use type hints where appropriate
- Document functions with docstrings

### Error Handling

- Always handle API errors gracefully
- Show user-friendly error messages
- Use Streamlit error components (`st.error`, `st.warning`)

### Testing

- Test tools individually
- Verify vault path handling for Obsidian tools
- Test API integrations with mock data when possible

---

## Future Enhancements

### Potential Improvements

1. **Testing Framework**: Add unit tests for tools
2. **Tool Versioning**: Track tool versions in metadata
3. **Plugin System**: Allow external tool plugins
4. **User Preferences**: Save user settings and preferences
5. **Tool Analytics**: Track tool usage statistics
6. **Batch Operations**: Queue multiple tool operations
7. **Export/Import**: Export tool configurations

---

## Troubleshooting

### Common Issues

**Tool not appearing in sidebar:**
- Check `ui_tools_metadata.py` registration
- Verify import in `tools/__init__.py`
- Check render function mapping in `app.py`

**Vault path errors:**
- Verify `OB_VAULT_PATH` in `.env`
- Check vault path exists and is accessible
- Ensure proper permissions

**API connection errors:**
- Verify API keys in environment variables
- Check network connectivity
- Review API rate limits

**AWS connection errors:**
- Verify `codiak` profile configured: `aws configure --profile codiak`
- Check AWS credentials are valid
- Verify IAM permissions

---

## Additional Resources

- **Streamlit Documentation**: https://docs.streamlit.io/
- **YNAB API Documentation**: https://api.youneedabudget.com/
- **Home Assistant API**: https://developers.home-assistant.io/
- **SmartThings API**: https://developer.smartthings.com/
- **AWS SDK Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

---

## License

MIT License

---

*This documentation is maintained as part of the Codiak project. For questions or contributions, please refer to the project repository.*

