import os
import json
import streamlit as st
from typing import Dict, Tuple, Any
from . import llm_utils


class ObsidianVaultManager:
    """Tool for managing Obsidian vault structure with LLM-powered recommendations."""

    def __init__(self):
        self.vault_structure = None
        self.vault_path = None
        self.file_index = {}
        self.folder_index = {}

    def scan_vault_structure(self, vault_path: str, max_depth: int = 5) -> Dict[str, Any]:
        """Scan the Obsidian vault and build a comprehensive structure index."""
        if not os.path.isdir(vault_path):
            raise ValueError(f"Vault path '{vault_path}' does not exist.")

        structure = {
            "vault_path": vault_path,
            "folders": {},
            "files": {},
            "stats": {
                "total_files": 0,
                "total_folders": 0,
                "empty_folders": [],
                "deep_nesting": []
            }
        }

        # Walk through the vault directory
        for root, dirs, files in os.walk(vault_path):
            # Skip .obsidian and .trash directories
            dirs[:] = [d for d in dirs if d not in ('.obsidian', '.trash')]

            # Calculate relative path and depth
            rel_path = os.path.relpath(root, vault_path)
            depth = rel_path.count(os.sep) if rel_path != '.' else 0

            # Skip if too deep
            if depth > max_depth:
                continue

            # Process folders
            if rel_path != '.':
                folder_info = {
                    "name": os.path.basename(root),
                    "path": rel_path,
                    "depth": depth,
                    "parent": os.path.dirname(rel_path) if os.path.dirname(rel_path) != '.' else None,
                    "file_count": len(files),
                    "subfolder_count": len(dirs),
                    "is_empty": len(files) == 0 and len(dirs) == 0
                }
                structure["folders"][rel_path] = folder_info
                structure["stats"]["total_folders"] += 1

                if folder_info["is_empty"]:
                    structure["stats"]["empty_folders"].append(rel_path)

                if depth >= max_depth - 1 and len(dirs) > 0:
                    structure["stats"]["deep_nesting"].append(rel_path)

            # Process files
            for file in files:
                if file.endswith('.md'):  # Focus on markdown files
                    file_path = os.path.join(rel_path, file) if rel_path != '.' else file
                    file_info = {
                        "name": file,
                        "path": file_path,
                        "folder": rel_path if rel_path != '.' else None,
                        "depth": depth,
                        "size": os.path.getsize(os.path.join(root, file))
                    }
                    structure["files"][file_path] = file_info
                    structure["stats"]["total_files"] += 1

        self.vault_structure = structure
        self.vault_path = vault_path
        self._build_indexes()

        return structure

    def _build_indexes(self):
        """Build searchable indexes for files and folders."""
        if not self.vault_structure:
            return

        self.file_index = {}
        self.folder_index = {}

        # Build file index by name and content keywords
        for file_path, file_info in self.vault_structure["files"].items():
            name_lower = file_info["name"].lower()
            name_words = name_lower.replace('.md', '').replace('-', ' ').replace('_', ' ').split()

            for word in name_words:
                if word not in self.file_index:
                    self.file_index[word] = []
                self.file_index[word].append(file_path)

        # Build folder index
        for folder_path, folder_info in self.vault_structure["folders"].items():
            name_lower = folder_info["name"].lower()
            name_words = name_lower.replace('-', ' ').replace('_', ' ').split()

            for word in name_words:
                if word not in self.folder_index:
                    self.folder_index[word] = []
                self.folder_index[word].append(folder_path)

    def recommend_folder_for_note(self, note_name: str, model: str = "gpt-4o-mini") -> Tuple[str, str]:
        """Use LLM to recommend the best folder for a note with the given name."""
        if not self.vault_structure:
            return "", "No vault structure loaded. Please scan the vault first."

        # Build context about available folders
        folder_context = []
        for folder_path, folder_info in self.vault_structure["folders"].items():
            folder_context.append(f"- {folder_path} (depth: {folder_info['depth']}, files: {folder_info['file_count']})")

        folder_list = "\n".join(folder_context[:50])  # Limit to avoid token limits

        prompt = f"""You are an expert in knowledge management and Obsidian vault organization.

Given a note name and the current folder structure of an Obsidian vault, recommend the most appropriate folder for this note.

Note name: "{note_name}"

Current folder structure:
{folder_list}

Consider:
1. Semantic meaning and topic alignment
2. Existing folder naming patterns
3. Logical hierarchy and depth
4. Avoiding overcrowded folders
5. Future scalability

Provide your recommendation in this exact format:
RECOMMENDED_FOLDER: [folder path]
REASONING: [brief explanation of why this folder is most appropriate]

If no existing folder is suitable, suggest creating a new folder:
RECOMMENDED_FOLDER: [suggested new folder path]
REASONING: [explanation of why a new folder is needed and what it should be named]"""

        messages = [
            {"role": "system", "content": "You are a knowledge management expert specializing in Obsidian vault organization. Provide clear, actionable recommendations."},
            {"role": "user", "content": prompt}
        ]

        response, error = llm_utils.llm_client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=300,
            temperature=0.1,
            tool_name="ObsidianVaultManager",
            function_name="recommend_folder_for_note"
        )

        return response, error

    def recommend_notes_for_task(self, task_description: str, model: str = "gpt-4o-mini") -> Tuple[str, str]:
        """Use LLM to recommend existing notes that might be relevant for a specific task or information need."""
        if not self.vault_structure:
            return "", "No vault structure loaded. Please scan the vault first."

        # Build context about available notes
        note_context = []
        for file_path, file_info in self.vault_structure["files"].items():
            note_context.append(f"- {file_path} (in folder: {file_info['folder'] or 'root'})")

        note_list = "\n".join(note_context[:100])  # Limit to avoid token limits

        prompt = f"""You are an expert in knowledge management and information retrieval.

Given a task or information need and the current notes in an Obsidian vault, recommend the most relevant existing notes that could help with this task.

Task/Information need: "{task_description}"

Available notes in the vault:
{note_list}

Consider:
1. Direct relevance to the task
2. Potential connections and relationships
3. Reference materials that might be useful
4. Notes that could provide context or background

Provide your recommendations in this exact format:
RECOMMENDED_NOTES:
1. [note path] - [brief reason why this note is relevant]
2. [note path] - [brief reason why this note is relevant]
3. [note path] - [brief reason why this note is relevant]

If no existing notes are relevant, respond:
RECOMMENDED_NOTES: None found
REASONING: [explanation of why no existing notes match this task]"""

        messages = [
            {"role": "system", "content": "You are a knowledge management expert specializing in information retrieval and note organization. Provide precise, helpful recommendations."},
            {"role": "user", "content": prompt}
        ]

        response, error = llm_utils.llm_client.chat_completion(
            messages=messages,
            model=model,
            max_tokens=400,
            temperature=0.1,
            tool_name="ObsidianVaultManager",
            function_name="recommend_notes_for_task"
        )

        return response, error

    def get_vault_summary(self) -> str:
        """Get a summary of the vault structure."""
        if not self.vault_structure:
            return "No vault structure loaded."

        stats = self.vault_structure["stats"]
        return f"""Vault Summary:
- Total files: {stats['total_files']}
- Total folders: {stats['total_folders']}
- Empty folders: {len(stats['empty_folders'])}
- Deep nesting issues: {len(stats['deep_nesting'])}

Vault path: {self.vault_structure['vault_path']}"""


