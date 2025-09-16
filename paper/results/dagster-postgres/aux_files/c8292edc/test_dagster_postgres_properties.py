"""Property-based tests for dagster_postgres.schedule_storage module."""

import sys
import time
from urllib.parse import unquote, urlparse, parse_qs
from hypothesis import given, strategies as st, assume, settings

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

# Import only what we need, with fallbacks for missing modules
try:
    import psycopg2
    import psycopg2.errorcodes
except ImportError:
    # Create mock psycopg2 for testing without database
    class MockPsycopg2:
        class ProgrammingError(Exception):
            def __init__(self):
                self.pgcode = "42P07"  # DUPLICATE_TABLE
        
        class OperationalError(Exception):
            pass
        
        class errorcodes:
            DUPLICATE_TABLE = "42P07"
    
    psycopg2 = MockPsycopg2()

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None

from dagster_postgres.utils import (
    get_conn_string,
    pg_url_from_config,
    retry_pg_creation_fn,
    retry_pg_connection_fn,
    DagsterPostgresException,
)


# Test property 1: pg_url_from_config must have exactly one of postgres_url or postgres_db
@given(
    postgres_url=st.one_of(st.none(), st.text(min_size=1)),
    postgres_db=st.one_of(
        st.none(),
        st.fixed_dictionaries({
            "username": st.text(min_size=1),
            "password": st.text(min_size=1),
            "hostname": st.text(min_size=1),
            "db_name": st.text(min_size=1),
            "port": st.text(min_size=1),
        })
    )
)
def test_pg_url_from_config_exactly_one(postgres_url, postgres_db):
    """Test that pg_url_from_config requires exactly one of postgres_url or postgres_db."""
    config = {}
    if postgres_url is not None:
        config["postgres_url"] = postgres_url
    if postgres_db is not None:
        config["postgres_db"] = postgres_db
    
    # Should only work if exactly one is provided
    has_url = postgres_url is not None
    has_db = postgres_db is not None
    
    if has_url and not has_db:
        # Should succeed
        result = pg_url_from_config(config)
        assert result == postgres_url
    elif has_db and not has_url:
        # Should succeed
        result = pg_url_from_config(config)
        assert isinstance(result, str)
    else:
        # Should fail if both or neither
        try:
            pg_url_from_config(config)
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "must have exactly one of" in str(e)


# Test property 2: get_conn_string should properly quote special characters
@given(
    username=st.text(min_size=1),
    password=st.text(min_size=1),
    hostname=st.text(min_size=1).filter(lambda x: "/" not in x and "@" not in x and ":" not in x),
    db_name=st.text(min_size=1).filter(lambda x: "/" not in x and "?" not in x),
    port=st.text(min_size=1, max_size=5, alphabet="0123456789"),
    scheme=st.sampled_from(["postgresql", "postgres", "postgresql+psycopg2"])
)
def test_get_conn_string_quoting(username, password, hostname, db_name, port, scheme):
    """Test that get_conn_string properly quotes/escapes special characters."""
    # Call the function
    result = get_conn_string(username, password, hostname, db_name, port, scheme=scheme)
    
    # Parse the resulting URL
    parsed = urlparse(result)
    
    # Check scheme
    assert parsed.scheme == scheme
    
    # Check that username and password are properly decoded
    if parsed.username:
        decoded_username = unquote(parsed.username)
        assert decoded_username == username
    
    if parsed.password:
        decoded_password = unquote(parsed.password)
        assert decoded_password == password
    
    # Check hostname and port
    assert parsed.hostname == hostname
    assert str(parsed.port) == port
    
    # Check database name
    assert parsed.path.lstrip("/") == db_name


