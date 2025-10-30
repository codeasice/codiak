import streamlit as st
import os
from typing import Optional, Tuple, Dict, Any
import json

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# LLM integration - you can replace this with your preferred LLM service
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class LLMClient:
    """Shared LLM client for use across multiple tools."""

    def __init__(self):
        self.client = None
        self.api_key = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the LLM client."""
        if not OPENAI_AVAILABLE:
            st.warning("OpenAI not available - install with 'pip install openai'")
            return

        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            st.warning("OpenAI API key not configured")
            return

        try:
            self.client = OpenAI(api_key=self.api_key)
        except Exception as e:
            st.error(f"Failed to initialize OpenAI client: {str(e)}")

    def is_available(self) -> bool:
        """Check if LLM is available and configured."""
        return OPENAI_AVAILABLE and self.client is not None and self.api_key is not None

    def _log_interaction(self, prompt: str, response: str, tool_name: str, function_name: str):
        """Log LLM interaction for debugging."""
        if 'llm_logs' not in st.session_state:
            st.session_state.llm_logs = []

        log_entry = {
            'tool': tool_name,
            'function': function_name,
            'prompt': prompt,
            'response': response,
            'timestamp': st.session_state.get('_timestamp', 'unknown')
        }

        st.session_state.llm_logs.append(log_entry)

        # Display in expander for debugging
        with st.expander(f"🤖 LLM Interaction: {function_name}", expanded=False):
            st.write("**Prompt:**")
            st.code(prompt, language="text")
            st.write("**Response:**")
            st.code(response, language="text")

    def chat_completion(self,
                       messages: list,
                       model: str = "gpt-3.5-turbo",
                       max_tokens: int = 100,
                       temperature: float = 0.1,
                       tool_name: str = "Unknown",
                       function_name: str = "chat_completion") -> Tuple[str, str]:
        """
        Make a chat completion request with logging.

        Returns:
            Tuple of (response_text, error_message)
        """
        if not self.is_available():
            return "", "LLM not available or not configured"

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            response_text = response.choices[0].message.content.strip()

            # Log the interaction
            prompt_text = json.dumps(messages, indent=2)
            self._log_interaction(prompt_text, response_text, tool_name, function_name)

            return response_text, ""

        except Exception as e:
            error_msg = f"LLM error: {str(e)}"
            self._log_interaction(json.dumps(messages, indent=2), error_msg, tool_name, function_name)
            return "", error_msg

# Global LLM client instance
llm_client = LLMClient()

def get_llm_suggestion(prompt: str,
                      tool_name: str = "Unknown",
                      function_name: str = "get_llm_suggestion",
                      model: str = "gpt-3.5-turbo",
                      max_tokens: int = 100,
                      temperature: float = 0.1) -> Tuple[str, str]:
    """
    Get LLM suggestion with logging.

    Args:
        prompt: The prompt to send to the LLM
        tool_name: Name of the tool making the request
        function_name: Name of the function making the request
        model: LLM model to use
        max_tokens: Maximum tokens for response
        temperature: Temperature for response generation

    Returns:
        Tuple of (response_text, error_message)
    """
    messages = [{"role": "user", "content": prompt}]
    return llm_client.chat_completion(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tool_name=tool_name,
        function_name=function_name
    )

def display_llm_logs():
    """Display all LLM interaction logs."""
    if 'llm_logs' not in st.session_state or not st.session_state.llm_logs:
        st.info("No LLM interactions logged yet.")
        return

    st.subheader("📋 LLM Interaction Logs")

    for i, log in enumerate(st.session_state.llm_logs):
        with st.expander(f"Interaction {i+1}: {log['tool']} - {log['function']}", expanded=False):
            st.write(f"**Tool:** {log['tool']}")
            st.write(f"**Function:** {log['function']}")
            st.write(f"**Timestamp:** {log['timestamp']}")

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Prompt:**")
                st.code(log['prompt'], language="text")
            with col2:
                st.write("**Response:**")
                st.code(log['response'], language="text")

def clear_llm_logs():
    """Clear all LLM interaction logs."""
    if 'llm_logs' in st.session_state:
        del st.session_state.llm_logs
        st.success("LLM logs cleared!")