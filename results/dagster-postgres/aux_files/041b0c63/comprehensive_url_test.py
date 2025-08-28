#!/usr/bin/env python3
"""Comprehensive test for special characters in get_conn_string."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse, unquote

# Test all URL-special characters systematically
special_chars = ['/', '\\', '@', ':', '?', '#', '[', ']', '!', '$', '&', "'", '(', ')', '*', '+', ',', ';', '=', ' ', '%']

print("Testing all special characters in passwords:")
print("=" * 60)

issues = []

for char in special_chars:
    password = f"pass{char}word"
    username = "user"
    hostname = "localhost"
    db_name = "db"
    
    conn_string = get_conn_string(username, password, hostname, db_name)
    parsed = urlparse(conn_string)
    
    # Check if we can recover the password
    recovered_password = unquote(parsed.password) if parsed.password else None
    
    if recovered_password != password:
        issues.append((char, password, recovered_password))
        print(f"❌ Character '{char}': Password '{password}' -> Recovered: '{recovered_password}'")
    else:
        print(f"✓ Character '{char}': Correctly handled")

print("\n" + "=" * 60)
print("Summary:")
if issues:
    print(f"Found {len(issues)} problematic characters:")
    for char, original, recovered in issues:
        print(f"  - '{char}': '{original}' became '{recovered}'")
else:
    print("All special characters handled correctly!")

# Test in usernames too
print("\n" + "=" * 60)
print("Testing special characters in usernames:")
print("=" * 60)

username_issues = []

for char in special_chars:
    username = f"user{char}name"
    password = "password"
    hostname = "localhost"
    db_name = "db"
    
    try:
        conn_string = get_conn_string(username, password, hostname, db_name)
        parsed = urlparse(conn_string)
        
        # Check if we can recover the username
        recovered_username = unquote(parsed.username) if parsed.username else None
        
        if recovered_username != username:
            username_issues.append((char, username, recovered_username))
            print(f"❌ Character '{char}': Username '{username}' -> Recovered: '{recovered_username}'")
        else:
            print(f"✓ Character '{char}': Correctly handled")
    except Exception as e:
        print(f"❌ Character '{char}': Error: {e}")
        username_issues.append((char, username, f"Error: {e}"))

print("\n" + "=" * 60)
print("Username Summary:")
if username_issues:
    print(f"Found {len(username_issues)} problematic characters in usernames:")
    for char, original, recovered in username_issues:
        print(f"  - '{char}': '{original}' became '{recovered}'")