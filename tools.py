# === File: tools.py ===
from langchain.tools import BaseTool
from langchain_core.tools import tool
import subprocess
from typing import ClassVar
import os
from config import WKSPACE, EXCLUDE_DIRS


# === Wrapper for WriteFileTool to make it single-input ===
class WriteFileSingleInputTool(BaseTool):
    name: ClassVar[str] = "write_file"
    description: ClassVar[str] = (
        "Write content to a file. "
        "Input should be a string in the format 'file_path::file_contents'."
    )

    def _run(self, file_input: str):
        try:
            file_path, content = file_input.split("::", 1)
            file_path = file_path.strip()
            content = content.lstrip()

            full_path = os.path.join(WKSPACE, file_path)
            with open(full_path, "w") as f:
                f.write(content)
            return f"Successfully wrote to {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")

# === Flake8 tool ===
class RunFlake8Tool(BaseTool):
    name: ClassVar[str] = "run_flake8"
    description: ClassVar[str] = "Run flake8 linter on a file and return linting issues."

    def _run(self, file_path: str) -> str:
        full_path = os.path.join(WKSPACE, file_path)
        if os.path.isdir(full_path):
            files_to_check = []
            for root, dirs, files in os.walk(full_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    if f.endswith(".py"):
                        files_to_check.append(os.path.join(root, f))
        else:
            files_to_check = [full_path]

        if not files_to_check:
            return "No Python files found."

        try:
            output = subprocess.check_output(
                ["flake8"] + files_to_check, stderr=subprocess.STDOUT, text=True
            )
            return output or "No lint issues found."
        except subprocess.CalledProcessError as e:
            return e.output.strip()


    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")

# === Docstyle (PEP257) tool ===
class RunDocstyleTool(BaseTool):
    name: ClassVar[str] = "run_docstyle"
    description: ClassVar[str] = "Run pydocstyle (PEP257) on a file and return docstring issues."


    def _run(self, file_path: str) -> str:
        full_path = os.path.join(WKSPACE, file_path)
        if os.path.isdir(full_path):
            files_to_check = []
            for root, dirs, files in os.walk(full_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    if f.endswith(".py"):
                        files_to_check.append(os.path.join(root, f))
        else:
            files_to_check = [full_path]

        if not files_to_check:
            return "No Python files found."

        try:
            output = subprocess.check_output(
                ["flake8"] + files_to_check, stderr=subprocess.STDOUT, text=True
            )
            return output or "No docstring issues found."
        except subprocess.CalledProcessError as e:
            return e.output.strip()



    def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async not supported")
