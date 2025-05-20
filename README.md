# MCP - ROS2 Coding Assistant

The **Modular Coding Partner (MCP)** is an AI-driven development assistant tailored for ROS2 workspaces. It integrates with OpenAI's GPT models to automate, guide, and validate code contributions across a ROS2 workspace. MCP combines static analysis, prompt-based code suggestions, workspace validation, and file change tracking into a single interface.

---

## 🧠 Core Goals

- Leverage LLMs to improve code structure and adherence to ROS2 Python standards.
- Assist developers with linting, docstring validation, and prompt-based changes.
- Perform intelligent file tracking and workspace integrity validation.
- Enable conversational or script-driven automation across large projects.

---

## 🗂️ Project Structure

```
mcp/
├── config.py              # Global config: WKSPACE and EXCLUDE_DIRS
├── mcp.py                 # Main MCP entry point (formerly main.py)
├── tools.py               # Custom langchain tools (flake8, docstyle, etc.)
├── backup_utils.py        # Backup and restore functionality
├── filetracker.py         # Change detection for Python files
├── workspace_checker.py   # Validates integrity of ROS2 packages
├── mcp.log                # Log file of command and agent output
├── README.md              # This file
```

---

## 🔧 Installation

Follow these steps to deploy the MCP agent on a fresh Ubuntu (22.04 or 24.04) VM:
1. Prepare the Virtual Machine

    Recommended: 4 CPU / 8GB RAM

    OS: Ubuntu Noble (for ROS 2 Jazzy compatibility)

2. Install base packages

   sudo apt update && sudo apt upgrade -y
   sudo apt install git curl wget openssh-client openssh-server nano net-tools

3. Enable SSH access

   sudo systemctl enable ssh
   sudo systemctl start ssh

   You can now connect using SSH or Termius.

4. Set up Git with SSH authentication

   ssh-keygen -t ed25519 -C "your_email@example.com"
   cat ~/.ssh/id_ed25519.pub

   Copy the key to your GitHub account under Settings → SSH Keys.

5. Clone the repository

   git clone git@github.com:stvenmobile/ros2-coding-agent.git
   cd ros2-coding-agent

6. Set up the Python environment

   python3 -m venv mcp_env
   source mcp_env/bin/activate
   pip install -r requirements.txt

7. Add OpenAI API key

   sudo mkdir -p /etc/mcp/conf  
   sudo nano /etc/mcp/conf/.apikey  
   sudo chmod 600 /etc/mcp/conf/.apikey  

   API Key format:
   ```
   sk-xxxxxxxxxxxxxxxxxxxxxxxx
   ```

   You're now ready to launch the MCP agent.


## ⚙️ Configuration (config.py)

```python
from pathlib import Path

WKSPACE = str(Path.hoe() / "mecca_ws")
EXCLUDE_DIRS = ["build", "install", "log", ".git"]
```

- `WKSPACE`: Points to the root ROS2 workspace (not just src/)
- `EXCLUDE_DIRS`: Any folders to skip in scans or recursive lookups

---

## 💬 Prompt Usage

Run the agent:

```bash
source mcp_env/bin/activate
python3 mcp.py
```

Then use interactive prompts like:

```txt
>> analyze_flake8 navigator_node.py
>> analyze_docstrings mecca_driver_node.py 
>> fix_flake8 navigator/setup.py
>> fix_docstrings navigator_node.py
>> list_backups navigator_node.py
>> restore navigator_node.py --version 2
>> list all python files under vl53l1x_sensor
>> run workspace check and report any issues
>> track changes to python files and summarize modified files
```

When referring to a file, use **workspace-relative paths** (e.g., `navigator/setup.py`), not full disk paths.

---

## 🧰 Tools Available

### 🔹 Code Analysis & Fixing Tools

MCP now provides clearly separated analysis and fix tools for better control:

#### Analysis Tools (read-only)
- `analyze_flake8` - Check code style without making changes  
- `analyze_docstrings` - Check docstrings without making changes

#### Fix Tools (with confirmation)
- `fix_flake8` - Apply automatic style fixes (requires confirmation)
- `fix_docstrings` - Apply automatic docstring fixes (requires confirmation)

Each fix operation will first show you what will be changed and prompt for confirmation before applying any changes.

### 🔹 Backup & Restore Tools

- `backup` - Create a backup of a file
- `restore` - Restore a file from backup (optionally use `--version N`)
- `list_backups` - List available backups for a file

### 🔹 File Tracker

- Uses `filetracker.py` to hash `.py` files and detect changes
- Runs automatically after each prompt
- Snapshot is stored in `.file_snapshot.json` in the workspace

