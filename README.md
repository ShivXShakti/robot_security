# robot_security

A ROS 2 package designed to manage, configure, and dynamically generate SROS2 security keystores, enclaves, and signed permission files for the Smart Wheelchair platform.

## Features

- **YAML-Based Configuration**: Easily configure the keystore name, storage path, active policy, and the enclaves list.
- **Support for Multiple Policies**: 
  - `mobile_robot` policy: A unified SROS2 enclave policy (mapping all nodes to a single identity `/wheelchair`).
  - `individual` policy: An isolated SROS2 multi-enclave policy with specific permissions for the LiDAR driver, DLIO odometry, base controller, and navigation.
- **Idempotent Generation**: Skipping key regeneration if enclave certificates already exist, but cleanly refreshing policies and signatures.
- **Automated Docker Integration**: Automatically generates security keystores during Docker image builds.

---

## Configuration (`config/security_config.yaml`)

Edit the configuration file to customize security parameters:

```yaml
keystore_name: "wheelchair_keystore"

# Path where the keystore files are generated. Defaults to the ROS 2 standard path.
keystore_path: "~/.ros/sros2/keystore"

# Policy type to activate ("mobile_robot" or "individual")
policy_type: "mobile_robot"

policies:
  mobile_robot:
    policy_file: "mobile_robot_policy.xml"
    enclaves:
      - name: "/wheelchair"
  
  individual:
    policy_file: "individual_policy.xml"
    enclaves:
      - name: "/livox_driver"
      - name: "/dlio_odom_node"
      - name: "/wheelchair2_base_controller"
      - name: "/navigation"
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

## Integration in Docker Builds

When building the workspace container, you can bake the SROS2 keystore directly into the image by running:

```dockerfile
# Run the generator script to create the keystore
RUN /bin/bash -c "source /opt/ros/humble/setup.bash && source install/setup.bash && ros2 run robot_security generate_keystore"
```

This populates `/home/container_user/.ros/sros2/keystore` inside the container. Since this location is in the home folder, it is not overwritten when bind-mounting the host's workspace directory over `~/wheelchair2/src`.
