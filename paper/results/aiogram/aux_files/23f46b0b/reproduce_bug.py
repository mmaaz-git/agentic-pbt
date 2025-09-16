"""Minimal reproduction of IPFilter bug with network addresses"""

from aiogram.webhook.security import IPFilter

# This should work - a user might naturally specify a network like this
# Example: "192.168.1.100/24" to mean "the /24 network containing 192.168.1.100"
print("Testing IPFilter with network address that has host bits set...")

try:
    ip_filter = IPFilter()
    # User wants to allow the entire 192.168.1.0/24 network
    # But they specify it using an IP in that network
    ip_filter.allow_ip("192.168.1.100/24")
    print("✓ Successfully added network")
except ValueError as e:
    print(f"✗ Failed with error: {e}")

# Another example
try:
    ip_filter = IPFilter()
    ip_filter.allow_ip("10.0.0.5/16")
    print("✓ Successfully added 10.0.0.5/16")
except ValueError as e:
    print(f"✗ Failed with error: {e}")

# The minimal failing case from hypothesis
try:
    ip_filter = IPFilter()
    ip_filter.allow_ip("0.0.0.1/24")
    print("✓ Successfully added 0.0.0.1/24")
except ValueError as e:
    print(f"✗ Failed with error: {e}")

print("\nThis is a legitimate bug because:")
print("1. Users might naturally specify networks using any IP in that network")
print("2. Many networking tools accept this notation (e.g., iptables, nmap)")
print("3. The fix is simple: use strict=False when creating IPv4Network")