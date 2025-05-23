#!/usr/bin/env python3
"""
ROS2 URDF Generator Backend - Fixed Positioning

This script provides command-line interface and validation capabilities for the URDF generator
with corrected wheel and chassis positioning logic.

Usage:
    urdf_generator.py --config config.json --output robot.xacro
    urdf_generator.py --validate existing_robot.urdf
    urdf_generator.py --interactive
    urdf_generator.py --web
"""

import json
import sys
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import math
from typing import Dict, Any, List, Tuple
import webbrowser
import http.server
import socketserver
import threading


class URDFGenerator:
    """Generate URDF files for ROS2 robots with proper validation and corrected positioning."""
    
    def __init__(self):
        """Initialize the URDF generator."""
        self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default robot configuration with corrected positioning."""
        return {
            "name": "meccabot",
            "driveType": "mecanum",
            "chassis": {
                "length": 0.275,
                "width": 0.145,
                "height": 0.125,
                "mass": 5.0
            },
            "wheels": {
                "radius": 0.050,  # 50mm
                "thickness": 0.03,
                "mass": 0.5,
                "separationLength": 0.175,
                "separationWidth": 0.175,
                "separation": 0.22,
                "zOffset": 0.017  # 17mm above chassis bottom
            },
            "groundClearance": 0.033,  # 33mm
            "sensors": {
                "lidar": {"enabled": False, "x": -0.05, "y": 0.0, "z": 0.14},
                "camera": {"enabled": False, "x": 0.1, "y": 0.0, "z": 0.1},
                "imu": {"enabled": False, "x": 0.0, "y": 0.0, "z": 0.0}
            }
        }
    
    def load_config(self, config_path: str) -> None:
        """Load configuration from a JSON file."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def save_config(self, config_path: str) -> None:
        """Save current configuration to a JSON file."""
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def validate_config(self) -> List[str]:
        """Validate the robot configuration and return warnings."""
        warnings = []
        
        # Check for reasonable dimensions
        if self.config["chassis"]["length"] < 0.1 or self.config["chassis"]["length"] > 2.0:
            warnings.append("Chassis length seems unrealistic")
        
        if self.config["wheels"]["radius"] < 0.01 or self.config["wheels"]["radius"] > 0.5:
            warnings.append("Wheel radius seems unrealistic")
        
        # Check wheel positioning logic
        wheel_bottom = self.config["groundClearance"] + self.config["wheels"]["zOffset"] - self.config["wheels"]["radius"]
        if abs(wheel_bottom) > 0.001:  # Should be very close to 0 (ground level)
            warnings.append(f"Wheels don't touch ground properly (wheel bottom at {wheel_bottom*1000:.1f}mm)")
        
        # Check wheel separation vs chassis size
        if self.config["driveType"] == "mecanum":
            if self.config["wheels"]["separationWidth"] > self.config["chassis"]["width"]:
                warnings.append("Wheel track width exceeds chassis width")
            if self.config["wheels"]["separationLength"] > self.config["chassis"]["length"]:
                warnings.append("Wheelbase exceeds chassis length")
        
        # Check sensor positions
        if self.config["sensors"]["lidar"]["enabled"]:
            max_reach = max(self.config["chassis"]["length"], self.config["chassis"]["width"]) / 2
            lidar_distance = math.sqrt(
                self.config["sensors"]["lidar"]["x"] ** 2 + 
                self.config["sensors"]["lidar"]["y"] ** 2
            )
            if lidar_distance > max_reach * 1.5:
                warnings.append("LiDAR position is far from chassis center")
        
        return warnings
    
    def calculate_inertia(self, mass: float, dimensions: Dict[str, float], shape: str) -> Dict[str, float]:
        """Calculate inertia tensor for different shapes."""
        if shape == "box":
            x, y, z = dimensions["x"], dimensions["y"], dimensions["z"]
            return {
                "ixx": (1/12) * mass * (y**2 + z**2),
                "iyy": (1/12) * mass * (x**2 + z**2),
                "izz": (1/12) * mass * (x**2 + y**2),
                "ixy": 0.0,
                "ixz": 0.0,
                "iyz": 0.0
            }
        elif shape == "cylinder":
            radius, length = dimensions["radius"], dimensions["length"]
            return {
                "ixx": (1/12) * mass * (3 * radius**2 + length**2),
                "iyy": (1/12) * mass * (3 * radius**2 + length**2),
                "izz": (1/2) * mass * radius**2,
                "ixy": 0.0,
                "ixz": 0.0,
                "iyz": 0.0
            }
        else:
            # Default to small inertia values
            return {
                "ixx": 0.001, "iyy": 0.001, "izz": 0.001,
                "ixy": 0.0, "ixz": 0.0, "iyz": 0.0
            }
    
    def generate_urdf(self) -> str:
        """Generate the complete URDF string."""
        urdf_parts = []
        
        # XML header and robot declaration
        urdf_parts.append('<?xml version="1.0"?>')
        urdf_parts.append(f'<robot xmlns:xacro="http://ros.org/wiki/xacro" name="{self.config["name"]}_robot">')
        urdf_parts.append('')
        
        # Include files
        urdf_parts.append('  <xacro:include filename="inertial_macros.xacro"/>')
        if self.config["driveType"] == "differential":
            urdf_parts.append('  <xacro:include filename="gazebo_control.xacro"/>')
        urdf_parts.append('')
        
        # Parameters with corrected positioning
        urdf_parts.extend(self._generate_parameters())
        urdf_parts.append('')
        
        # Materials
        urdf_parts.extend(self._generate_materials())
        urdf_parts.append('')
        
        # Base link and chassis
        urdf_parts.extend(self._generate_base_links())
        urdf_parts.append('')
        
        # Wheel macro and instantiations
        urdf_parts.extend(self._generate_wheel_macro())
        urdf_parts.extend(self._generate_wheel_instantiations())
        urdf_parts.append('')
        
        # Sensors
        if any(sensor["enabled"] for sensor in self.config["sensors"].values()):
            urdf_parts.extend(self._generate_sensor_links())
            urdf_parts.append('')
        
        # ROS2 Control
        urdf_parts.extend(self._generate_ros2_control())
        urdf_parts.append('')
        
        urdf_parts.append('</robot>')
        
        return '\n'.join(urdf_parts)
    
    def _generate_parameters(self) -> List[str]:
        """Generate xacro parameters with corrected positioning logic."""
        params = [
            '  <!-- Parameters -->',
            f'  <xacro:property name="wheel_radius" value="{self.config["wheels"]["radius"]}"/>',
            f'  <xacro:property name="wheel_thickness" value="{self.config["wheels"]["thickness"]}"/>',
            f'  <xacro:property name="chassis_length" value="{self.config["chassis"]["length"]}"/>',
            f'  <xacro:property name="chassis_width" value="{self.config["chassis"]["width"]}"/>',
            f'  <xacro:property name="chassis_height" value="{self.config["chassis"]["height"]}"/>',
            f'  <xacro:property name="ground_clearance" value="{self.config["groundClearance"]}"/>',
            f'  <xacro:property name="wheel_z_offset" value="{self.config["wheels"]["zOffset"]}"/>',
            '',
            '  <!-- Derived positioning parameters -->',
            '  <xacro:property name="chassis_half_length" value="${chassis_length/2}"/>',
            '  <xacro:property name="chassis_half_width" value="${chassis_width/2}"/>',
            '  <xacro:property name="chassis_z_offset" value="${ground_clearance + chassis_height/2}"/>',
        ]
        
        if self.config["driveType"] == "mecanum":
            params.extend([
                '',
                f'  <xacro:property name="wheel_separation_length" value="{self.config["wheels"]["separationLength"]}"/>',
                f'  <xacro:property name="wheel_separation_width" value="{self.config["wheels"]["separationWidth"]}"/>',
                '  <xacro:property name="wheel_x_offset" value="${wheel_separation_length/2}"/>',
                '  <xacro:property name="wheel_y_offset" value="${wheel_separation_width/2}"/>',
            ])
        elif self.config["driveType"] == "differential":
            params.extend([
                '',
                f'  <xacro:property name="wheel_separation" value="{self.config["wheels"]["separation"]}"/>',
                '  <xacro:property name="wheel_y_offset" value="${wheel_separation/2}"/>',
            ])
        
        return params
    
    def _generate_materials(self) -> List[str]:
        """Generate material definitions."""
        return [
            '  <!-- Define Colors -->',
            '  <material name="white">',
            '    <color rgba="1 1 1 1" />',
            '  </material>',
            '',
            '  <material name="orange">',
            '    <color rgba="1 0.3 0.1 1" />',
            '  </material>',
            '',
            '  <material name="red">',
            '    <color rgba="1 0 0 1" />',
            '  </material>',
            '',
            '  <material name="blue">',
            '    <color rgba="0.0 0.0 0.8 1.0" />',
            '  </material>',
            '',
            '  <material name="green">',
            '    <color rgba="0.2 0.9 0.2 1"/>',
            '  </material>',
            '',
            '  <material name="darkgrey">',
            '    <color rgba="0.1 0.1 0.1 1.0" />',
            '  </material>',
            '',
            '  <material name="grey">',
            '    <color rgba="0.5 0.5 0.5 1.0" />',
            '  </material>',
            '',
            '  <material name="black">',
            '    <color rgba="0 0 0 1" />',
            '  </material>',
        ]
    
    def _generate_base_links(self) -> List[str]:
        """Generate base link and chassis with corrected positioning."""
        chassis_mass = self.config["chassis"]["mass"]
        chassis_inertia = self.calculate_inertia(
            chassis_mass,
            {
                "x": self.config["chassis"]["length"],
                "y": self.config["chassis"]["width"],
                "z": self.config["chassis"]["height"]
            },
            "box"
        )
        
        return [
            '  <!-- Base link -->',
            '  <link name="base_link">',
            '    <inertial>',
            '      <origin xyz="0 0 0" rpy="0 0 0"/>',
            '      <mass value="0.1"/>',
            '      <inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.001"/>',
            '    </inertial>',
            '  </link>',
            '',
            '  <joint name="base_to_chassis" type="fixed">',
            '    <parent link="base_link"/>',
            '    <child link="chassis_link"/>',
            '    <origin xyz="0 0 ${chassis_z_offset}" rpy="0 0 0"/>',
            '  </joint>',
            '',
            '  <!-- Chassis -->',
            '  <link name="chassis_link">',
            '    <inertial>',
            f'      <origin xyz="0 0 0" rpy="0 0 0"/>',
            f'      <mass value="{chassis_mass}"/>',
            '      <inertia',
            f'        ixx="{chassis_inertia["ixx"]:.6f}"',
            f'        ixy="{chassis_inertia["ixy"]:.6f}" ixz="{chassis_inertia["ixz"]:.6f}"',
            f'        iyy="{chassis_inertia["iyy"]:.6f}"',
            f'        iyz="{chassis_inertia["iyz"]:.6f}"',
            f'        izz="{chassis_inertia["izz"]:.6f}"/>',
            '    </inertial>',
            '    <visual>',
            f'      <origin xyz="0 0 0" rpy="0 0 0"/>',
            '      <geometry>',
            '        <box size="${chassis_length} ${chassis_width} ${chassis_height}"/>',
            '      </geometry>',
            '      <material name="green"/>',
            '    </visual>',
            '    <collision>',
            f'      <origin xyz="0 0 0" rpy="0 0 0"/>',
            '      <geometry>',
            '        <box size="${chassis_length} ${chassis_width} ${chassis_height}"/>',
            '      </geometry>',
            '    </collision>',
            '  </link>',
        ]
    
    def _generate_wheel_macro(self) -> List[str]:
        """Generate wheel macro definition."""
        wheel_mass = self.config["wheels"]["mass"]
        wheel_inertia = self.calculate_inertia(
            wheel_mass,
            {
                "radius": self.config["wheels"]["radius"],
                "length": self.config["wheels"]["thickness"]
            },
            "cylinder"
        )
        
        return [
            '  <!-- Wheel macro -->',
            '  <xacro:macro name="wheel" params="name x y z rpy">',
            '    <joint name="${name}_joint" type="continuous">',
            '      <parent link="chassis_link"/>',
            '      <child link="${name}"/>',
            '      <origin xyz="${x} ${y} ${z}" rpy="${rpy}"/>',
            '      <axis xyz="0 1 0"/>',
            '    </joint>',
            '    <link name="${name}">',
            '      <inertial>',
            '        <origin xyz="0 0 0" rpy="0 0 0"/>',
            f'        <mass value="{wheel_mass}"/>',
            '        <inertia',
            f'          ixx="{wheel_inertia["ixx"]:.6f}" ixy="{wheel_inertia["ixy"]:.6f}" ixz="{wheel_inertia["ixz"]:.6f}"',
            f'          iyy="{wheel_inertia["iyy"]:.6f}" iyz="{wheel_inertia["iyz"]:.6f}"',
            f'          izz="{wheel_inertia["izz"]:.6f}"/>',
            '      </inertial>',
            '      <visual>',
            '        <origin xyz="0 0 0" rpy="1.5708 0 0"/>',
            '        <geometry>',
            '          <cylinder radius="${wheel_radius}" length="${wheel_thickness}"/>',
            '        </geometry>',
            '        <material name="grey"/>',
            '      </visual>',
            '      <collision>',
            '        <origin xyz="0 0 0" rpy="1.5708 0 0"/>',
            '        <geometry>',
            '          <cylinder radius="${wheel_radius}" length="${wheel_thickness}"/>',
            '        </geometry>',
            '      </collision>',
            '    </link>',
            '  </xacro:macro>',
        ]
    
    def _generate_wheel_instantiations(self) -> List[str]:
        """Generate wheel instantiations with corrected positioning."""
        if self.config["driveType"] == "mecanum":
            return [
                '',
                '  <!-- Instantiate wheels -->',
                '  <xacro:wheel name="front_left_wheel"',
                '               x="${wheel_x_offset}"',
                '               y="${wheel_y_offset + wheel_thickness/2}"',
                '               z="${wheel_z_offset}"',
                '               rpy="0 0 0"/>',
                '',
                '  <xacro:wheel name="front_right_wheel"',
                '               x="${wheel_x_offset}"',
                '               y="${-(wheel_y_offset + wheel_thickness/2)}"',
                '               z="${wheel_z_offset}"',
                '               rpy="0 0 0"/>',
                '',
                '  <xacro:wheel name="rear_left_wheel"',
                '               x="${-wheel_x_offset}"',
                '               y="${wheel_y_offset + wheel_thickness/2}"',
                '               z="${wheel_z_offset}"',
                '               rpy="0 0 0"/>',
                '',
                '  <xacro:wheel name="rear_right_wheel"',
                '               x="${-wheel_x_offset}"',
                '               y="${-(wheel_y_offset + wheel_thickness/2)}"',
                '               z="${wheel_z_offset}"',
                '               rpy="0 0 0"/>',
            ]
        elif self.config["driveType"] == "differential":
            return [
                '',
                '  <!-- Instantiate wheels -->',
                '  <xacro:wheel name="left_wheel"',
                '               x="0"',
                '               y="${wheel_y_offset + wheel_thickness/2}"',
                '               z="${wheel_z_offset}"',
                '               rpy="0 0 0"/>',
                '',
                '  <xacro:wheel name="right_wheel"',
                '               x="0"',
                '               y="${-(wheel_y_offset + wheel_thickness/2)}"',
                '               z="${wheel_z_offset}"',
                '               rpy="0 0 0"/>',
            ]
        return []
    
    def _generate_sensor_links(self) -> List[str]:
        """Generate sensor links and joints."""
        sensor_links = []
        base_z = self.config["groundClearance"] + self.config["chassis"]["height"]
        
        if self.config["sensors"]["lidar"]["enabled"]:
            lidar = self.config["sensors"]["lidar"]
            sensor_links.extend([
                '  <!-- LiDAR -->',
                '  <link name="lidar_link">',
                '    <visual>',
                '      <geometry>',
                '        <cylinder length="0.05" radius="0.04"/>',
                '      </geometry>',
                '      <material name="red"/>',
                '    </visual>',
                '    <collision>',
                '      <geometry>',
                '        <cylinder length="0.05" radius="0.04"/>',
                '      </geometry>',
                '    </collision>',
                '    <inertial>',
                '      <mass value="0.1"/>',
                '      <inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.001"/>',
                '    </inertial>',
                '  </link>',
                '  <joint name="lidar_joint" type="fixed">',
                '    <parent link="base_link"/>',
                '    <child link="lidar_link"/>',
                f'    <origin xyz="{lidar["x"]} {lidar["y"]} {lidar["z"] + base_z}" rpy="0 0 0"/>',
                '  </joint>',
                '',
            ])
        
        if self.config["sensors"]["camera"]["enabled"]:
            camera = self.config["sensors"]["camera"]
            sensor_links.extend([
                '  <!-- Camera -->',
                '  <link name="camera_link">',
                '    <visual>',
                '      <geometry>',
                '        <box size="0.025 0.05 0.015"/>',
                '      </geometry>',
                '      <material name="blue"/>',
                '    </visual>',
                '    <collision>',
                '      <geometry>',
                '        <box size="0.025 0.05 0.015"/>',
                '      </geometry>',
                '    </collision>',
                '    <inertial>',
                '      <mass value="0.05"/>',
                '      <inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.001"/>',
                '    </inertial>',
                '  </link>',
                '  <joint name="camera_joint" type="fixed">',
                '    <parent link="base_link"/>',
                '    <child link="camera_link"/>',
                f'    <origin xyz="{camera["x"]} {camera["y"]} {camera["z"] + base_z}" rpy="0 0 0"/>',
                '  </joint>',
                '',
            ])
        
        if self.config["sensors"]["imu"]["enabled"]:
            imu = self.config["sensors"]["imu"]
            sensor_links.extend([
                '  <!-- IMU -->',
                '  <link name="imu_link">',
                '    <visual>',
                '      <geometry>',
                '        <box size="0.02 0.02 0.01"/>',
                '      </geometry>',
                '      <material name="orange"/>',
                '    </visual>',
                '    <collision>',
                '      <geometry>',
                '        <box size="0.02 0.02 0.01"/>',
                '      </geometry>',
                '    </collision>',
                '    <inertial>',
                '      <mass value="0.01"/>',
                '      <inertia ixx="0.001" ixy="0.0" ixz="0.0" iyy="0.001" iyz="0.0" izz="0.001"/>',
                '    </inertial>',
                '  </link>',
                '  <joint name="imu_joint" type="fixed">',
                '    <parent link="base_link"/>',
                '    <child link="imu_link"/>',
                f'    <origin xyz="{imu["x"]} {imu["y"]} {imu["z"] + base_z}" rpy="0 0 0"/>',
                '  </joint>',
                '',
            ])
        
        return sensor_links
    
    def _generate_ros2_control(self) -> List[str]:
        """Generate ROS2 control configuration."""
        robot_name = self.config["name"]
        hardware_class = f"{robot_name}_hardware_interface/{robot_name.capitalize()}Hardware"
        
        if self.config["driveType"] == "mecanum":
            return [
                '  <ros2_control name="MecanumRobot" type="system">',
                '    <hardware>',
                f'      <plugin>{hardware_class}</plugin>',
                '    </hardware>',
                '',
                '    <!-- Joint 1: Front Left Wheel -->',
                '    <joint name="front_left_wheel_joint">',
                '      <command_interface name="velocity"/>',
                '      <state_interface name="velocity"/>',
                '      <state_interface name="position"/>',
                '    </joint>',
                '',
                '    <!-- Joint 2: Front Right Wheel -->',
                '    <joint name="front_right_wheel_joint">',
                '      <command_interface name="velocity"/>',
                '      <state_interface name="velocity"/>',
                '      <state_interface name="position"/>',
                '    </joint>',
                '',
                '    <!-- Joint 3: Rear Left Wheel -->',
                '    <joint name="rear_left_wheel_joint">',
                '      <command_interface name="velocity"/>',
                '      <state_interface name="velocity"/>',
                '      <state_interface name="position"/>',
                '    </joint>',
                '',
                '    <!-- Joint 4: Rear Right Wheel -->',
                '    <joint name="rear_right_wheel_joint">',
                '      <command_interface name="velocity"/>',
                '      <state_interface name="velocity"/>',
                '      <state_interface name="position"/>',
                '    </joint>',
                '  </ros2_control>',
            ]
        elif self.config["driveType"] == "differential":
            return [
                '  <ros2_control name="DifferentialRobot" type="system">',
                '    <hardware>',
                f'      <plugin>{hardware_class}</plugin>',
                '    </hardware>',
                '',
                '    <!-- Left Wheel Joint -->',
                '    <joint name="left_wheel_joint">',
                '      <command_interface name="velocity"/>',
                '      <state_interface name="velocity"/>',
                '      <state_interface name="position"/>',
                '    </joint>',
                '',
                '    <!-- Right Wheel Joint -->',
                '    <joint name="right_wheel_joint">',
                '      <command_interface name="velocity"/>',
                '      <state_interface name="velocity"/>',
                '      <state_interface name="position"/>',
                '    </joint>',
                '  </ros2_control>',
            ]
        return []
    
    def validate_urdf_xml(self, urdf_content: str) -> Tuple[bool, List[str]]:
        """Validate URDF XML structure."""
        errors = []
        warnings = []
        
        try:
            # Parse XML
            root = ET.fromstring(urdf_content)
            
            # Check root element
            if root.tag != 'robot':
                errors.append("Root element must be 'robot'")
                return False, errors
            
            # Check for required attributes
            if 'name' not in root.attrib:
                warnings.append("Robot should have a 'name' attribute")
            
            # Find all links and joints
            links = root.findall('.//link')
            joints = root.findall('.//joint')
            
            if len(links) < 2:
                errors.append("Robot must have at least 2 links")
            
            # Check link structure
            for link in links:
                if 'name' not in link.attrib:
                    errors.append("All links must have a 'name' attribute")
                
                # Check for inertial properties (warn if missing)
                if link.find('inertial') is None:
                    warnings.append(f"Link '{link.get('name', 'unnamed')}' missing inertial properties")
            
            # Check joint structure
            for joint in joints:
                if 'name' not in joint.attrib:
                    errors.append("All joints must have a 'name' attribute")
                if 'type' not in joint.attrib:
                    errors.append("All joints must have a 'type' attribute")
                
                # Check for parent and child
                if joint.find('parent') is None:
                    errors.append(f"Joint '{joint.get('name', 'unnamed')}' missing parent")
                if joint.find('child') is None:
                    errors.append(f"Joint '{joint.get('name', 'unnamed')}' missing child")
            
            # Check for kinematic loops (basic check)
            link_names = [link.get('name') for link in links]
            parent_child_pairs = []
            for joint in joints:
                parent_elem = joint.find('parent')
                child_elem = joint.find('child')
                if parent_elem is not None and child_elem is not None:
                    parent = parent_elem.get('link')
                    child = child_elem.get('link')
                    parent_child_pairs.append((parent, child))
                    
                    # Check if links exist
                    if parent not in link_names:
                        errors.append(f"Parent link '{parent}' not found")
                    if child not in link_names:
                        errors.append(f"Child link '{child}' not found")
            
        except ET.ParseError as e:
            errors.append(f"XML parsing error: {str(e)}")
            return False, errors
        
        return len(errors) == 0, errors + warnings
    
    def start_web_interface(self, port: int = 8000, host: str = "0.0.0.0") -> None:
        """Start the web interface for interactive URDF generation."""
        
        # Determine the directory to serve files from
        # If running from a symlink, resolve to the actual script location
        script_path = Path(__file__).resolve()
        serve_directory = script_path.parent
        
        # Check if we're running from a symlink (like in /mcp/bin)
        # and the HTML file isn't in the current directory
        html_file = serve_directory / "urdf_generator.html"
        if not html_file.exists():
            # Look for the HTML file in the tools directory
            tools_dir = serve_directory.parent / "tools" / "urdf_generator"
            if (tools_dir / "urdf_generator.html").exists():
                serve_directory = tools_dir
        
        class URDFHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                # Set the directory to serve files from
                super().__init__(*args, directory=str(serve_directory), **kwargs)
            
            def do_GET(self):
                """Handle GET requests with proper index file handling."""
                if self.path == '/':
                    # Redirect root to index.html
                    self.send_response(302)
                    self.send_header('Location', '/index.html')
                    self.end_headers()
                    return
                elif self.path == '/index.html':
                    # Redirect index.html to urdf_generator.html
                    self.send_response(302)
                    self.send_header('Location', '/urdf_generator.html')
                    self.end_headers()
                    return
                else:
                    # Handle all other requests normally
                    super().do_GET()
        
        print(f"Serving files from: {serve_directory}")
        print(f"Files available:")
        for file in serve_directory.iterdir():
            if file.is_file():
                print(f"  {file.name}")
        
        try:
            # Get the local IP address for display
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            with socketserver.TCPServer((host, port), URDFHandler) as httpd:
                print(f"Starting URDF Generator web interface...")
                print(f"  Root access:    http://localhost:{port}/")
                print(f"  Direct access:  http://localhost:{port}/urdf_generator.html")
                print(f"  Network root:   http://{local_ip}:{port}/")
                print(f"  Network direct: http://{local_ip}:{port}/urdf_generator.html")
                
                # Try to open browser on local machine
                try:
                    webbrowser.open(f'http://localhost:{port}/')
                except:
                    pass  # Might fail on headless servers
                
                print(f"Server listening on {host}:{port}")
                print("Press Ctrl+C to stop the server")
                httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down web server...")
        except Exception as e:
            print(f"Error starting web server: {e}")
    
    def interactive_config(self) -> None:
        """Interactive command-line configuration."""
        print("=== ROS2 URDF Generator - Interactive Mode ===\n")
        
        # Robot name
        name = input(f"Robot name [{self.config['name']}]: ").strip()
        if name:
            self.config['name'] = name
        
        # Drive type
        print("\nDrive Types:")
        print("1. Mecanum Drive (4 wheels)")
        print("2. Differential Drive (2 wheels)")
        print("3. Ackermann Steering (4 wheels)")
        
        drive_choice = input("Select drive type [1]: ").strip()
        drive_types = {'1': 'mecanum', '2': 'differential', '3': 'ackermann'}
        if drive_choice in drive_types:
            self.config['driveType'] = drive_types[drive_choice]
        
        # Chassis dimensions
        print(f"\nChassis Dimensions (current: {self.config['chassis']['length']}m x {self.config['chassis']['width']}m x {self.config['chassis']['height']}m)")
        
        length = input(f"Length (m) [{self.config['chassis']['length']}]: ").strip()
        if length:
            self.config['chassis']['length'] = float(length)
            
        width = input(f"Width (m) [{self.config['chassis']['width']}]: ").strip()
        if width:
            self.config['chassis']['width'] = float(width)
            
        height = input(f"Height (m) [{self.config['chassis']['height']}]: ").strip()
        if height:
            self.config['chassis']['height'] = float(height)
            
        mass = input(f"Chassis mass (kg) [{self.config['chassis']['mass']}]: ").strip()
        if mass:
            self.config['chassis']['mass'] = float(mass)
        
        # Wheel configuration
        print(f"\nWheel Configuration:")
        print(f"Current: radius={self.config['wheels']['radius']}m, thickness={self.config['wheels']['thickness']}m")
        print(f"Ground clearance: {self.config['groundClearance']}m, Wheel Z-offset: {self.config['wheels']['zOffset']}m")
        
        radius = input(f"Wheel radius (m) [{self.config['wheels']['radius']}]: ").strip()
        if radius:
            self.config['wheels']['radius'] = float(radius)
            
        thickness = input(f"Wheel thickness (m) [{self.config['wheels']['thickness']}]: ").strip()
        if thickness:
            self.config['wheels']['thickness'] = float(thickness)
            
        ground_clearance = input(f"Ground clearance (m) [{self.config['groundClearance']}]: ").strip()
        if ground_clearance:
            self.config['groundClearance'] = float(ground_clearance)
            
        wheel_z_offset = input(f"Wheel Z-offset above chassis bottom (m) [{self.config['wheels']['zOffset']}]: ").strip()
        if wheel_z_offset:
            self.config['wheels']['zOffset'] = float(wheel_z_offset)
        
        # Sensors
        print("\nSensors:")
        
        lidar_enabled = input("Include LiDAR? (y/n) [n]: ").strip().lower()
        self.config['sensors']['lidar']['enabled'] = lidar_enabled == 'y'
        
        camera_enabled = input("Include camera? (y/n) [n]: ").strip().lower()
        self.config['sensors']['camera']['enabled'] = camera_enabled == 'y'
        
        imu_enabled = input("Include IMU? (y/n) [n]: ").strip().lower()
        self.config['sensors']['imu']['enabled'] = imu_enabled == 'y'


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='ROS2 URDF Generator with Fixed Positioning')
    
    parser.add_argument('--config', help='Load configuration from JSON file')
    parser.add_argument('--output', help='Output URDF file path')
    parser.add_argument('--validate', help='Validate existing URDF file')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    parser.add_argument('--web', action='store_true', help='Start web interface')
    parser.add_argument('--port', type=int, default=8000, help='Port for web interface')
    parser.add_argument('--host', default='0.0.0.0', help='Host address for web interface (default: 0.0.0.0 for all interfaces)')
    parser.add_argument('--save-config', help='Save current configuration to JSON file')
    
    args = parser.parse_args()
    
    generator = URDFGenerator()
    
    # Load configuration if specified
    if args.config:
        if Path(args.config).exists():
            generator.load_config(args.config)
            print(f"Loaded configuration from {args.config}")
        else:
            print(f"Configuration file {args.config} not found")
            sys.exit(1)
    
    # Validate existing URDF
    if args.validate:
        if not Path(args.validate).exists():
            print(f"URDF file {args.validate} not found")
            sys.exit(1)
        
        with open(args.validate, 'r') as f:
            urdf_content = f.read()
        
        is_valid, messages = generator.validate_urdf_xml(urdf_content)
        
        if is_valid:
            print("✅ URDF is valid")
        else:
            print("❌ URDF validation failed")
        
        for message in messages:
            print(f"  - {message}")
        
        sys.exit(0 if is_valid else 1)
    
    # Start web interface
    if args.web:
        generator.start_web_interface(args.port, args.host)
        return
    
    # Interactive configuration
    if args.interactive:
        generator.interactive_config()
    
    # Validate configuration
    warnings = generator.validate_config()
    if warnings:
        print("⚠️  Configuration warnings:")
        for warning in warnings:
            print(f"  - {warning}")
        print()
    
    # Generate URDF
    urdf_content = generator.generate_urdf()
    
    # Validate generated URDF
    is_valid, messages = generator.validate_urdf_xml(urdf_content)
    if not is_valid:
        print("❌ Generated URDF is invalid:")
        for message in messages:
            print(f"  - {message}")
        sys.exit(1)
    
    # Save configuration if requested
    if args.save_config:
        generator.save_config(args.save_config)
        print(f"Configuration saved to {args.save_config}")
    
    # Output URDF
    if args.output:
        with open(args.output, 'w') as f:
            f.write(urdf_content)
        print(f"URDF saved to {args.output}")
    else:
        print(urdf_content)


if __name__ == "__main__":
    main()