### 🔹 Workspace Checker

- Finds issues with:
  - Missing setup.py, package.xml
  - Missing launch/ or config/ folders
  - Incorrectly named resource files
- Output is categorized by severity

---

## ⚙️ Command Format Details

### Analysis Commands

- **Basic Format**: `analyze_flake8 <filename>`
- **Example**: `analyze_flake8 navigator_node.py`
- **Output**: Shows issues separated by auto-fixable vs manual-fix categories

### Fix Commands (with confirmation)

1. **Command Entry**: `fix_flake8 <filename>`
2. **Analysis Phase**: Tool will first analyze and show issues
3. **Confirmation Prompt**: `Apply automatic flake8 fixes to <filename>? [y/n]:`
4. **Application Phase**: Only if you confirm with "y", changes will be applied

### Package-Specific Commands

- You can specify a package for operations: `backup navigator navigator_node.py`
- This helps disambiguate files with the same name in different packages

### Backup & Restore Commands

- Create a backup: `backup <filename>` or `backup <package> <filename>`
- List backups: `list_backups <filename>` or `list_backups <package> <filename>`
- Restore latest backup: `restore <filename>` or `restore <package> <filename>`
- Restore specific version: `restore <filename> --version N`

---

## 🛣️ Roadmap

### ✅ Current Strengths

The MCP agent already delivers strong AI-assisted development tooling for ROS 2 workspaces:

- 🧠 **LLM-Driven Agent**: Interact with your codebase via natural language prompts for code exploration, linting, and docstring analysis.
- 🧪 **Linting & Doc Checks**: Built-in support for flake8 and pydocstyle (PEP257) with automatic tracking of changes.
- 📁 **File Change Tracking**: After each prompt, MCP compares current file states against a snapshot to detect code modifications.
- 🔎 **Recursive File Listing**: Supports list_rec and list_recursive prompts to find all Python files below a given path.
- 📦 **Workspace Integrity Checker**: Analyzes expected structural elements in ROS 2 packages (e.g., launch, config, tests).
- 🧰 **Modular Architecture**: Components like tools.py, filetracker.py, and workspace_checker.py are independently extendable.
- 💾 **Backup & Restore**: Create, list, and restore backups of any file in the workspace.
- 🛡️ **Confirmation System**: Changes to files require explicit user confirmation.

### 🎯 Near-Term Priorities (Low-Hanging Fruit)

These features build upon existing code and offer a high-value improvement path:

- 🧪 **Generate Test Stubs**
  - Automatically generate pytest-based test scaffolding for Python modules that lack testing coverage.

- 📄 **Validate Required Metadata**
  - Cross-check setup.py, package.xml, and installed scripts against the actual file system. Detect:
    - Missing entry_points
    - Unlisted dependencies
    - Undeclared test requirements

- 🧱 **Template Generators**
  - Prompt-driven generation of:
    - ROS 2 node templates (publisher, subscriber, etc.)
    - New package skeletons
    - Standard launch and config files

- 📚 **Generate Workspace Summary**
  - Generate a top-level summary of:
    - Packages, nodes, and message types
    - Existing tests and lint coverage
    - Inter-package interactions (if detectable)

- 🧠 **Track Change History**
  - Track and summarize changes made during the session.
  - Prompts like:
    - "Summarize all file changes made today"
    - "Undo last flake8 fix"

- 💬 **Intelligent Prompt Suggestions**
  - Detect vague or mistyped input and offer helpful corrections:
  - e.g., "Did you mean list_rec mecca_driver_node?"

### 🧭 Long-Term Goals

These items represent more ambitious feature additions:

- 🔁 **Chained Commands**: Support multi-step operations in one prompt (e.g., lint ➝ fix ➝ test).
- 🕸️ **ROS Graph Summary**: Visualize node → topic relationships from workspace analysis.
- 🧪 **Test Execution Support**: Allow running existing test suites and reporting outcomes.
- 🌍 **Web Interface**: Optional browser UI for prompt entry, file viewing, and result feedback.
- 🛠️ **Refactor Suggestions**: Auto-detect duplicated logic or structural code smells for improvement.
- 🧩 **VSCode integration**: Integrate with VSCode for better development experience.
- 🔄 **Auto-fix mode for common issues**: Provide options for automatic fixing of common issues.
- 📋 **Self-updating package list / dependency checker**: Automatically update package list and dependencies.
- 🤖 **Natural language to test stub generator**: Generate test stubs from natural language descriptions.

---

## 🪪 License

This project is MIT licensed and intended for educational and development productivity enhancement. Contributions welcome!

---
