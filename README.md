# robot_security

A ROS 2 package designed to manage, configure, and dynamically generate SROS2 security keystores, enclaves, and signed permission files for the Smart Wheelchair and TurtleBot3 platforms.

## Features

- **YAML-Based Configuration**: Easily configure the keystore name, storage path, active policy, and the enclaves list.
- **Support for Multiple Policies**: 
  - `wheelchair` policy: A unified SROS2 enclave policy (mapping all nodes to a single identity `/wheelchair`).
  - `individual` policy: An isolated SROS2 multi-enclave policy with specific permissions for the LiDAR driver, DLIO odometry, base controller, and navigation.
  - `turtlebot3` policy: Standard SROS2 policy for simulated and physical TurtleBot3 systems (burger, waffle_pi) in Gazebo and real environments.
- **Idempotent Generation**: Skipping key regeneration if enclave certificates already exist, but cleanly refreshing policies and signatures.
- **Automated Docker Integration**: Automatically generates security keystores during Docker image builds.

---

## Configuration (`config/security_config.yaml`)

Edit the configuration file to customize security parameters:

```yaml
keystore_name: "wheelchair_keystore"

# Path where the keystore files are generated. Defaults to the ROS 2 standard path.
keystore_path: "~/.ros/sros2/keystore"

# Policy type to activate ("wheelchair", "individual", or "turtlebot3")
policy_type: "wheelchair"

policies:
  wheelchair:
    policy_file: "wheelchair_policy.xml"
    enclaves:
      - name: "/wheelchair"
  
  individual:
    policy_file: "individual_policy.xml"
    enclaves:
      - name: "/livox_driver"
      - name: "/dlio_odom_node"
      - name: "/wheelchair2_base_controller"
      - name: "/navigation"

  turtlebot3:
    policy_file: "turtlebot3_policy.xml"
    enclaves:
      - name: "/"
      - name: "/cmd_vel_publisher"
      - name: "/cmd_vel_subscriber"
      - name: "/fake_cmd_vel_publisher"
      - name: "/gazebo"
      - name: "/gazebo_ros_factory"
      - name: "/gazebo_ros_force_system"
      - name: "/turtlebot3_diff_drive"
      - name: "/turtlebot3_imu"
      - name: "/turtlebot3_joint_state"
      - name: "/camera_driver"
      - name: "/robot_state_publisher"
      - name: "/spawn_entity"
      - name: "/turtlebot3"
```

---

## Usage

### 1. Build the Package
Build the package inside your ROS 2 workspace:

```bash
cd ~/wheelchair_ws/ros2_ws
colcon build --packages-select robot_security
source install/setup.bash
```

### 2. Run the Keystore Generator
Execute the keystore generator node:

```bash
ros2 run robot_security generate_keystore
```

The script will:
1. Parse `security_config.yaml`.
2. Initialize SROS2 CA under the target `keystore_path` (if it does not exist).
3. Generate private keys and certificates for each enclave.
4. Parse the active SROS2 XML policy file, map topic/service permissions, and output signed governance and permission files.

---

## Documentation

- [TurtleBot3 SROS2 Guide](docs/turtlebot3_security_README.md): Detailed manual for running secure TurtleBot3 Gazebo simulations and testing authorized vs. unauthorized/rogue publishers.
