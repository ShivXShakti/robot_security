# Wheelchair Security
---

## Table of Contents
1. [Generate Keystores](#generate-keystores)
2. [Wheelchair Security Demo on Host](#wheelchair-security-demo-on-host)
   - [Terminal 1: Launch Secure Navigation stack](#terminal-1-launch-secure-navigation-stack)
   - [Terminal 2: Test Authorized Publisher (Robot Moves)](#terminal-2-test-authorized-publisher-robot-moves-)
   - [Terminal 3: Test Unauthorized Enclave Publisher (Blocked)](#terminal-3-test-unauthorized-enclave-publisher-blocked-)
   - [Terminal 4: Test without Enclave](#terminal-4-test-without-enclave)
3. [Wheelchair Security Demo using system](#wheelchair-security-demo-using-remote-system)
   - [Terminal 1: Launch Secure Navigation stack](#terminal-1-launch-secure-secure-navigation-stack)
   - [Terminal 2: Test Authorized Publisher (Robot Moves)](#terminal-2-test-authorized-publisher-robot-moves-)
   - [Terminal 3: Test Unauthorized Enclave Publisher (Blocked)](#terminal-3-test-unauthorized-enclave-publisher-blocked-)
   - [Terminal 4: Test without Enclave](#terminal-4-test-without-enclave)
4. [Wheelchair security Demo videos](#wheelchair-security-demo-videos)

---

## Generate Keystores

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
   cd ~/wheelchair2
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
   cd ~/wheelchair2
   source install/setup.bash
   rm -rf ~/.ros/sros2/rogue_keystore
   ros2 run robot_security generate_keystore
   ```
---
## Wheelchair Security Demo on Host
### Terminal 1: Launch Secure Navigation stack
Launch using the trusted `wheelchair_keystore`. It will run under the root enclave `/`:

Ensure this is source in the launch file-nav_3D_loc_cyclone.tmux
```bash
sudo sysctl -w net.core.rmem_max=10485760
sudo sysctl -w net.core.wmem_max=10485760

# Make it permanent:
echo "net.core.rmem_max=10485760" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=10485760" | sudo tee -a /etc/sysctl.con
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/wheelchair_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/container_user/wheelchair2/src/scripts/cyclonedds_jetson.xml

or

SEC_ENV="source /opt/ros/humble/setup.bash && source /home/container_user/wheelchair2/install/setup.bash && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export ROS_SECURITY_ENABLE=true && export ROS_SECURITY_STRATEGY=Enforce && export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/wheelchair_keystore && export ROS_SECURITY_ENCLAVE=/wheelchair && export ROS_DOMAIN_ID=56 && export CYCLONEDDS_URI=file:///home/container_user/wheelchair2/src/scripts/cyclonedds_jetson.xml"

```
---
Then run
```bash
cd ~/wheelchair2
./src/wheelchair2_navigation/shell_scripts/nav_3D_loc_cyclone.tmux
```

---

### Terminal 2: Test Authorized Publisher (Robot Moves)
Run the publisher using the trusted `wheelchair_keystore` enclave:
```bash
cd ~/wheelchair2
sudo sysctl -w net.core.rmem_max=10485760
sudo sysctl -w net.core.wmem_max=10485760

# Make it permanent:
echo "net.core.rmem_max=10485760" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=10485760" | sudo tee -a /etc/sysctl.con
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/wheelchair_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/container_user/wheelchair2/src/scripts/cyclonedds_jetson.xml

ros2 run robot_security e_send_goal
```

OR (Ensure export CYCLONEDDS_URI=file:///home/container_user/wheelchair2/src/scripts/cyclonedds_jetson.xml)

```
cd ~/wheelchair2
./dependencies/robot_security/scripts/send_goal_secure.sh
```
**Result**: Enclave `/wheelchair` is signed by the trusted CA and has access control permission to `navigate_to_pose` request.

---

### Terminal 3: Test Rogue CA Publisher
Run the publisher using the untrusted `rogue_keystore` enclave:
```bash
cd ~/wheelchair2
sudo sysctl -w net.core.rmem_max=10485760
sudo sysctl -w net.core.wmem_max=10485760

# Make it permanent
echo "net.core.rmem_max=10485760" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=10485760" | sudo tee -a /etc/sysctl.con
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/rogue_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/container_user/wheelchair2/src/scripts/cyclonedds_jetson.xml

ros2 run robot_security e_send_goal
```

OR

```
cd ~/wheelchair2
./dependencies/robot_security/scripts/send_goal_rogue.sh
```
**Result**: The wheelchair immediately rejects the publisher during the PKI handshake phase because its CA certificate (`identity_ca.cert.pem`) is not trusted by `wheelchair_keystore`.

---

### Terminal 4: Test without Enclave
Run the publisher using the untrusted `rogue_keystore` enclave:
```bash
cd ~/wheelchair2
source install/setup.bash
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

ros2 run robot_security e_send_goal
```
OR

```
cd ~/wheelchair2
./dependencies/robot_security/scripts/send_goal.sh
```













## Wheelchair Security Demo using remote system
### Terminal 1: Launch Secure Navigation stack
Launch using the trusted `wheelchair_keystore`. It will run under the root enclave `/`:

Ensure this is source in the launch file-nav_3D_loc_cyclone.tmux: *RUN THIS ON JETSON*
```bash
sudo sysctl -w net.core.rmem_max=10485760
sudo sysctl -w net.core.wmem_max=10485760

# Make it permanent:
echo "net.core.rmem_max=10485760" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=10485760" | sudo tee -a /etc/sysctl.con
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/wheelchair_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/container_user/wheelchair2/src/scripts/cyclonedds_jetson.xml

or

SEC_ENV="source /opt/ros/humble/setup.bash && source /home/container_user/wheelchair2/install/setup.bash && export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp && export ROS_SECURITY_ENABLE=true && export ROS_SECURITY_STRATEGY=Enforce && export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/wheelchair_keystore && export ROS_SECURITY_ENCLAVE=/wheelchair && export ROS_DOMAIN_ID=56 && export CYCLONEDDS_URI=file:///home/container_user/wheelchair2/src/scripts/cyclonedds_jetson.xml"

```
---
Then run
```bash
cd ~/wheelchair2
./src/wheelchair2_navigation/shell_scripts/nav_3D_loc_cyclone.tmux
```
---

### Terminal 2: Test Authorized Publisher (Robot Moves)
Run the publisher using the trusted `wheelchair_keystore` enclave:
```bash
cd ~/wheelchair_ws/wheelchair2
sudo sysctl -w net.core.rmem_max=10485760
sudo sysctl -w net.core.wmem_max=10485760

# Make it permanent:
echo "net.core.rmem_max=10485760" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=10485760" | sudo tee -a /etc/sysctl.con
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/robot/.ros/sros2/wheelchair_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/robot/wheelchair_ws/wheelchair2/scripts/cyclonedds_laptop.xml

ros2 run robot_security e_send_goal
```

OR (Ensure export CYCLONEDDS_URI=file:///home/robot/wheelchair_ws/wheelchair2/scripts/cyclonedds_laptop.xml)

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
sudo sysctl -w net.core.rmem_max=10485760
sudo sysctl -w net.core.wmem_max=10485760

# Make it permanent
echo "net.core.rmem_max=10485760" | sudo tee -a /etc/sysctl.conf
echo "net.core.wmem_max=10485760" | sudo tee -a /etc/sysctl.con
source install/setup.bash
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=/home/container_user/.ros/sros2/rogue_keystore
export ROS_SECURITY_ENCLAVE=/wheelchair
export ROS_DOMAIN_ID=56
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file:///home/robot/wheelchair_ws/wheelchair2/scripts/cyclonedds_laptop.xml

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
cd ~/wheelchair2
./dependencies/robot_security/scripts/send_goal.sh


