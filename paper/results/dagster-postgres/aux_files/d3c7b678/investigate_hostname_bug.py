#!/usr/bin/env python3
import sys
from urllib.parse import urlparse, quote

sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string

# Test the failing case
username = "test"
password = "test"
hostname = "MyHost.Example.COM"  # Mixed case hostname
db_name = "testdb"
port = "5432"

print(f"Original hostname: {hostname}")

# Generate connection string
conn_string = get_conn_string(username, password, hostname, db_name, port)
print(f"\nGenerated connection string: {conn_string}")

# Parse it back
parsed = urlparse(conn_string)
print(f"\nParsed hostname: {parsed.hostname}")

# Compare
print(f"\nHostnames match? {parsed.hostname == hostname}")
print(f"Hostnames match (case-insensitive)? {parsed.hostname.lower() == hostname.lower()}")

# Test with IP address
ip_hostname = "192.168.1.1"
conn_string_ip = get_conn_string(username, password, ip_hostname, db_name, port)
parsed_ip = urlparse(conn_string_ip)
print(f"\nIP hostname: {ip_hostname}")
print(f"Parsed IP hostname: {parsed_ip.hostname}")
print(f"IP hostnames match? {parsed_ip.hostname == ip_hostname}")

# Check if this is a urllib behavior
test_url = f"postgresql://user:pass@{hostname}:5432/db"
parsed_test = urlparse(test_url)
print(f"\nDirect URL construction test:")
print(f"URL: {test_url}")
print(f"Parsed hostname: {parsed_test.hostname}")
print(f"Is urllib.parse lowercasing? {parsed_test.hostname != hostname}")