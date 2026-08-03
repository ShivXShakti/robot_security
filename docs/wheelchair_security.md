# Wheelchair Security
---

## Table of Contents
1. [Testing TurtleBot3 in Gazebo Simulation](#testing-turtlebot3-in-gazebo-simulation)
   - [Step 0: Cleanup Old Gazebo Processes](#step-0-cleanup-old-gazebo-processes)
   - [Terminal 1: Launch Secure Gazebo Simulation](#terminal-1-launch-secure-gazebo-simulation)
   - [Terminal 2: Test Authorized Publisher (Robot Moves)](#terminal-2-test-authorized-publisher-robot-moves-)
   - [Terminal 3: Test Unauthorized Enclave Publisher (Blocked)](#terminal-3-test-unauthorized-enclave-publisher-blocked-)
   - [Terminal 4: Test without Enclave](#terminal-4-test-without-enclave)

---

## Wheelchair Security Demo

### Step 1: Generate Keystores with `robot_security` Package

To run this test, you need to generate two separate keystores signed by different Root CAs: `wheelchair_keystore` (trusted) and `rogue_keystore` (untrusted).

#### A. Generate `wheelchair_keystore`
1. Edit `config/security_config.yaml` inside `robot_security` package:
   ```yaml
   keystore_name: "wheelchair_keystore"
   keystore_path: "~/.ros/sros2/wheelchair_keystore"
   policy_type: "wheelchair"    ## Policy type to activate ("wheelchair", "wheelchair_individual", or "turtlebot3")
   ```
2. Build and run the generator:
   ```bash
   cd ~/wheelchair_ws/wheelchair2
   source install/setup.bash
   rm -rf ~/.ros/sros2/wheelchair_keystore
   ros2 run robot_security generate_keystore
   ```
#### B. Generate `rogue_keystore`
1. Edit `config/security_config.yaml` to configure the rogue keystore (using the same `wheelchair` policy):
   ```yaml
   keystore_name: "rogue_keystore"
   keystore_path: "~/.ros/sros2/rogue_keystore"
   policy_type: "wheelchair"
   ```
2. Build and run the generator:
   ```bash
   cd ~/wheelchair_ws/wheelchair2
   source install/setup.bash
   rm -rf ~/.ros/sros2/rogue_keystore
   ros2 run robot_security generate_keystore
   ```
---
### Step 2: Run Nodes with security Enclave

### Terminal 1: Launch Secure Navigation stack
Launch the simulator using the trusted `wheelchair_keystore`. It will run under the root enclave `/`:
```bash
cd ~/wheelchair_ws/wheelchair2
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/wheelchair_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

./src/wheelchair2_navigation/shell_scripts/nav_3D_loc_cyclone.tmux
```

---

### Terminal 2: Test Authorized Publisher (Robot Moves)
Run the publisher using the trusted `wheelchair_keystore` enclave:
```bash
cd ~/wheelchair_ws/wheelchair2
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/wheelchair_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 run robot_security e_send_goal
```

OR

```
cd ~/wheelchair_ws/wheelchair2
./dependencies/robot_security/scripts/send_goal_secure.sh
```
**Result**: Enclave `/wheelchair` is signed by the trusted CA and has access control permission to `navigate_to_pose` request.

---

### Terminal 3: Test Rogue CA Publisher
Run the publisher using the untrusted `rogue_keystore` enclave:
```bash
cd ~/wheelchair_ws/wheelchair2
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/rogue_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 run robot_security e_send_goal
```

OR

```
cd ~/wheelchair_ws/wheelchair2
./dependencies/robot_security/scripts/send_goal_rogue.sh
```
**Result**: The wheelchair immediately rejects the publisher during the PKI handshake phase because its CA certificate (`identity_ca.cert.pem`) is not trusted by `wheelchair_keystore`.

---

### Terminal 4: Test without Enclave
Run the publisher using the untrusted `rogue_keystore` enclave:
```bash
cd ~/wheelchair_ws/wheelchair2
source install/setup.bash
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 run robot_security e_send_goal
```
OR

```
cd ~/wheelchair_ws/wheelchair2
./dependencies/robot_security/scripts/send_goal.sh
```
