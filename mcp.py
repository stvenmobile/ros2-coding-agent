import os
import subprocess
from pathlib import Path
from typing import Optional, Type

from langchain.agents import initialize_agent, AgentType, Tool, AgentExecutor
from langchain.tools.base import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI
from langchain_community.tools import ReadFileTool, ListDirectoryTool
from langchain_community.agent_toolkits.file_management.toolkit import FileManagementToolkit


# Custom tool for flake8
class RunFlake8Tool(BaseTool):
    name: str = "run_flake8"
    description: str = "Run flake8 linter on a Python file and return the output."
    args_schema: Type = None

    def _run(
        self, file_path: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        full_path = os.path.expanduser(f"~/mecca_ws/src/{file_path}")
        try:
            result = subprocess.run(
                ["flake8", full_path],
                capture_output=True,
                text=True,
                check=False
            )
            return result.stdout or "No issues found."
        except Exception as e:
            return f"Error running flake8: {e}"

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported.")


# Load OpenAI API key from file
api_key_file = Path.home() / "mcp" / "openai_apikey.txt"
if not api_key_file.exists():
    raise FileNotFoundError(f"API key file not found at {api_key_file}")
api_key = api_key_file.read_text().strip()

# Initialize the language model
llm = ChatOpenAI(temperature=0, openai_api_key=api_key)

# Setup tools
toolkit = FileManagementToolkit(
    root_dir=str(Path.home() / "mecca_ws" / "src"),
    selected_tools=["read_file", "list_directory"]
)
tools = toolkit.get_tools()
tools.append(RunFlake8Tool())

# Initialize agent
agent_executor: AgentExecutor = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

# Interactive loop
if __name__ == "__main__":
    print("MCP AI Agent ready. Monitoring ~/mecca_ws/src")
    while True:
        try:
            user_input = input(">> ")
            response = agent_executor.run(user_input)
            print(response)
        except KeyboardInterrupt:
            print("\nMCP terminated.")
            break
