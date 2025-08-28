import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from urllib.parse import quote, unquote, urlparse, parse_qs
import pytest
from hypothesis import given, strategies as st, assume, settings
from dagster_postgres.utils import (
    get_conn_string,
    pg_url_from_config,
    retry_pg_creation_fn,
    retry_pg_connection_fn,
    DagsterPostgresException
)
from dagster._core.errors import DagsterInvariantViolationError
import psycopg2


# Property 1: get_conn_string should properly encode special characters
@given(
    username=st.text(min_size=1, max_size=50),
    password=st.text(min_size=1, max_size=50),
    hostname=st.text(min_size=1, max_size=50).filter(lambda x: ':' not in x and '@' not in x),
    db_name=st.text(min_size=1, max_size=50).filter(lambda x: '?' not in x and '/' not in x),
    port=st.text(min_size=1, max_size=5).filter(lambda x: x.isdigit()),
)
def test_get_conn_string_encoding(username, password, hostname, db_name, port):
    conn_str = get_conn_string(username, password, hostname, db_name, port)
    
    # Parse the connection string
    parsed = urlparse(conn_str)
    
    # Check that username and password are properly encoded/decoded
    assert unquote(parsed.username) == username
    assert unquote(parsed.password) == password
    assert parsed.hostname == hostname
    assert parsed.port == int(port)
    assert parsed.path == f"/{db_name}"


# Property 2: get_conn_string with params should properly append them
@given(
    params=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda x: '=' not in x and '&' not in x),
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=5
    )
)
def test_get_conn_string_params(params):
    conn_str = get_conn_string("user", "pass", "host", "db", params=params)
    
    parsed = urlparse(conn_str)
    query_params = parse_qs(parsed.query)
    
    # All params should be present in the query string
    for key, value in params.items():
        assert key in query_params
        assert query_params[key][0] == str(value)


# Property 3: pg_url_from_config must have exactly one of postgres_url or postgres_db
@given(
    has_url=st.booleans(),
    has_db=st.booleans(),
    url_value=st.text(min_size=1),
    db_value=st.dictionaries(
        st.sampled_from(["username", "password", "hostname", "db_name"]),
        st.text(min_size=1),
        min_size=4,
        max_size=4
    )
)
def test_pg_url_from_config_invariant(has_url, has_db, url_value, db_value):
    config = {}
    if has_url:
        config["postgres_url"] = url_value
    if has_db:
        config["postgres_db"] = db_value
    
    # Should work if exactly one is present
    if has_url ^ has_db:  # XOR - exactly one is True
        result = pg_url_from_config(config)
        if has_url:
            assert result == url_value
        else:
            # Should call get_conn_string with the db params
            assert "postgresql://" in result
    else:
        # Should fail if both or neither are present
        with pytest.raises(DagsterInvariantViolationError) as exc_info:
            pg_url_from_config(config)
        assert "must have exactly one of" in str(exc_info.value)


# Property 4: retry_pg_creation_fn should retry up to limit times
@given(
    retry_limit=st.integers(min_value=0, max_value=5),
    fail_count=st.integers(min_value=0, max_value=10)
)
def test_retry_pg_creation_fn_limit(retry_limit, fail_count):
    call_count = [0]
    
    def failing_fn():
        call_count[0] += 1
        if call_count[0] <= fail_count:
            # Simulate duplicate table error
            error = psycopg2.ProgrammingError()
            error.pgcode = psycopg2.errorcodes.DUPLICATE_TABLE
            raise error
        return "success"
    
    if fail_count <= retry_limit:
        # Should succeed after retries
        result = retry_pg_creation_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.001)
        assert result == "success"
        assert call_count[0] == fail_count + 1
    else:
        # Should raise after too many retries
        with pytest.raises(DagsterPostgresException) as exc_info:
            retry_pg_creation_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.001)
        assert "too many retries" in str(exc_info.value)
        # Should have tried retry_limit + 1 times (initial + retries)
        assert call_count[0] == retry_limit + 1


# Property 5: retry_pg_connection_fn should retry up to limit times
@given(
    retry_limit=st.integers(min_value=1, max_value=5),
    fail_count=st.integers(min_value=0, max_value=10)
)
def test_retry_pg_connection_fn_limit(retry_limit, fail_count):
    call_count = [0]
    
    def failing_fn():
        call_count[0] += 1
        if call_count[0] <= fail_count:
            raise psycopg2.OperationalError("Connection failed")
        return "connected"
    
    if fail_count <= retry_limit:
        # Should succeed after retries
        result = retry_pg_connection_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.001)
        assert result == "connected"
        assert call_count[0] == fail_count + 1
    else:
        # Should raise after too many retries
        with pytest.raises(DagsterPostgresException) as exc_info:
            retry_pg_connection_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.001)
        assert "too many retries" in str(exc_info.value)
        # Should have tried retry_limit + 1 times (initial + retries)
        assert call_count[0] == retry_limit + 1


# Property 6: Special characters in connection string components should round-trip correctly
@given(
    username=st.text(min_size=1).filter(lambda x: x),
    password=st.text(min_size=1).filter(lambda x: x),
)
@settings(max_examples=100)
def test_get_conn_string_special_chars_roundtrip(username, password):
    # Test that special characters that need URL encoding work correctly
    conn_str = get_conn_string(username, password, "localhost", "testdb")
    
    # Parse and verify we can recover the original values
    parsed = urlparse(conn_str)
    
    # These should round-trip correctly through URL encoding
    recovered_username = unquote(parsed.username) if parsed.username else ""
    recovered_password = unquote(parsed.password) if parsed.password else ""
    
    assert recovered_username == username
    assert recovered_password == password


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])