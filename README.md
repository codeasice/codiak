# Codiak

> **Note:** Codiak is a work-in-progress (WIP) project that houses a growing suite of personal utilities for managing notes, automations, and integrations.

Codiak is a Streamlit-based app that provides a unified interface for managing and updating your Obsidian vault notes, automating workflows, and integrating with external services like YNAB, Home Assistant, and SmartThings. It offers a collection of tools for:

- Batch-renaming and retagging notes
- Fixing and updating internal links
- Converting and cleaning up Markdown and HTML
- Integrating with home automation and finance APIs
- And more!

## Features & Tools

### Note Taking & Markdown Utilities
- **HTML to Markdown Converter**: Convert rich HTML content to Markdown for easy import into Obsidian.
- **Items to Links**: Convert a list of items (one per line) into Obsidian-style links (`[[item]]`).
- **Markdown Stripper**: Remove selected Markdown formatting (headings, lists, bold, etc.) from pasted text.
- **Color Swatch Injector**: Augment Markdown color lists with color swatches next to each color name.

### Obsidian Vault Management
- **Emoji Tag Renamer**: Find notes with a given tag (including YAML frontmatter) that do **not** start with a specified emoji, and batch-rename them.
- **Find Unupdated Links**: Identify and optionally fix links in your vault that do not use the emoji-based filename convention.
- **Remove Emoji Links**: Remove links from your notes that contain emojis in the link text or destination.
- **Replace Tag**: Perform a find-and-replace operation for a specific tag across all notes in your vault.
- **Tag Search**: Search notes in your vault that contain any of the specified tags (YAML or body).

### Home Automation
- **Home Assistant Sensors**: Connect to Home Assistant and list all sensor entities.
- **Home Assistant Dashboard**: Dashboard for Home Assistant entities grouped by type, with toggling for lights and switches.
- **SmartThings Devices**: Connect to SmartThings and list all devices.
- **SmartThings Dashboard**: Dashboard for SmartThings devices grouped by type.

### Finance (YNAB)
- **YNAB List Budgets**: Fetch and display a list of all your available budgets from the YNAB API.
- **YNAB Get Transactions**: Select a budget and fetch a list of its recent transactions from the YNAB API.
- **YNAB Create Transaction**: Create a new transaction in a selected budget and account via the YNAB API.

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
   - `streamlit-quill` (rich text input in Streamlit)
   - `markdownify` (convert HTML to Markdown)
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

| Tool                   | Category         | Description |
|------------------------|-----------------|-------------|
| MCP Client             | MCP             | Interactive client for MCP servers |
| HTML to Markdown       | Note Taking     | Convert HTML content to Markdown |
| Emoji Tag Renamer      | Obsidian        | Rename tags with emojis for Obsidian compatibility |
| Find Unupdated Links   | Obsidian        | Find and fix outdated internal links |
| Remove Emoji Links     | Obsidian        | Remove links with emojis from notes |
| Replace Tag            | Obsidian        | Find-and-replace tags across notes |
| Tag Search             | Obsidian        | Search notes by tags (YAML/body) |
| YNAB List Budgets      | YNAB            | List all YNAB budgets |
| YNAB Get Transactions  | YNAB            | Fetch transactions from a YNAB budget |
| YNAB Create Transaction| YNAB            | Create a new YNAB transaction |
| Home Assistant Sensors | Home Automation | List all Home Assistant sensors |
| Home Assistant Dashboard| Home Automation| Dashboard for Home Assistant entities |
| SmartThings Devices    | Home Automation | List all SmartThings devices |
| SmartThings Dashboard  | Home Automation | Dashboard for SmartThings devices |
| Items to Links         | Note Taking     | Convert list items to Obsidian links |
| Markdown Stripper      | Note Taking     | Remove Markdown formatting |
| Color Swatch Injector  | Note Taking     | Add color swatches to Markdown lists |

## Notes
- The app works with standard Obsidian markdown vaults.
- Always back up your vault before running batch rename or link-fix operations.
- The app does not modify note content unless you explicitly enable fixing links or batch operations.

---
MIT License