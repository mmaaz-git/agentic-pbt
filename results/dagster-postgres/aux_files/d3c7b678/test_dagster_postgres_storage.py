#!/usr/bin/env python3
import sys
import re
from urllib.parse import urlparse, parse_qs, unquote
from unittest.mock import Mock, patch
import time

# Add the dagster-postgres environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings
import dagster_postgres.storage
import dagster_postgres.utils
from dagster_postgres.utils import (
    get_conn_string, 
    pg_url_from_config, 
    retry_pg_creation_fn,
    retry_pg_connection_fn,
    DagsterPostgresException
)
from dagster_postgres.storage import DagsterPostgresStorage
import psycopg2
import sqlalchemy


# Strategy for PostgreSQL usernames and passwords that might contain special characters
special_chars_text = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Po", "Ps", "Pe", "Pi", "Pf", "Sm", "Sc", "Sk", "So")),
    min_size=1,
    max_size=50
)

# Strategy for valid hostnames
hostname_strategy = st.one_of(
    st.from_regex(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$', fullmatch=True),
    st.from_regex(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', fullmatch=True)  # IP addresses
)

# Strategy for database names
db_name_strategy = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="/\\?#"),
    min_size=1,
    max_size=63
)

# Strategy for port numbers
port_strategy = st.integers(min_value=1, max_value=65535).map(str)


class TestConnectionString:
    """Test properties of the get_conn_string function."""
    
    @given(
        username=special_chars_text,
        password=special_chars_text,
        hostname=hostname_strategy,
        db_name=db_name_strategy,
        port=port_strategy
    )
    @settings(max_examples=200)
    def test_conn_string_can_be_parsed(self, username, password, hostname, db_name, port):
        """Property: Generated connection strings should be parseable as valid URIs."""
        conn_string = get_conn_string(username, password, hostname, db_name, port)
        
        # Should be able to parse as URI
        parsed = urlparse(conn_string)
        assert parsed.scheme == "postgresql"
        # Hostnames are case-insensitive per RFC 3986, urllib normalizes to lowercase
        assert parsed.hostname == hostname.lower()
        assert parsed.port == int(port)
        assert parsed.path == f"/{db_name}"
        
        # Username and password should be properly encoded
        # They should be recoverable by unquoting
        if parsed.username:
            assert unquote(parsed.username) == username
        if parsed.password:
            assert unquote(parsed.password) == password
    
    @given(
        username=special_chars_text,
        password=special_chars_text,
        hostname=hostname_strategy,
        db_name=db_name_strategy,
        params=st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="=&")),
            st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_conn_string_with_params(self, username, password, hostname, db_name, params):
        """Property: Connection strings with params should preserve all parameters."""
        conn_string = get_conn_string(username, password, hostname, db_name, params=params)
        
        parsed = urlparse(conn_string)
        query_params = parse_qs(parsed.query)
        
        # All params should be present in the query string
        for key, value in params.items():
            assert key in query_params
            # parse_qs returns lists, get the first item
            assert query_params[key][0] == str(value)


class TestPgUrlFromConfig:
    """Test properties of the pg_url_from_config function."""
    
    @given(postgres_url=st.text(min_size=1))
    def test_postgres_url_takes_precedence(self, postgres_url):
        """Property: When postgres_url is provided, it should be returned as-is."""
        config = {"postgres_url": postgres_url}
        result = pg_url_from_config(config)
        assert result == postgres_url
    
    @given(
        username=st.text(min_size=1, max_size=20),
        password=st.text(min_size=1, max_size=20),
        hostname=hostname_strategy,
        db_name=db_name_strategy,
        port=port_strategy
    )
    def test_postgres_db_config_generates_url(self, username, password, hostname, db_name, port):
        """Property: postgres_db config should generate a valid connection URL."""
        config = {
            "postgres_db": {
                "username": username,
                "password": password,
                "hostname": hostname,
                "db_name": db_name,
                "port": port
            }
        }
        result = pg_url_from_config(config)
        
        # Should generate same URL as get_conn_string
        expected = get_conn_string(username, password, hostname, db_name, port)
        assert result == expected
    
    @given(st.data())
    def test_mutual_exclusivity(self, data):
        """Property: Config must have exactly one of postgres_url or postgres_db."""
        # Test with both present
        config_both = {
            "postgres_url": "postgresql://test:test@localhost/test",
            "postgres_db": {
                "username": "user",
                "password": "pass",
                "hostname": "host",
                "db_name": "db"
            }
        }
        
        with pytest.raises(Exception) as exc_info:
            pg_url_from_config(config_both)
        assert "exactly one of" in str(exc_info.value)
        
        # Test with neither present
        config_neither = {}
        with pytest.raises(Exception) as exc_info:
            pg_url_from_config(config_neither)
        assert "exactly one of" in str(exc_info.value)


