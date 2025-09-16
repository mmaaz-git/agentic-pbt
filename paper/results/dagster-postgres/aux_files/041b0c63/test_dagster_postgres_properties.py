import sys
import os
from urllib.parse import urlparse, parse_qs, unquote
import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.provisional import urls

# Add the site-packages directory to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

from dagster_postgres.utils import (
    get_conn_string, 
    pg_url_from_config,
    retry_pg_creation_fn,
    retry_pg_connection_fn,
    DagsterPostgresException
)


# Strategy for valid database components
valid_username = st.text(min_size=1, max_size=50).filter(lambda x: x and not x.isspace())
valid_password = st.text(min_size=1, max_size=50)
valid_hostname = st.from_regex(r'^[a-zA-Z0-9.-]+$', fullmatch=True).filter(lambda x: len(x) > 0 and len(x) <= 100)
valid_db_name = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters='/\\?#'), min_size=1, max_size=50).filter(lambda x: not x.isspace())
valid_port = st.integers(min_value=1, max_value=65535).map(str)
valid_scheme = st.sampled_from(['postgresql', 'postgres', 'postgresql+psycopg2'])

# Strategy for query parameters
query_params = st.dictionaries(
    keys=st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()),
    values=st.text(min_size=0, max_size=50),
    max_size=5
)


class TestGetConnString:
    """Test properties of the get_conn_string function."""
    
    @given(
        username=valid_username,
        password=valid_password,
        hostname=valid_hostname,
        db_name=valid_db_name,
        port=valid_port,
        params=st.one_of(st.none(), query_params),
        scheme=valid_scheme
    )
    @settings(max_examples=500)
    def test_get_conn_string_produces_valid_url(self, username, password, hostname, db_name, port, params, scheme):
        """Property: get_conn_string should always produce a parseable URL."""
        conn_string = get_conn_string(username, password, hostname, db_name, port, params, scheme)
        
        # Should be parseable as a URL
        parsed = urlparse(conn_string)
        assert parsed.scheme == scheme
        assert parsed.hostname == hostname
        assert str(parsed.port) == port
        assert parsed.path == f'/{db_name}'
        
    @given(
        username=st.text(min_size=1, max_size=50),
        password=st.text(min_size=1, max_size=50),
        hostname=valid_hostname,
        db_name=valid_db_name,
        port=valid_port
    )
    @settings(max_examples=500)
    def test_get_conn_string_escapes_special_chars(self, username, password, hostname, db_name, port):
        """Property: Special characters in username/password should be properly escaped."""
        conn_string = get_conn_string(username, password, hostname, db_name, port)
        
        # The URL should be parseable even with special characters
        parsed = urlparse(conn_string)
        
        # Username and password should be extractable
        if parsed.username:
            # Unquoting should give us back the original
            assert unquote(parsed.username) == username
        if parsed.password:
            assert unquote(parsed.password) == password
            
    @given(
        username=st.text(alphabet='@:/?#[]!$&\'()*+,;=', min_size=1, max_size=20),
        password=st.text(alphabet='@:/?#[]!$&\'()*+,;=', min_size=1, max_size=20),
        hostname=valid_hostname,
        db_name=valid_db_name
    )
    @settings(max_examples=200)
    def test_get_conn_string_handles_url_special_chars(self, username, password, hostname, db_name):
        """Property: URL special characters should be properly encoded."""
        conn_string = get_conn_string(username, password, hostname, db_name)
        
        # Should not raise when parsing
        parsed = urlparse(conn_string)
        
        # The connection string should contain encoded versions
        assert '@' in conn_string  # @ separator should be there
        assert f'{hostname}:' in conn_string  # hostname should be intact
        

