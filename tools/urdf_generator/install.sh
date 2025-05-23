#!/bin/bash
# Install the ROS2 URDF Generator tools into the MCP tools directory

# Determine MCP root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_ROOT="${HOME}/mcp"

# Create MCP tools directory structure if it doesn't exist
TOOLS_DIR="${MCP_ROOT}/tools/urdf_generator"
mkdir -p "${TOOLS_DIR}"

# Create MCP bin directory if it doesn't exist
BIN_DIR="${MCP_ROOT}/bin"
mkdir -p "${BIN_DIR}"

echo "Installing URDF Generator tools to ${TOOLS_DIR}..."

# Copy the files to the tools directory
cp "${SCRIPT_DIR}/urdf_generator.html" "${TOOLS_DIR}/"
cp "${SCRIPT_DIR}/urdf_generator.py" "${TOOLS_DIR}/"

# Make the Python script executable
chmod +x "${TOOLS_DIR}/urdf_generator.py"

# Create symlink in the MCP bin directory
echo "Creating symlink in ${BIN_DIR}..."
ln -sf "${TOOLS_DIR}/urdf_generator.py" "${BIN_DIR}/urdf_generator"

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
echo "  urdf_generator --web                    # Start web interface"
echo "  urdf_generator --interactive            # Interactive CLI mode"
echo "  urdf_generator --config robot.json     # Generate from config file"
echo "  urdf_generator --validate robot.urdf   # Validate existing URDF"
echo ""
if ! echo "$PATH" | grep -q "${BIN_DIR}"; then
    echo "You need to update your PATH for this session:"
    echo "  export PATH=\"\$PATH:${BIN_DIR}\""
fi
