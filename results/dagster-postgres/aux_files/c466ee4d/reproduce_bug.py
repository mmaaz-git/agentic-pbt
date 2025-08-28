#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from urllib.parse import urlparse, unquote
from dagster_postgres.utils import get_conn_string

# Bug reproduction: special characters in password break URL parsing
def test_special_char_bug():
    # Test 1: Forward slash in password
    username = "testuser"
    password = "pass/word"  
    hostname = "localhost"
    dbname = "testdb"
    
    conn_str = get_conn_string(username, password, hostname, dbname)
    print(f"Original: username='{username}', password='{password}'")
    print(f"Conn string: {conn_str}")
    
    parsed = urlparse(conn_str)
    recovered_username = unquote(parsed.username) if parsed.username else None
    recovered_password = unquote(parsed.password) if parsed.password else None
    
    print(f"Recovered: username='{recovered_username}', password='{recovered_password}'")
    
    if recovered_username != username or recovered_password != password:
        print("BUG: Failed to properly encode/decode credentials!")
        return False
    return True

# Test 2: Colon in password  
def test_colon_in_password():
    username = "user"
    password = "pass:word"
    hostname = "localhost"
    dbname = "testdb"
    
    conn_str = get_conn_string(username, password, hostname, dbname)
    print(f"\nOriginal: username='{username}', password='{password}'")
    print(f"Conn string: {conn_str}")
    
    parsed = urlparse(conn_str)
    recovered_username = unquote(parsed.username) if parsed.username else None
    recovered_password = unquote(parsed.password) if parsed.password else None
    
    print(f"Recovered: username='{recovered_username}', password='{recovered_password}'")
    
    if recovered_username != username or recovered_password != password:
        print("BUG: Failed to properly encode/decode credentials with colon!")
        return False
    return True

# Test 3: @ symbol in password
def test_at_in_password():
    username = "user"
    password = "p@ssword"
    hostname = "localhost"
    dbname = "testdb"
    
    conn_str = get_conn_string(username, password, hostname, dbname)
    print(f"\nOriginal: username='{username}', password='{password}'")
    print(f"Conn string: {conn_str}")
    
    parsed = urlparse(conn_str)
    recovered_username = unquote(parsed.username) if parsed.username else None
    recovered_password = unquote(parsed.password) if parsed.password else None
    
    print(f"Recovered: username='{recovered_username}', password='{recovered_password}'")
    
    if recovered_username != username or recovered_password != password:
        print("BUG: Failed to properly encode/decode credentials with @ symbol!")
        return False
    return True

if __name__ == "__main__":
    test_special_char_bug()
    test_colon_in_password()
    test_at_in_password()