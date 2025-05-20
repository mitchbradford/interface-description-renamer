import napalm
from getpass import getpass

# Device connection details
hostname = input('Enter IP address of device:')
username = input('Enter your username:')
password = getpass("Enter your password: ")

driver_name = 'ios'  # Change to your device type, e.g., 'eos', 'junos', etc.

# Connect to the device - need optional arg if the device does not have a secret ie: enable password
driver = napalm.get_network_driver(driver_name)
device = driver(hostname=hostname, username=username, password=password,optional_args={'inline_transfer': True})
device.open()

# Get interface descriptions and LLDP neighbor details
interfaces = device.get_interfaces()
# IOS driver doesn't support get_interfaces_descriptions
#descriptions = device.get_interfaces_description()
descriptions = device.get_interfaces()
lldp_neighbors = device.get_lldp_neighbors_detail()

# Prepare configuration changes
config_commands = []

for iface, details in interfaces.items():
    # Check if description is empty or missing
    desc = descriptions.get(iface, {}).get('description', '')
    if not desc or desc.strip() == '':
        lldp_info = lldp_neighbors.get(iface)
        if lldp_info:
            # Use the first neighbor's system name and port
            neighbor = lldp_info[0]
            neighbor_name = neighbor.get('remote_system_name', 'LLDP Neighbor')
            neighbor_port = neighbor.get('remote_port', '')
            new_desc = f"Connected to {neighbor_name} via {neighbor_port}".strip()
            config_commands.append(f"interface {iface}\ndescription {new_desc}")

# debug
# print(config_commands)

# Apply configuration if there are changes
if config_commands:
    config_str = '\n'.join(config_commands)
    device.load_merge_candidate(config=config_str)
    print("Proposed config changes:\n", device.compare_config())
    device.commit_config()
    print("Descriptions updated.")
else:
    print("No empty descriptions found or no LLDP info available.")

device.close()