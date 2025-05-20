"""
Backup and restore utilities for MCP agent.
This module provides functionality for creating, tracking and restoring file backups.
"""

import os
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
from langchain_core.tools import BaseTool
from config import WKSPACE, EXCLUDE_DIRS


def get_ros2_packages():
    """Get a list of ROS2 packages in the workspace."""
    packages = {}
    src_path = Path(WKSPACE) / "src"
    
    if not src_path.exists():
        return packages
        
    # Scan for package directories (those with package.xml)
    for pkg_dir in src_path.iterdir():
        if pkg_dir.is_dir() and (pkg_dir / "package.xml").exists():
            packages[pkg_dir.name] = pkg_dir
            
    return packages


def resolve_package_path(package_name, file_path):
    """
    Resolve a file path within a ROS2 package.
    
    Args:
        package_name (str): Name of the ROS2 package
        file_path (str): Path to the file, relative to the package
        
    Returns:
        Path or None: Full path to the file if found, None otherwise
    """
    packages = get_ros2_packages()
    
    if package_name not in packages:
        return None
        
    package_dir = packages[package_name]
    full_path = package_dir / file_path
    
    if full_path.exists():
        return full_path
        
    # Search recursively within the package directory
    for root, _, files in os.walk(package_dir):
        for name in files:
            if name == os.path.basename(file_path):
                return Path(root) / name
                
    return None


def create_backup(file_path, tool_name="unknown"):
    """
    Create a backup of the specified file.
    
    Args:
        file_path (str or Path): Path to the file to backup
        tool_name (str): Name of the tool creating the backup
        
    Returns:
        tuple: (success, message)
    """
    try:
        file_path = Path(file_path)
        backup_dir = Path(WKSPACE) / ".mcp_backups"
        backup_dir.mkdir(exist_ok=True)
        
        rel_path = file_path.relative_to(Path(WKSPACE))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{rel_path}.{timestamp}.bak"
        
        # Create parent directories if needed
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(file_path, backup_path)
        
        # Update the index
        update_backup_index(rel_path, backup_path, timestamp, tool_name)
        
        return True, f"✅ Created backup of {rel_path} at {timestamp}"
    except Exception as e:
        return False, f"❌ Backup failed: {e}"


def get_backup_list(file_path):
    """
    Get list of available backups for a file.
    
    Args:
        file_path (str or Path): Path to the file
        
    Returns:
        list: List of backup data dictionaries, sorted newest first
    """
    try:
        file_path = Path(file_path)
        rel_path = file_path.relative_to(Path(WKSPACE))
        file_key = str(rel_path)
        
        backup_dir = Path(WKSPACE) / ".mcp_backups"
        index_path = backup_dir / "backup_index.json"
        
        if not index_path.exists():
            return []
            
        with open(index_path, "r") as f:
            index = json.load(f)
        
        if file_key not in index:
            return []
            
        backups = index[file_key]
        # Sort newest first
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    except Exception:
        return []


def restore_backup(file_path, version=None):
    """
    Restore a file from backup.
    
    Args:
        file_path (str or Path): Path to the file
        version (int, optional): Version number to restore (1-based index)
            If None, restores the most recent backup
            
    Returns:
        tuple: (success, message)
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return False, f"❌ File not found: {file_path}"
            
        # Get all backups for this file
        backups = get_backup_list(file_path)
        if not backups:
            return False, f"❌ No backups found for {file_path}"
            
        # Create a fresh backup before restoring (safety first!)
        create_backup(file_path, "prerestore")
        
        # Select the backup to restore
        if version is not None:
            if version < 1 or version > len(backups):
                return False, f"❌ Invalid version {version}. Available versions: 1-{len(backups)}"
            backup = backups[version - 1]
        else:
            # Default to most recent
            backup = backups[0]
        
        # Get the backup path and check if it exists
        backup_path = Path(backup["path"])
        if not backup_path.exists():
            return False, f"❌ Backup file not found: {backup_path}"
        
        # Copy the backup over the original file
        shutil.copy2(backup_path, file_path)
        
        timestamp = backup["timestamp"]
        tool = backup.get("tool", "unknown")
        return True, f"✅ Restored {file_path.name} from backup {timestamp} (created by {tool})"
        
    except Exception as e:
        return False, f"❌ Restore failed: {e}"


def get_backup_list(file_path):
    """
    Get list of available backups for a file.
    
    Args:
        file_path (str or Path): Path to the file
        
    Returns:
        list: List of backup data dictionaries, sorted newest first
    """
    try:
        file_path = Path(file_path)
        rel_path = file_path.relative_to(Path(WKSPACE))
        file_key = str(rel_path)
        
        backup_dir = Path(WKSPACE) / ".mcp_backups"
        index_path = backup_dir / "backup_index.json"
        
        if not index_path.exists():
            return []
            
        with open(index_path, "r") as f:
            index = json.load(f)
        
        if file_key not in index:
            return []
            
        backups = index[file_key]
        # Sort newest first
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    except Exception:
        return []


def restore_backup(file_path, version=None):
    """
    Restore a file from backup.
    
    Args:
        file_path (str or Path): Path to the file
        version (int, optional): Version number to restore (1-based index)
            If None, restores the most recent backup
            
    Returns:
        tuple: (success, message)
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return False, f"❌ File not found: {file_path}"
            
        # Get all backups for this file
        backups = get_backup_list(file_path)
        if not backups:
            return False, f"❌ No backups found for {file_path}"
            
        # Create a fresh backup before restoring (safety first!)
        create_backup(file_path, "prerestore")
        
        # Select the backup to restore
        if version is not None:
            if version < 1 or version > len(backups):
                return False, f"❌ Invalid version {version}. Available versions: 1-{len(backups)}"
            backup = backups[version - 1]
        else:
            # Default to most recent
            backup = backups[0]
        
        # Get the backup path and check if it exists
        backup_path = Path(backup["path"])
        if not backup_path.exists():
            return False, f"❌ Backup file not found: {backup_path}"
        
        # Copy the backup over the original file
        shutil.copy2(backup_path, file_path)
        
        timestamp = backup["timestamp"]
        tool = backup.get("tool", "unknown")
        return True, f"✅ Restored {file_path.name} from backup {timestamp} (created by {tool})"
        
    except Exception as e:
        return False, f"❌ Restore failed: {e}"


