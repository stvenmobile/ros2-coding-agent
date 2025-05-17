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
├── filetracker.py         # Change detection for Python files
├── workspace_checker.py   # Validates integrity of ROS2 packages
├── mcp.log                # Log file of command and agent output
├── README.md              # This file
```

---

## ⚙️ Configuration (config.py)

```python
from pathlib import Path

WKSPACE = str(Path.home() / "mecca_ws")
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
>> run flake8 on navigator/setup.py
>> fix pep257 issues in mecca_driver_node.py
>> list all python files under vl53l1x_sensor
>> run workspace check and report any issues
>> track changes to python files and summarize modified files
```

When referring to a file, use **workspace-relative paths** (e.g., `navigator/setup.py`), not full disk paths.

---

## 🧰 Tools Available

### 🔹 flake8 Linter

- Run `flake8` on specific files or recursively on packages
- Output is reported in-place and optionally fixed

### 🔹 Docstyle (PEP257)

- Validates and optionally improves docstrings

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

## 🔒 OpenAI API Key

Store the API key securely at:

```
/etc/mcp/conf/.apikey
```

Format:
```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

Permissions:
```bash
sudo chmod 600 /etc/mcp/conf/.apikey
```

---

🛣️ Roadmap
✅ Current Strengths

The MCP agent already delivers strong AI-assisted development tooling for ROS 2 workspaces:

    🧠 LLM-Driven Agent: Interact with your codebase via natural language prompts for code exploration, linting, and docstring analysis.

    🧪 Linting & Doc Checks: Built-in support for flake8 and pydocstyle (PEP257) with automatic tracking of changes.

    📁 File Change Tracking: After each prompt, MCP compares current file states against a snapshot to detect code modifications.

    🔎 Recursive File Listing: Supports list_rec and list_recursive prompts to find all Python files below a given path.

    📦 Workspace Integrity Checker: Analyzes expected structural elements in ROS 2 packages (e.g., launch, config, tests).

    🧰 Modular Architecture: Components like tools.py, filetracker.py, and workspace_checker.py are independently extendable.

🎯 Near-Term Priorities (Low-Hanging Fruit)

These features build upon existing code and offer a high-value improvement path:

    🧪 Generate Test Stubs
    Automatically generate pytest-based test scaffolding for Python modules that lack testing coverage.

    📄 Validate Required Metadata
    Cross-check setup.py, package.xml, and installed scripts against the actual file system. Detect:

        Missing entry_points

        Unlisted dependencies

        Undeclared test requirements

    🧱 Template Generators
    Prompt-driven generation of:

        ROS 2 node templates (publisher, subscriber, etc.)

        New package skeletons

        Standard launch and config files

    📚 Generate Workspace Summary
    Generate a top-level summary of:

        Packages, nodes, and message types

        Existing tests and lint coverage

        Inter-package interactions (if detectable)

    🧠 Track Change History
    Track and summarize changes made during the session.
    Prompts like:

        "Summarize all file changes made today"

        "Undo last flake8 fix"

    💬 Intelligent Prompt Suggestions
    Detect vague or mistyped input and offer helpful corrections:
    e.g., "Did you mean list_rec mecca_driver_node?"

🧭 Long-Term Goals

These items represent more ambitious feature additions:

    🔁 Chained Commands: Support multi-step operations in one prompt (e.g., lint ➝ fix ➝ test).

    🕸️ ROS Graph Summary: Visualize node → topic relationships from workspace analysis.

    🧪 Test Execution Support: Allow running existing test suites and reporting outcomes.

    🌍 Web Interface: Optional browser UI for prompt entry, file viewing, and result feedback.

    🛠️ Refactor Suggestions: Auto-detect duplicated logic or structural code smells for improvement.

- VSCode integration
- Web interface (socket or REST-based)
- Auto-fix mode for common issues
- Self-updating package list / dependency checker
- Natural language to test stub generator

---

## 🪪 License

This project is MIT licensed and intended for educational and development productivity enhancement. Contributions welcome!

---
