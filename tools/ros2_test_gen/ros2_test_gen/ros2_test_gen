#!/usr/bin/env python3
"""
ROS2 Test Generator

A command-line tool for generating and running test stubs for ROS2 packages.
This tool operates on ROS2 workspaces but resides in the MCP tools directory.

Usage:
    ros2_test_gen [command] [options] [package_name]

Commands:
    generate    Generate test stubs for a package
    run         Run tests for a package
    list        List packages in the workspace

Options:
    --workspace=PATH  Path to the ROS2 workspace (default: current directory)
    --all            Process all packages in the workspace
    --interactive    Run in interactive mode (default)
    --dry-run        Show what would be generated without writing files
    --verbose        Display detailed information during execution
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET


def find_mcp_root():
    """Find the root of the MCP directory."""
    # Default MCP root
    mcp_root = Path.home() / 'mcp'
    if not mcp_root.exists():
        print(f"Warning: MCP root directory not found at {mcp_root}")
        print("Creating directory structure...")
        mcp_root.mkdir(parents=True, exist_ok=True)
        (mcp_root / 'tools').mkdir(exist_ok=True)
        (mcp_root / 'bin').mkdir(exist_ok=True)
    
    return mcp_root


def find_workspace_root(path=None):
    """Find the root of the ROS2 workspace."""
    # If path is provided, use it
    if path:
        workspace_path = Path(path)
        src_path = workspace_path / 'src'
        if src_path.exists() and src_path.is_dir():
            return workspace_path
        else:
            print(f"Error: {workspace_path} does not appear to be a ROS2 workspace (no src directory)")
            sys.exit(1)
    
    # Otherwise, try to find it from the current directory
    current_path = Path.cwd()
    
    while current_path != Path('/'):
        src_path = current_path / 'src'
        if src_path.exists() and src_path.is_dir():
            return current_path
        current_path = current_path.parent
    
    # If we got here, we're not in a workspace
    print("Error: Not in a ROS2 workspace (could not find src directory)")
    print("Use --workspace=PATH to specify the workspace path")
    sys.exit(1)


def list_workspaces():
    """List all ROS2 workspaces in the home directory."""
    home = Path.home()
    
    # Look for directories ending with _ws that contain a src directory
    workspaces = []
    
    for item in home.iterdir():
        if item.is_dir() and item.name.endswith('_ws'):
            src_path = item / 'src'
            if src_path.exists() and src_path.is_dir():
                workspaces.append(item)
    
    return workspaces


def list_packages(workspace_path):
    """List all packages in the workspace."""
    packages = []
    src_path = workspace_path / 'src'
    
    # Check each directory in src
    for item in src_path.iterdir():
        if item.is_dir():
            package_xml_path = item / 'package.xml'
            if package_xml_path.exists():
                try:
                    tree = ET.parse(package_xml_path)
                    root = tree.getroot()
                    # Try different tag names for package name (name or n)
                    package_name_elem = root.find('name') or root.find('n')
                    if package_name_elem is not None:
                        package_name = package_name_elem.text
                        build_type = "Unknown"
                        
                        # Try to determine build type
                        if (item / 'CMakeLists.txt').exists():
                            build_type = "CMake"
                        elif (item / 'setup.py').exists():
                            build_type = "Python"
                        
                        packages.append((package_name, str(item), build_type))
                except Exception as e:
                    print(f"Warning: Error parsing {package_xml_path}: {e}")
    
    return packages


def print_package_list(packages):
    """Print the list of packages in a formatted table."""
    if not packages:
        print("No packages found in workspace")
        return
    
    # Calculate column widths
    name_width = max(len(p[0]) for p in packages) + 2
    path_width = max(len(p[1]) for p in packages) + 2
    type_width = max(len(p[2]) for p in packages) + 2
    
    # Print header
    print(f"{'Package Name':<{name_width}} {'Path':<{path_width}} {'Build Type':<{type_width}}")
    print(f"{'-' * (name_width - 1)} {'-' * (path_width - 1)} {'-' * (type_width - 1)}")
    
    # Print each package
    for package_name, package_path, build_type in sorted(packages):
        print(f"{package_name:<{name_width}} {package_path:<{path_width}} {build_type:<{type_width}}")


def print_workspace_list(workspaces):
    """Print the list of workspaces."""
    if not workspaces:
        print("No ROS2 workspaces found in home directory")
        return
    
    print("Available ROS2 workspaces:")
    for i, workspace in enumerate(workspaces, 1):
        package_count = len(list_packages(workspace))
        print(f"{i}. {workspace.name} ({package_count} packages)")
    
    print("\nUse --workspace=PATH to specify a workspace")


def get_test_generator_path():
    """Get the path to the test_stub_generator.py script."""
    # First, try to find it relative to this script
    script_dir = Path(__file__).parent
    generator_path = script_dir / "test_stub_generator.py"
    
    if generator_path.exists():
        return generator_path
    
    # Otherwise, check in the MCP tools directory
    mcp_root = find_mcp_root()
    generator_path = mcp_root / "tools" / "ros2_test_gen" / "test_stub_generator.py"
    
    if generator_path.exists():
        return generator_path
    
    print(f"Error: Test stub generator not found at {generator_path}")
    sys.exit(1)


def install_dependencies():
    """Install required dependencies if they're not already installed."""
    try:
        import docstring_parser
    except ImportError:
        print("Installing required dependency: docstring-parser")
        subprocess.run([sys.executable, "-m", "pip", "install", "docstring-parser"])
    
    try:
        import pytest
    except ImportError:
        print("Installing required dependency: pytest")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest"])


