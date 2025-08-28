"""Property-based tests for dagster_postgres.utils module."""

import sys
import os
import time
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse, parse_qs, unquote

import pytest
from hypothesis import given, strategies as st, assume, settings

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import (
    get_conn_string,
    pg_url_from_config,
    retry_pg_creation_fn,
    retry_pg_connection_fn,
    DagsterPostgresException,
)
import psycopg2.errorcodes
import psycopg2.extensions


# Strategy for generating PostgreSQL connection parameters
@st.composite
def postgres_params(draw):
    """Generate valid PostgreSQL connection parameters."""
    # Include special characters that need URL encoding
    special_chars = "@:/?#[]!$&'()*+,;= %\t\n\r"
    
    username = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
    password = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
    hostname = draw(st.one_of(
        st.just("localhost"),
        st.just("127.0.0.1"),
        st.from_regex(r"[a-z][a-z0-9\-]{0,20}(\.[a-z][a-z0-9\-]{0,20}){0,3}", fullmatch=True),
        st.from_regex(r"(\d{1,3}\.){3}\d{1,3}", fullmatch=True).filter(
            lambda ip: all(0 <= int(part) <= 255 for part in ip.split('.'))
        )
    ))
    db_name = draw(st.text(min_size=1, max_size=30, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="/?#")))
    port = draw(st.one_of(
        st.just("5432"),
        st.integers(min_value=1, max_value=65535).map(str)
    ))
    
    return {
        "username": username,
        "password": password,
        "hostname": hostname,
        "db_name": db_name,
        "port": port,
    }


