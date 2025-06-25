import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv("local.env")

logger = logging.getLogger(__name__)


def random_uuid():
    return str(uuid.uuid4())


async def astream_and_get_final_response(agent, astream_input, callback=None, config=None):
    final_response = None
    async for chunk in agent.astream(astream_input, config=config):
        if callback:
            # The original callback expected a dict with 'content'
            # The chunk from astream is a dict with node names as keys.
            # We'll pass the whole chunk.
            callback(chunk)
        final_response = chunk
    return final_response


class MCPClientTool:
    def __init__(self, config_file_path="config.json", system_prompt=None):
        self.config_file_path = config_file_path
        self.output_token_info = {
            "claude-3-5-sonnet-latest": {"max_tokens": 8192},
            "claude-3-5-haiku-latest": {"max_tokens": 8192},
            "claude-3-7-sonnet-latest": {"max_tokens": 64000},
            "gpt-4o": {"max_tokens": 16000},
            "gpt-4o-mini": {"max_tokens": 16000},
            "anthropic.claude-3-sonnet-20240229-v1:0": {"max_tokens": 64000},
            "anthropic.claude-3-haiku-20240307-v1:0": {"max_tokens": 8192},
            "anthropic.claude-3-5-sonnet-20240620-v1:0": {"max_tokens": 64000},
            "us.anthropic.claude-3-7-sonnet-20250219-v1:0": {"max_tokens": 64000},
        }
        self.system_prompt = (
            system_prompt
            if system_prompt
            else """<ROLE>
You are a smart agent with an ability to use tools.
You will be given a question and you will use the tools to answer the question.
Pick the most relevant tool to answer the question.
If you are failed to answer the question, try different tools to get context.
Your answer should be very polite and professional.
</ROLE>

----

<INSTRUCTIONS>
Step 1: Analyze the question
- Analyze user's question and final goal.
- If the user's question is consist of multiple sub-questions, split them into smaller sub-questions.

Step 2: Pick the most relevant tool
- Pick the most relevant tool to answer the question.
- If you are failed to answer the question, try different tools to get context.

Step 3: Answer the question
- Answer the question in the same language as the question.
- Your answer should be very polite and professional.

Step 4: Provide the source of the answer(if applicable)
- If you've used the tool, provide the source of the answer.
- Valid sources are either a website(URL) or a document(PDF, etc).

Guidelines:
- If you've used the tool, your answer should be based on the tool's output(tool's output is more important than your own knowledge).
- If you've used the tool, and the source is valid URL, provide the source(URL) of the answer.
- Skip providing the source if the source is not URL.
- Answer in the same language as the question.
- Answer should be concise and to the point.
- Avoid response your output with any other information than the answer and the source.
</INSTRUCTIONS>

----

<OUTPUT_FORMAT>
(concise answer to the question)

**Source**(if applicable)
- (source1: valid URL)
- (source2: valid URL)
- ...
</OUTPUT_FORMAT>
"""
        )
        self.mcp_client = None
        self.agent = None
        self.thread_id = random_uuid()
        self.recursion_limit = 100
        self.selected_model = "claude-3-7-sonnet-latest"

    def write_env_file(self, filename="runtime.env", keys=None):
        abs_path = os.path.abspath(filename)
        cwd = os.getcwd()

        logger.info(f"Writing environment variables to file: {abs_path}")
        logger.info(f"Current working directory: {cwd}")

        vars_to_write = {
            k: v for k, v in os.environ.items() if keys is None or k in keys
        }
        logger.info(f"Writing {len(vars_to_write)} environment variables")

        try:
            with open(filename, "w") as f:
                current_time = datetime.now().isoformat()
                f.write(f"TIMESTAMP={current_time}\\n")
                logger.info(f"Wrote timestamp: {current_time}")

                for key, value in vars_to_write.items():
                    f.write(f"{key}={value}\\n")

            if os.path.exists(abs_path):
                file_size = os.path.getsize(abs_path)
                logger.info(f"Successfully wrote {file_size} bytes to {abs_path}")
            else:
                logger.error(f"Failed to write file: {abs_path}")

        except Exception as e:
            logger.error(f"Error writing environment file: {str(e)}")

    def load_config_from_json(self) -> Dict[str, Any]:
        default_config = {
            "get_current_time": {
                "command": "python",
                "args": ["./mcp_server_time.py"],
                "transport": "stdio",
            }
        }

        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                self.save_config_to_json(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading settings file: {str(e)}")
            return default_config

    def save_config_to_json(self, config: Dict[str, Any]) -> bool:
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving settings file: {str(e)}")
            return False

    def cleanup(self) -> None:
        if self.mcp_client:
            try:
                self.mcp_client.__exit__(None, None, None)
                self.mcp_client = None
            except Exception as e:
                logger.error(f"Error while terminating MCP client: {str(e)}")

    async def initialize_agent(
        self,
        mcp_config: Optional[Dict[str, Any]] = None,
        model_name="claude-3-7-sonnet-latest",
        recursion_limit=100,
    ):
        self.write_env_file(
            keys=[
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
                "AWS_SESSION_TOKEN",
                "AWS_REGION",
                "AWS_DEFAULT_REGION",
                "AWS_EXECUTION_ENV",
                "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
                "GITLAB_URL",
                "GITLAB_SUBGROUP_PATH",
                "ELASTICSEARCH_HOST",
                "ELASTICSEARCH_PORT",
                "ELASTICSEARCH_USER",
                "ELASTICSEARCH_PASSWORD",
                "ELASTICSEARCH_USE_SSL",
                "ELASTICSEARCH_DEFAULT_INDEX",
                "JIRA_EMAIL",
                "JIRA_API_TOKEN",
                "JIRA_SERVER_URL",
                "CONFLUENCE_TOKEN",
                "CONFLUENCE_URL",
                "CONFLUENCE_USERNAME",
                "GITLAB_ACCESS_TOKEN",
                "BITBUCKET_APP_PASSWORD",
                "BITBUCKET_USERNAME",
                "BITBUCKET_WORKSPACE",
            ]
        )

        self.cleanup()

        if mcp_config is None:
            mcp_config = self.load_config_from_json()
        client = MultiServerMCPClient(mcp_config)
        client.__enter__()
        tools = client.get_tools()
        self.mcp_client = client

        self.selected_model = model_name
        self.recursion_limit = recursion_limit

        if self.selected_model in [
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
        ]:
            model = ChatAnthropic(
                model=self.selected_model,
                temperature=0.1,
                max_tokens=self.output_token_info[self.selected_model]["max_tokens"],
            )
        elif self.selected_model in [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        ]:
            model = ChatBedrock(
                model_id=self.selected_model,
                temperature=0.1,
                max_tokens=self.output_token_info[self.selected_model]["max_tokens"],
            )
        else:
            # Assuming OpenAI, which was commented out in the original file
            # from langchain_openai import ChatOpenAI
            # model = ChatOpenAI(
            #     model=self.selected_model,
            #     temperature=0.1,
            #     max_tokens=self.output_token_info[self.selected_model]["max_tokens"],
            # )
            raise ValueError(f"Unsupported model: {self.selected_model}")

        self.agent = create_react_agent(
            model,
            tools,
            checkpointer=MemorySaver(),
            prompt=self.system_prompt,
        )
        return True

    async def run_query(self, query: str, timeout_seconds: int = 60, streaming_callback=None):
        if not self.agent:
            raise Exception("Agent not initialized. Call initialize_agent first.")

        try:
            response = await asyncio.wait_for(
                astream_and_get_final_response(
                    self.agent,
                    {"messages": [HumanMessage(content=query)]},
                    callback=streaming_callback,
                    config=RunnableConfig(
                        recursion_limit=self.recursion_limit,
                        thread_id=self.thread_id,
                    ),
                ),
                timeout=timeout_seconds,
            )
            return response
        except asyncio.TimeoutError:
            error_msg = f"Request time exceeded {timeout_seconds} seconds."
            logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            logger.error(f"Error occurred during query processing: {str(e)}")
            return {"error": str(e)}

    def reset_conversation(self):
        self.thread_id = random_uuid()