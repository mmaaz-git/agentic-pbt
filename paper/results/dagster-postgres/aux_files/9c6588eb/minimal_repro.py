"""Minimal reproduction demonstrating URL encoding bug in get_conn_string."""

import sys
from urllib.parse import urlparse, quote

sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string

# Bug: Forward slash in password breaks URL structure
conn_string = get_conn_string(
    username="user",
    password="pass/word",
    hostname="localhost", 
    db_name="testdb",
    port="5432"
)

print(f"Input password: 'pass/word'")
print(f"Generated URL: {conn_string}")
print(f"Expected URL:  postgresql://user:pass%2Fword@localhost:5432/testdb")

parsed = urlparse(conn_string)
print(f"\nParsed URL components:")
print(f"  Hostname: {parsed.hostname} (expected: localhost)")
print(f"  Username: {parsed.username} (expected: user)")
print(f"  Password: {parsed.password} (expected: pass/word after decoding)")

if parsed.hostname != "localhost":
    print("\n✗ BUG CONFIRMED: The forward slash in password corrupts the URL structure!")
    print("  The '/' is not being properly percent-encoded as %2F")
    
# Show the correct encoding
print(f"\nCorrect encoding of 'pass/word': {quote('pass/word', safe='')}")
print("The function should use quote() with safe='' to encode all special chars")