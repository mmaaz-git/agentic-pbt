#!/usr/bin/env python3
"""Bug reproduction: is_valid_cidr incorrectly rejects /0 CIDR"""

import requests.utils

# Test the bug
cidr = '0.0.0.0/0'
result = requests.utils.is_valid_cidr(cidr)
print(f"is_valid_cidr('{cidr}') = {result}")
print(f"Expected: True (0.0.0.0/0 represents all IPv4 addresses)")
print(f"Actual: {result}")

# Show that /0 is valid in networking
print("\nWhy /0 should be valid:")
print("- CIDR notation allows masks from /0 to /32")
print("- /0 means 'match all addresses' (0 network bits, 32 host bits)")
print("- Common in firewall rules and routing tables")
print("- Used in NO_PROXY='0.0.0.0/0' to bypass proxy for all IPs")

# Show the related functions work correctly with /0
print("\nRelated functions work correctly with /0:")
netmask = requests.utils.dotted_netmask(0)
print(f"dotted_netmask(0) = {netmask}")

# address_in_network works with /0
is_in = requests.utils.address_in_network('192.168.1.1', '0.0.0.0/0')
print(f"address_in_network('192.168.1.1', '0.0.0.0/0') = {is_in}")

# Show the bug's location in code
print("\nThe bug is in utils.py line 721:")
print("    if mask < 1 or mask > 32:")
print("        return False")
print("Should be:")
print("    if mask < 0 or mask > 32:")
print("        return False")