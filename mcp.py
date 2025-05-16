# === File: mcp.py ===
import os
from pathlib import Path
from datetime import datetime
from langchain.agents import initialize_agent, AgentType
from langchain.agents.agent import AgentExecutor
from langchain_community.tools import ReadFileTool, WriteFileTool, ListDirectoryTool
from langchain_openai import ChatOpenAI
from filetracker import FileChangeTracker

import tools

from config import BASE_DIR   # base directory for all file requests

# Set up logging
log_file = Path("mcp_command.log")
def log_command(command: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {command}\n")

# Load OpenAI API key from a file
key_file = Path("/etc/mcp/conf/.apikey")

if key_file.exists():
    api_key = key_file.read_text().strip()
else:
    raise FileNotFoundError(f"API key file not found: {key_file}")

# Initialize language model
llm = ChatOpenAI(temperature=0, openai_api_key=api_key)

# Tools setup
read_tool = ReadFileTool(root_dir=BASE_DIR)
write_tool = tools.WriteFileSingleInputTool()
list_tool = ListDirectoryTool(root_dir=BASE_DIR)
flake8_tool = tools.RunFlake8Tool()
docstyle_tool = tools.RunDocstyleTool()
tool_list = [read_tool, write_tool, list_tool, flake8_tool, docstyle_tool]

# Initialize agent
agent_executor: AgentExecutor = initialize_agent(
    tools=tool_list,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    max_iterations=60,
    max_execution_time=600,
)

# File change tracker
tracker = FileChangeTracker(BASE_DIR)
tracker.snapshot()

if __name__ == "__main__":
    print(f"MCP AI Agent ready. Monitoring {BASE_DIR}")

    while True:
        try:
            user_input = input(">> ")
            if not user_input.strip():
                continue
            log_command(user_input)
            response = agent_executor.run(user_input)
            print(response)

            # Show file diffs after each command
            changes = tracker.diff()
            tracker.snapshot()

            if changes:
                print(f"\n📄 File changes detected: {len(changes)}")
                if "verbose" in user_input.lower():
                    for change_type, path in changes:
                        print(f"  {change_type:<8} {path}")
            else:
                print("\n✅ No file changes detected.")

        except KeyboardInterrupt:
            print("\nMCP terminated.")
            break