@st.composite
def url_params(draw):
    """Generate valid URL query parameters."""
    keys = draw(st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        min_size=0,
        max_size=5,
        unique=True
    ))
    
    if not keys:
        return None
    
    params = {}
    for key in keys:
        value = draw(st.text(min_size=0, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
        params[key] = value
    
    return params


@given(params=postgres_params(), url_params=url_params())
@settings(max_examples=200)
def test_get_conn_string_produces_parseable_urls(params, url_params):
    """Test that get_conn_string produces valid, parseable PostgreSQL URLs."""
    
    # Generate connection string
    conn_string = get_conn_string(
        username=params["username"],
        password=params["password"],
        hostname=params["hostname"],
        db_name=params["db_name"],
        port=params["port"],
        params=url_params
    )
    
    # Parse the URL - this should not raise an exception
    parsed = urlparse(conn_string)
    
    # Check that all components are present
    assert parsed.scheme == "postgresql"
    assert parsed.hostname == params["hostname"]
    assert str(parsed.port) == params["port"]
    assert parsed.path.lstrip("/") == params["db_name"]
    
    # Check username and password are properly encoded
    # They should be extractable after unquoting
    if parsed.username:
        assert unquote(parsed.username) == params["username"]
    if parsed.password:
        assert unquote(parsed.password) == params["password"]
    
    # Check query params if provided
    if url_params:
        query_dict = parse_qs(parsed.query)
        # Each param should be present (values are lists in parse_qs)
        for key, value in url_params.items():
            assert key in query_dict
            # parse_qs returns lists, get first element
            assert unquote(query_dict[key][0]) == str(value)


@given(params=postgres_params())
def test_get_conn_string_with_different_schemes(params):
    """Test that get_conn_string works with different schemes."""
    schemes = ["postgresql", "postgresql+psycopg2", "postgres"]
    
    for scheme in schemes:
        conn_string = get_conn_string(
            username=params["username"],
            password=params["password"],
            hostname=params["hostname"],
            db_name=params["db_name"],
            port=params["port"],
            scheme=scheme
        )
        
        parsed = urlparse(conn_string)
        assert parsed.scheme == scheme


@st.composite
def config_values(draw):
    """Generate config values for pg_url_from_config."""
    choice = draw(st.integers(min_value=0, max_value=2))
    
    if choice == 0:
        # Only postgres_url
        return {"postgres_url": draw(st.text(min_size=1))}
    elif choice == 1:
        # Only postgres_db
        params = draw(postgres_params())
        return {"postgres_db": params}
    else:
        # Both (should fail)
        params = draw(postgres_params())
        return {
            "postgres_url": draw(st.text(min_size=1)),
            "postgres_db": params
        }


@given(config=config_values())
def test_pg_url_from_config_invariant(config):
    """Test that pg_url_from_config enforces exactly one of postgres_url or postgres_db."""
    
    has_url = "postgres_url" in config
    has_db = "postgres_db" in config
    
    if has_url and has_db:
        # Should raise an error
        with pytest.raises(Exception) as exc_info:
            pg_url_from_config(config)
        assert "exactly one of" in str(exc_info.value)
    elif not has_url and not has_db:
        # Should raise an error
        with pytest.raises(Exception) as exc_info:
            pg_url_from_config(config)
        assert "exactly one of" in str(exc_info.value)
    else:
        # Should succeed
        result = pg_url_from_config(config)
        assert result is not None
        
        if has_url:
            assert result == config["postgres_url"]
        else:
            # Should call get_conn_string
            assert "postgresql://" in result or "postgres://" in result


@given(
    retry_limit=st.integers(min_value=0, max_value=10),
    retry_wait=st.floats(min_value=0.001, max_value=0.1)
)
def test_retry_pg_creation_fn_respects_retry_limit(retry_limit, retry_wait):
    """Test that retry_pg_creation_fn respects the retry limit."""
    
    call_count = 0
    
    def failing_fn():
        nonlocal call_count
        call_count += 1
        # Simulate a duplicate table error that should be retried
        error = psycopg2.ProgrammingError()
        error.pgcode = psycopg2.errorcodes.DUPLICATE_TABLE
        raise error
    
    with pytest.raises(DagsterPostgresException) as exc_info:
        retry_pg_creation_fn(failing_fn, retry_limit=retry_limit, retry_wait=retry_wait)
    
    # Should have called fn exactly retry_limit + 1 times (initial + retries)
    assert call_count == retry_limit + 1
    assert "too many retries" in str(exc_info.value)


@given(
    retry_limit=st.integers(min_value=0, max_value=10),
    retry_wait=st.floats(min_value=0.001, max_value=0.01)
)
def test_retry_pg_connection_fn_respects_retry_limit(retry_limit, retry_wait):
    """Test that retry_pg_connection_fn respects the retry limit."""
    
    call_count = 0
    
    def failing_fn():
        nonlocal call_count
        call_count += 1
        raise psycopg2.OperationalError("Connection failed")
    
    with pytest.raises(DagsterPostgresException) as exc_info:
        retry_pg_connection_fn(failing_fn, retry_limit=retry_limit, retry_wait=retry_wait)
    
    # Should have called fn exactly retry_limit + 1 times (initial + retries)
    assert call_count == retry_limit + 1
    assert "too many retries" in str(exc_info.value)


@given(
    success_after=st.integers(min_value=0, max_value=5),
    retry_limit=st.integers(min_value=0, max_value=10),
    retry_wait=st.floats(min_value=0.001, max_value=0.01)
)
def test_retry_pg_creation_fn_eventually_succeeds(success_after, retry_limit, retry_wait):
    """Test that retry_pg_creation_fn returns result when function eventually succeeds."""
    
    assume(success_after <= retry_limit)
    
    call_count = 0
    expected_result = "success"
    
    def sometimes_failing_fn():
        nonlocal call_count
        call_count += 1
        if call_count <= success_after:
            error = psycopg2.ProgrammingError()
            error.pgcode = psycopg2.errorcodes.DUPLICATE_TABLE
            raise error
        return expected_result
    
    result = retry_pg_creation_fn(sometimes_failing_fn, retry_limit=retry_limit, retry_wait=retry_wait)
    
    assert result == expected_result
    assert call_count == success_after + 1


@given(
    success_after=st.integers(min_value=0, max_value=5),
    retry_limit=st.integers(min_value=0, max_value=10),
    retry_wait=st.floats(min_value=0.001, max_value=0.01)
)
def test_retry_pg_connection_fn_eventually_succeeds(success_after, retry_limit, retry_wait):
    """Test that retry_pg_connection_fn returns result when function eventually succeeds."""
    
    assume(success_after <= retry_limit)
    
    call_count = 0
    expected_result = "connection_established"
    
    def sometimes_failing_fn():
        nonlocal call_count
        call_count += 1
        if call_count <= success_after:
            raise psycopg2.OperationalError("Connection failed")
        return expected_result
    
    result = retry_pg_connection_fn(sometimes_failing_fn, retry_limit=retry_limit, retry_wait=retry_wait)
    
    assert result == expected_result
    assert call_count == success_after + 1


@given(
    username=st.text(min_size=1, max_size=50).filter(lambda x: "@" in x or ":" in x or "/" in x),
    password=st.text(min_size=1, max_size=50).filter(lambda x: "@" in x or ":" in x or "/" in x)
)
def test_get_conn_string_handles_special_chars_in_credentials(username, password):
    """Test that special characters in username/password are properly escaped."""
    
    conn_string = get_conn_string(
        username=username,
        password=password,
        hostname="localhost",
        db_name="testdb",
        port="5432"
    )
    
    # Parse and verify we can recover the original values
    parsed = urlparse(conn_string)
    
    # Unquoting should give us back the original values
    if parsed.username:
        assert unquote(parsed.username) == username
    if parsed.password:
        assert unquote(parsed.password) == password


if __name__ == "__main__":
    pytest.main([__file__, "-v"])