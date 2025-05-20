# === File: mcp.py ===

# Standard library
import os
import re
import sys
from pathlib import Path
from datetime import datetime
import warnings
import readline
import atexit

# Third-party packages
from langchain_core._api.deprecation import LangChainDeprecationWarning

log_output = open("langchain_warnings.log", "a")
histfile = Path.home() / ".mcp_history"

# Load history if available
try:
    readline.read_history_file(histfile)
except FileNotFoundError:
    pass

# Save history on exit
atexit.register(readline.write_history_file, histfile)


def log_warning(message, category, filename, lineno, file=None, line=None):
    print(f"{filename}:{lineno}: {category.__name__}: {message}", file=log_output)

warnings.showwarning = log_warning

from langchain.agents import initialize_agent, AgentType, AgentExecutor
from langchain_community.tools import ReadFileTool, WriteFileTool, ListDirectoryTool
from langchain_openai import ChatOpenAI

# Local modules
from config import WKSPACE, EXCLUDE_DIRS
import tools
import backup_utils
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

# Define a custom system message that clarifies expected behavior
custom_system_message = """
You are MCP (Modular Coding Partner), an AI-driven development assistant tailored for ROS2 workspaces.

IMPORTANT INSTRUCTIONS ABOUT TOOL USAGE:

1. When analyzing code:
   - Use 'analyze_flake8' to check Python code style without making changes
   - Use 'analyze_docstrings' to check docstrings without making changes
   
2. When fixing code:
   - Do NOT automatically fix code after analysis
   - Wait for explicit user confirmation before applying fixes
   - Only suggest fixes, never apply them without permission

3. Your primary goal is to assist with:
   - Code analysis (linting, docstring validation)
   - Workspace integrity validation
   - File change tracking
   - Backup and restore operations

Follow these guidelines strictly to maintain user control over code changes.
"""

# Initialize language model with the custom system message
llm = ChatOpenAI(
    temperature=0, 
    openai_api_key=api_key,
    model_kwargs={"messages": [{"role": "system", "content": custom_system_message}]}
)

# Tools setup
read_tool = ReadFileTool(root_dir=str(WKSPACE))
write_tool = tools.WriteFileSingleInputTool()
list_tool = ListDirectoryTool(root_dir=str(WKSPACE))

# Use the new, separate analysis and fix tools
analyze_flake8_tool = tools.AnalyzeFlake8Tool()
fix_flake8_tool = tools.FixFlake8Tool()
analyze_docstrings_tool = tools.AnalyzePydocstyleTool()
fix_docstrings_tool = tools.FixPydocstyleTool()

# Old tools - kept for backward compatibility, but redirected to analyze-only by default
flake8_tool = tools.RunFlake8Tool()
docstyle_tool = tools.RunDocstyleTool()

# Backup tools
backup_tool = backup_utils.FileBackupTool()
restore_tool = backup_utils.FileRestoreTool()
list_backups_tool = backup_utils.ListBackupsTool()

# Initialize agent with all tools
tool_list = [
    read_tool, 
    write_tool, 
    list_tool, 
    
    # Analysis tools only - fix tools will be managed by the main loop with confirmation
    analyze_flake8_tool,
    analyze_docstrings_tool,
    
    # Backward compatibility tools
    flake8_tool,
    docstyle_tool,
    
    # Backup tools
    backup_tool,
    restore_tool,
    list_backups_tool
]


# Initialize agent
agent_executor: AgentExecutor = initialize_agent(
    tools=tool_list,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,  
    max_iterations=60,
    max_execution_time=600,
)

# File change tracker
tracker = FileChangeTracker(WKSPACE)
tracker.snapshot()

