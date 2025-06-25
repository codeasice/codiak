"""UI Tools Manager - handles tool discovery and access with multiple modes."""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class UIToolsManager:
    """Manages UI tools with multiple access modes."""

    def __init__(self, use_fast_mode: bool = True):
        """
        Initialize the UI Tools Manager.

        Args:
            use_fast_mode: If True, use metadata-only mode for fast access
        """
        self.use_fast_mode = use_fast_mode
        self._tools_cache = None

    def get_tools(self, aipman_instance=None) -> List[Dict[str, Any]]:
        """
        Get tools list based on the configured mode.

        Args:
            aipman_instance: Optional AI Procurement Manager instance (needed for full mode)

        Returns:
            List of tool dictionaries
        """
        if self.use_fast_mode:
            return self._get_tools_fast()
        else:
            return self._get_tools_full(aipman_instance)

    def _get_tools_fast(self) -> List[Dict[str, Any]]:
        """
        Get tools metadata without instantiation (fast mode).
        Uses the metadata file as single source of truth.
        """
        try:
            from tools.ui_tools_metadata import get_tools_metadata_fast
            return get_tools_metadata_fast()
        except ImportError as e:
            logger.warning(f"Could not import metadata tools: {e}")
            return []

    def _get_tools_full(self, aipman_instance) -> List[Dict[str, Any]]:
        """
        Get fully instantiated tools (full mode).
        Requires AI Procurement Manager instance.
        """
        if aipman_instance is None:
            logger.error("AI Procurement Manager instance required for full mode")
            return self._get_tools_fast()  # Fallback to fast mode

        try:
            from tools.ui_tools_definitions import instantiate_tools
            return instantiate_tools(aipman_instance)
        except Exception as e:
            logger.warning(f"Could not get full tools, falling back to fast mode: {e}")
            return self._get_tools_fast()

    def filter_tools(self, tools: List[Dict[str, Any]],
                    category: Optional[str] = None,
                    tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Filter tools by category and/or tag.

        Args:
            tools: List of tool dictionaries
            category: Optional category to filter by
            tag: Optional tag to filter by

        Returns:
            Filtered list of tools
        """
        filtered_tools = tools

        if category:
            filtered_tools = [
                tool for tool in filtered_tools
                if tool.get("category", "").lower() == category.lower()
            ]

        if tag:
            filtered_tools = [
                tool for tool in filtered_tools
                if tag.lower() in [t.lower() for t in tool.get("tags", [])]
            ]

        return filtered_tools

    def get_tools_summary(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary statistics about the tools.

        Args:
            tools: List of tool dictionaries

        Returns:
            Dictionary with summary statistics
        """
        if not tools:
            return {"total_tools": 0, "categories": {}, "tags": {}}

        categories = {}
        tags = {}

        for tool in tools:
            # Count categories
            category = tool.get("category", "Unknown")
            categories[category] = categories.get(category, 0) + 1

            # Count tags
            for tag in tool.get("tags", []):
                tags[tag] = tags.get(tag, 0) + 1

        return {
            "total_tools": len(tools),
            "categories": categories,
            "tags": tags,
            "most_common_category": max(categories.keys(), key=categories.get) if categories else None,
            "most_common_tag": max(tags.keys(), key=tags.get) if tags else None
        }