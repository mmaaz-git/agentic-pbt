"""Minimal reproduction of get_conn_string bug with bracket in hostname."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse

# Bug: Hostname containing "[" causes Invalid IPv6 URL error
hostname_with_bracket = "host[name"
result = get_conn_string(
    username="testuser",
    password="testpass",
    hostname=hostname_with_bracket,
    db_name="testdb",
    port="5432"
)
print(f"Generated URL: {result}")

try:
    parsed = urlparse(result)
    print(f"Parsed hostname: {parsed.hostname}")
except ValueError as e:
    print(f"ERROR parsing URL: {e}")
    print("This is a bug - hostname with '[' should be properly escaped or rejected")
    print("The function creates an invalid URL that cannot be parsed")