class TestRetryFunctions:
    """Test properties of retry functions."""
    
    @given(
        return_value=st.integers(),
        retry_limit=st.integers(min_value=0, max_value=10)
    )
    def test_retry_pg_creation_successful_preserves_value(self, return_value, retry_limit):
        """Property: Successful function calls should preserve return values."""
        successful_fn = Mock(return_value=return_value)
        result = retry_pg_creation_fn(successful_fn, retry_limit=retry_limit)
        assert result == return_value
        successful_fn.assert_called_once()
    
    @given(retry_limit=st.integers(min_value=0, max_value=5))
    def test_retry_pg_creation_exhausts_retries(self, retry_limit):
        """Property: Should exhaust retries and raise DagsterPostgresException."""
        failing_fn = Mock(side_effect=psycopg2.IntegrityError())
        
        with pytest.raises(DagsterPostgresException) as exc_info:
            retry_pg_creation_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.001)
        
        assert "too many retries" in str(exc_info.value)
        # Should be called retry_limit + 1 times (initial + retries)
        assert failing_fn.call_count == retry_limit + 1
    
    @given(
        return_value=st.integers(),
        retry_limit=st.integers(min_value=0, max_value=10)
    )
    def test_retry_pg_connection_successful_preserves_value(self, return_value, retry_limit):
        """Property: Successful connection calls should preserve return values."""
        successful_fn = Mock(return_value=return_value)
        result = retry_pg_connection_fn(successful_fn, retry_limit=retry_limit)
        assert result == return_value
        successful_fn.assert_called_once()
    
    @given(retry_limit=st.integers(min_value=0, max_value=5))
    def test_retry_pg_connection_exhausts_retries(self, retry_limit):
        """Property: Should exhaust connection retries and raise DagsterPostgresException."""
        failing_fn = Mock(side_effect=psycopg2.OperationalError())
        
        with pytest.raises(DagsterPostgresException) as exc_info:
            retry_pg_connection_fn(failing_fn, retry_limit=retry_limit, retry_wait=0.001)
        
        assert "too many retries" in str(exc_info.value)
        # Should be called retry_limit + 1 times
        assert failing_fn.call_count == retry_limit + 1


class TestDagsterPostgresStorage:
    """Test properties of DagsterPostgresStorage class."""
    
    @given(
        postgres_url=st.text(min_size=1),
        should_autocreate_tables=st.booleans()
    )
    def test_storage_preserves_config(self, postgres_url, should_autocreate_tables):
        """Property: Storage should preserve its configuration."""
        with patch('dagster_postgres.storage.PostgresRunStorage'), \
             patch('dagster_postgres.storage.PostgresEventLogStorage'), \
             patch('dagster_postgres.storage.PostgresScheduleStorage'):
            
            storage = DagsterPostgresStorage(
                postgres_url=postgres_url,
                should_autocreate_tables=should_autocreate_tables
            )
            
            assert storage.postgres_url == postgres_url
            assert storage.should_autocreate_tables == should_autocreate_tables
    
    @given(st.data())
    def test_storage_data_properties_consistency(self, data):
        """Property: Storage data properties should return consistent ConfigurableClassData."""
        postgres_url = "postgresql://test:test@localhost/test"
        
        with patch('dagster_postgres.storage.PostgresRunStorage'), \
             patch('dagster_postgres.storage.PostgresEventLogStorage'), \
             patch('dagster_postgres.storage.PostgresScheduleStorage'):
            
            # Create storage with inst_data
            from dagster._serdes.config_class import ConfigurableClassData
            inst_data = ConfigurableClassData(
                module_name="test_module",
                class_name="TestClass",
                config_yaml="test: config"
            )
            
            storage = DagsterPostgresStorage(
                postgres_url=postgres_url,
                inst_data=inst_data
            )
            
            # Check that storage data properties return correct ConfigurableClassData
            event_data = storage.event_storage_data
            assert event_data.module_name == "dagster_postgres"
            assert event_data.class_name == "PostgresEventLogStorage"
            assert event_data.config_yaml == inst_data.config_yaml
            
            run_data = storage.run_storage_data
            assert run_data.module_name == "dagster_postgres"
            assert run_data.class_name == "PostgresRunStorage"
            assert run_data.config_yaml == inst_data.config_yaml
            
            schedule_data = storage.schedule_storage_data
            assert schedule_data.module_name == "dagster_postgres"
            assert schedule_data.class_name == "PostgresScheduleStorage"
            assert schedule_data.config_yaml == inst_data.config_yaml
    
    @given(postgres_url=st.text(min_size=1))
    def test_storage_without_inst_data_returns_none(self, postgres_url):
        """Property: Storage without inst_data should return None for data properties."""
        with patch('dagster_postgres.storage.PostgresRunStorage'), \
             patch('dagster_postgres.storage.PostgresEventLogStorage'), \
             patch('dagster_postgres.storage.PostgresScheduleStorage'):
            
            storage = DagsterPostgresStorage(postgres_url=postgres_url)
            
            assert storage.inst_data is None
            assert storage.event_storage_data is None
            assert storage.run_storage_data is None
            assert storage.schedule_storage_data is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])