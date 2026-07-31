#!/usr/bin/env python3

import os
import sys
import yaml
import subprocess
import shutil
from ament_index_python.packages import get_package_share_directory

def log(msg):
    print(f"[robot_security] {msg}", flush=True)

def run_cmd(cmd):
    log(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        log(f"Error executing command: {' '.join(cmd)}")
        log(f"Stdout:\n{result.stdout}")
        log(f"Stderr:\n{result.stderr}")
        return False
    return True

def main():
    try:
        share_dir = get_package_share_directory('robot_security')
    except Exception as e:
        log(f"Could not find package share directory: {e}")
        log("Make sure to run: colcon build && source install/setup.bash")
        sys.exit(1)

    config_path = os.path.join(share_dir, 'config', 'security_config.yaml')
    if not os.path.exists(config_path):
        log(f"Configuration file not found: {config_path}")
        sys.exit(1)

    log(f"Loading configuration from {config_path}")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    keystore_name = config.get('keystore_name', 'wheelchair_keystore')
    keystore_path_raw = config.get('keystore_path', '~/.ros/sros2/keystore')
    keystore_path = os.path.expanduser(keystore_path_raw)
    
    # If the keystore_path itself is a relative path or doesn't end with keystore name, 
    # we can append the keystore_name, but standard SROS2 uses the folder directly.
    # We will use keystore_path as the direct root.
    log(f"Target keystore path: {keystore_path}")

    # 1. Initialize keystore if not exists
    if not os.path.exists(os.path.join(keystore_path, 'public', 'ca.cert.pem')):
        log("Keystore CA not found. Initializing keystore...")
        os.makedirs(keystore_path, exist_ok=True)
        if not run_cmd(['ros2', 'security', 'create_keystore', keystore_path]):
            log("Failed to initialize keystore CA.")
            sys.exit(1)
    else:
        log("Keystore CA already exists. Skipping initialization.")

    policy_type = config.get('policy_type', 'mobile_robot')
    log(f"Active policy type: {policy_type}")

    policies_config = config.get('policies', {})
    if policy_type not in policies_config:
        log(f"Policy type '{policy_type}' is not defined in configuration.")
        sys.exit(1)

    policy_data = policies_config[policy_type]
    policy_file_name = policy_data.get('policy_file')
    policy_file_path = os.path.join(share_dir, 'policies', policy_file_name)
    
    if not os.path.exists(policy_file_path):
        log(f"Policy file not found: {policy_file_path}")
        sys.exit(1)

    log(f"Using policy file: {policy_file_path}")

    enclaves = policy_data.get('enclaves', [])
    for enclave_info in enclaves:
        enclave_name = enclave_info.get('name')
        if not enclave_name:
            continue

        log(f"Processing enclave: {enclave_name}")

        # Check if enclave keys already exist
        enclave_dir_name = enclave_name.lstrip('/')
        # Root enclave '/' maps to the 'enclaves' folder direct children or an empty string name.
        if not enclave_dir_name:
            # Root enclave files are directly under keystore_path/enclaves
            enclave_key_path = os.path.join(keystore_path, 'enclaves', 'key.pem')
        else:
            enclave_key_path = os.path.join(keystore_path, 'enclaves', enclave_dir_name, 'key.pem')

        if not os.path.exists(enclave_key_path):
            log(f"Generating keys for enclave: {enclave_name}")
            if not run_cmd(['ros2', 'security', 'create_enclave', keystore_path, enclave_name]):
                log(f"Failed to create enclave {enclave_name}.")
                sys.exit(1)
        else:
            log(f"Enclave keys already exist for {enclave_name}. Skipping key generation.")

        # Create/update permission based on policy file
        log(f"Generating permissions for enclave: {enclave_name}")
        if not run_cmd(['ros2', 'security', 'create_permission', keystore_path, enclave_name, policy_file_path]):
            log(f"Failed to generate permissions for {enclave_name}.")
            sys.exit(1)

    log("Keystore and enclave permissions generated successfully!")

if __name__ == '__main__':
    main()