def render(vault_path_default: str = ""):
    """Render the Obsidian Vault Manager UI."""
    st.title("🗂️ Obsidian Vault Manager")
    st.write("Scan your Obsidian vault and get AI-powered recommendations for organizing notes and finding relevant information.")

    # Initialize session state
    if 'ovm_structure' not in st.session_state:
        st.session_state.ovm_structure = None
    if 'ovm_manager' not in st.session_state:
        st.session_state.ovm_manager = ObsidianVaultManager()

    manager = st.session_state.ovm_manager

    # Vault scanning section
    st.subheader("📁 Vault Structure Analysis")

    col1, col2 = st.columns([3, 1])
    with col1:
        vault_path = st.text_input("Obsidian Vault Path", value=vault_path_default)
    with col2:
        max_depth = st.number_input("Max Depth", min_value=1, max_value=10, value=5)

    scan_btn = st.button("🔍 Scan Vault Structure")

    if scan_btn:
        if not vault_path:
            st.error("Please enter a vault path.")
        else:
            with st.spinner("Scanning vault structure..."):
                try:
                    structure = manager.scan_vault_structure(vault_path, max_depth)
                    st.session_state.ovm_structure = structure
                    st.success(f"Successfully scanned vault! Found {structure['stats']['total_files']} files and {structure['stats']['total_folders']} folders.")
                except (ValueError, OSError) as e:
                    st.error(f"Error scanning vault: {str(e)}")

    # Display vault summary
    if st.session_state.ovm_structure:
        st.subheader("📊 Vault Summary")
        st.text(manager.get_vault_summary())

        # Show structure preview
        with st.expander("📋 Folder Structure Preview", expanded=False):
            folders = st.session_state.ovm_structure["folders"]
            if folders:
                for folder_path, folder_info in list(folders.items())[:20]:  # Show first 20 folders
                    st.write(f"📁 {folder_path} (files: {folder_info['file_count']}, depth: {folder_info['depth']})")
                if len(folders) > 20:
                    st.write(f"... and {len(folders) - 20} more folders")
            else:
                st.write("No folders found.")

    # LLM Configuration
    st.subheader("🤖 AI Recommendations")

    # Debug section
    with st.expander("🔧 Debug LLM Configuration", expanded=False):
        st.write(f"OpenAI Available: {llm_utils.OPENAI_AVAILABLE}")
        st.write(f"LLM Client Available: {llm_utils.llm_client.is_available()}")
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            st.write(f"API Key Found: {api_key[:10]}...{api_key[-4:]}")
        else:
            st.write("No API Key Found")

    col1, col2, col3 = st.columns(3)
    with col1:
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], index=0)
    with col2:
        st.slider("Max tokens", min_value=100, max_value=1000, value=400, step=50)
    with col3:
        st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.05)

    # Recommendation tabs
    if st.session_state.ovm_structure:
        tab1, tab2 = st.tabs(["📝 Recommend Folder for Note", "🔍 Find Notes for Task"])

        with tab1:
            st.write("Get AI recommendations for where to place a new note based on its name.")

            note_name = st.text_input("Note Name", placeholder="e.g., 'Project Planning Template', 'Meeting Notes - Q4 Planning'")
            recommend_folder_btn = st.button("🎯 Get Folder Recommendation")

            if recommend_folder_btn:
                if not note_name:
                    st.error("Please enter a note name.")
                elif not llm_utils.llm_client.is_available():
                    st.error("LLM not available or API key not configured. Set OPENAI_API_KEY.")
                else:
                    with st.spinner("Analyzing note name and vault structure..."):
                        response, error = manager.recommend_folder_for_note(note_name, model)

                        if error:
                            st.error(f"Error: {error}")
                        else:
                            st.markdown("**AI Recommendation:**")
                            st.code(response, language="text")

        with tab2:
            st.write("Find existing notes that might be relevant for a specific task or information need.")

            task_description = st.text_area("Task or Information Need",
                                        placeholder="e.g., 'I need to plan a software development project', 'Looking for information about budgeting'")
            find_notes_btn = st.button("🔍 Find Relevant Notes")

            if find_notes_btn:
                if not task_description:
                    st.error("Please enter a task description.")
                elif not llm_utils.llm_client.is_available():
                    st.error("LLM not available or API key not configured. Set OPENAI_API_KEY.")
                else:
                    with st.spinner("Searching for relevant notes..."):
                        response, error = manager.recommend_notes_for_task(task_description, model)

                        if error:
                            st.error(f"Error: {error}")
                        else:
                            st.markdown("**AI Recommendations:**")
                            st.code(response, language="text")

    else:
        st.info("Please scan your vault structure first to enable AI recommendations.")

    # Export functionality
    if st.session_state.ovm_structure:
        st.subheader("💾 Export Data")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Download Structure JSON",
                data=json.dumps(st.session_state.ovm_structure, indent=2),
                file_name="obsidian_vault_structure.json",
                mime="application/json"
            )

        with col2:
            if st.button("📋 Copy Summary"):
                st.code(manager.get_vault_summary())
                st.success("Summary copied to clipboard!")
