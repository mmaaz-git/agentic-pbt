"""Minimal reproduction of bugs found in dagster_postgres.utils."""

import sys
from urllib.parse import urlparse, parse_qs, unquote

sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string

print("Bug 1: Empty parameter values are dropped from URL")
print("-" * 50)

# Test case 1: Empty parameter value
conn_string = get_conn_string(
    username="user",
    password="pass",
    hostname="localhost",
    db_name="testdb",
    port="5432",
    params={"key1": "value1", "key2": ""}  # key2 has empty value
)

print(f"Generated URL: {conn_string}")
parsed = urlparse(conn_string)
query_dict = parse_qs(parsed.query)
print(f"Parsed query params: {query_dict}")

# Check if key2 is present
if "key2" not in query_dict:
    print("❌ BUG: Empty parameter 'key2' was dropped from the URL!")
else:
    print("✓ key2 is present in query")

print("\n" + "="*60 + "\n")

print("Bug 2: Special character '/' in password corrupts URL parsing")
print("-" * 50)

# Test case 2: Password with forward slash
conn_string = get_conn_string(
    username="user",
    password="/",  # Just a forward slash
    hostname="localhost",
    db_name="testdb",
    port="5432"
)

print(f"Generated URL: {conn_string}")
parsed = urlparse(conn_string)
print(f"Parsed hostname: {parsed.hostname}")
print(f"Expected hostname: localhost")

if parsed.hostname != "localhost":
    print(f"❌ BUG: Hostname is '{parsed.hostname}' instead of 'localhost'!")
    print("   The forward slash in the password corrupted the URL structure.")
else:
    print("✓ Hostname is correct")

# Let's also check if we can recover the password
if parsed.password:
    recovered_password = unquote(parsed.password)
    print(f"Recovered password: '{recovered_password}'")
    if recovered_password != "/":
        print(f"❌ BUG: Password is '{recovered_password}' instead of '/'!")
else:
    print("❌ BUG: Password is missing from parsed URL!")

print("\n" + "="*60 + "\n")

print("Bug 3: Hostname containing forward slash breaks URL structure")
print("-" * 50)

# Test with a more complex password
conn_string = get_conn_string(
    username="user",
    password="pass/word",  # Password with slash in the middle
    hostname="localhost",
    db_name="testdb",
    port="5432"
)

print(f"Generated URL: {conn_string}")
parsed = urlparse(conn_string)
print(f"Parsed components:")
print(f"  - Scheme: {parsed.scheme}")
print(f"  - Username: {parsed.username}")
print(f"  - Password: {parsed.password}")
print(f"  - Hostname: {parsed.hostname}")
print(f"  - Port: {parsed.port}")
print(f"  - Path: {parsed.path}")

if parsed.hostname != "localhost":
    print(f"❌ BUG: Hostname is '{parsed.hostname}' instead of 'localhost'!")

if parsed.password:
    recovered_password = unquote(parsed.password)
    if recovered_password != "pass/word":
        print(f"❌ BUG: Password is '{recovered_password}' instead of 'pass/word'!")
else:
    print("❌ BUG: Password is missing!")