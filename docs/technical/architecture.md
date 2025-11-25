# Codiak Architecture Documentation

## System Architecture Overview

Codiak follows a **modular, registry-based architecture** designed for scalability and maintainability. The application is built on Streamlit and uses a plugin-like system for tools.

## Architectural Layers

### 1. Presentation Layer

**Component:** `app.py`

**Responsibilities:**
- User interface rendering
- Navigation and routing
- Session state management
- Query parameter handling

**Key Design Decisions:**
- **Single Page Application**: All tools render in the same Streamlit app
- **URL-Based Routing**: Uses query parameters for deep linking
- **Category-Based Navigation**: Tools organized in sidebar by category
- **Dynamic Tool Loading**: Tools loaded on-demand based on selection

### 2. Tool Management Layer

**Components:**
- `tools/ui_tools_manager.py` - Tool discovery and access
- `tools/ui_tools_metadata.py` - Pure metadata definitions
- `tools/ui_tools_definitions.py` - Full tool definitions (optional)

**Responsibilities:**
- Tool discovery and registration
- Metadata management
- Fast vs. full mode switching
- Tool filtering and querying

**Design Pattern:** Registry Pattern

### 3. Tool Layer

**Component:** `tools/` directory

**Responsibilities:**
- Individual tool implementations
- Tool-specific business logic
- UI rendering for each tool

**Design Pattern:** Modular Tool Pattern

Each tool is:
- Self-contained
- Independent
- Follows consistent interface (`render()` function)
- Optionally requires vault path

### 4. Integration Layer

**Components:**
- API clients (YNAB, Home Assistant, SmartThings, AWS)
- LLM clients (`tools/llm_utils.py`)
- Database connections (SQLite for accounts)

**Responsibilities:**
- External API communication
- Data persistence
- AI/LLM interactions

## Data Flow

### Tool Selection Flow

```
User clicks tool in sidebar
    ↓
Query parameter updated: ?tool=ToolId
    ↓
app.py reads query parameter
    ↓
Looks up tool in TOOLS_METADATA
    ↓
Finds render function in RENDER_FUNC_MAP
    ↓
Calls render function (with vault_path if needed)
    ↓
Tool renders its UI
```

### Tool Discovery Flow

```
Application startup
    ↓
UIToolsManager initialized (fast_mode=True)
    ↓
Calls get_tools()
    ↓
Reads ui_tools_metadata.py (no imports)
    ↓
Returns list of tool dictionaries
    ↓
app.py groups by category
    ↓
Sidebar displays categories and tools
```

## Design Patterns

### 1. Registry Pattern

**Implementation:**
- Tools registered in `UI_TOOLS_METADATA` list
- Each tool has unique ID
- Metadata includes all display information

**Benefits:**
- Single source of truth
- Easy to add/remove tools
- No code changes needed in main app

### 2. Factory Pattern (Implicit)

**Implementation:**
- `RENDER_FUNC_MAP` maps tool IDs to render functions
- Render functions created on-demand

**Benefits:**
- Lazy loading
- Reduced memory usage
- Fast startup

### 3. Strategy Pattern

**Implementation:**
- Each tool implements `render()` function
- Different tools have different strategies
- Consistent interface

**Benefits:**
- Polymorphism
- Easy to swap implementations
- Testable

### 4. Facade Pattern

**Implementation:**
- `UIToolsManager` provides simple interface
- Hides complexity of tool discovery
- Abstracts fast vs. full mode

**Benefits:**
- Simplified API
- Encapsulation
- Easy to change implementation

## State Management

### Session State

**Usage:**
- Tool selection: `st.session_state.selected_tool_id`
- Success messages: `st.session_state.success_message`
- Tool-specific state: Tool modules manage their own state

**Pattern:**
```python
# Set state
st.session_state.selected_tool_id = tool_id

# Read state
selected_id = st.session_state.get('selected_tool_id')

# Clear state
if 'message' in st.session_state:
    del st.session_state['message']
```

### Query Parameters

**Usage:**
- Navigation: `?tool=ToolId`
- Deep linking: Direct URLs to tools
- Browser back/forward support

