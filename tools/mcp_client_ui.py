import streamlit as st
import asyncio
import json
import os
import logging
from tools.mcp_client_tool import MCPClientTool, random_uuid
from langchain_core.messages import AIMessageChunk, ToolMessage

logger = logging.getLogger(__name__)

def get_streaming_callback(text_placeholder, tool_placeholder):
    accumulated_text = []
    accumulated_tool = []

    def callback_func(message: dict):
        nonlocal accumulated_text, accumulated_tool

        # This callback will receive the raw chunks from langgraph's astream
        # We need to parse them to extract text and tool calls.

        for key, value in message.items():
            if 'messages' in value:
                message_content = value['messages'][-1]

                if isinstance(message_content, AIMessageChunk):
                    content = message_content.content
                    if isinstance(content, str):
                        accumulated_text.append(content)
                        text_placeholder.markdown("".join(accumulated_text))

                    if message_content.tool_call_chunks:
                        for chunk in message_content.tool_call_chunks:
                            tool_info = f"Tool: {chunk['name']}\\nArgs: {chunk['args']}"
                            accumulated_tool.append(f"\\n```json\\n{tool_info}\\n```\\n")
                            with tool_placeholder.expander("🔧 Tool Call Information", expanded=True):
                                st.markdown("".join(accumulated_tool))

                elif isinstance(message_content, ToolMessage):
                    accumulated_tool.append(f"\\n```json\\n{str(message_content.content)}\\n```\\n")
                    with tool_placeholder.expander("🔧 Tool Call Information", expanded=True):
                        st.markdown("".join(accumulated_tool))

    return callback_func, accumulated_text, accumulated_tool


async def process_query_for_ui(query: str, text_placeholder, tool_placeholder, timeout_seconds: int = 60):
    mcp_tool = st.session_state.mcp_tool

    try:
        if mcp_tool.agent:
            streaming_callback, accumulated_text_obj, accumulated_tool_obj = get_streaming_callback(text_placeholder, tool_placeholder)

            # We are not using the returned response directly for final text,
            # as the callback handles the streaming display.
            # The final response from `run_query` will have the complete state.
            response = await mcp_tool.run_query(
                query,
                timeout_seconds=timeout_seconds,
                streaming_callback=streaming_callback
            )

            final_text = "".join(accumulated_text_obj)
            final_tool = "".join(accumulated_tool_obj)

            # Extract final message from response
            if response and 'agent' in response and 'messages' in response['agent']:
                 final_message = response['agent']['messages'][-1].content
                 text_placeholder.markdown(final_message)
                 final_text = final_message

            return response, final_text, final_tool
        else:
            msg = "🚫 Agent has not been initialized."
            return {"error": msg}, msg, ""
    except Exception as e:
        logger.error(f"Error occurred during query processing: {str(e)}")
        error_msg = f"❌ Error occurred during query processing: {str(e)}"
        return {"error": error_msg}, error_msg, ""

