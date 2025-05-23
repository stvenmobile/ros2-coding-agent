# ROS2 Test Stub Generator

A tool for automatically generating test stubs for ROS2 Python packages. This tool is part of the MCP (Mechatronics Control Project) toolset and operates on ROS2 workspaces from an external location, keeping your workspaces clean.

## Features

- Analyzes Python modules to identify untested public functions and classes
- Generates pytest-compatible test skeletons with proper setup
- Supports both standalone functions and class methods
- Extracts parameter types and docstrings to create appropriate test cases
- Interactive mode to select which modules to process
- Includes a test runner to execute generated tests

## Installation

Run the installation script to set up the tool:

```bash
./install.sh
```

This will:
1. Install the test generator in your `~/mcp/tools/ros2_test_gen` directory
2. Create symlinks in the `~/mcp/bin` directory
3. Install required dependencies
4. Add the MCP bin directory to your PATH (in .bashrc)

## Directory Structure

The tool maintains a clean separation between tooling and workspaces:

```
~/mcp/                  # MCP root directory (tools, not ROS2 code)
  ├── tools/
  │   └── ros2_test_gen/   # Test generator tools
  └── bin/                 # Executable symlinks

~/mecca_ws/             # Your ROS2 workspace (unmodified)
  └── src/
      └── ... packages ...
```

## Usage

```bash
# List all packages in the current workspace
ros2_test_gen list

# Specify a different workspace
ros2_test_gen --workspace=~/another_ws list

# Generate test stubs for a specific package
ros2_test_gen generate <package_name>

# Generate test stubs for all packages in the workspace
ros2_test_gen generate --all

# Show what would be generated without writing files
ros2_test_gen generate <package_name> --dry-run

# Run tests for a specific package
ros2_test_gen run <package_name>
```

## Generated Tests

The generated test stubs follow best practices for ROS2 testing:

- Organized using the pytest framework
- Follow the Arrange-Act-Assert pattern
- Include basic, edge case, and exception handling tests
- Include proper docstrings and type annotations
- Have appropriate class fixtures for setup and teardown

## Example

For a function like:

```python
def calculate_velocity(linear_speed: float, angular_rate: float) -> dict:
    """Calculate wheel velocities for a mecanum drive robot.
    
    Args:
        linear_speed: The linear speed in m/s
        angular_rate: The angular rate in rad/s
        
    Returns:
        A dictionary with wheel velocities
    """
    # Function implementation
```

The generator will create test stubs like:

```python
def test_calculate_velocity_basic():
    """Test basic functionality of calculate_velocity().
    
    This test verifies the basic functionality of the function.
    """
    # Arrange
    linear_speed = 1.0
    angular_rate = 0.5
    
    # Act
    result = calculate_velocity(linear_speed=linear_speed, angular_rate=angular_rate)
    
    # Assert
    # TODO: Add assertions here
    
def test_calculate_velocity_edge_case():
    """Test edge cases of calculate_velocity().
    
    This test verifies the behavior of the function with edge case inputs.
    """
    # Arrange
    # TODO: Set up edge case test preconditions here
    
    # Act & Assert
    # TODO: Test edge cases (empty inputs, boundary values, etc.)
```

## License

Apache License 2.0
