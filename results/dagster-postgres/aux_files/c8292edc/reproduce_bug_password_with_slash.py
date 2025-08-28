"""Minimal reproduction of get_conn_string bug with special characters in password."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse

# Bug 1: Password containing ":/" corrupts the URL
password_with_colon_slash = ":/"
result = get_conn_string(
    username="testuser",
    password=password_with_colon_slash,
    hostname="localhost", 
    db_name="testdb",
    port="5432"
)
print(f"Generated URL: {result}")

try:
    parsed = urlparse(result)
    print(f"Parsed port: {parsed.port}")
except ValueError as e:
    print(f"ERROR parsing URL: {e}")
    print("This is a bug - the password should be properly quoted to avoid URL parsing errors")

print("\n" + "="*60 + "\n")

# Bug 2: Password containing "#" gets treated as URL fragment
password_with_hash = "pass#word"
result2 = get_conn_string(
    username="testuser",
    password=password_with_hash,
    hostname="localhost",
    db_name="testdb",
    port="5432"
)
print(f"Generated URL: {result2}")
parsed2 = urlparse(result2)
print(f"Parsed password: {parsed2.password}")
print(f"Parsed fragment: {parsed2.fragment}")

if parsed2.password != password_with_hash:
    print(f"BUG: Password was incorrectly parsed. Expected '{password_with_hash}' but got '{parsed2.password}'")
    print("The '#' character should be properly escaped in the password")