# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Codiak is a personal utility platform migrating from a **Streamlit** monolith to a **React + FastAPI** stack. Both versions run side-by-side. Tools are being incrementally migrated: Streamlit tools remain fully functional while migrated tools get React UIs backed by FastAPI.

## Running the Application

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install fastapi uvicorn[standard] markdownify pdfkit

# Install frontend dependencies
cd web && npm install && cd ..

# Run React + FastAPI (new version) - launches both servers in separate windows
.\run_react.bat
#   React frontend: http://localhost:5173
#   FastAPI backend: http://localhost:8000
#   API docs (Swagger): http://localhost:8000/docs

# Run Streamlit (legacy version)
streamlit run app.py
#   Streamlit UI: http://localhost:8501
```

## Environment

Create a `.env` file in the project root:
- `OB_VAULT_PATH` - Path to your Obsidian vault (defaults to `./vault`)
- API keys for YNAB, Home Assistant, SmartThings, AWS as needed

## Architecture

### Dual-Stack Overview

```
web/src/          React + TypeScript frontend (Vite)
api/              FastAPI backend
  main.py         App entry point, CORS config (allows :5173)
  routers/        Route handlers (tools.py, text_tools.py)
  services/       Business logic (text_tools_service.py)
tools/            Streamlit tool modules + shared utilities
app.py            Streamlit entry point
```

### Streamlit Tool Registration (3-file pattern)

To add a new Streamlit tool, register it in all three places:

1. **`tools/ui_tools_metadata.py`** — Add metadata dict to `UI_TOOLS_METADATA`:
   ```python
   {
       "id": "MyNewTool",           # CamelCase, unique
       "short_title": "My Tool",    # Sidebar label
       "long_title": "My Full Name",
       "category": "Category Name",
       "description": "What it does.",
       "requires_vault_path": False  # True → render(vault_path)
   }
   ```

2. **`tools/__init__.py`** — `from . import my_new_tool`

3. **`app.py`** — Add to `RENDER_FUNC_MAP`: `'MyNewTool': tools.my_new_tool.render`

Each tool file exports a `render()` function (or `render(vault_path)` if `requires_vault_path=True`). Do **not** include `st.header` inside render — the app framework handles the title.

### React Tool Migration Pattern

When migrating a Streamlit tool to React:

1. **FastAPI service** — Add pure business logic to `api/services/text_tools_service.py` (or a new service file)
2. **FastAPI router** — Add POST endpoint(s) in `api/routers/text_tools.py` (or new router); include in `api/main.py`
3. **React component** — Create `web/src/tools/MyTool.tsx`; use `apiFetch()` from `web/src/api.ts` (base URL: `http://localhost:8000/api`)
4. **Register in React** — Import the component and add to `TOOL_COMPONENTS` map in `web/src/components/ToolPage.tsx`

Tools not yet in `TOOL_COMPONENTS` show a "React version coming soon" placeholder that links back to Streamlit on `:8501`.

### Key Shared Utilities

- **`tools/llm_utils.py`** — Shared AI/LLM helpers for Streamlit tools
- **`tools/tag_search_util.py`** — Obsidian tag search logic (YAML + body)
- **`tools/ui_tools_manager.py`** — `UIToolsManager` with fast metadata mode for CLI and API use
- **`web/src/api.ts`** — `apiFetch<T>()` wrapper used by all React tool components

### React Frontend Stack

- **Vite** + React 18 + TypeScript
- **TanStack Query** (`@tanstack/react-query`) for server state
- **React Router** for `/` (tool directory) and `/tool/:toolId` routes
- Routing: `Layout` → `ToolDirectory` or `ToolPage` (which resolves `toolId` to a component)
