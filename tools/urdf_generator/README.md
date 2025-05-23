# ROS2 URDF Generator Wizard

A comprehensive tool for generating accurate URDF files for ROS2 robots with visual preview and validation capabilities. This tool supports differential drive, mecanum drive, and ackermann steering configurations.

## Features

- **Web-based Interface**: Interactive visual editor with real-time robot preview
- **Multiple Drive Types**: Support for differential, mecanum, and ackermann drive systems
- **Sensor Integration**: Easy addition of LiDAR, cameras, and IMU sensors
- **Automatic Calculations**: Proper inertia tensor calculations for all components
- **Real-time Validation**: Instant feedback on configuration validity
- **Multiple Interfaces**: Web GUI, interactive CLI, and programmatic API
- **Export/Import**: Save configurations as JSON for reuse

## Installation

1. **Create the MCP directory structure** (if not already done):
   ```bash
   mkdir -p ~/mcp/tools/urdf_generator
   mkdir -p ~/mcp/bin
   ```

2. **Install the URDF generator**:
   ```bash
   # Save the files to ~/mcp/tools/urdf_generator/
   # - urdf_generator.html (web interface)
   # - urdf_generator.py (backend script)
   # - install.sh (installation script)
   
   cd ~/mcp/tools/urdf_generator
   chmod +x install.sh
   ./install.sh
   ```

3. **Update your PATH** (if not done automatically):
   ```bash
   echo 'export PATH="$PATH:~/mcp/bin"' >> ~/.bashrc
   source ~/.bashrc
   ```

## Usage

### Web Interface (Recommended)

Start the web-based visual editor:

```bash
urdf_generator --web
```

This will:
- Start a local web server (default port 8000)
- Open your browser to the URDF generator interface
- Provide real-time visual feedback as you configure your robot

### Interactive CLI Mode

For command-line configuration:

```bash
urdf_generator --interactive
```

This provides a step-by-step configuration wizard.

### Configuration File Mode

Generate URDF from a saved configuration:

```bash
# Create a URDF from a configuration file
urdf_generator --config my_robot.json --output my_robot.xacro

# Save your current configuration
urdf_generator --interactive --save-config my_robot.json
```

### Validation

Validate existing URDF files:

```bash
urdf_generator --validate existing_robot.urdf
```

## Configuration Format

The tool uses JSON configuration files with the following structure:

```json
{
  "name": "meccabot",
  "driveType": "mecanum",
  "chassis": {
    "length": 0.275,
    "width": 0.145,
    "height": 0.125,
    "mass": 5.0
  },
  "wheels": {
    "radius": 0.05,
    "thickness": 0.03,
    "mass": 0.5,
    "separationLength": 0.175,
    "separationWidth": 0.175,
    "separation": 0.22
  },
  "groundClearance": 0.015,
  "sensors": {
    "lidar": {
      "enabled": true,
      "x": -0.05,
      "y": 0.0,
      "z": 0.14
    },
    "camera": {
      "enabled": false,
      "x": 0.1,
      "y": 0.0,
      "z": 0.1
    },
    "imu": {
      "enabled": false,
      "x": 0.0,
      "y": 0.0,
      "z": 0.0
    }
  }
}
```

## Drive Type Configurations

### Mecanum Drive
- **4 wheels** arranged in a rectangular pattern
- **Omnidirectional movement** capability
- Requires `separationLength` (wheelbase) and `separationWidth` (track width)
- Generates individual control for each wheel

### Differential Drive
- **2 wheels** for propulsion
- **Skid steering** for turning
- Requires `separation` (distance between wheels)
- Common for simple mobile robots

### Ackermann Steering
- **4 wheels** with front steering
- **Car-like kinematics**
- Front wheels can turn for steering
- Rear wheels provide propulsion

## Sensor Integration

The tool supports automatic integration of common robot sensors:

### LiDAR
- Automatically generates appropriate mounting link
- Configurable position relative to robot base
- Includes proper collision and visual geometry

### Camera
- Rectangular sensor geometry
- Configurable mounting position
- Includes optical frame conventions

### IMU
- Small sensor package geometry
- Typically mounted at robot center of mass
- Includes proper orientation conventions

## Generated URDF Features

The generated URDF files include:

1. **Proper Inertial Properties**
   - Calculated inertia tensors for all components
   - Realistic mass distributions
   - Proper center of mass locations

2. **ROS2 Control Integration**
   - Hardware interface declarations
   - Joint command and state interfaces
   - Compatible with ros2_control framework

