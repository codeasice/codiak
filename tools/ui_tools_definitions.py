"""UI Tools definitions generated from metadata - single source of truth approach."""

import importlib
from typing import Dict, Any, List

# Import metadata as the single source of truth
from tools.ui_tools_metadata import UI_TOOLS_METADATA

# Tool ID to (class_name, module_path) mapping - only used for full instantiation
TOOL_CLASS_MAP = {
    "DiagnosticsExperiment": ("DiagnosticsExperiment", "aipman.experiments.diagnostics_experiment"),
    "MCPClient": ("MCPClientExperiment", "aipman.experiments.mcp_client"),
    "BasicPrompt": ("PromptModule", "aipman.experiments.basic_prompt"),
    "JsonCsvConverter": ("JsonCsvConverter", "aipman.experiments.json_csv_converter"),
    "JsonSchemaDetector": ("JsonSchemaDetector", "aipman.experiments.json_schema_detector"),
    "MarkdownToCanvas": ("MarkdownToCanvas", "aipman.experiments.markdown_to_canvas"),
    "IndexCreator": ("IndexCreator", "aipman.experiments.index_creator"),
    "IndexPopulator": ("IndexPopulator", "aipman.experiments.index_populator"),
    "S3FileSummarizer": ("S3FileSummarizer", "aipman.experiments.s3_file_summarizer"),
    "S3FileUploader": ("S3FileUploader", "aipman.experiments.s3_file_uploader"),
    "SupplierTool": ("PromptModule", "aipman.experiments.basic_prompt"),
    "SpreadsheetAnalysis": ("SpreadsheetAnalysis", "aipman.experiments.spreadsheet_analysis"),
    "ClusterAnalysis": ("ClusterAnalysis", "aipman.experiments.cluster_analysis"),
    "FilePromptExecutor": ("FilePromptExecutor", "aipman.experiments.file_prompt_executor"),
    "RCAReportGenerator": ("RCAReportGenerator", "aipman.experiments.rca_report_helper"),
    "PowerPointAnalysis": ("PowerPointAnalysis", "aipman.experiments.powerpoint_analysis"),
    "DevCycleTicketAnalyzer": ("DevCycleTicketAnalyzer", "aipman.experiments.dev_cycle_ticket_analyzer"),
    "CsvSqlAnalyzer": ("CsvSqlAnalyzer", "aipman.experiments.csv_sql_analyzer"),
    "SupplierJsonToCsv": ("SupplierJsonToCsv", "aipman.experiments.supplier_json_to_csv"),
    "JiraTicketAnalyzer": ("JiraTicketAnalyzer", "aipman.experiments.jira_ticket_analyzer"),
    "GitCommitsAnalyzer": ("GitCommitsAnalyzer", "aipman.experiments.git_commits_analyzer"),
    "GitReposAnalyzer": ("GitReposAnalyzer", "aipman.experiments.git_repos_analyzer"),
    "BulkWinProbabilityAnalysis": ("BulkWinProbabilityAnalysis", "aipman.experiments.bulk_win_probability_analysis"),
    "VendorProfileGeneration": ("VendorProfileGeneration", "aipman.experiments.vendor_profile_generation"),
    "BedrockAgent": ("BedrockAgent", "aipman.experiments.bedrock_agent"),
    "spreadsheet_module": ("PromptModule", "aipman.experiments.basic_prompt"),
    "ListDifferenceVisualizer": ("ListDifferenceVisualizer", "aipman.experiments.list_difference_visualizer"),
    "PiiStripper": ("PiiStripper", "aipman.experiments.pii_stripper"),
    "severity_ticket_analyzer": ("SeverityTicketAnalyzer", "aipman.experiments.severity_ticket_analyzer"),
    "TicketTableAnalyzer": ("TicketTableAnalyzer", "aipman.experiments.ticket_table_analyzer"),
    "ElasticsearchQueryExecutor": ("ElasticsearchQueryExecutor", "aipman.experiments.elasticsearch_query_executor"),
    "confluence_explorer": ("ConfluenceContentExplorer", "aipman.experiments.confluence_content_explorer"),
    "confluence_creator": ("ConfluencePageCreator", "aipman.experiments.confluence_page_creator"),
    "confluence_space_analyzer": ("ConfluenceSpaceAnalyzer", "aipman.experiments.confluence_space_analyzer"),
    "confluence_page_placer": ("ConfluencePagePlacer", "aipman.experiments.confluence_page_placer"),
    "KnowledgeBaseNavigator": ("KnowledgeBaseNavigator", "aipman.experiments.knowledge_base_navigator"),
    "ContractMetatagExtraction": ("ContractMetatagExtraction", "aipman.experiments.contract_metatag_extraction"),
    "RCAForm": ("RCAForm", "aipman.experiments.rca_form"),
    "executive_summary_combined": ("ExecutiveSummaryCombined", "aipman.experiments.executive_summary_combined"),
    "TavilySearch": ("TavilySearch", "aipman.experiments.tavily_search"),
    "JiraTicketHierarchyAnalyzer": ("JiraTicketHierarchyAnalyzer", "aipman.experiments.jira_ticket_hierarchy_analyzer"),
    "ImageAnalyzer": ("ImageAnalyzer", "aipman.experiments.image_analyzer"),
    "EmbeddingGenerator": ("EmbeddingGenerator", "aipman.experiments.embedding_generator"),
    "ProjectManager": ("ProjectManager", "aipman.experiments.project_manager"),
    "ElasticVectorUpdater": ("ElasticVectorUpdater", "aipman.experiments.elastic_vector_updater"),
    "IndexMappingViewer": ("IndexMappingViewer", "aipman.experiments.index_mapping_viewer"),
    "EsKnnQuery": ("EsKnnQuery", "aipman.experiments.es_knn_query"),
    "AIExam": ("AIExam", "aipman.experiments.ai_exam"),
    "JiraFieldInspector": ("JiraFieldInspector", "aipman.experiments.jira_field_inspector"),
    "JiraTeamPerformanceTracker": ("JiraTeamPerformanceTracker", "aipman.experiments.jira_team_performance_tracker"),
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