class TestPgUrlFromConfig:
    """Test properties of pg_url_from_config function."""
    
    @given(
        postgres_url=st.text(min_size=10, max_size=200),
        postgres_db_config=st.dictionaries(
            keys=st.just('username'),
            values=valid_username,
            min_size=1, max_size=1
        )
    )
    def test_pg_url_from_config_invariant_mutex(self, postgres_url, postgres_db_config):
        """Property: Config must have exactly one of postgres_url or postgres_db (not both)."""
        # Test the invariant that both cannot be present
        config_with_both = {
            'postgres_url': postgres_url,
            'postgres_db': postgres_db_config
        }
        
        with pytest.raises(Exception) as exc_info:
            pg_url_from_config(config_with_both)
        
        assert "exactly one of" in str(exc_info.value)
        
    @given(st.data())
    def test_pg_url_from_config_invariant_at_least_one(self, data):
        """Property: Config must have at least one of postgres_url or postgres_db."""
        # Test empty config
        with pytest.raises(Exception) as exc_info:
            pg_url_from_config({})
        
        assert "exactly one of" in str(exc_info.value)
        
    @given(postgres_url=st.text(min_size=1, max_size=200))
    @settings(max_examples=100)
    def test_pg_url_from_config_returns_url_unchanged(self, postgres_url):
        """Property: When postgres_url is provided, it should be returned unchanged."""
        config = {'postgres_url': postgres_url}
        result = pg_url_from_config(config)
        assert result == postgres_url
        
    @given(
        username=valid_username,
        password=valid_password,
        hostname=valid_hostname,
        db_name=valid_db_name,
        port=valid_port
    )
    @settings(max_examples=100)
    def test_pg_url_from_config_constructs_from_db_config(self, username, password, hostname, db_name, port):
        """Property: When postgres_db is provided, a valid connection string should be constructed."""
        config = {
            'postgres_db': {
                'username': username,
                'password': password,
                'hostname': hostname,
                'db_name': db_name,
                'port': port
            }
        }
        result = pg_url_from_config(config)
        
        # Should produce a valid URL
        parsed = urlparse(result)
        assert parsed.scheme in ['postgresql', 'postgres']
        assert parsed.hostname == hostname
        

class TestRetryFunctions:
    """Test properties of retry functions."""
    
    @given(
        retry_limit=st.integers(min_value=0, max_value=10),
        retry_wait=st.floats(min_value=0.001, max_value=0.01)
    )
    @settings(max_examples=100, deadline=5000)
    def test_retry_pg_creation_fn_respects_limit(self, retry_limit, retry_wait):
        """Property: retry_pg_creation_fn should fail after retry_limit attempts."""
        import psycopg2.errorcodes
        
        attempt_count = 0
        
        def failing_fn():
            nonlocal attempt_count
            attempt_count += 1
            # Raise a retryable error (DUPLICATE_TABLE)
            error = psycopg2.IntegrityError()
            error.pgcode = psycopg2.errorcodes.DUPLICATE_TABLE
            raise error
        
        with pytest.raises(DagsterPostgresException) as exc_info:
            retry_pg_creation_fn(failing_fn, retry_limit=retry_limit, retry_wait=retry_wait)
        
        assert "too many retries" in str(exc_info.value)
        # Should attempt retry_limit + 1 times (initial + retries)
        assert attempt_count == retry_limit + 1
        
    @given(
        retry_limit=st.integers(min_value=1, max_value=5),
        success_on_attempt=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100, deadline=2000)
    def test_retry_pg_creation_fn_succeeds_within_limit(self, retry_limit, success_on_attempt):
        """Property: Should succeed if function succeeds within retry limit."""
        assume(success_on_attempt <= retry_limit + 1)
        
        attempt_count = 0
        
        def sometimes_failing_fn():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < success_on_attempt:
                error = psycopg2.IntegrityError()
                error.pgcode = psycopg2.errorcodes.DUPLICATE_TABLE
                raise error
            return "success"
        
        result = retry_pg_creation_fn(sometimes_failing_fn, retry_limit=retry_limit, retry_wait=0.001)
        assert result == "success"
        assert attempt_count == success_on_attempt
        
    @given(
        retry_limit=st.integers(min_value=0, max_value=10),
        retry_wait=st.floats(min_value=0.001, max_value=0.01)
    )
    @settings(max_examples=100, deadline=5000)
    def test_retry_pg_connection_fn_respects_limit(self, retry_limit, retry_wait):
        """Property: retry_pg_connection_fn should fail after retry_limit attempts."""
        attempt_count = 0
        
        def failing_fn():
            nonlocal attempt_count
            attempt_count += 1
            raise psycopg2.OperationalError("Connection failed")
        
        with pytest.raises(DagsterPostgresException) as exc_info:
            retry_pg_connection_fn(failing_fn, retry_limit=retry_limit, retry_wait=retry_wait)
        
        assert "too many retries" in str(exc_info.value)
        # Should attempt retry_limit + 1 times
        assert attempt_count == retry_limit + 1
        
    @given(st.data())
    @settings(max_examples=50, deadline=2000)
    def test_retry_functions_non_retryable_errors(self, data):
        """Property: Non-retryable errors should be raised immediately."""
        
        def fn_with_non_retryable_error():
            raise ValueError("This is not a database error")
        
        # Should raise immediately without retrying
        with pytest.raises(ValueError) as exc_info:
            retry_pg_creation_fn(fn_with_non_retryable_error, retry_limit=5, retry_wait=0.001)
        
        assert "This is not a database error" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            retry_pg_connection_fn(fn_with_non_retryable_error, retry_limit=5, retry_wait=0.001)
        
        assert "This is not a database error" in str(exc_info.value)