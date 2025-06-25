import os
from typing import Dict, List
from tools.tag_search_util import find_notes_with_tags

async def search_tags_mcp(input_dict: Dict) -> Dict:
    """
    MCP tool for searching notes by tags.
    Input: {"tags": [..], "vault_path": ...}
    Output: {"results": [{"title": ..., "path": ...}, ...]}
    """
    tags = input_dict.get("tags", [])
    vault_path = input_dict.get("vault_path")
    if not tags or not vault_path or not os.path.isdir(vault_path):
        return {"results": []}
    results = find_notes_with_tags(vault_path, tags)
    return {"results": results}