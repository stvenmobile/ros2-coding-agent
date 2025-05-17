# === File: workspace_checker.py ===
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from config import WKSPACE, EXCLUDE_DIRS



# Define severity levels
SEVERITY = {
    "FATAL": "❌ FATAL",
    "WARN": "⚠️ WARNING",
    "INFO": "ℹ️ INFO"
}

def check_package(package_path):
    results = []
    package_name = package_path.name

    # --- FATAL Checks ---
    if not (package_path / "package.xml").exists():
        results.append((SEVERITY["FATAL"], f"{package_name}: missing package.xml"))

    if not ((package_path / "setup.py").exists() or (package_path / "CMakeLists.txt").exists()):
        results.append((SEVERITY["FATAL"], f"{package_name}: missing setup.py or CMakeLists.txt"))

    # --- WARN Checks ---
    if not (package_path / "LICENSE").exists():
        results.append((SEVERITY["WARN"], f"{package_name}: missing LICENSE file"))

    if not (package_path / "resource").exists():
        results.append((SEVERITY["WARN"], f"{package_name}: missing resource/ directory"))

    if not (package_path / "test").exists():
        results.append((SEVERITY["WARN"], f"{package_name}: missing test/ directory"))

    if not (package_path / "launch").exists():
        results.append((SEVERITY["INFO"], f"{package_name}: no launch/ directory found"))

    if not (package_path / "README.md").exists():
        results.append((SEVERITY["INFO"], f"{package_name}: no README.md"))

    # --- package.xml content checks ---
    try:
        tree = ET.parse(package_path / "package.xml")
        root = tree.getroot()
        license_tag = root.find("license")
        maintainer_tag = root.find("maintainer")

        if license_tag is None or not license_tag.text.strip():
            results.append((SEVERITY["WARN"], f"{package_name}: license tag missing or empty in package.xml"))

        if maintainer_tag is None or not maintainer_tag.text.strip():
            results.append((SEVERITY["WARN"], f"{package_name}: maintainer tag missing or empty in package.xml"))

    except Exception as e:
        results.append((SEVERITY["WARN"], f"{package_name}: failed to parse package.xml ({e})"))

    return results


def check_workspace(base_path=WKSPACE):
    print(f"\n📦 Checking ROS 2 workspace integrity in: {base_path}\n")
    all_results = []

    for path in base_path.iterdir():
    if path.name in EXCLUDE_DIRS:
        continue
    if path.is_dir() and (path / "package.xml").exists():
            results = check_package(path)
            all_results.extend(results)

    if not all_results:
        print("✅ All packages passed integrity checks.")
    else:
        for level, message in all_results:
            print(f"{level}: {message}")


if __name__ == "__main__":
    check_workspace()