def render():
    """Main experiment logic."""
    if "mcp_tool" not in st.session_state:
        st.session_state.mcp_tool = MCPClientTool()

    mcp_tool = st.session_state.mcp_tool

    # Initialize session state
    if "mcp_session_initialized" not in st.session_state:
        st.session_state.mcp_session_initialized = False
        st.session_state.mcp_history = []
        st.session_state.mcp_timeout_seconds = 120
        st.session_state.mcp_selected_model = "claude-3-7-sonnet-latest"
        st.session_state.mcp_recursion_limit = 100

    if "mcp_thread_id" not in st.session_state:
        st.session_state.mcp_thread_id = mcp_tool.thread_id
    else:
        mcp_tool.thread_id = st.session_state.mcp_thread_id


    # Create and reuse global event loop
    if "event_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        st.session_state.event_loop = loop
        asyncio.set_event_loop(loop)

    with st.sidebar:
        st.subheader("⚙️ System Settings")

        available_models = list(mcp_tool.output_token_info.keys())

        previous_model = st.session_state.mcp_selected_model
        st.session_state.mcp_selected_model = st.selectbox(
            "🤖 Select model to use",
            options=available_models,
            index=(
                available_models.index(st.session_state.mcp_selected_model)
                if st.session_state.mcp_selected_model in available_models
                else 0
            ),
        )

        if (
            previous_model != st.session_state.mcp_selected_model
            and st.session_state.mcp_session_initialized
        ):
            st.warning(
                "⚠️ Model has been changed. Click 'Apply Settings' button to apply changes."
            )

        st.session_state.mcp_timeout_seconds = st.slider(
            "⏱️ Response generation time limit (seconds)",
            min_value=60,
            max_value=600,
            value=st.session_state.mcp_timeout_seconds,
            step=10,
        )

        st.session_state.mcp_recursion_limit = st.slider(
            "⏱️ Recursion call limit (count)",
            min_value=10,
            max_value=200,
            value=st.session_state.mcp_recursion_limit,
            step=10,
        )

        st.divider()

        st.subheader("🔧 Tool Settings")

        loaded_config = mcp_tool.load_config_from_json()

        if "pending_mcp_config" not in st.session_state:
            st.session_state.pending_mcp_config = loaded_config

        config_text = json.dumps(st.session_state.pending_mcp_config, indent=2, ensure_ascii=False)

        edited_config = st.text_area("MCP Server Config (JSON)", config_text, height=300)

        try:
            new_config = json.loads(edited_config)
            st.session_state.pending_mcp_config = new_config
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")


        if st.button(
            "Apply Settings",
            key="apply_button",
            type="primary",
            use_container_width=True,
        ):
            apply_status = st.empty()
            with apply_status.container():
                st.warning("🔄 Applying changes. Please wait...")

                mcp_tool.save_config_to_json(st.session_state.pending_mcp_config)

                success = st.session_state.event_loop.run_until_complete(
                    mcp_tool.initialize_agent(
                        mcp_config=st.session_state.pending_mcp_config,
                        model_name=st.session_state.mcp_selected_model,
                        recursion_limit=st.session_state.mcp_recursion_limit,
                    )
                )

                if success:
                    st.session_state.mcp_session_initialized = True
                    st.success("✅ New settings have been applied.")
                else:
                    st.error("❌ Failed to apply settings.")

            st.rerun()

        st.divider()

        if st.button("Reset Conversation", use_container_width=True, type="primary"):
            mcp_tool.reset_conversation()
            st.session_state.mcp_thread_id = mcp_tool.thread_id
            st.session_state.mcp_history = []
            st.success("✅ Conversation has been reset.")
            st.rerun()

    if not st.session_state.mcp_session_initialized:
        st.info(
            "MCP server and agent are not initialized. Configure settings and click 'Apply Settings' in the sidebar."
        )

    for message in st.session_state.mcp_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_query = st.chat_input("💬 Enter your question")
    if user_query:
        if st.session_state.mcp_session_initialized:
            st.session_state.mcp_history.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                tool_placeholder = st.empty()
                text_placeholder = st.empty()

                resp, final_text, final_tool = (
                    st.session_state.event_loop.run_until_complete(
                        process_query_for_ui(
                            user_query,
                            text_placeholder,
                            tool_placeholder,
                            st.session_state.mcp_timeout_seconds,
                        )
                    )
                )

            if "error" in resp:
                st.error(resp["error"])
            else:
                assistant_response = {"role": "assistant", "content": final_text}
                if final_tool:
                    assistant_response["content"] += f"\\n\\n**Tool Calls:**\\n{final_tool}"

                st.session_state.mcp_history.append(assistant_response)
                st.rerun()
        else:
            st.warning(
                "⚠️ MCP server and agent are not initialized. Please click the 'Apply Settings' button in the left sidebar to initialize."
            )