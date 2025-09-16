#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

print("Testing imports...")
try:
    from dagster_postgres.utils import get_conn_string
    print("✓ Successfully imported get_conn_string")
    
    # Test basic functionality
    result = get_conn_string("user", "pass", "localhost", "db")
    print(f"✓ Basic test: {result}")
    
    # Test with special characters
    result2 = get_conn_string("user@host", "pass:word", "localhost", "mydb")
    print(f"✓ Special chars test: {result2}")
    
    from urllib.parse import urlparse, unquote
    parsed = urlparse(result2)
    print(f"  Parsed username: {parsed.username}")
    print(f"  Decoded username: {unquote(parsed.username) if parsed.username else 'None'}")
    
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()