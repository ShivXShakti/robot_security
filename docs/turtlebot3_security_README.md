# Complete SROS2 Security Implementation Guide for ROS 2 Humble & TurtleBot3

This document is a comprehensive, step-by-step manual for implementing ROS 2 Security (SROS2 — OMG DDS-SECURITY 1.1 Standard) from scratch. It explains security policy design, keystore management, Access Control (Topics, Services, Actions), Untrusted CA Certificate Rejection, and practical testing using TurtleBot3 and Gazebo simulations.

---

## Table of Contents
1. [Key Concepts & Critical Security Principles](#key-concepts--critical-security-principles)
2. [Step-by-Step SROS2 Implementation from Scratch](#step-by-step-sros2-implementation-from-scratch)
   - [Step 1: Initialize the Keystore](#step-1-initialize-the-keystore)
   - [Step 2: Create `policy.xml` Rules](#step-2-create-policyxml-rules)
   - [Step 3: Generate Artifacts & Sign Permissions](#step-3-generate-artifacts--sign-permissions)
3. [How to Accommodate Other Nodes, Topics, Services & Actions](#how-to-accommodate-other-nodes-topics-services--actions)
   - [1. Topics (Publishers & Subscribers)](#1-topics-publishers--subscribers)
   - [2. Services (Clients & Servers)](#2-services-clients--servers)
   - [3. Actions (Action Clients & Action Servers)](#3-actions-action-clients--action-servers)
4. [Creating Security Test Enclaves](#creating-security-test-enclaves)
   - [A. Unauthorized Enclave in Same Keystore (Access Control Test)](#a-unauthorized-enclave-in-same-keystore-access-control-test)
   - [B. Untrusted / Rogue Keystore (PKI CA Certificate Test)](#b-untrusted--rogue-keystore-pki-ca-certificate-test)
5. [Testing TurtleBot3 in Gazebo Simulation](#testing-turtlebot3-in-gazebo-simulation)
   - [Step 0: Cleanup Old Gazebo Processes](#step-0-cleanup-old-gazebo-processes)
   - [Terminal 1: Launch Secure Gazebo Simulation](#terminal-1-launch-secure-gazebo-simulation)
   - [Terminal 2: Test Authorized Publisher (Robot Moves)](#terminal-2-test-authorized-publisher-robot-moves-)
   - [Terminal 3: Test Unauthorized Enclave Publisher (Blocked)](#terminal-3-test-unauthorized-enclave-publisher-blocked-)
   - [Terminal 4: Test Rogue CA Publisher (Handshake Rejected)](#terminal-4-test-rogue-ca-publisher-handshake-rejected-)
6. [Layer-wise Robot Security Guide](#layer-wise-robot-security-guide)
7. [Troubleshooting & Common Pitfalls](#troubleshooting--common-pitfalls)

---

## Key Concepts & Critical Security Principles

> [!IMPORTANT]
> **1. FastDDS Topic Wildcards Require Slashes (`*/*`, `rq/*`, `rr/*`, `rt/*`)**  
> FastDDS Security fnmatch evaluator treats `/` as a strict path delimiter. Writing `<topic>*</topic>` matches simple topic names (e.g. `rosout`), but **fails to match** slash-delimited topic and service names like `rt/cmd_vel`, `rq/spawn_entityRequest`, or `rr/spawn_entityReply`. You MUST include `<topic>*/*</topic>`, `<topic>rt/*</topic>`, `<topic>rq/*</topic>`, and `<topic>rr/*</topic>`.

> [!WARNING]
> **2. Domain ID Matching in Governance vs Permissions**  
> Both `governance.xml` and `permissions.xml` must agree on the domain ID (e.g. `<id>56</id>`). If `governance.xml` specifies `<id>56</id>` and `permissions.xml` specifies `<id>0-232</id>`, FastDDS Security rejects remote participant handshakes with `Not found a rule allowing to use the domain_id`.

> [!NOTE]
> **3. S/MIME PKCS#7 Permission Signing (`permissions.p7s`)**  
> Editing `permissions.xml` manually does NOT update `permissions.p7s`. DDS Security enforces signed PKCS#7 envelopes. Always re-sign permissions using `python3 src/turtlebot3_security/sign_keystore_permissions.py <keystore_path>` after modifying permissions.

---

## Step-by-Step SROS2 Implementation from Scratch

### Step 1: Initialize the Keystore
From your workspace root (`turtlebot3_ws`), initialize the primary keystore:
```bash
source /opt/ros/humble/setup.bash
cd /home/robot/Documents/turtlebot3_ws

# Create the master security keystore
ros2 security create_keystore src/test_keystore
```

---

### Step 2: Create `policy.xml` Rules
File location: `/home/robot/Documents/turtlebot3_ws/src/policy.xml`

```xml
<policy version="0.2.0">
  <enclaves>
    <!-- Root Enclave (Gazebo & Core Nodes) -->
    <enclave path="/">
      <profiles>
        <profile node="*" ns="/">
          <services reply="ALLOW" request="ALLOW"><service>*</service></services>
          <topics publish="ALLOW"><topic>*</topic><topic>*/*</topic><topic>rt/*</topic></topics>
          <topics subscribe="ALLOW"><topic>*</topic><topic>*/*</topic><topic>rt/*</topic></topics>
        </profile>
      </profiles>
    </enclave>

    <!-- Authorized CmdVel Publisher Enclave -->
    <enclave path="/cmd_vel_publisher">
      <profiles>
        <profile node="cmd_vel_publisher" ns="/">
          <services reply="ALLOW" request="ALLOW"><service>*</service></services>
          <topics publish="ALLOW">
            <topic>cmd_vel</topic>
            <topic>parameter_events</topic>
            <topic>rosout</topic>
          </topics>
        </profile>
      </profiles>
    </enclave>

    <!-- Authorized CmdVel Subscriber / Robot Enclave -->
    <enclave path="/cmd_vel_subscriber">
      <profiles>
        <profile node="cmd_vel_subscriber" ns="/">
          <services reply="ALLOW" request="ALLOW"><service>*</service></services>
          <topics subscribe="ALLOW"><topic>*</topic><topic>*/*</topic><topic>rt/*</topic></topics>
          <topics publish="ALLOW"><topic>*</topic><topic>*/*</topic><topic>rt/*</topic></topics>
        </profile>
      </profiles>
    </enclave>

    <!-- Unauthorized Fake Publisher Enclave (NO cmd_vel publish permission) -->
    <enclave path="/fake_cmd_vel_publisher">
      <profiles>
        <profile node="fake_cmd_vel_publisher" ns="/">
          <services reply="ALLOW" request="ALLOW"><service>*</service></services>
          <topics publish="ALLOW">
            <topic>parameter_events</topic>
            <topic>rosout</topic>
          </topics>
        </profile>
      </profiles>
    </enclave>
  </enclaves>
</policy>
```

---

### Step 3: Generate Artifacts & Sign Permissions
```bash
ros2 security generate_artifacts -k src/test_keystore -p src/policy.xml
python3 src/turtlebot3_security/sign_keystore_permissions.py src/test_keystore
```

---

## How to Accommodate Other Nodes, Topics, Services & Actions

### 1. Topics (Publishers & Subscribers)
In `src/policy.xml`:
```xml
<profile node="my_node_name" ns="/">
  <topics publish="ALLOW">
    <topic>cmd_vel</topic>
    <topic>tf</topic>
    <topic>rosout</topic>
    <topic>parameter_events</topic>
  </topics>
  <topics subscribe="ALLOW">
    <topic>odom</topic>
    <topic>scan</topic>
  </topics>
</profile>
```

### 2. Services (Clients & Servers)
Services use request topics (`rq/service_nameRequest`) and reply topics (`rr/service_nameReply`).
- **Server**: `<services reply="ALLOW"><service>~/my_service</service></services>`
- **Client**: `<services request="ALLOW"><service>/server_node/my_service</service></services>`

### 3. Actions (Action Clients & Action Servers)
An action combines 3 services (`send_goal`, `get_result`, `cancel_goal`) and 2 topics (`feedback`, `status`).

- **Action Server Policy**:
  ```xml
  <services reply="ALLOW" request="ALLOW"><service>~/navigate_to_pose/*</service></services>
  <topics publish="ALLOW">
    <topic>navigate_to_pose/_action/feedback</topic>
    <topic>navigate_to_pose/_action/status</topic>
  </topics>
  ```
- **Action Client Policy**:
  ```xml
  <services request="ALLOW" reply="ALLOW"><service>/nav_server/navigate_to_pose/*</service></services>
  <topics subscribe="ALLOW">
    <topic>navigate_to_pose/_action/feedback</topic>
    <topic>navigate_to_pose/_action/status</topic>
  </topics>
  ```

---

## Creating Security Test Enclaves

### A. Unauthorized Enclave in Same Keystore (Access Control Test)
We create enclave `/fake_cmd_vel_publisher` in `src/test_keystore` (signed by the official Root CA).  
Its `permissions.xml` **omits** `<topic>rt/cmd_vel</topic>` under `<publish>`:
```bash
ros2 security create_enclave src/test_keystore /fake_cmd_vel_publisher
python3 src/turtlebot3_security/sign_keystore_permissions.py src/test_keystore
```
*Result*: Node authenticates with the network, but FastDDS Security **blocks topic packets** on `cmd_vel`.

---

### B. Untrusted / Rogue Keystore (PKI CA Certificate Test)
We create a separate keystore (`rogue_keystore`) signed by a **different, untrusted Root CA key**:
```bash
ros2 security create_keystore src/rogue_keystore
ros2 security create_enclave src/rogue_keystore /cmd_vel_publisher
cp src/test_keystore/enclaves/governance.* src/rogue_keystore/enclaves/cmd_vel_publisher/
python3 src/turtlebot3_security/sign_keystore_permissions.py src/rogue_keystore
```
*Result*: Even if `/cmd_vel_publisher` in `rogue_keystore` has `cmd_vel` publish permissions in its XML, DDS Security **rejects the participant during the PKI handshake** because its CA certificate (`identity_ca.cert.pem`) is not trusted by `test_keystore`.

---

## Testing TurtleBot3 in Gazebo Simulation

### Step 1: Generate Keystores with `robot_security` Package

To run this test, you need to generate two separate keystores signed by different Root CAs: `turtlebot3_keystore` (trusted) and `rogue_keystore` (untrusted).

#### A. Generate `turtlebot3_keystore`
1. Edit `config/security_config.yaml` inside `robot_security` package:
   ```yaml
   keystore_name: "turtlebot3_keystore"
   keystore_path: "~/.ros/sros2/turtlebot3_keystore"
   policy_type: "turtlebot3"
   ```
2. Build and run the generator:
   ```bash
   cd ~/wheelchair_ws/ros2_ws
   colcon build --packages-select robot_security
   source install/setup.bash
   rm -rf ~/.ros/sros2/turtlebot3_keystore
   ros2 run robot_security generate_keystore
   ```

#### B. Generate `rogue_keystore`
1. Edit `config/security_config.yaml` to configure the rogue keystore (using the same `turtlebot3` policy):
   ```yaml
   keystore_name: "rogue_keystore"
   keystore_path: "~/.ros/sros2/rogue_keystore"
   policy_type: "turtlebot3"
   ```
2. Build and run the generator:
   ```bash
   cd ~/wheelchair_ws/ros2_ws
   colcon build --packages-select robot_security
   source install/setup.bash
   rm -rf ~/.ros/sros2/rogue_keystore
   ros2 run robot_security generate_keystore
   ```

---

### Step 2: Cleanup Old Gazebo Processes
Before launching, make sure to clean up any running simulator instances:
```bash
pkill -9 -f gzserver || true
pkill -9 -f gzclient || true
```

---

### Terminal 1: Launch Secure Gazebo Simulation
Launch the simulator using the trusted `turtlebot3_keystore`. It will run under the root enclave `/`:
```bash
source /opt/ros/humble/setup.bash
source /home/robot/Documents/turtlebot3_ws/install/setup.bash

export TURTLEBOT3_MODEL=waffle_pi
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/robot/.ros/sros2/turtlebot3_keystore
export ROS_DOMAIN_ID=56

ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```
*(TurtleBot3 spawns securely in Gazebo listening for `/cmd_vel` commands.)*

---

### Terminal 2: Test Authorized Publisher (Robot Moves)
Run the publisher using the trusted `turtlebot3_keystore` under the `/cmd_vel_publisher` enclave:
```bash
source /opt/ros/humble/setup.bash
source /home/robot/Documents/turtlebot3_ws/install/setup.bash

export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/robot/.ros/sros2/turtlebot3_keystore
export ROS_SECURITY_ENCLAVE=/cmd_vel_publisher
export ROS_DOMAIN_ID=56

ros2 run turtlebot3_security cmd_vel_publisher
```
**Result**: Enclave `/cmd_vel_publisher` is signed by the trusted CA and has access control permission to publish `cmd_vel`. **TurtleBot3 moves in circles!**

---

### Terminal 3: Test Rogue CA Publisher (Blocked at Handshake)
Run the publisher using the untrusted `rogue_keystore` under the `/cmd_vel_publisher` enclave:
```bash
source /opt/ros/humble/setup.bash
source /home/robot/Documents/turtlebot3_ws/install/setup.bash

export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/robot/.ros/sros2/rogue_keystore
export ROS_SECURITY_ENCLAVE=/cmd_vel_publisher
export ROS_DOMAIN_ID=56

ros2 run turtlebot3_security cmd_vel_publisher
```
**Result**: The Gazebo simulator immediately rejects the publisher during the PKI handshake phase because its CA certificate (`identity_ca.cert.pem`) is not trusted by `turtlebot3_keystore`. **TurtleBot3 DOES NOT move!**

---

### Terminal 4: Test Unauthorized Enclave Publisher (Access Control Blocked)
Run the fake publisher using the trusted `turtlebot3_keystore` but under the `/fake_cmd_vel_publisher` enclave:
```bash
source /opt/ros/humble/setup.bash
source /home/robot/Documents/turtlebot3_ws/install/setup.bash

export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/robot/.ros/sros2/turtlebot3_keystore
export ROS_SECURITY_ENCLAVE=/fake_cmd_vel_publisher
export ROS_DOMAIN_ID=56

ros2 run turtlebot3_security fake_cmd_vel_publisher
```
**Result**: The enclave `/fake_cmd_vel_publisher` is signed by the trusted CA, but lacks permissions to publish `/cmd_vel` in its policy. FastDDS drops its packets at the reader side. **TurtleBot3 DOES NOT move!**

---

### Secure Navigation2 (Nav2) with RViz2 Goal Planner

To run the secure TurtleBot3 Gazebo simulation and the Navigation2 stack under our SROS2 configuration, both terminals must enforce the security strategy and point to the trusted `keystore`. Because the launch files spawn multiple core nodes, services, and plugins, they run under the root enclave (`/`), which has wildcard permissions for all necessary topics, services, and actions.

#### Terminal A: Launch Secure Gazebo World (e.g. Burger model)
```bash
source /opt/ros/humble/setup.bash
source /home/robot/Documents/turtlebot3_ws/install/setup.bash

export TURTLEBOT3_MODEL=burger
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/robot/.ros/sros2/keystore
export ROS_SECURITY_ENCLAVE=/
export ROS_DOMAIN_ID=56

ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

#### Terminal B: Launch Secure Nav2 & RViz2
```bash
source /opt/ros/humble/setup.bash
source /home/robot/Documents/turtlebot3_ws/install/setup.bash

export TURTLEBOT3_MODEL=burger
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/robot/.ros/sros2/keystore
export ROS_SECURITY_ENCLAVE=/
export ROS_DOMAIN_ID=56

ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=/home/robot/Documents/turtlebot3_ws/src/tb3_sim_bringup/maps/tb3_map.yaml
```

**Result**: All navigation nodes (Planner, Controller, AMCL, BT Navigator) and RViz2 successfully establish mutual authentication handshakes with Gazebo. When you set a target pose using "Nav2 Goal" in RViz2, Nav2 securely plans and controller server publishes control commands over `cmd_vel`, moving the simulated robot.

---

## Layer-wise Robot Security Guide

To secure a physical or simulated TurtleBot3 from external attacks, you must implement defense-in-depth across three layers: **DDS Security (SROS2)**, **Network Security**, and **Operating System Security**.

### Layer 1: ROS 2 / DDS Security (SROS2)
This secures the middleware layer directly on the robot network.
* **Mutual Authentication (PKI)**: Every node on the robot and the control station has a unique certificate signed by a shared **Certificate Authority (CA)**. Non-signed nodes cannot join or discover the ROS 2 graph.
* **Access Control (Permissions)**: Restrict what topics, services, and actions each specific node is allowed to publish, subscribe, request, or reply to (defined in `policy.xml`).
* **Data Encryption**: Set `metadata_protection_kind` and `data_protection_kind` to `ENCRYPT` in the governance configuration to encrypt payload data and discovery packets using AES-GCM, preventing eavesdropping.

### Layer 2: Network-Level Security
This protects communication transport over wireless networks.
* **Dedicated, Encrypted Wi-Fi (WPA3)**: Keep the robot and control station on an isolated VLAN or Wi-Fi network separate from guest/office networks. Enforce WPA3 encryption.
* **DDS Domain ID Isolation**: Use a unique `ROS_DOMAIN_ID` to isolate your network packets from other ROS 2 networks on the same router.
* **Firewall Rules (UFW / iptables)**: Enable a local firewall on the robot's onboard computer to drop all incoming packets except those from trusted IPs.

### Layer 3: Operating System & Hardware Security
This secures the host operating system from direct compromise.
* **Secure SSH Access**: Disable password-based SSH logins (`PasswordAuthentication no` in `/etc/ssh/sshd_config`), change default SSH ports, and enforce SSH Public Key authentication only. Never use default passwords like `ubuntu` or `robot`.
* **Regular OS Updates**: Keep the robot OS (Ubuntu) and ROS 2 distribution patched with the latest security updates.
* **Physical Port Security**: Disable unused USB ports and secure physical access to the onboard computer to prevent malicious USB drive injections.

---

## Troubleshooting & Common Pitfalls

1. **`Unable to start server[bind: Address already in use]`**:
   - Cause: An orphaned `gzserver` process is running in the background holding Gazebo port 11345. Run `pkill -9 -f gzserver`.

2. **`libobstacle1.so: cannot open shared object file` (Stage 4 World Crash)**:
   - Cause: `turtlebot3_dqn_stage4.launch.py` uses reinforcement learning obstacle plugins (`libobstacle1.so`). Use standard `turtlebot3_world.launch.py` or `turtlebot3_house.launch.py`.

3. **`Not found a rule allowing to use the domain_id`**:
   - Cause: Mismatch between `<id>` in `governance.xml` and `permissions.xml`. Ensure both specify `<id>56</id>`.

4. **Node Falls Back to Root Enclave (`/`)**:
   - Cause: Missing `export ROS_SECURITY_ENCLAVE=/my_enclave` or path error. Ensure the enclave path matches the directory name under `enclaves/`.
