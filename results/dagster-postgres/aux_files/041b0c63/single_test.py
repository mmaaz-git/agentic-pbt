#!/usr/bin/env python3
import sys
import os
from urllib.parse import urlparse, unquote

# Add the site-packages directory to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string

# Test with some specific examples
test_cases = [
    ("user", "pass", "localhost", "db", "5432", None, "postgresql"),
    ("user@example", "pass:word", "localhost", "my_db", "5432", None, "postgresql"),
    ("user", "p@ss:w/rd#123", "db.example.com", "database", "5432", None, "postgresql"),
    ("user:name", "pass@word", "127.0.0.1", "test_db", "3306", {"sslmode": "require"}, "postgresql"),
]

print("Testing get_conn_string with specific examples:")
print("=" * 60)

for i, (username, password, hostname, db_name, port, params, scheme) in enumerate(test_cases, 1):
    print(f"\nTest case {i}:")
    print(f"  Input: username='{username}', password='{password}', hostname='{hostname}', db_name='{db_name}'")
    
    try:
        conn_string = get_conn_string(username, password, hostname, db_name, port, params, scheme)
        print(f"  Result: {conn_string}")
        
        # Try to parse it
        parsed = urlparse(conn_string)
        print(f"  Parsed URL components:")
        print(f"    - scheme: {parsed.scheme}")
        print(f"    - hostname: {parsed.hostname}")
        print(f"    - port: {parsed.port}")
        print(f"    - path: {parsed.path}")
        print(f"    - username (decoded): {unquote(parsed.username) if parsed.username else None}")
        print(f"    - password (decoded): {unquote(parsed.password) if parsed.password else None}")
        
        # Check if decoded values match original
        if parsed.username:
            decoded_username = unquote(parsed.username)
            if decoded_username != username:
                print(f"  ⚠️ WARNING: Username mismatch! Original: '{username}', Decoded: '{decoded_username}'")
        
        if parsed.password:
            decoded_password = unquote(parsed.password)
            if decoded_password != password:
                print(f"  ⚠️ WARNING: Password mismatch! Original: '{password}', Decoded: '{decoded_password}'")
                
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()