class FileBackupTool(BaseTool):
    name: str = "backup"
    description: str = (
        "Create a backup of a file. Input can be just a filename to search for, "
        "or 'package_name file_path' to specify a file in a specific ROS2 package."
    )

    def _run(self, input_str: str) -> str:
        from tools import resolve_path_or_search  # Import here to avoid circular imports
        
        parts = input_str.strip().split()
        
        # Check if we have package + file format
        if len(parts) >= 2:
            package_name = parts[0]
            file_path = " ".join(parts[1:])  # Join in case of spaces in filename
            
            # Try to resolve as package path
            resolved = resolve_package_path(package_name, file_path)
            if resolved:
                success, message = create_backup(resolved, "manual_backup")
                return message
        
        # Fall back to standard path search
        resolved = resolve_path_or_search(input_str.strip())
        if not resolved or not resolved.exists():
            return f"❌ File not found: {input_str}"
        
        success, message = create_backup(resolved, "manual_backup")
        return message


class FileRestoreTool(BaseTool):
    name: str = "restore"
    description: str = (
        "Restore a file from backup. Input can be a single filename, or 'package_name file_path' to specify a file in a specific ROS2 package. "
        "Append '--version N' to restore a specific version (otherwise restores most recent backup)."
    )

    def _run(self, input_str: str) -> str:
        from tools import resolve_path_or_search  # Import here to avoid circular imports
        
        try:
            parts = input_str.strip().split()
            
            # Extract version if specified
            version = None
            version_idx = -1
            for i, part in enumerate(parts):
                if part == "--version" and i+1 < len(parts):
                    try:
                        version = int(parts[i+1])
                        version_idx = i
                        break
                    except ValueError:
                        return f"❌ Invalid version number: {parts[i+1]}"
            
            # Remove version parts from the input if found
            if version_idx >= 0:
                parts = parts[:version_idx] + parts[version_idx+2:]
            
            # Try package path format
            if len(parts) >= 2:
                package_name = parts[0]
                file_path = " ".join(parts[1:])
                
                resolved = resolve_package_path(package_name, file_path)
                if resolved:
                    success, message = restore_backup(resolved, version)
                    return message
            
            # Fall back to standard path search
            filepath = " ".join(parts)
            resolved = resolve_path_or_search(filepath)
            if not resolved:
                return f"❌ File not found: {filepath}"
                
            # Restore the file
            success, message = restore_backup(resolved, version)
            return message
            
        except Exception as e:
            return f"❌ Restore failed: {e}"


class ListBackupsTool(BaseTool):
    name: str = "list_backups"
    description: str = (
        "List available backups for a file. Input can be a single filename, "
        "or 'package_name file_path' to specify a file in a specific ROS2 package."
    )

    def _run(self, input_str: str) -> str:
        from tools import resolve_path_or_search  # Import here to avoid circular imports
        
        try:
            parts = input_str.strip().split()
            
            # Try package path format
            if len(parts) >= 2:
                package_name = parts[0]
                file_path = " ".join(parts[1:])
                
                resolved = resolve_package_path(package_name, file_path)
                if resolved:
                    return self._format_backup_list(resolved, f"{package_name} {file_path}")
            
            # Fall back to standard path search
            filepath = " ".join(parts)
            resolved = resolve_path_or_search(filepath)
            if not resolved:
                return f"❌ File not found: {filepath}"
                
            return self._format_backup_list(resolved, filepath)
            
        except Exception as e:
            return f"❌ Failed to list backups: {e}"
            
    def _format_backup_list(self, file_path, display_path):
        """Format the backup list for display."""
        backups = get_backup_list(file_path)
        
        if not backups:
            return f"❌ No backups found for {display_path}"
            
        result = [f"📂 Available backups for {display_path}:"]
        for i, backup in enumerate(backups):
            timestamp = backup["timestamp"]
            dt = datetime.fromtimestamp(backup["created"])
            readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            tool = backup.get("tool", "unknown")
            result.append(f"  {i+1}. {timestamp} - {readable_time} (by {tool})")
            
        result.append(f"\n💡 To restore a specific version, use: restore {display_path} --version NUMBER")
        return "\n".join(result)


