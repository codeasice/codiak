"""
Router: text-transform tool endpoints.
All endpoints are stateless POST requests — input in, result out.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api.services.text_tools_service import (
    html_to_markdown,
    strip_markdown,
    inject_color_swatches,
    list_to_table,
    join_tables,
    convert_markdown_table,
    convert_excel_to_markdown,
    items_to_links,
    items_to_links_bold_only,
    links_to_items,
    categorize_home_automation,
)
from api.services.obsidian_service import recommend_note_placement
from api.services.bmad_service import analyze_bmad_project

router = APIRouter()


# ---------------------------------------------------------------------------
# HtmlToMarkdown
# ---------------------------------------------------------------------------

class HtmlToMarkdownRequest(BaseModel):
    html: str


@router.post("/html-to-markdown")
def html_to_markdown_endpoint(req: HtmlToMarkdownRequest):
    try:
        result = html_to_markdown(req.html)
        return {"result": result}
    except ImportError:
        raise HTTPException(status_code=500, detail="markdownify package not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# MarkdownStripper
# ---------------------------------------------------------------------------

class MarkdownStripperRequest(BaseModel):
    text: str
    options: Dict[str, bool] = {
        "h1": True, "h2": True, "h3": True, "bullets": True,
        "checkboxes": True, "bold": True, "italic": True,
        "inline_code": True, "code_block": True, "blockquote": True,
        "hr": True, "table": False,
    }


@router.post("/markdown-stripper")
def markdown_stripper_endpoint(req: MarkdownStripperRequest):
    result = strip_markdown(req.text, req.options)
    return {"result": result}


# ---------------------------------------------------------------------------
# ColorSwatchInjector
# ---------------------------------------------------------------------------

class ColorSwatchRequest(BaseModel):
    markdown: str


@router.post("/color-swatch-injector")
def color_swatch_endpoint(req: ColorSwatchRequest):
    return inject_color_swatches(req.markdown)


# ---------------------------------------------------------------------------
# TableCreator
# ---------------------------------------------------------------------------

class ListToTableRequest(BaseModel):
    input_text: str
    delimiter: Optional[str] = None
    force_single_column: bool = False


class JoinTablesRequest(BaseModel):
    table1: str
    table2: str
    how: str = "append"  # "append" or "align"


@router.post("/table-creator/from-list")
def list_to_table_endpoint(req: ListToTableRequest):
    result = list_to_table(req.input_text, req.delimiter, req.force_single_column)
    if not result:
        raise HTTPException(status_code=400, detail="No items to convert")
    return {"result": result}


@router.post("/table-creator/join")
def join_tables_endpoint(req: JoinTablesRequest):
    result = join_tables(req.table1, req.table2, req.how)
    return {"result": result}


# ---------------------------------------------------------------------------
# MarkdownTableConverter
# ---------------------------------------------------------------------------

class MarkdownTableRequest(BaseModel):
    markdown: str


class ExcelToMarkdownRequest(BaseModel):
    excel_text: str


@router.post("/markdown-table-converter/from-markdown")
def convert_markdown_endpoint(req: MarkdownTableRequest):
    result = convert_markdown_table(req.markdown)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/markdown-table-converter/from-excel")
def convert_excel_endpoint(req: ExcelToMarkdownRequest):
    result = convert_excel_to_markdown(req.excel_text)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# ItemsToLinks
# ---------------------------------------------------------------------------

class ItemsToLinksRequest(BaseModel):
    text: str
    exclude_numbers: bool = False
    bold_only: bool = False


class LinksToItemsRequest(BaseModel):
    text: str


@router.post("/items-to-links")
def items_to_links_endpoint(req: ItemsToLinksRequest):
    if req.bold_only:
        result = items_to_links_bold_only(req.text, req.exclude_numbers)
    else:
        result = items_to_links(req.text, req.exclude_numbers)
    return {"result": result}


@router.post("/links-to-items")
def links_to_items_endpoint(req: LinksToItemsRequest):
    result = links_to_items(req.text)
    return {"result": result}


# ---------------------------------------------------------------------------
# HomeAutomationCategorizer
# ---------------------------------------------------------------------------

class HomeAutomationRequest(BaseModel):
    items_text: str


@router.post("/home-automation-categorizer")
def home_automation_categorizer_endpoint(req: HomeAutomationRequest):
    return categorize_home_automation(req.items_text)


# ---------------------------------------------------------------------------
# ObsidianNotePlacement
# ---------------------------------------------------------------------------

class ObsidianNotePlacementRequest(BaseModel):
    vault_path: str
    page_name: str
    page_description: str = ""
    depth: int = 3
    parent_note_query: str = ""
    model: str = "gpt-4o"
    max_tokens: int = 500
    temperature: float = 0.2


@router.post("/obsidian-note-placement")
def obsidian_note_placement_endpoint(req: ObsidianNotePlacementRequest):
    result = recommend_note_placement(
        vault_path=req.vault_path,
        page_name=req.page_name,
        page_description=req.page_description,
        depth=req.depth,
        parent_note_query=req.parent_note_query,
        model=req.model,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )
    if "error" in result and "tree_preview" not in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ---------------------------------------------------------------------------
# BmadProjectStatus
# ---------------------------------------------------------------------------

class BmadProjectStatusRequest(BaseModel):
    project_path: str


class ListSubdirsRequest(BaseModel):
    folder_path: str


@router.post("/list-subdirs")
def list_subdirs_endpoint(req: ListSubdirsRequest):
    import os
    path = req.folder_path
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Not a valid directory: {path}")
    try:
        entries = sorted(
            e for e in os.listdir(path)
            if os.path.isdir(os.path.join(path, e)) and not e.startswith(".")
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"subdirs": entries}


@router.post("/scan-bmad-projects")
def scan_bmad_projects_endpoint(req: ListSubdirsRequest):
    """Scan a folder and return only subdirectories that contain a BMAD project."""
    import os
    path = req.folder_path
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail=f"Not a valid directory: {path}")
    bmad_markers = (".bmad", "bmad", "_bmad")
    projects = []
    try:
        for entry in sorted(os.listdir(path)):
            full = os.path.join(path, entry)
            if not os.path.isdir(full) or entry.startswith("."):
                continue
            for marker in bmad_markers:
                if os.path.isdir(os.path.join(full, marker)):
                    projects.append(entry)
                    break
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"projects": projects}


@router.post("/bmad-project-status")
def bmad_project_status_endpoint(req: BmadProjectStatusRequest):
    return analyze_bmad_project(req.project_path)