# Function to run fix tools with confirmation
def run_fix_with_confirmation(fix_type, file_path):
    """Run a fix tool after user confirmation."""
    while True:
        confirm = input(f"\n⚠️ Apply automatic {fix_type} fixes to {file_path}? [y/n]: ").lower()
        if confirm in ['y', 'yes']:
            print(f"✅ Applying {fix_type} fixes...")
            if fix_type == "flake8":
                result = fix_flake8_tool._run(file_path)
            elif fix_type == "docstring":
                result = fix_docstrings_tool._run(file_path)
            print(result)
            
            # Update file tracker
            changes = tracker.diff()
            tracker.snapshot()
            
            # Show file change status
            if changes:
                print(f"\n📄 File changes detected: {len(changes)}")
            else:
                print("\n✅ No file changes detected.")
                
            return True
        elif confirm in ['n', 'no']:
            print(f"❌ No changes applied to {file_path}.")
            return False
        else:
            print("Please answer 'y' or 'n'.")

if __name__ == "__main__":
    print(f"MCP AI Agent ready. Monitoring {WKSPACE}")
    print("NEW TOOLS AVAILABLE:")
    print("  - analyze_flake8: Check code style without changes")
    print("  - analyze_docstrings: Check docstrings without changes")
    print("PROTECTED COMMANDS (require confirmation):")
    print("  - fix_flake8: Apply automatic style fixes (with confirmation)")
    print("  - fix_docstrings: Apply automatic docstring fixes (with confirmation)")

    while True:
        try:
            user_input = input("\n>> ")
            if not user_input.strip():
                continue
            log_command(user_input)

            # Special handling for recursive list command
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

            # Add special handling for old-style commands
            # Automatically redirect to analysis-only versions to prevent unwanted changes
            if user_input.lower().startswith("run flake8_"):
                print("⚠️ NOTE: Using 'run_flake8' is deprecated. Please use 'analyze_flake8' or 'fix_flake8' instead.")
                if "write_changes" in user_input.lower():
                    # Get file path
                    parts = user_input.split("write_changes")
                    if len(parts) > 1:
                        file_path = parts[1].strip()
                    else:
                        file_path = parts[0].replace("run flake8_", "").strip()
                    
                    # First run analysis
                    print("🔍 First analyzing issues...")
                    analysis_result = analyze_flake8_tool._run(file_path)
                    print(analysis_result)
                    
                    # Then ask for confirmation
                    run_fix_with_confirmation("flake8", file_path)
                    continue
                else:
                    print("⚠️ Using 'analyze_flake8' for safer operation...")
                    user_input = user_input.lower().replace("run flake8_propose_only", "analyze_flake8")
            
            if user_input.lower().startswith("run docstyle_"):
                print("⚠️ NOTE: Using 'run_docstyle' is deprecated. Please use 'analyze_docstrings' or 'fix_docstrings' instead.")
                if "write_changes" in user_input.lower():
                    # Get file path
                    parts = user_input.split("write_changes")
                    if len(parts) > 1:
                        file_path = parts[1].strip()
                    else:
                        file_path = parts[0].replace("run docstyle_", "").strip()
                    
                    # First run analysis
                    print("🔍 First analyzing issues...")
                    analysis_result = analyze_docstrings_tool._run(file_path)
                    print(analysis_result)
                    
                    # Then ask for confirmation
                    run_fix_with_confirmation("docstring", file_path)
                    continue
                else:
                    print("⚠️ Using 'analyze_docstrings' for safer operation...")
                    user_input = user_input.lower().replace("run docstyle_propose_only", "analyze_docstrings")
                    
            # Handle direct fix_flake8 and fix_docstrings commands with confirmation
            if user_input.lower().startswith("fix_flake8"):
                # Extract file path
                file_path = user_input.replace("fix_flake8", "").strip()
                
                # First run analysis
                print("🔍 First analyzing issues...")
                analysis_result = analyze_flake8_tool._run(file_path)
                print(analysis_result)
                
                # Then ask for confirmation
                run_fix_with_confirmation("flake8", file_path)
                continue
                
            if user_input.lower().startswith("fix_docstrings"):
                # Extract file path
                file_path = user_input.replace("fix_docstrings", "").strip()
                
                # First run analysis
                print("🔍 First analyzing issues...")
                analysis_result = analyze_docstrings_tool._run(file_path)
                print(analysis_result)
                
                # Then ask for confirmation
                run_fix_with_confirmation("docstring", file_path)
                continue

            # Run the agent to process the command (for all other commands)
            response = agent_executor.run(user_input)
            print(response)

            # Show file diffs after command execution
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
