# === File: mcp.py ===

# Standard library
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# Third-party packages
from langchain.agents import initialize_agent, AgentType, AgentExecutor
from langchain_community.tools import ReadFileTool, WriteFileTool, ListDirectoryTool
from langchain_openai import ChatOpenAI

# Local modules
from config import WKSPACE, EXCLUDE_DIRS
import tools
from filetracker import FileChangeTracker


# Set up logging
log_file = Path("mcp_command.log")
def log_command(command: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {command}\n")

def list_files_recursive(start_dir=WKSPACE, extensions=None, exclude_dirs=None):
    """Recursively list files under the workspace, optionally filtering by extension and excluding dirs."""
    start_dir = Path(start_dir)
    extensions = extensions or [".py"]
    exclude_dirs = set(exclude_dirs or [])

    results = []
    for root, dirs, files in os.walk(start_dir):
        rel_root = Path(root).relative_to(start_dir)
        if any(part in exclude_dirs for part in rel_root.parts):
            continue
        for fname in files:
            if any(fname.endswith(ext) for ext in extensions):
                full_path = Path(root) / fname
                rel_path = str(full_path.relative_to(start_dir))
                results.append(rel_path)
    return results



# Load OpenAI API key from a file
key_file = Path("/etc/mcp/conf/.apikey")

if key_file.exists():
    api_key = key_file.read_text().strip()
else:
    raise FileNotFoundError(f"API key file not found: {key_file}")

# Initialize language model
llm = ChatOpenAI(temperature=0, openai_api_key=api_key)

# Tools setup
read_tool = ReadFileTool(root_dir=WKSPACE)
write_tool = tools.WriteFileSingleInputTool()
list_tool = ListDirectoryTool(root_dir=WKSPACE)
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
tracker = FileChangeTracker(WKSPACE)
tracker.snapshot()

if __name__ == "__main__":
    print(f"MCP AI Agent ready. Monitoring {WKSPACE}")

    while True:
        try:
            user_input = input(">> ")
            if not user_input.strip():
                continue
            log_command(user_input)
            response = agent_executor.run(user_input)

            # Intercept recursive list command

            if user_input.lower().strip().startswith(("list_rec", "list_recursive")):
                match = re.search(r"under\s+([a-zA-Z0-9_\/-]+)", user_input, re.IGNORECASE)
                if match:
                    subdir = match.group(1).strip()
                    start_path = Path(WKSPACE) / subdir
                else:
                    start_path = Path(WKSPACE)

                print(f"📁 Recursively listing all Python files under: {start_path}\n")
                files = list_files_recursive(start_path, extensions=[".py"], exclude_dirs=EXCLUDE_DIRS)
                for file in sorted(files):
                    print(file)
                print(f"\n✅ {len(files)} file(s) found.")
                continue


            # Run standard LLM agent
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