def run_generator(package_path, interactive, dry_run, verbose):
    """Run the test stub generator on a package."""
    generator_path = get_test_generator_path()
    
    cmd = [sys.executable, str(generator_path), str(package_path)]
    
    if interactive:
        cmd.append("--interactive")
    else:
        cmd.append("--all")
        
    if dry_run:
        cmd.append("--dry-run")
        
    if verbose:
        cmd.append("--verbose")
    
    return subprocess.run(cmd)


def run_tests(package_path):
    """Run the tests for a package."""
    generator_path = get_test_generator_path()
    
    cmd = [sys.executable, str(generator_path), str(package_path), "--run"]
    return subprocess.run(cmd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ROS2 Test Generator")
    
    # Global options
    parser.add_argument("--workspace", help="Path to the ROS2 workspace")
    
    # Commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate test stubs for a package")
    generate_parser.add_argument("package", nargs="?", help="Package name or path")
    generate_parser.add_argument("--all", action="store_true", help="Process all packages in the workspace")
    generate_parser.add_argument("--interactive", action="store_true", help="Run in interactive mode", default=True)
    generate_parser.add_argument("--non-interactive", action="store_false", dest="interactive", help="Run in non-interactive mode")
    generate_parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without writing files")
    generate_parser.add_argument("--verbose", action="store_true", help="Display detailed information during execution")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run tests for a package")
    run_parser.add_argument("package", nargs="?", help="Package name or path")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List packages in the workspace")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Default to help if no command is specified
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Install dependencies
    install_dependencies()
    
    # List workspaces if no workspace is specified and we're not in one
    if args.command == "list" and not args.workspace:
        try:
            workspace_path = find_workspace_root()
            print(f"Current workspace: {workspace_path}")
            packages = list_packages(workspace_path)
            print_package_list(packages)
        except SystemExit:
            # If find_workspace_root exited, list available workspaces
            workspaces = list_workspaces()
            print_workspace_list(workspaces)
        return
    
    # Find the workspace root
    workspace_path = find_workspace_root(args.workspace)
    print(f"Using workspace: {workspace_path}")
    
    # Handle the commands
    if args.command == "list":
        packages = list_packages(workspace_path)
        print_package_list(packages)
    
    elif args.command == "generate":
        if args.all:
            # Process all packages
            packages = list_packages(workspace_path)
            for package_name, package_path, _ in packages:
                print(f"\nProcessing package: {package_name}")
                run_generator(package_path, args.interactive, args.dry_run, args.verbose)
        elif args.package:
            # Process a single package
            # Determine if args.package is a name or a path
            package_path = Path(args.package)
            if not package_path.is_absolute():
                # Try to find the package by name
                packages = list_packages(workspace_path)
                found = False
                for name, path, _ in packages:
                    if name == args.package:
                        package_path = Path(path)
                        found = True
                        break
                if not found:
                    print(f"Error: Package '{args.package}' not found in workspace")
                    sys.exit(1)
            
            run_generator(package_path, args.interactive, args.dry_run, args.verbose)
        else:
            print("Error: No package specified. Use --all to process all packages or specify a package name/path.")
            sys.exit(1)
    
    elif args.command == "run":
        if args.package:
            # Determine if args.package is a name or a path
            package_path = Path(args.package)
            if not package_path.is_absolute():
                # Try to find the package by name
                packages = list_packages(workspace_path)
                found = False
                for name, path, _ in packages:
                    if name == args.package:
                        package_path = Path(path)
                        found = True
                        break
                if not found:
                    print(f"Error: Package '{args.package}' not found in workspace")
                    sys.exit(1)
            
            run_tests(package_path)
        else:
            print("Error: No package specified for the run command.")
            sys.exit(1)


if __name__ == "__main__":
    main()