**Pattern:**
```python
# Read
query_params = st.query_params
tool_id = query_params.get_all('tool')[0] if 'tool' in query_params else None

# Write
st.query_params.update(tool=tool_id)
```

## Error Handling Strategy

### Levels of Error Handling

1. **API Level**: Try/except around API calls
2. **Tool Level**: Tool-specific error handling
3. **UI Level**: Streamlit error components

### Error Display Pattern

```python
try:
    result = api_call()
except NoCredentialsError:
    st.error("❌ **Credentials Missing**\n\nPlease configure your API credentials.")
    return
except ClientError as e:
    st.error(f"❌ **API Error**: {str(e)}")
    return
except Exception as e:
    st.error(f"❌ **Unexpected Error**: {str(e)}")
    st.exception(e)  # Show full traceback in expander
    return
```

## Performance Optimizations

### 1. Fast Metadata Mode

**Problem:** Importing all tools on startup is slow

**Solution:** Pure metadata file with no imports

**Impact:**
- Startup time: ~100ms vs. ~2-3s
- Memory: Minimal vs. Full tool instantiation

### 2. Lazy Loading

**Implementation:**
- Tools only imported when selected
- Render functions called on-demand

**Impact:**
- Reduced initial memory footprint
- Faster application startup

### 3. Caching

**Usage:**
- Streamlit's built-in caching for expensive operations
- Session state for API responses

**Example:**
```python
@st.cache_data
def expensive_operation():
    # Cached across reruns
    return result
```

## Security Considerations

### 1. API Keys

**Storage:**
- Environment variables (`.env` file)
- Never committed to git
- Loaded via `python-dotenv`

### 2. Vault Access

**Pattern:**
- User provides vault path
- Application validates path exists
- No hardcoded paths

### 3. AWS Credentials

**Pattern:**
- AWS profile: `codiak`
- User configures via AWS CLI
- No credentials in code

## Scalability Considerations

### Adding New Tools

**Steps:**
1. Create tool module
2. Add metadata entry
3. Add import
4. Map render function

**Impact:** No changes to core architecture

### Tool Categories

**Current:** 8 categories
**Scalability:** Unlimited categories supported

### Tool Count

**Current:** 36+ tools
**Scalability:** Architecture supports hundreds of tools

## Extension Points

### 1. Custom Tool Categories

Simply add new category name in tool metadata.

### 2. Tool Dependencies

Tools can import and use other tools if needed.

### 3. Shared Utilities

Common utilities in `tools/llm_utils.py` and similar files.

### 4. Plugin System (Future)

Potential for external tool plugins via:
- Plugin directory
- Dynamic loading
- Plugin registry

## Technology Stack

### Core
- **Streamlit 1.49.1**: Web framework
- **Python 3.x**: Language

### Data
- **Pandas**: Data manipulation
- **SQLite**: Local database

### APIs
- **YNAB SDK**: Financial API
- **Boto3**: AWS SDK
- **Requests/HTTPX**: HTTP clients

### AI/LLM
- **Anthropic SDK**: Claude API
- **OpenAI SDK**: GPT API
- **LangChain**: LLM framework

### UI
- **Streamlit Components**: Rich UI elements
- **Altair**: Visualizations

## Deployment Considerations

### Local Development
- Run via `streamlit run app.py`
- Uses local environment
- Access at `http://localhost:8501`

### Production Deployment
- Streamlit Cloud
- Docker container
- Cloud hosting (AWS, GCP, Azure)

### Environment Variables
- Required: API keys
- Optional: Vault path, AWS profile

## Monitoring and Logging

### Current State
- Print statements for tool access
- Streamlit error display
- No formal logging framework

### Future Enhancements
- Structured logging
- Error tracking
- Usage analytics
- Performance monitoring

## Testing Strategy

### Current State
- Manual testing
- No automated tests

### Recommended Approach
- Unit tests for tool functions
- Integration tests for API calls
- E2E tests for critical workflows
- Mock external services

## Documentation

### Current Documentation
- README.md: User-facing
- This file: Architecture
- Code comments: Inline documentation

### Future Enhancements
- API documentation
- Tool development guide
- Deployment guide
- Troubleshooting guide

---

*This architecture documentation is part of the Codiak project documentation suite.*

