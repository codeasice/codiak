"""MCP tool wrapper for UI tools functionality."""
from typing import Optional, Dict
import logging

# Import tools with path handling for deployment compatibility
try:
    from tools.ui_tools_manager import UIToolsManager
except ImportError:
    import sys
    import os
    # Add the project root directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from tools.ui_tools_manager import UIToolsManager

logger = logging.getLogger(__name__)

async def list_ui_tools_mcp(
    category_filter: Optional[str] = None,
    tag_filter: Optional[str] = None,
    include_descriptions: bool = True
) -> Dict:
    """
    MCP tool wrapper for listing UI tools.

    Args:
        category_filter (str, optional): Filter tools by category
        tag_filter (str, optional): Filter tools by tag
        include_descriptions (bool): Whether to include full descriptions

    Returns:
        Dict: A dictionary containing the list of tools and metadata
    """
    manager = UIToolsManager(use_fast_mode=True)  # MCP always uses fast mode

    # Get tools
    tools = manager.get_tools()

    # Apply filters
    if category_filter or tag_filter:
        tools = manager.filter_tools(tools, category=category_filter, tag=tag_filter)

    # Remove descriptions if not wanted
    if not include_descriptions:
        for tool in tools:
            tool.pop('description', None)

    # Get summary
    summary = manager.get_tools_summary(tools)

    return {
        'tools': tools,
        'metadata': summary
    }