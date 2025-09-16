#!/usr/bin/env python3
"""Investigate the issue with slash in password."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse, unquote, quote

# Test cases with slashes
test_cases = [
    ("user", "pass/word", "localhost", "db"),
    ("user", "pass//word", "localhost", "db"),
    ("user", "/pass", "localhost", "db"),
    ("user", "pass/", "localhost", "db"),
    ("user", "a/b/c", "localhost", "db"),
    ("user/name", "pass", "localhost", "db"),
]

print("Testing get_conn_string with slashes in credentials:")
print("=" * 60)

for username, password, hostname, db_name in test_cases:
    print(f"\nInput: username='{username}', password='{password}'")
    
    # Get the connection string
    conn_string = get_conn_string(username, password, hostname, db_name)
    print(f"  Generated URL: {conn_string}")
    
    # Try to parse it
    parsed = urlparse(conn_string)
    print(f"  Parsed components:")
    print(f"    - scheme: {parsed.scheme}")
    print(f"    - netloc: {parsed.netloc}")
    print(f"    - hostname: {parsed.hostname}")
    print(f"    - username: {parsed.username}")
    print(f"    - password: {parsed.password}")
    print(f"    - path: {parsed.path}")
    
    # Check if we can recover the original values
    if parsed.username:
        decoded_username = unquote(parsed.username)
        if decoded_username != username:
            print(f"  ❌ Username mismatch! Original: '{username}', Decoded: '{decoded_username}'")
    else:
        if username:
            print(f"  ❌ Username lost! Original: '{username}', Parsed: None")
    
    if parsed.password:
        decoded_password = unquote(parsed.password)
        if decoded_password != password:
            print(f"  ❌ Password mismatch! Original: '{password}', Decoded: '{decoded_password}'")
    else:
        if password:
            print(f"  ❌ Password lost! Original: '{password}', Parsed: None")

print("\n" + "=" * 60)
print("Analysis of the issue:")
print("-" * 40)

# Show how quote works
test_strings = ["/", "//", "pass/word", "@", ":", "#"]
for s in test_strings:
    print(f"quote('{s}') = '{quote(s)}'")

print("\nPython's urlparse behavior:")
# Manual construction to understand the issue
url1 = "postgresql://user:pass/word@localhost:5432/db"
url2 = "postgresql://user:pass%2Fword@localhost:5432/db"

print(f"\nUnencoded slash: {url1}")
parsed1 = urlparse(url1)
print(f"  username: {parsed1.username}, password: {parsed1.password}")

print(f"\nEncoded slash: {url2}")
parsed2 = urlparse(url2)
print(f"  username: {parsed2.username}, password: {parsed2.password}")