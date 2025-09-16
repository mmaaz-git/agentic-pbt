#!/usr/bin/env python3
"""Verify the slash bug is legitimate and create minimal reproduction."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import get_conn_string
from urllib.parse import urlparse, unquote, quote

print("Minimal Bug Reproduction")
print("=" * 60)

# Real-world example: password with slash
username = "postgres_user"
password = "secure/pass123"  # Valid password that could be used in production
hostname = "db.example.com"
db_name = "production_db"

print(f"Input credentials:")
print(f"  Username: {username}")
print(f"  Password: {password}")
print(f"  Host: {hostname}")
print(f"  Database: {db_name}")
print()

# Generate connection string using dagster_postgres
conn_string = get_conn_string(username, password, hostname, db_name)
print(f"Generated URL: {conn_string}")
print()

# Try to parse it back
parsed = urlparse(conn_string)
print("Parsed URL components:")
print(f"  Username from URL: {parsed.username}")
print(f"  Password from URL: {parsed.password}")
print(f"  Hostname from URL: {parsed.hostname}")
print()

# Show the issue
if parsed.username != username or (parsed.password and unquote(parsed.password) != password):
    print("❌ BUG CONFIRMED: Cannot recover original credentials from URL!")
    print("   The URL is malformed and would fail to connect to the database.")
else:
    print("✓ URL correctly preserves credentials")

print()
print("Expected behavior:")
print("-" * 40)
# Show correct encoding
from urllib.parse import quote_plus
correct_password = quote(password, safe='')
correct_url = f"postgresql://{quote(username, safe='')}:{correct_password}@{hostname}:5432/{db_name}"
print(f"Correctly encoded URL: {correct_url}")
parsed_correct = urlparse(correct_url)
print(f"  Username: {unquote(parsed_correct.username) if parsed_correct.username else None}")
print(f"  Password: {unquote(parsed_correct.password) if parsed_correct.password else None}")

print()
print("Impact Assessment:")
print("-" * 40)
print("This bug affects any Dagster deployment where:")
print("1. PostgreSQL passwords contain forward slashes ('/')")
print("2. The configuration uses postgres_db instead of postgres_url")
print()
print("The resulting connection string is malformed and will fail to connect.")
print("This is a REAL bug that breaks database connectivity.")