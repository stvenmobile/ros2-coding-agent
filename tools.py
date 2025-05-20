"""
Custom tools for ROS2 MCP agent.
"""
import os
import subprocess
import re
from langchain_core.tools import BaseTool
from typing import List, Optional, Union
from pathlib import Path
import fnmatch
from config import WKSPACE, EXCLUDE_DIRS

# Import backup utilities
from backup_utils import create_backup, FileBackupTool, FileRestoreTool, ListBackupsTool


class WriteFileSingleInputTool(BaseTool):
    name: str = "write_file"
    description: str = "Writes content to a file. Input format: '<relative_path>::<content>'"

    def _run(self, input_str: str) -> str:
        try:
            if "::" not in input_str:
                return "❌ Invalid input. Use format '<relative_path>::<content>'."
            rel_path, content = input_str.split("::", 1)
            target_path = Path(WKSPACE) / rel_path.strip()
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


class AnalyzeFlake8Tool(BaseTool):
    """Analyze Python code with flake8 linter without making changes."""
    name: str = "analyze_flake8"
    description: str = (
        "Analyze Python file with flake8 linter and show issues. "
        "This tool NEVER modifies files, only shows issues."
    )

    def _run(self, filepath: str) -> str:
        target = filepath.strip()
        resolved = resolve_path_or_search(target)
        if not resolved:
            return f"❌ Could not find {target}"

        try:
            # Run flake8 to get all issues
            result = subprocess.run(
                ["flake8", str(resolved)],
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()

            if not output:
                return f"✅ No issues found in {target}."

            # Define auto-fixable issue codes
            auto_fixable_codes = [
                "W291",  # trailing whitespace
                "W292",  # no newline at end of file
                "W293",  # blank line contains whitespace
                "E265",  # block comment should start with '# '
                "E302",  # expected 2 blank lines, found X
                "E303",  # too many blank lines
                "E305",  # expected 2 blank lines after class or function definition
            ]

            # Parse and categorize the flake8 output
            all_issues = []
            auto_fixable_issues = []
            manual_fix_issues = []
            
            for line in output.splitlines():
                all_issues.append(line)
                
                # Check if this is an auto-fixable issue
                if any(code in line for code in auto_fixable_codes):
                    auto_fixable_issues.append(line)
                else:
                    manual_fix_issues.append(line)

            # Create a structured response with clear separation
            response = [f"📋 Flake8 Analysis for {target}:"]
            
            # First list the auto-fixable issues
            if auto_fixable_issues:
                response.append("\n✅ Issues that can be automatically fixed:")
                for issue in auto_fixable_issues:
                    response.append(issue)
                    
            # Then list the manual fix issues
            if manual_fix_issues:
                response.append("\n⚠️ Issues that require manual fixing:")
                for issue in manual_fix_issues:
                    response.append(issue)
            
            # Add a summary section
            response.append(f"\n📊 Summary: {len(auto_fixable_issues)} of {len(all_issues)} issues can be automatically fixed.")
            response.append(f"💡 Use 'fix_flake8' to apply automatic fixes.")
            
            return "\n".join(response)

        except Exception as e:
            return f"❌ Error running flake8: {e}"


class FixFlake8Tool(BaseTool):
    """Apply automatic fixes for flake8 issues in Python code."""
    name: str = "fix_flake8"
    description: str = (
        "Apply automatic fixes for flake8 issues to a Python file. "
        "This will modify the file. Use analyze_flake8 first to see issues."
    )

    def _run(self, filepath: str) -> str:
        target = filepath.strip()
        resolved = resolve_path_or_search(target)
        if not resolved:
            return f"❌ Could not find {target}"

        try:
            # Run flake8 to get all issues
            result = subprocess.run(
                ["flake8", str(resolved)],
                capture_output=True,
                text=True,
            )
            output = result.stdout.strip()

            if not output:
                return f"✅ No issues found in {target}."

            # Define auto-fixable issue codes
            auto_fixable_codes = [
                "W291",  # trailing whitespace
                "W292",  # no newline at end of file
                "W293",  # blank line contains whitespace
                "E265",  # block comment should start with '# '
                "E302",  # expected 2 blank lines, found X
                "E303",  # too many blank lines
                "E305",  # expected 2 blank lines after class or function definition
            ]

            # Parse and categorize the flake8 output
            all_issues = []
            auto_fixable_issues = []
            manual_fix_issues = []
            
            for line in output.splitlines():
                all_issues.append(line)
                
                # Check if this is an auto-fixable issue
                if any(code in line for code in auto_fixable_codes):
                    auto_fixable_issues.append(line)
                else:
                    manual_fix_issues.append(line)

            if not auto_fixable_issues:
                return f"⚠️ No auto-fixable issues found in {target}. All issues require manual fixing."
            
            # Create a backup before modifying
            create_backup(resolved, self.name)
                
            # Apply fixes and get the modification details
            modifications = self._apply_fixes(resolved, auto_fixable_issues)
            
            # Format the modification details for display
            mod_output = []
            if modifications:
                mod_output.append(f"🛠️ Applied {len(modifications)} automatic fixes to {target}:")
                
                for line_num, before, after in modifications:
                    # Format the output to show special characters but be readable
                    before_display = repr(before.rstrip('\n'))[1:-1]  # Display special chars but remove quotes
                    after_display = repr(after.rstrip('\n'))[1:-1]
                    mod_output.append(f"Line {line_num+1}: \"{before_display}\" → \"{after_display}\"")
                
                # Show remaining issues
                remaining = len(all_issues) - len(auto_fixable_issues)
                if remaining > 0:
                    mod_output.append(f"\n⚠️ {remaining} issues remain that need manual fixing:")
                    # List the remaining issues
                    for issue in manual_fix_issues:
                        mod_output.append(issue)
            else:
                mod_output.append(f"⚠️ No changes were applied to {target}.")
                mod_output.append("All issues require manual fixing:")
                mod_output.extend(all_issues)
            
            return "\n".join(mod_output)

        except Exception as e:
            return f"❌ Error running flake8: {e}"
            
    def _apply_fixes(self, file_path, issues):
        """
        Apply automatic fixes to the file.
        
        Returns:
            list: List of tuples (line_num, before, after) showing modifications
        """
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            modifications = []  # Track all modifications with before/after content
            
            # Group issues by line number for efficient processing
            line_issues = {}
            for issue in issues:
                match = re.search(r':(\d+):', issue)
                if match:
                    line_num = int(match.group(1)) - 1  # Convert to 0-based index
                    error_code_match = re.search(r': ([EWF]\d+) ', issue)
                    if error_code_match:
                        error_code = error_code_match.group(1)
                        if line_num not in line_issues:
                            line_issues[line_num] = []
                        line_issues[line_num].append(error_code)
            
            # Apply fixes line by line
            for line_num, error_codes in line_issues.items():
                if line_num < 0 or line_num >= len(lines):
                    continue
                    
                original_line = lines[line_num]
                modified_line = original_line
                
                # Fix whitespace issues
                if "W291" in error_codes:  # trailing whitespace
                    modified_line = modified_line.rstrip() + '\n'
                    
                if "W293" in error_codes:  # blank line contains whitespace
                    if modified_line.strip() == '':
                        modified_line = '\n'
                
                # Fix comment formatting
                if "E265" in error_codes:  # block comment should start with '# '
                    if modified_line.strip().startswith('#') and not modified_line.strip().startswith('# '):
                        modified_line = modified_line.replace('#', '# ', 1)
                
                # Fix end of file newline
                if "W292" in error_codes and line_num == len(lines) - 1:  # no newline at end of file
                    if not modified_line.endswith('\n'):
                        modified_line = modified_line + '\n'
                
                # If we made any changes to this line, record the modification
                if modified_line != original_line:
                    lines[line_num] = modified_line
                    modifications.append((line_num, original_line, modified_line))
            
            # Fix blank line issues (requires looking at surrounding lines)
            blank_line_fixes = []
            for issue in issues:
                if "E302" in issue or "E305" in issue:  # blank line requirements
                    match = re.search(r':(\d+):', issue)
                    if match:
                        line_num = int(match.group(1)) - 1
                        blank_line_fixes.append((line_num, "E302" if "E302" in issue else "E305"))
                        
            for line_num, code in blank_line_fixes:
                if line_num < 0 or line_num >= len(lines):
                    continue
                    
                if code == "E302":  # expected 2 blank lines before class/function
                    # Insert blank lines before this line
                    blank_count = 0
                    check_line = line_num - 1
                    while check_line >= 0 and lines[check_line].strip() == '':
                        blank_count += 1
                        check_line -= 1
                    
                    if blank_count < 2:
                        # Record the state before modification
                        context_before = "".join(lines[max(0, line_num-3):line_num+1])
                        
                        # Insert needed blank lines
                        lines.insert(line_num, '\n' * (2 - blank_count))
                        
                        # Record the state after modification
                        context_after = "".join(lines[max(0, line_num-3):line_num+3])
                        modifications.append((line_num, context_before, context_after))
                        
                elif code == "E305":  # expected 2 blank lines after class/function
                    # Check for blank lines after this line
                    blank_count = 0
                    check_line = line_num + 1
                    while check_line < len(lines) and lines[check_line].strip() == '':
                        blank_count += 1
                        check_line += 1
                    
                    if blank_count < 2:
                        # Record the state before modification
                        context_before = "".join(lines[line_num:min(line_num+3, len(lines))])
                        
                        # Insert needed blank lines
                        lines.insert(line_num + 1, '\n' * (2 - blank_count))
                        
                        # Record the state after modification
                        context_after = "".join(lines[line_num:min(line_num+5, len(lines))])
                        modifications.append((line_num, context_before, context_after))
            
            # Fix too many blank lines (E303)
            for issue in issues:
                if "E303" in issue:  # too many blank lines
                    match = re.search(r':(\d+):', issue)
                    if match:
                        line_num = int(match.group(1)) - 1
                        
                        # Extract how many blank lines were found
                        count_match = re.search(r"too many blank lines \((\d+)\)", issue)
                        if count_match:
                            found_lines = int(count_match.group(1))
                            desired_lines = 1  # Usually we want 1 blank line
                            
                            # Record the state before modification
                            context_before = "".join(lines[max(0, line_num-found_lines-1):line_num+1])
                            
                            # Count blank lines before this line
                            blank_lines = []
                            check_line = line_num - 1
                            while check_line >= 0 and lines[check_line].strip() == '':
                                blank_lines.append(check_line)
                                check_line -= 1
                            
                            # Remove excess blank lines
                            if len(blank_lines) > desired_lines:
                                for _ in range(len(blank_lines) - desired_lines):
                                    del lines[blank_lines.pop()]
                            
                            # Record the state after modification
                            context_after = "".join(lines[max(0, line_num-desired_lines-1):line_num+1])
                            modifications.append((line_num, context_before, context_after))
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.writelines(lines)
                
            return modifications
                
        except Exception as e:
            print(f"Error fixing file: {e}")
            return []


class AnalyzePydocstyleTool(BaseTool):
    """Analyze Python docstrings with pydocstyle without making changes."""
    name: str = "analyze_docstrings"
    description: str = (
        "Analyze Python file docstrings using pydocstyle and show issues. "
        "This tool NEVER modifies files, only shows issues."
    )

    def _run(self, filepath: str) -> str:
        filepath = filepath.strip()
        full_path = resolve_path_or_search(filepath)
        if not full_path or not full_path.exists():
            return f"❌ File not found: {filepath}"

        # Run pydocstyle
        result = subprocess.run(
            ["pydocstyle", "--convention=pep257", str(full_path)],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()
        
        # Debug output
        print(f"PYDOCSTYLE RAW OUTPUT for {full_path}:")
        print(output)
        print(f"Return code: {result.returncode}")

        if result.returncode == 0:
            return f"✅ No docstring issues found in {filepath}. ✅ Completed."

        # Load original lines - DO NOT MODIFY THE FILE
        try:
            with open(full_path) as f:
                lines = f.readlines()
        except Exception as e:
            return f"❌ Failed to read file: {e}"

        # Initialize lists for issues
        general_issues = []
        d401_suggestions = []

        # Process the output to identify D401 issues and other issues
        current_file = None
        current_method = None
        current_lineno = None
        
        for line in output.splitlines():
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for a line with file path, line number, and method info
            file_line_match = re.search(r"(.+):(\d+) in (.+):", line)
            if file_line_match:
                current_file = file_line_match.group(1)
                current_lineno = int(file_line_match.group(2))
                current_method = file_line_match.group(3)
                continue
            
            # Check for D401 error lines
            d401_match = re.search(r"D401: First line should be in imperative mood \(perhaps '([^']+)', not '([^']+)'\)", line)
            if d401_match and current_lineno is not None:
                suggested_word = d401_match.group(1)  # e.g., 'Determine'
                current_word = d401_match.group(2)   # e.g., 'Determines'
                
                # Search for the docstring line with the current word
                found = False
                for offset in range(-2, 5):  # Check a few lines around the reported line
                    check_line = current_lineno + offset - 1  # Convert to 0-based index
                    if 0 <= check_line < len(lines):
                        doc_line = lines[check_line]
                        # Check if this line contains the word we need to replace
                        if current_word in doc_line:
                            # Create proposed fix
                            proposed_line = doc_line.replace(current_word, suggested_word, 1)
                            d401_suggestions.append((check_line, doc_line, proposed_line, current_lineno))
                            found = True
                            break
                
                if not found:
                    general_issues.append(f"Line {current_lineno}: D401: Unable to locate exact line for '{current_word}' in {current_method}")
            
            # Check for other error codes
            elif "D" in line:  # Other docstring issues
                other_error_match = re.search(r"(D\d+): (.+)", line)
                if other_error_match and current_lineno is not None:
                    error_code = other_error_match.group(1)
                    error_desc = other_error_match.group(2)
                    general_issues.append(f"Line {current_lineno}: {error_code}: {error_desc} in {current_method}")

        # Build the response with clear separation of issue types
        result_lines = []
        result_lines.append(f"📋 Docstring Analysis for {filepath}:")

        # First show D401 issues that can be auto-fixed
        if d401_suggestions:
            result_lines.append("\n✅ Issues that can be automatically fixed:")
            for lineno, original, proposed, reported_line in d401_suggestions:
                # Format with line numbers for display (convert back to 1-based for display)
                original_display = original.strip().replace('"', '\\"')  # Escape quotes in the string
                proposed_display = proposed.strip().replace('"', '\\"')
                result_lines.append(f"Line {lineno+1}: D401: \"{original_display}\" → \"{proposed_display}\"")

        # Then show general issues that need manual fixing
        if general_issues:
            result_lines.append("\n⚠️ Issues that require manual fixing:")
            result_lines.extend(general_issues)

        # Summary section
        result_lines.append(f"\n📊 Summary: {len(d401_suggestions)} of {len(d401_suggestions) + len(general_issues)} issues can be automatically fixed.")
        
        if d401_suggestions:
            result_lines.append("💡 Use 'fix_docstrings' to apply these fixes.")
        else:
            result_lines.append("⚠️ All issues require manual fixing.")
            
        result_lines.append("✅ Analysis completed.")
        
        return "\n".join(result_lines)


class FixPydocstyleTool(BaseTool):
    """Fix Python docstring issues with pydocstyle."""
    name: str = "fix_docstrings"
    description: str = (
        "Apply auto-fixes to docstring issues in a Python file. "
        "This will modify the file. Currently supports fixing D401 issues (imperative mood)."
    )

    def _run(self, filepath: str) -> str:
        filepath = filepath.strip()
        full_path = resolve_path_or_search(filepath)
        if not full_path or not full_path.exists():
            return f"❌ File not found: {filepath}"

        # Run pydocstyle
        result = subprocess.run(
            ["pydocstyle", "--convention=pep257", str(full_path)],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()
        
        # Debug output
        print(f"PYDOCSTYLE RAW OUTPUT for {full_path}:")
        print(output)
        print(f"Return code: {result.returncode}")

        if result.returncode == 0:
            return f"✅ No docstring issues found in {filepath}. ✅ Completed."

        # Load original lines
        try:
            with open(full_path) as f:
                lines = f.readlines()
        except Exception as e:
            return f"❌ Failed to read file: {e}"

        # Initialize lists for issues
        general_issues = []
        d401_suggestions = []

        # Process the output to identify D401 issues and other issues
        current_file = None
        current_method = None
        current_lineno = None
        
        for line in output.splitlines():
            # Skip empty lines
            if not line.strip():
                continue
            
            # Check for a line with file path, line number, and method info
            file_line_match = re.search(r"(.+):(\d+) in (.+):", line)
            if file_line_match:
                current_file = file_line_match.group(1)
                current_lineno = int(file_line_match.group(2))
                current_method = file_line_match.group(3)
                continue
            
            # Check for D401 error lines
            d401_match = re.search(r"D401: First line should be in imperative mood \(perhaps '([^']+)', not '([^']+)'\)", line)
            if d401_match and current_lineno is not None:
                suggested_word = d401_match.group(1)  # e.g., 'Determine'
                current_word = d401_match.group(2)   # e.g., 'Determines'
                
                # Search for the docstring line with the current word
                found = False
                for offset in range(-2, 5):  # Check a few lines around the reported line
                    check_line = current_lineno + offset - 1  # Convert to 0-based index
                    if 0 <= check_line < len(lines):
                        doc_line = lines[check_line]
                        # Check if this line contains the word we need to replace
                        if current_word in doc_line:
                            # Create proposed fix
                            proposed_line = doc_line.replace(current_word, suggested_word, 1)
                            d401_suggestions.append((check_line, doc_line, proposed_line, current_lineno))
                            found = True
                            break
                
                if not found:
                    general_issues.append(f"Line {current_lineno}: D401: Unable to locate exact line for '{current_word}' in {current_method}")
            
            # Check for other error codes
            elif "D" in line:  # Other docstring issues
                other_error_match = re.search(r"(D\d+): (.+)", line)
                if other_error_match and current_lineno is not None:
                    error_code = other_error_match.group(1)
                    error_desc = other_error_match.group(2)
                    general_issues.append(f"Line {current_lineno}: {error_code}: {error_desc} in {current_method}")

        # Check if we have any D401 fixes to apply
        if not d401_suggestions:
            if general_issues:
                return "\n⚠️ No automatically fixable D401 issues found.\n" + \
                       f"⚠️ {len(general_issues)} issue(s) still require manual fixing. ✅ Completed."
            else:
                return "\n✅ No issues found that need fixing. File is compliant. ✅ Completed."
                
        # Create a backup before modifying
        create_backup(full_path, self.name)
        
        # Make a copy of the suggestions before modifications
        applied_fixes = []
        
        for lineno, original, proposed, _ in d401_suggestions:
            lines[lineno] = proposed
            original_display = original.strip().replace('"', '\\"')
            proposed_display = proposed.strip().replace('"', '\\"')
            applied_fixes.append((lineno+1, original_display, proposed_display))

        try:
            with open(full_path, "w") as f:
                f.writelines(lines)
        except Exception as e:
            return f"❌ Failed to write changes to file: {e}"

        # Construct the response showing what was fixed and what still needs attention
        modifications_output = [f"🛠️ Applied D401 fixes to {filepath}:"]
        for line_num, before, after in applied_fixes:
            modifications_output.append(f"Line {line_num}: \"{before}\" → \"{after}\"")

        if general_issues:
            modifications_output.append("\n⚠️ Remaining issues that need manual fixing:")
            modifications_output.extend(general_issues)

        modifications_output.append(f"\n✅ {len(d401_suggestions)} line(s) fixed automatically.")
        modifications_output.append(f"⚠️ {len(general_issues)} issue(s) still need manual attention. ✅ Completed.")
        
        return "\n".join(modifications_output)


# For backward compatibility - keep the old tool names but make them analysis-only
class RunFlake8Tool(BaseTool):
    name: str = "run_flake8"
    description: str = (
        "DEPRECATED - Use analyze_flake8 or fix_flake8 instead. "
        "Run flake8 linter on a specified Python file. "
        "Optionally add 'propose_only' or 'write_changes' to control output."
    )

    def _run(self, filepath: str) -> str:
        # Extract optional mode (default is propose_only)
        args = filepath.strip().split()
        target = args[0]
        mode = args[1] if len(args) > 1 else "propose_only"

        # Create instances of the new tools
        analyze_tool = AnalyzeFlake8Tool()
        fix_tool = FixFlake8Tool()

        # Redirect to the appropriate tool based on mode
        if mode == "propose_only":
            return analyze_tool._run(target)
        elif mode == "write_changes":
            return fix_tool._run(target)
        else:
            return f"❌ Unknown mode: {mode}. Use 'propose_only' or 'write_changes'."


class RunDocstyleTool(BaseTool):
    name: str = "run_docstyle"
    description: str = (
        "DEPRECATED - Use analyze_docstrings or fix_docstrings instead. "
        "Run pydocstyle on a Python file. Append 'propose_only' to only show suggestions, "
        "or 'write_changes' to apply safe fixes to docstrings (D401 rule only)."
    )

    def _run(self, filepath: str) -> str:
        # Default mode
        mode = "propose_only"  # Default to propose_only for safety
        filepath = filepath.strip()

        # Parse mode
        if "::" in filepath:
            filepath, mode = filepath.split("::", 1)
            filepath = filepath.strip()
            mode = mode.strip()
        elif " " in filepath:
            parts = filepath.split()
            filepath = parts[0]
            if len(parts) > 1 and parts[-1] in ["propose_only", "write_changes"]:
                mode = parts[-1]

        # Create instances of the new tools
        analyze_tool = AnalyzePydocstyleTool()
        fix_tool = FixPydocstyleTool()

        # Redirect to the appropriate tool based on mode
        if mode == "propose_only":
            return analyze_tool._run(filepath)
        elif mode == "write_changes":
            return fix_tool._run(filepath)
        else:
            return f"❌ Unknown mode: {mode}. Use 'propose_only' or 'write_changes'."
