# External Integrations Documentation

This document details all external services and APIs integrated into Codiak.

## Table of Contents

1. [YNAB (You Need A Budget)](#ynab-you-need-a-budget)
2. [Home Assistant](#home-assistant)
3. [SmartThings](#smartthings)
4. [AWS Services](#aws-services)
5. [LLM Services](#llm-services)
6. [MCP (Model Context Protocol)](#mcp-model-context-protocol)

---

## YNAB (You Need A Budget)

### Overview

YNAB is a personal budgeting application. Codiak integrates with the YNAB API to provide transaction management, categorization, and financial analysis tools.

### API Details

**Base URL:** `https://api.youneedabudget.com/v1`

**Authentication:**
- API Key required
- Set via `YNAB_API_KEY` environment variable
- Get from: https://app.youneedabudget.com/settings/developer

**Rate Limits:**
- 200 requests per hour per API key
- Tools implement caching to minimize API calls

### Integration Points

#### 1. Budget Management

**Tools:**
- `ynab_list_budgets.py` - List all budgets
- `ynab_list_categories.py` - List categories in a budget

**Key Functions:**
```python
from ynab import YNAB

configuration = YNAB(api_key=os.getenv('YNAB_API_KEY'))
budgets = configuration.budgets.get_budgets()
```

#### 2. Transaction Management

**Tools:**
- `ynab_get_transactions.py` - Fetch transactions
- `ynab_create_transaction.py` - Create new transactions
- `ynab_unknown_category_transactions.py` - Find uncategorized transactions

**Key Functions:**
```python
transactions = configuration.transactions.get_transactions(budget_id)
transaction = configuration.transactions.create_transaction(budget_id, transaction_data)
```

#### 3. Categorization System

**Tools:**
- `ynab_rules.py` - Manage categorization rules
- `ynab_apply_rules.py` - Apply rules to transactions
- `ynab_map_uncategorized.py` - AI-assisted categorization

**Rule Format:**
```json
{
  "payee": "Starbucks",
  "category_id": "category-uuid",
  "memo_contains": "coffee"
}
```

**Storage:**
- Rules stored in `ynab_categorizer_rules.json`
- Local SQLite database (`accounts.db`) for account management

#### 4. Data Visualization

**Tools:**
- `ynab_alluvial_diagram.py` - Money flow visualization
- `ynab_spend_graph.py` - Daily spend graphs
- `ynab_payee_manager.py` - Payee analysis

**Data Sources:**
- YNAB API for live data
- Local database for historical analysis

#### 5. Account Management

**Tools:**
- `account_dashboard.py` - Account overview
- `account_manager.py` - Account CRUD operations
- `account_link_manager.py` - Link local accounts to YNAB

**Database Schema:**
- SQLite database: `accounts.db`
- Tables: accounts, transactions, links

### Error Handling

```python
try:
    result = configuration.budgets.get_budgets()
except Exception as e:
    st.error(f"❌ **YNAB API Error**: {str(e)}")
    if "401" in str(e):
        st.error("Invalid API key. Please check your YNAB_API_KEY.")
    return
```

### Configuration

**Required:**
- `YNAB_API_KEY` environment variable

**Optional:**
- Budget selection via UI
- Local database path (defaults to `accounts.db`)

---

## Home Assistant

### Overview

Home Assistant is an open-source home automation platform. Codiak provides tools to interact with Home Assistant entities and control devices.

### API Details

**Base URL:** User-provided (e.g., `http://homeassistant.local:8123`)

**Authentication:**
- Long-lived access token
- Set via UI input or environment variable
- Generate from: Profile → Long-Lived Access Tokens

**API Endpoints:**
- `/api/states` - Get all entities
- `/api/services` - Call services
- `/api/events` - Event stream

### Integration Points

#### 1. Sensor Listing

**Tool:** `home_assistant_sensors.py`

**Functionality:**
- Lists all sensor entities
- Groups by domain
- Displays current state

**Implementation:**
```python
import requests

url = f"{ha_url}/api/states"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(url, headers=headers)
entities = response.json()
```

#### 2. Entity Dashboard

**Tool:** `home_assistant_dashboard.py`

**Functionality:**
- Groups entities by type
- Toggle lights and switches
- Display sensor values
- Control devices

**Implementation:**
```python
# Toggle entity
service_url = f"{ha_url}/api/services/{domain}/toggle"
data = {"entity_id": entity_id}
requests.post(service_url, headers=headers, json=data)
```

### Error Handling

```python
try:
    response = requests.get(url, headers=headers, timeout=5)
    response.raise_for_status()
except requests.exceptions.ConnectionError:
    st.error("❌ **Connection Error**: Cannot reach Home Assistant.")
except requests.exceptions.Timeout:
    st.error("❌ **Timeout**: Home Assistant did not respond.")
except requests.exceptions.HTTPError as e:
    st.error(f"❌ **HTTP Error**: {e.response.status_code}")
```

### Configuration

**Required:**
- Home Assistant URL (via UI or environment)
- Access token (via UI or environment)

**Optional:**
- Timeout settings
- SSL verification settings

---

## SmartThings

### Overview

SmartThings is Samsung's home automation platform. Codiak integrates to list and manage SmartThings devices.

### API Details

**Base URL:** `https://api.smartthings.com/v1`

**Authentication:**
- Personal Access Token
- Set via UI input or environment variable
- Generate from: https://account.smartthings.com/tokens

**API Endpoints:**
- `/devices` - List devices
- `/devices/{deviceId}` - Device details
- `/devices/{deviceId}/commands` - Send commands

### Integration Points

#### 1. Device Listing

**Tool:** `smartthings_list_devices.py`

**Functionality:**
- Lists all devices
- Shows device status
- Displays device capabilities

**Implementation:**
```python
import requests

url = "https://api.smartthings.com/v1/devices"
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(url, headers=headers)
devices = response.json()["items"]
```

#### 2. Device Dashboard

**Tool:** `smartthings_dashboard.py`

**Functionality:**
- Groups devices by type
- Displays device status
- Control devices (if supported)

### Error Handling

```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        st.error("❌ **Authentication Error**: Invalid SmartThings token.")
    else:
        st.error(f"❌ **API Error**: {e.response.status_code}")
```

### Configuration

**Required:**
- SmartThings Personal Access Token (via UI or environment)

---

## AWS Services

### Overview

Codiak integrates with AWS services for cloud resource management, specifically EC2 instances and cost monitoring.

### Authentication

**Method:** AWS Profile (`codiak`)

**Configuration:**
```bash
aws configure --profile codiak
```

**Pattern (from `.cursor-rules.yaml`):**
```python
session = boto3.Session(profile_name='codiak')
client = session.client('service_name')
```

### Integration Points

#### 1. EC2 Management

**Tool:** `aws_ec2_manager.py`

**Functionality:**
- List EC2 instances
- Start/stop instances
- View instance status
- Filter by region

**Implementation:**
```python
import boto3

session = boto3.Session(profile_name='codiak')
ec2 = session.client('ec2', region_name=region)

# List instances
instances = ec2.describe_instances()

# Start instance
ec2.start_instances(InstanceIds=[instance_id])

# Stop instance
ec2.stop_instances(InstanceIds=[instance_id])
```

**Error Handling:**
```python
try:
    instances = ec2.describe_instances()
except botocore.exceptions.NoCredentialsError:
    st.error("❌ **AWS Credentials Missing**: Please configure 'codiak' profile.")
except botocore.exceptions.ClientError as e:
    st.error(f"❌ **AWS Error**: {str(e)}")
```

#### 2. Cost Monitoring

**Tool:** `aws_cost_monitor.py`

**Functionality:**
- View costs by service
- View costs by region
- Date range filtering
- Cost trends

**Implementation:**
```python
import boto3

session = boto3.Session(profile_name='codiak')
ce = session.client('ce')  # Cost Explorer

response = ce.get_cost_and_usage(
    TimePeriod={
        'Start': start_date,
        'End': end_date
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    GroupBy=[
        {'Type': 'DIMENSION', 'Key': 'SERVICE'},
    ]
)
```

**Required Permissions:**
- `ec2:DescribeInstances`
- `ec2:StartInstances`
- `ec2:StopInstances`
- `ce:GetCostAndUsage`

### Configuration

**Required:**
- AWS profile `codiak` configured
- Appropriate IAM permissions

**Optional:**
- Region selection (defaults to us-east-1)

---

## LLM Services

### Overview

Codiak uses Large Language Models (LLMs) for AI-assisted features like transaction categorization and vault analysis.

### Supported Providers

#### 1. Anthropic (Claude)

**SDK:** `anthropic==0.64.0`

**Usage:**
- Transaction categorization
- Vault structure analysis
- Note placement recommendations

**Implementation:**
```python
from tools.llm_utils import LLMClient

client = LLMClient(provider='anthropic')
response = client.chat_completion(messages=[...])
```

#### 2. OpenAI (GPT)

**SDK:** `openai==1.102.0`

**Usage:**
- Alternative LLM provider
- Same interface as Anthropic

### Integration Points

#### 1. Transaction Categorization

**Tool:** `ynab_map_uncategorized.py`

**Functionality:**
- AI categorizes transactions that don't match rules
- Uses transaction details (payee, memo, amount)
- Suggests category based on context

**Prompt Structure:**
```
Given transaction: {payee}, {memo}, ${amount}
Categorize into one of these categories: {categories}
```

#### 2. Vault Analysis

**Tool:** `obsidian_vault_manager.py`

**Functionality:**
- Analyzes vault structure
- Provides organization recommendations
- Identifies patterns and issues

#### 3. Note Placement

**Tool:** `note_placement.py`

**Functionality:**
- Recommends folder for new note
- Analyzes existing structure
- Uses semantic understanding

### Configuration

**Required:**
- API key for chosen provider
- Set via environment variables:
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`

**Optional:**
- Model selection (defaults to latest)
- Temperature settings
- Max tokens

### Error Handling

```python
try:
    response = client.chat_completion(messages)
except Exception as e:
    st.error(f"❌ **LLM Error**: {str(e)}")
    # Fallback to manual categorization
```

---

## MCP (Model Context Protocol)

### Overview

MCP is a protocol for connecting AI assistants to external data sources and tools. Codiak includes an MCP client for interactive server communication.

### Integration Points

#### 1. MCP Client

**Tool:** `mcp_client_ui.py`

**Functionality:**
- Connect to MCP servers
- Discover available tools
- Execute tool calls
- Agent-based interactions

**Implementation:**
```python
from tools.mcp_client_tool import MCPClientTool

client = MCPClientTool(config_file_path="config.json")
client.connect()
tools = client.list_tools()
result = client.call_tool(tool_name, arguments)
```

### Configuration

**Required:**
- MCP server configuration in `config.json`
- Server URL and authentication

**Optional:**
- Custom system prompts
- Agent settings

---

## Common Integration Patterns

### 1. API Key Management

**Pattern:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY_NAME')
if not api_key:
    st.error("API key not configured")
    return
```

### 2. Error Handling

**Pattern:**
```python
try:
    response = api_call()
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        st.error("Authentication failed")
    elif e.response.status_code == 429:
        st.warning("Rate limit exceeded")
    else:
        st.error(f"API error: {e}")
except requests.exceptions.RequestException as e:
    st.error(f"Request failed: {e}")
```

### 3. Caching

**Pattern:**
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_data():
    return api_call()
```

### 4. Loading States

**Pattern:**
```python
with st.spinner("Loading data..."):
    data = fetch_data()
st.success("Data loaded!")
```

---

## Security Best Practices

### 1. API Keys

- Never commit API keys to git
- Use environment variables
- Rotate keys regularly

### 2. Credentials

- Use AWS profiles for AWS
- Use long-lived tokens for Home Assistant
- Store tokens securely

### 3. Network Security

- Use HTTPS for all API calls
- Validate SSL certificates
- Implement timeouts

### 4. Error Messages

- Don't expose sensitive data in errors
- Log errors securely
- Provide user-friendly messages

---

*This integrations documentation is part of the Codiak project documentation suite.*