# Test property 3: get_conn_string with params should properly encode them
@given(
    username=st.text(min_size=1),
    password=st.text(min_size=1),
    hostname=st.text(min_size=1).filter(lambda x: "/" not in x and "@" not in x and ":" not in x),
    db_name=st.text(min_size=1).filter(lambda x: "/" not in x and "?" not in x),
    port=st.text(min_size=1, max_size=5, alphabet="0123456789"),
    params=st.dictionaries(
        st.text(min_size=1).filter(lambda x: "=" not in x and "&" not in x),
        st.text(min_size=1),
        min_size=1,
        max_size=3
    )
)
def test_get_conn_string_with_params(username, password, hostname, db_name, port, params):
    """Test that get_conn_string properly encodes query parameters."""
    result = get_conn_string(username, password, hostname, db_name, port, params=params)
    
    # Parse the URL
    parsed = urlparse(result)
    
    # Parse query string
    parsed_params = parse_qs(parsed.query)
    
    # Check that all params are present
    for key, value in params.items():
        assert key in parsed_params
        # parse_qs returns lists
        assert parsed_params[key][0] == str(value)


# Test property 4: retry_pg_creation_fn should respect retry limits
@given(
    retry_limit=st.integers(min_value=0, max_value=5),
    should_fail=st.booleans()
)
@settings(deadline=5000)  # Allow more time for retries
def test_retry_pg_creation_fn_respects_limit(retry_limit, should_fail):
    """Test that retry_pg_creation_fn respects the retry limit."""
    call_count = [0]
    
    def failing_fn():
        call_count[0] += 1
        if should_fail or call_count[0] <= retry_limit:
            # Simulate a duplicate table error
            error = psycopg2.ProgrammingError()
            error.pgcode = psycopg2.errorcodes.DUPLICATE_TABLE
            raise error
        return "success"
    
    if should_fail:
        # Should exhaust retries and raise DagsterPostgresException
        try:
            retry_pg_creation_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.01)
            assert False, "Should have raised DagsterPostgresException"
        except DagsterPostgresException as e:
            assert "too many retries" in str(e)
            # Should have tried retry_limit + 1 times (initial + retries)
            assert call_count[0] == retry_limit + 1
    else:
        # Should succeed eventually
        result = retry_pg_creation_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.01)
        assert result == "success"


# Test property 5: retry_pg_connection_fn should use exponential backoff
@given(
    retry_limit=st.integers(min_value=1, max_value=3),
    base_delay=st.floats(min_value=0.01, max_value=0.1)
)
@settings(deadline=10000)  # Allow more time for retries with backoff
def test_retry_pg_connection_fn_exponential_backoff(retry_limit, base_delay):
    """Test that retry_pg_connection_fn uses exponential backoff."""
    call_times = []
    
    def failing_fn():
        call_times.append(time.time())
        if len(call_times) <= retry_limit:
            raise psycopg2.OperationalError("Connection failed")
        return "success"
    
    start_time = time.time()
    result = retry_pg_connection_fn(failing_fn, retry_limit=retry_limit, retry_wait=base_delay)
    assert result == "success"
    
    # Check that delays increase (roughly exponentially)
    if len(call_times) > 2:
        delays = []
        for i in range(1, len(call_times)):
            delays.append(call_times[i] - call_times[i-1])
        
        # Later delays should generally be larger than earlier ones (with some tolerance for jitter)
        # We can't be too strict because of jitter
        for i in range(1, len(delays)):
            # Allow for jitter but expect general increase
            assert delays[i] >= delays[i-1] * 0.5  # Allow some variance due to jitter


# Test property 6: Invalid URL schemes should be preserved
@given(
    scheme=st.text(min_size=1, max_size=20).filter(lambda x: ":" not in x and "/" not in x)
)
def test_get_conn_string_preserves_scheme(scheme):
    """Test that get_conn_string preserves any scheme provided."""
    result = get_conn_string(
        username="user",
        password="pass",
        hostname="localhost",
        db_name="db",
        port="5432",
        scheme=scheme
    )
    
    parsed = urlparse(result)
    assert parsed.scheme == scheme