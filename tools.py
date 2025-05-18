import os
import subprocess
from langchain_core.tools import BaseTool
from typing import List, Optional, Union
from pathlib import Path
import fnmatch
import re
from config import WKSPACE, EXCLUDE_DIRS



class WriteFileSingleInputTool(BaseTool):
    name: str = "write_file"
    description: str = "Writes content to a file. Input format: '<relative_path>::<content>'"

    def _run(self, input_str: str) -> str:
        try:
            if "::" not in input_str:
                return "❌ Invalid input. Use format '<relative_path>::<content>'."
            rel_path, content = input_str.split("::", 1)
            target_path = WKSPACE / rel_path.strip()
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content)
            return f"✅ Successfully wrote to {rel_path.strip()}"
        except Exception as e:
            return f"❌ Failed to write file: {e}"

def resolve_path_or_search(filepath: str) -> Optional[Path]:
    base_path = Path(WKSPACE)
    full_path = base_path / filepath
    if full_path.exists():
        return full_path.resolve()

    # Recursive search
    matches = []
    for root, _, files in os.walk(base_path):
        if any(excl in root for excl in EXCLUDE_DIRS):
            continue
        for name in files:
            if name == os.path.basename(filepath):
                matches.append(Path(root) / name)

    if len(matches) == 1:
        return matches[0].resolve()
    elif len(matches) > 1:
        print(f"Multiple matches found for '{filepath}':")
        for m in matches:
            print(" -", m)
        return None
    else:
        return None

class RunFlake8Tool(BaseTool):
    name: str = "run_flake8"
    description: str = (
        "Run flake8 linter on a specified Python file. "
        "Optionally add 'propose_only' or 'write_changes' to control output."
    )

    def _run(self, filepath: str) -> str:
        import subprocess

        # Extract optional mode (default is propose_only)
        args = filepath.strip().split()
        target = args[0]
        mode = args[1] if len(args) > 1 else "propose_only"

        resolved = resolve_path_or_search(target)
        if not resolved:
            return f"❌ Could not find {target}"

        try:
            result = subprocess.run(
                ["flake8", str(resolved)],
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()

            if mode == "propose_only":
                return (
                    f"📋 Proposed flake8 changes for {target}:\n"
                    + (output if output else "✅ No issues found.")
                )
            elif mode == "write_changes":
                return (
                    f"✏️ Would apply changes to {target}, but auto-fix not implemented yet.\n"
                    f"Detected issues:\n{output if output else '✅ No issues found.'}"
                )
            else:
                return f"❌ Unknown mode: {mode}"

        except Exception as e:
            return f"❌ Error running flake8: {e}"


class RunDocstyleTool(BaseTool):
    name: str = "run_docstyle"
    description: str = (
        "Run pydocstyle on a Python file. "
        "Use format: 'relative/path/to/file.py::propose_only' to only propose changes "
        "or '::write_changes' to modify the file in-place."
    )

    def _run(self, filepath: str) -> str:
        # Split options if provided like 'path/to/file.py::propose_only'
        mode = "propose_only"
        if "::" in filepath:
            filepath, mode = filepath.split("::", 1)
            mode = mode.strip().lower()
        else:
            filepath = filepath.strip()

        # Resolve the file path relative to workspace
        resolved_path = resolve_path_or_search(filepath)
        if not resolved_path or not resolved_path.exists():
            return f"❌ File not found: {filepath}"

        with open(resolved_path, "r") as f:
            lines = f.readlines()

        changes = []
        for i, line in enumerate(lines):
            match = re.match(r'\s*def\s+(\w+)\(', line)
            if match:
                func_name = match.group(1)
                docstring_line = i + 1
                # Check for simple one-line docstring below the def
                if docstring_line < len(lines):
                    doc_line = lines[docstring_line].strip()
                    if '"""' in doc_line or "'''" in doc_line:
                        cleaned = doc_line.strip('"\'')

                        if cleaned.lower().startswith("handles"):
                            suggestion = "Handle"
                        elif cleaned.lower().startswith("updates"):
                            suggestion = "Update"
                        elif cleaned.lower().startswith("processes"):
                            suggestion = "Process"
                        elif cleaned.lower().startswith("determines"):
                            suggestion = "Determine"
                        elif cleaned.lower().startswith("applies"):
                            suggestion = "Apply"
                        else:
                            suggestion = None

                        if suggestion and not cleaned.startswith(suggestion):
                            changes.append(
                                (docstring_line, cleaned, f"{suggestion}{cleaned[len(cleaned.split()[0]):]}")
                            )

        if not changes:
            return f"✅ No pydocstyle D401 issues found in {filepath}."

        summary_lines = []
        modified_lines = 0

        for lineno, original, updated in changes:
            summary_lines.append(
                f"Line {lineno+1}: \"{original}\" → \"{updated}\""
            )
            if mode == "write_changes":
                lines[lineno] = lines[lineno].replace(original, updated)
                modified_lines += 1

        if mode == "write_changes":
            with open(resolved_path, "w") as f:
                f.writelines(lines)

            return (
                f"✍️ {modified_lines} line(s) modified in {filepath}:\n\n"
                + "\n".join(summary_lines)
                + "\n\n✅ Docstring updates completed."
            )

        return (
            f"📋 Proposed pydocstyle changes for {filepath}:\n\n"
            + "\n".join(summary_lines)
            + f"\n\n✅ {len(changes)} docstring suggestion(s) found. No file was modified."
        )
