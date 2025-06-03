# Codiak

> **Note:** Codiak is a work-in-progress (WIP) project that will eventually house numerous personal utilities for Cody.

This Streamlit app helps you manage and update your Obsidian vault notes, especially for workflows that use emoji-based filename conventions and tags (like #person). It provides tools to:

- Identify notes with a specific tag that do not start with a specified emoji, and batch-rename them.
- Find and optionally fix links in your vault that do not use the emoji-based filename convention.

## Features

### 1. Emoji Tag Renamer
- Search for notes with a given tag (including YAML frontmatter) that do **not** start with a specified emoji.
- Exclude files by filename substring (e.g., 'template').
- Batch-rename files to prepend the emoji.
- Limit the number of files renamed per operation.

### 2. Find Unupdated Links
- Identify all notes with a tag (e.g., #person) that start with the emoji.
- Search all notes for links to these notes that do **not** include the emoji in the link.
- See real-time progress and results.
- Optionally, batch-fix a limited number of invalid links automatically.

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
3. **Run the app:**
   ```sh
   streamlit run app.py
   ```

## Usage
- Set your Obsidian vault path and desired tag/emoji in the sidebar.
- Use the "Emoji Tag Renamer" tool to find and rename notes.
- Use the "Find Unupdated Links" tool to find and optionally fix links to emoji-named notes.
- Adjust limits and options as needed for safe batch operations.

## Notes
- The app works with standard Obsidian markdown vaults.
- Always back up your vault before running batch rename or link-fix operations.
- The app does not modify note content unless you explicitly enable fixing links.

---
MIT License