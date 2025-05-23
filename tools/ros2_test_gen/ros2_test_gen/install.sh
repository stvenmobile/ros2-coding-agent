#!/bin/bash
# Install the ROS2 Test Generator tools into the MCP tools directory

# Determine MCP root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_ROOT="${HOME}/mcp"

# Create MCP tools directory structure if it doesn't exist
TOOLS_DIR="${MCP_ROOT}/tools/ros2_test_gen"
mkdir -p "${TOOLS_DIR}"

# Create MCP bin directory if it doesn't exist
BIN_DIR="${MCP_ROOT}/bin"
mkdir -p "${BIN_DIR}"

echo "Installing test generation tools to ${TOOLS_DIR}..."

# Copy the files to the tools directory
cp "${SCRIPT_DIR}/test_stub_generator.py" "${TOOLS_DIR}/"
cp "${SCRIPT_DIR}/ros2_test_gen" "${TOOLS_DIR}/"
cp "${SCRIPT_DIR}/test_test_stub_generator.py" "${TOOLS_DIR}/"
cp "${SCRIPT_DIR}/README.md" "${TOOLS_DIR}/"

# Make scripts executable
chmod +x "${TOOLS_DIR}/test_stub_generator.py"
chmod +x "${TOOLS_DIR}/ros2_test_gen"

# Create symlink in the MCP bin directory
echo "Creating symlink in ${BIN_DIR}..."
ln -sf "${TOOLS_DIR}/ros2_test_gen" "${BIN_DIR}/ros2_test_gen"

# Install dependencies
echo "Installing dependencies..."
pip install docstring-parser pytest

# Add MCP bin to PATH in .bashrc if not already there
if ! grep -q "PATH=\"\$PATH:${BIN_DIR}\"" "${HOME}/.bashrc"; then
    echo "# Add MCP bin directory to PATH" >> "${HOME}/.bashrc"
    echo "export PATH=\"\$PATH:${BIN_DIR}\"" >> "${HOME}/.bashrc"
    echo "Added ${BIN_DIR} to PATH in .bashrc"
    echo "Please run 'source ~/.bashrc' to update your current session"
fi

echo "Installation complete!"
echo ""
echo "Usage:"
echo "  ros2_test_gen list                  # List all packages in the workspace"
echo "  ros2_test_gen generate <package>    # Generate test stubs for a package"
echo "  ros2_test_gen run <package>         # Run tests for a package"
echo ""
if ! echo "$PATH" | grep -q "${BIN_DIR}"; then
    echo "You need to update your PATH for this session:"
    echo "  export PATH=\"\$PATH:${BIN_DIR}\""
fi
