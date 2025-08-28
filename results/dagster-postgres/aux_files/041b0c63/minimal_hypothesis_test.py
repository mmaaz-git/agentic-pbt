#!/usr/bin/env python3
"""Minimal property-based test runner for dagster_postgres."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, Phase, Verbosity
from urllib.parse import urlparse, unquote
import traceback

# Import the function to test
from dagster_postgres.utils import get_conn_string

# Define test strategies
valid_username = st.text(min_size=1, max_size=20).filter(lambda x: x and not x.isspace())
valid_password = st.text(min_size=1, max_size=20)
valid_hostname = st.from_regex(r'^[a-zA-Z0-9.-]+$', fullmatch=True).filter(lambda x: 0 < len(x) <= 50)
valid_db_name = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters='/\\?#'), min_size=1, max_size=20).filter(lambda x: not x.isspace())

# Run a simple property test
print("Testing get_conn_string URL encoding property...")
print("=" * 60)

@given(
    username=st.text(alphabet='@:/?#[]!$&\'()*+,;=', min_size=1, max_size=10),
    password=st.text(alphabet='@:/?#[]!$&\'()*+,;=', min_size=1, max_size=10),
    hostname=valid_hostname,
    db_name=valid_db_name
)
@settings(
    max_examples=100,
    phases=[Phase.generate, Phase.target],
    verbosity=Verbosity.verbose,
    print_blob=True
)
def test_special_char_encoding(username, password, hostname, db_name):
    """Test that special characters are properly encoded in URLs."""
    conn_string = get_conn_string(username, password, hostname, db_name)
    
    # Parse the URL
    parsed = urlparse(conn_string)
    
    # Check that we can decode back to original values
    if parsed.username:
        decoded_username = unquote(parsed.username)
        assert decoded_username == username, f"Username mismatch: {username!r} != {decoded_username!r}"
    
    if parsed.password:
        decoded_password = unquote(parsed.password)
        assert decoded_password == password, f"Password mismatch: {password!r} != {decoded_password!r}"

# Run the test
try:
    test_special_char_encoding()
    print("✓ All property tests passed!")
except AssertionError as e:
    print(f"✗ Property test failed!")
    print(f"Error: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"✗ Test error: {e}")
    traceback.print_exc()

print("\nNow testing with manually crafted edge cases...")
edge_cases = [
    ("user@host", "pass@word", "localhost", "db"),
    ("user:pass", "real:pass", "localhost", "db"),
    ("user", "pass/word", "localhost", "db"),
    ("user", "pass#hash", "localhost", "db"),
    ("user?query", "pass", "localhost", "db"),
]

for username, password, hostname, db_name in edge_cases:
    print(f"\nTesting: username={username!r}, password={password!r}")
    conn_string = get_conn_string(username, password, hostname, db_name)
    print(f"  Connection string: {conn_string}")
    
    parsed = urlparse(conn_string)
    if parsed.username and parsed.password:
        decoded_user = unquote(parsed.username)
        decoded_pass = unquote(parsed.password)
        
        if decoded_user != username:
            print(f"  ⚠️ Username mismatch: {username!r} != {decoded_user!r}")
        if decoded_pass != password:
            print(f"  ⚠️ Password mismatch: {password!r} != {decoded_pass!r}")
    else:
        print(f"  ⚠️ Could not parse username/password from URL")