def get_backup_list(file_path):
    """
    Get list of available backups for a file.
    
    Args:
        file_path (str or Path): Path to the file
        
    Returns:
        list: List of backup data dictionaries, sorted newest first
    """
    try:
        file_path = Path(file_path)
        rel_path = file_path.relative_to(Path(WKSPACE))
        file_key = str(rel_path)
        
        backup_dir = Path(WKSPACE) / ".mcp_backups"
        index_path = backup_dir / "backup_index.json"
        
        if not index_path.exists():
            return []
            
        with open(index_path, "r") as f:
            index = json.load(f)
        
        if file_key not in index:
            return []
            
        backups = index[file_key]
        # Sort newest first
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups
    except Exception:
        return []


def restore_backup(file_path, version=None):
    """
    Restore a file from backup.
    
    Args:
        file_path (str or Path): Path to the file
        version (int, optional): Version number to restore (1-based index)
            If None, restores the most recent backup
            
    Returns:
        tuple: (success, message)
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return False, f"❌ File not found: {file_path}"
            
        # Get all backups for this file
        backups = get_backup_list(file_path)
        if not backups:
            return False, f"❌ No backups found for {file_path}"
            
        # Create a fresh backup before restoring (safety first!)
        create_backup(file_path, "prerestore")
        
        # Select the backup to restore
        if version is not None:
            if version < 1 or version > len(backups):
                return False, f"❌ Invalid version {version}. Available versions: 1-{len(backups)}"
            backup = backups[version - 1]
        else:
            # Default to most recent
            backup = backups[0]
        
        # Get the backup path and check if it exists
        backup_path = Path(backup["path"])
        if not backup_path.exists():
            return False, f"❌ Backup file not found: {backup_path}"
        
        # Copy the backup over the original file
        shutil.copy2(backup_path, file_path)
        
        timestamp = backup["timestamp"]
        tool = backup.get("tool", "unknown")
        return True, f"✅ Restored {file_path.name} from backup {timestamp} (created by {tool})"
        
    except Exception as e:
        return False, f"❌ Restore failed: {e}"


class FileBackupTool(BaseTool):
    name: str = "file_backup"
    description: str = "Create a backup of a file. Input is the relative path to the file."

    def _run(self, filepath: str) -> str:
        from tools import resolve_path_or_search  # Import here to avoid circular imports
        
        resolved = resolve_path_or_search(filepath.strip())
        if not resolved or not resolved.exists():
            return f"❌ File not found: {filepath}"
        
        success, message = create_backup(resolved, "manual_backup")
        return message


class FileRestoreTool(BaseTool):
    name: str = "file_restore"
    description: str = (
        "Restore a file from backup. Input can be just a filename to restore the most recent backup, "
        "or 'filename --version N' to restore the Nth most recent backup, "
        "or 'filename --all' to list all available backups."
    )

    def _run(self, input_str: str) -> str:
        from tools import resolve_path_or_search  # Import here to avoid circular imports
        
        try:
            parts = input_str.strip().split()
            filepath = parts[0]
            
            # Check for options
            version = None
            list_all = False
            
            if len(parts) > 1:
                if parts[1] == "--all":
                    list_all = True
                elif parts[1] == "--version" and len(parts) > 2:
                    try:
                        version = int(parts[2])
                    except ValueError:
                        return f"❌ Invalid version number: {parts[2]}"
            
            # Resolve the file path
            resolved = resolve_path_or_search(filepath)
            if not resolved:
                return f"❌ File not found: {filepath}"
                
            # List all backups if requested
            if list_all:
                backups = get_backup_list(resolved)
                if not backups:
                    return f"❌ No backups found for {filepath}"
                    
                result = [f"📂 Available backups for {filepath}:"]
                for i, backup in enumerate(backups):
                    timestamp = backup["timestamp"]
                    dt = datetime.fromtimestamp(backup["created"])
                    readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                    tool = backup.get("tool", "unknown")
                    result.append(f"  {i+1}. {timestamp} - {readable_time} (by {tool})")
                return "\n".join(result)
            
            # Restore from backup
            success, message = restore_backup(resolved, version)
            return message
            
        except Exception as e:
            return f"❌ Restore failed: {e}"
