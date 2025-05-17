# === File: config.py ===
from pathlib import Path

WKSPACE = str(Path.home() / "mecca_ws" / "src")
EXCLUDE_DIRS = ["build", "install", "log", ".git", ".vscode", "__pycache__"]
