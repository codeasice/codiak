# Codiak Developer Guide

Quick reference guide for developers working on Codiak.

## Quick Start

### Adding a New Tool

1. **Create tool file** (`tools/my_tool.py`):
```python
import streamlit as st

def render(vault_path: str = ""):
    """Main render function."""
    st.title("My Tool")
    st.write("Tool description")
    # Your implementation here
```

2. **Add to metadata** (`tools/ui_tools_metadata.py`):
```python
{
    "id": "MyTool",
    "short_title": "My Tool",
    "long_title": "My New Tool",
    "category": "Category Name",
    "description": "What this tool does",
    "requires_vault_path": False  # True if needs Obsidian vault
}
```

3. **Add import** (`tools/__init__.py`):
```python
from . import my_tool
```

4. **Map render function** (`app.py`):
```python
RENDER_FUNC_MAP = {
    # ... existing tools
    'MyTool': tools.my_tool.render,
}
```

### Tool Categories

Available categories:
- `MCP`
- `Note Taking`
- `Obsidian`
- `Financial/YNAB`
- `Home Automation`
- `AWS`
- `Network Analysis`
- `Game Development`

Or create a new category by using it in metadata.

## Code Patterns

### Standard Tool Structure

```python
import streamlit as st
import os

def render(vault_path: str = ""):
    """Main render function for the tool."""
    st.title("Tool Title")
    st.write("Tool description")
    
    # Check prerequisites
    if not os.getenv('REQUIRED_API_KEY'):
        st.error("❌ **API Key Missing**")
        st.markdown("Please set REQUIRED_API_KEY in your .env file.")
        return
    
    # Tool implementation
    try:
        # Your code here
        result = do_something()
        st.success("✅ Operation completed!")
    except Exception as e:
        st.error(f"❌ **Error**: {str(e)}")
```

### API Integration Pattern

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def render():
    api_key = os.getenv('API_KEY')
    if not api_key:
        st.error("API key not configured")
        return
    
    try:
        response = requests.get(
            "https://api.example.com/endpoint",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        # Process data
    except requests.exceptions.HTTPError as e:
        st.error(f"API Error: {e.response.status_code}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
```

### Vault Path Pattern

```python
def render(vault_path: str = ""):
    if not vault_path:
        st.error("Vault path not provided")
        return
    
    if not os.path.exists(vault_path):
        st.error(f"Vault path does not exist: {vault_path}")
        return
    
    # Use vault_path
    note_files = find_notes(vault_path)
```

### AWS Integration Pattern

```python
import boto3
import botocore.exceptions

def render():
    try:
        session = boto3.Session(profile_name='codiak')
        client = session.client('ec2')
        # Use client
    except botocore.exceptions.NoCredentialsError:
        st.error("❌ **AWS Credentials Missing**")
        st.markdown("Please configure: `aws configure --profile codiak`")
        return
    except botocore.exceptions.ClientError as e:
        st.error(f"❌ **AWS Error**: {str(e)}")
        return
```

### LLM Integration Pattern

```python
from tools.llm_utils import LLMClient

def render():
    client = LLMClient(provider='anthropic')  # or 'openai'
    
    try:
        response = client.chat_completion(
            messages=[
                {"role": "user", "content": "Your prompt here"}
            ]
        )
        result = response['content']
        st.write(result)
    except Exception as e:
        st.error(f"❌ **LLM Error**: {str(e)}")
```

### Caching Pattern

```python
import streamlit as st

@st.cache_data(ttl=300)  # Cache for 5 minutes
def expensive_operation(param):
    # Expensive computation or API call
    return result

def render():
    result = expensive_operation(param)
    st.write(result)
```

### Session State Pattern

```python
import streamlit as st

def render():
    # Initialize state
    if 'my_state' not in st.session_state:
        st.session_state.my_state = []
    
    # Use state
    if st.button("Add Item"):
        st.session_state.my_state.append("item")
    
    # Display state
    st.write(st.session_state.my_state)
    
    # Clear state
    if st.button("Clear"):
        del st.session_state.my_state
```

## File Structure

```
tools/
├── __init__.py              # Tool imports
├── ui_tools_manager.py      # Tool management
├── ui_tools_metadata.py     # Tool metadata
├── llm_utils.py            # LLM client
└── [tool_name].py          # Individual tools
```

## Environment Variables

Common environment variables:

```env
# Obsidian
OB_VAULT_PATH=C:\Users\Name\Documents\ObsidianVault

# YNAB
YNAB_API_KEY=your_ynab_api_key

# LLM
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Home Assistant (optional)
HA_URL=http://homeassistant.local:8123
HA_TOKEN=your_token

# SmartThings (optional)
ST_TOKEN=your_token
```

## Testing

### Manual Testing Checklist

- [ ] Tool appears in sidebar
- [ ] Tool renders correctly
- [ ] Error handling works
- [ ] API integrations function
- [ ] Vault path handling (if applicable)
- [ ] Session state persists correctly

### Testing API Integrations

1. Test with valid credentials
2. Test with invalid credentials
3. Test with missing credentials
4. Test network errors
5. Test rate limiting

## Debugging

### Common Issues

**Tool not appearing:**
- Check metadata registration
- Check import in `__init__.py`
- Check render function mapping

**Import errors:**
- Verify all dependencies in `requirements.txt`
- Check virtual environment activated
- Verify Python version

**API errors:**
- Check environment variables
- Verify API keys are valid
- Check network connectivity
- Review API rate limits

### Debugging Tips

1. **Use print statements:**
```python
print(f"Debug: {variable}")
```

2. **Use Streamlit debug:**
```python
st.write("Debug info:", variable)
```

3. **Check logs:**
- Streamlit logs in terminal
- Browser console for frontend issues

## Code Style

### Python Style

- Follow PEP 8
- Max line length: 100 characters
- Use type hints where appropriate
- Document functions with docstrings

### Streamlit Best Practices

- Use `st.set_page_config()` at top (in app.py)
- Group related UI elements
- Use columns for layout
- Provide loading states
- Show clear error messages

### Naming Conventions

- Tool files: `snake_case.py`
- Tool IDs: `PascalCase`
- Functions: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`

## Performance Tips

1. **Use caching:**
   - `@st.cache_data` for data
   - `@st.cache_resource` for resources

2. **Lazy loading:**
   - Only import when needed
   - Load data on demand

3. **Optimize API calls:**
   - Cache responses
   - Batch requests when possible
   - Use pagination for large datasets

## Security Best Practices

1. **Never commit:**
   - API keys
   - Credentials
   - `.env` files
   - Personal data

2. **Validate input:**
   - Check file paths exist
   - Validate API responses
   - Sanitize user input

3. **Error messages:**
   - Don't expose sensitive data
   - Provide helpful but safe messages

## Git Workflow

### Before Committing

- [ ] Code follows style guide
- [ ] No API keys or secrets
- [ ] Tool tested and working
- [ ] Documentation updated (if needed)

### Commit Messages

Use clear, descriptive messages:
```
Add new YNAB transaction analyzer tool
Fix vault path validation in tag search
Update Home Assistant dashboard UI
```

## Resources

- **Streamlit Docs:** https://docs.streamlit.io/
- **YNAB API:** https://api.youneedabudget.com/
- **AWS Boto3:** https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- **Anthropic API:** https://docs.anthropic.com/
- **OpenAI API:** https://platform.openai.com/docs/

## Getting Help

1. Check existing tools for examples
2. Review architecture documentation
3. Check integration documentation
4. Review code comments
5. Test in isolation

---

*This developer guide is part of the Codiak project documentation suite.*

