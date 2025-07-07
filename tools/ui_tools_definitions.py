"""UI Tools definitions generated from metadata - single source of truth approach."""

import importlib
from typing import Dict, Any, List

# Import metadata as the single source of truth
from tools.ui_tools_metadata import UI_TOOLS_METADATA

# Tool ID to (class_name, module_path) mapping - only used for full instantiation
TOOL_CLASS_MAP = {
    "FastProjectCounter": ("FastProjectCounter", "aipman.experiments.fast_project_counter")
}

def get_tool_definitions():
    """Get tool definitions from metadata (legacy compatibility)."""
    return UI_TOOLS_METADATA

def get_tool_metadata_only():
    """Get tool metadata without class instantiation."""
    return UI_TOOLS_METADATA

def instantiate_tools(aipman_instance):
    """
    Instantiate all tools for the AI Procurement Manager.
    Uses metadata as single source of truth with dynamic class loading.

    Args:
        aipman_instance: The AIProcurementManager instance to pass to tools

    Returns:
        List: List of tool dictionaries with instantiated classes
    """
    instantiated_tools = []

    # Import constants only when needed for instantiation
    try:
        from aipman.constants import DEFAULT_SUPPLIER_TOOL_TEMPLATE, DEFAULT_VENDOR_PROFILE, DEFAULT_SOLICITATION
    except ImportError:
        DEFAULT_SUPPLIER_TOOL_TEMPLATE = ""
        DEFAULT_VENDOR_PROFILE = ""
        DEFAULT_SOLICITATION = ""

    for tool_meta in UI_TOOLS_METADATA:
        tool_id = tool_meta["id"]

        if tool_id not in TOOL_CLASS_MAP:
            print(f"Warning: No class mapping for {tool_id}")
            continue

        class_name, module_path = TOOL_CLASS_MAP[tool_id]

        try:
            # Dynamic import - only happens when actually needed
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)

            # Determine init args based on tool type
            if tool_id == "BasicPrompt":
                init_args = {"aipman": aipman_instance, "default_prompt": "What is the capital of France?"}
            elif tool_id == "SupplierTool":
                init_args = {"aipman": aipman_instance, "default_prompt": DEFAULT_SUPPLIER_TOOL_TEMPLATE}
            elif tool_id == "spreadsheet_module":
                init_args = {"aipman": aipman_instance, "default_prompt": "Analyze the spreadsheet and provide insights."}
            else:
                init_args = {"aipman": aipman_instance}

            # Create instance
            instance = tool_class(**init_args)

            # Handle post-initialization methods (like add_variable for PromptModule)
            if tool_id == "SupplierTool":
                # Add variables for supplier tool
                instance.add_variable("Vendor Profile", DEFAULT_VENDOR_PROFILE)
                instance.add_variable("Solicitation", DEFAULT_SOLICITATION)
            elif tool_id == "spreadsheet_module":
                # Add variables for spreadsheet module
                instance.add_variable("Spreadsheet Analysis Context", "")

            # Create tool definition with metadata + instance
            tool_def = tool_meta.copy()
            tool_def["instance"] = instance
            instantiated_tools.append(tool_def)

        except Exception as e:
            print(f"Warning: Could not instantiate {tool_id}: {e}")
            continue

    return instantiated_tools