3. **Gazebo Compatibility**
   - Optional Gazebo plugin configurations
   - Proper material definitions
   - Collision and visual geometries

4. **Best Practices**
   - Consistent naming conventions
   - Proper joint hierarchies
   - Xacro macros for reusability

## Validation Features

The tool performs comprehensive validation:

### Configuration Validation
- ✅ Reasonable dimension checks
- ✅ Wheel placement validation
- ✅ Sensor position verification
- ⚠️ Physics plausibility warnings

### URDF Validation
- ✅ XML syntax validation
- ✅ Required element verification
- ✅ Link/joint relationship checks
- ✅ Naming convention compliance

## Integration with Your Mecca Robot

To generate a URDF for your Mecca robot:

1. **Start with the web interface**:
   ```bash
   urdf_generator --web
   ```

2. **Configure your robot**:
   - Name: `meccabot`
   - Drive Type: `Mecanum Drive`
   - Chassis: 275mm × 145mm × 125mm
   - Wheels: 50mm radius, 30mm thickness
   - Ground Clearance: 15mm
   - Enable LiDAR at position (-50mm, 0, 140mm)

3. **Generate and validate**:
   - Click "Generate URDF"
   - Click "Validate URDF"
   - Download the generated `meccabot.xacro`

4. **Replace your existing URDF**:
   ```bash
   cp meccabot.xacro ~/mecca_ws/src/mecca_description/urdf/
   ```

## Addressing Your Current URDF Issues

Based on your existing `meccabot.xacro`, the generator will help fix:

1. **Inconsistent Joint Names**: The generator ensures consistent naming between wheel joints and ros2_control declarations

2. **Improper Wheel Placement**: Calculates correct wheel positions based on chassis dimensions and separations

3. **Missing Inertial Properties**: Automatically calculates proper inertia tensors for all components

4. **Gazebo Compatibility**: Ensures proper plugin configurations for simulation

## Troubleshooting

### Common Issues

**Port Already in Use**
```bash
urdf_generator --web --port 8001
```

**Permission Denied**
```bash
chmod +x ~/mcp/bin/urdf_generator
```

**Path Not Updated**
```bash
export PATH="$PATH:~/mcp/bin"
source ~/.bashrc
```

### Debugging Generated URDFs

1. **Test in RViz**:
   ```bash
   ros2 launch robot_state_publisher view_robot.launch.py model:=path/to/robot.urdf
   ```

2. **Validate with urdf_parser**:
   ```bash
   check_urdf robot.urdf
   ```

3. **Test in Gazebo**:
   ```bash
   ros2 launch gazebo_ros spawn_entity.py -file robot.urdf -entity robot_name
   ```

## Advanced Usage

### Programmatic Generation

```python
from urdf_generator import URDFGenerator

generator = URDFGenerator()
generator.config['name'] = 'my_robot'
generator.config['driveType'] = 'mecanum'
# ... configure other parameters

urdf_content = generator.generate_urdf()
with open('my_robot.xacro', 'w') as f:
    f.write(urdf_content)
```

### Custom Sensor Positions

Use the web interface to fine-tune sensor positions with real-time visual feedback, or modify the JSON configuration:

```json
{
  "sensors": {
    "lidar": {
      "enabled": true,
      "x": -0.05,  // 50mm behind center
      "y": 0.0,    // centered
      "z": 0.14    // 140mm above base
    }
  }
}
```

## Integration with Test Generator

The URDF generator complements the test stub generator by:

1. **Providing Valid Test Targets**: Generated URDFs are properly structured for testing
2. **Configuration Validation**: Ensures test scenarios are based on valid robot configurations
3. **Consistent Naming**: Generated names follow conventions that test generators can rely on

## Future Enhancements

- **Visual STL Import**: Support for custom chassis and wheel meshes
- **Advanced Kinematics**: Support for more complex joint arrangements
- **Sensor Libraries**: Expanded sensor database with manufacturer-specific models
- **Gazebo World Integration**: Automatic world file generation for testing
- **Hardware Interface Generation**: Automatic C++ hardware interface code generation

## License

Apache License 2.0

## Contributing

Contributions welcome! Areas for improvement:
- Additional drive types (e.g., omnidirectional, tracked)
- More sensor types (e.g., ultrasonic, GPS)
- Advanced material definitions
- Performance optimizations for large robots

---

This URDF generator significantly streamlines robot definition creation and ensures your robots have proper physics properties for both simulation and real-world deployment.
