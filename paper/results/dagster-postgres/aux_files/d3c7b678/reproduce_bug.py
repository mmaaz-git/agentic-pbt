#!/usr/bin/env python3
import sys
from urllib.parse import urlparse

sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')
from dagster_postgres.utils import get_conn_string

print("Bug reproduction: Passwords with URL delimiters break connection string parsing\n")

# Test case 1: Password with colon and slash
print("Test 1: Password = ':/'")
conn_str = get_conn_string(
    username="user",
    password=":/",
    hostname="localhost",
    db_name="testdb",
    port="5432"
)
print(f"Generated: {conn_str}")
parsed = urlparse(conn_str)
print(f"Parsed hostname: {parsed.hostname}")
print(f"Parsed port: {parsed.port}")
try:
    port_value = parsed.port
    print(f"Port parsing succeeded: {port_value}")
except ValueError as e:
    print(f"ERROR: Port parsing failed: {e}")
print()

# Test case 2: Password with single slash
print("Test 2: Password = '/'")
conn_str = get_conn_string(
    username="user",
    password="/",
    hostname="localhost",
    db_name="testdb",
    port="5432"
)
print(f"Generated: {conn_str}")
parsed = urlparse(conn_str)
print(f"Parsed hostname: {parsed.hostname}")
print(f"Parsed port: {parsed.port}")
print(f"Parsed path: {parsed.path}")
print(f"Expected path: /testdb")
print()

# Test case 3: Password with at symbol
print("Test 3: Password = '@'")
conn_str = get_conn_string(
    username="user",
    password="@",
    hostname="localhost",
    db_name="testdb",
    port="5432"
)
print(f"Generated: {conn_str}")
parsed = urlparse(conn_str)
print(f"Parsed hostname: {parsed.hostname}")
print(f"Parsed username: {parsed.username}")
print(f"Parsed password: {parsed.password}")
print()

# Show the issue
print("THE BUG:")
print("The get_conn_string function uses quote() to encode username and password,")
print("but quote() does NOT encode '/', ':', and '@' by default.")
print("These characters have special meaning in URLs and break parsing!")
print()
print("URLs with unencoded special chars in passwords are ambiguous:")
print("postgresql://user:pass/word@host:5432/db")
print("Is the password 'pass' with path '/word@host:5432/db'?")
print("Or is the password 'pass/word' with hostname 'host'?")