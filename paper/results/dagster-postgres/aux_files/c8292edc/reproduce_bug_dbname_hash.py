"""Minimal reproduction of get_conn_string bug with # in database name."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse, parse_qs

# Bug: Database name containing "#" causes params to be lost
db_name_with_hash = "test#db"
params = {"sslmode": "require", "connect_timeout": "10"}

result = get_conn_string(
    username="testuser",
    password="testpass",
    hostname="localhost",
    db_name=db_name_with_hash,
    port="5432",
    params=params
)
print(f"Generated URL: {result}")

parsed = urlparse(result)
parsed_params = parse_qs(parsed.query)

print(f"Parsed database name: {parsed.path.lstrip('/')}")
print(f"Parsed query params: {parsed_params}")
print(f"Parsed fragment: {parsed.fragment}")

if not parsed_params:
    print("BUG: Query parameters were lost!")
    print("The '#' in database name is being treated as a URL fragment marker")
    print("This causes all query parameters after it to be lost")