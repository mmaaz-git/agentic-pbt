"""Test for scheme preservation bug."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse

# Test with numeric scheme (which is technically valid but unusual)
result = get_conn_string(
    username="user",
    password="pass", 
    hostname="localhost",
    db_name="db",
    port="5432",
    scheme="0"
)
print(f"Generated URL: {result}")
parsed = urlparse(result)
print(f"Parsed scheme: '{parsed.scheme}'")

if parsed.scheme != "0":
    print(f"BUG: Scheme '0' was not preserved, got '{parsed.scheme}' instead")
    print("This happens because urlparse doesn't recognize '0' as a valid scheme")