#!/usr/bin/env python3
import sys
from unittest.mock import patch, Mock

sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, settings, assume
from dagster_postgres.storage import DagsterPostgresStorage
from dagster_postgres.utils import pg_url_from_config


class TestConfigEdgeCases:
    """Test configuration edge cases."""
    
    @given(
        should_autocreate=st.booleans(),
        config_with_url=st.booleans()
    )
    def test_from_config_value_handles_autocreate(self, should_autocreate, config_with_url):
        """Test that from_config_value properly handles should_autocreate_tables."""
        
        if config_with_url:
            config = {
                "postgres_url": "postgresql://user:pass@localhost/db",
                "should_autocreate_tables": should_autocreate
            }
        else:
            config = {
                "postgres_db": {
                    "username": "user",
                    "password": "pass",
                    "hostname": "localhost",
                    "db_name": "db"
                },
                "should_autocreate_tables": should_autocreate
            }
        
        with patch('dagster_postgres.storage.PostgresRunStorage'), \
             patch('dagster_postgres.storage.PostgresEventLogStorage'), \
             patch('dagster_postgres.storage.PostgresScheduleStorage'):
            
            storage = DagsterPostgresStorage.from_config_value(None, config)
            assert storage.should_autocreate_tables == should_autocreate
    
    def test_from_config_value_defaults_autocreate_to_true(self):
        """Test that should_autocreate_tables defaults to True when not specified."""
        config = {"postgres_url": "postgresql://user:pass@localhost/db"}
        
        with patch('dagster_postgres.storage.PostgresRunStorage'), \
             patch('dagster_postgres.storage.PostgresEventLogStorage'), \
             patch('dagster_postgres.storage.PostgresScheduleStorage'):
            
            storage = DagsterPostgresStorage.from_config_value(None, config)
            assert storage.should_autocreate_tables == True
    
    @given(st.data())
    def test_config_validation_edge_cases(self, data):
        """Test various invalid config combinations."""
        
        # Test empty config dict
        empty_config = {}
        with pytest.raises(Exception) as exc:
            pg_url_from_config(empty_config)
        assert "exactly one of" in str(exc.value)
        
        # Test config with both postgres_url and postgres_db
        both_config = {
            "postgres_url": "postgresql://test@localhost/test",
            "postgres_db": {"username": "u", "password": "p", "hostname": "h", "db_name": "d"}
        }
        with pytest.raises(Exception) as exc:
            pg_url_from_config(both_config)
        assert "exactly one of" in str(exc.value)
    
    @given(
        extra_keys=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=5
        )
    )
    def test_config_ignores_extra_keys(self, extra_keys):
        """Test that extra keys in config are ignored gracefully."""
        assume("postgres_url" not in extra_keys)
        assume("postgres_db" not in extra_keys)
        assume("should_autocreate_tables" not in extra_keys)
        
        config = {"postgres_url": "postgresql://user:pass@localhost/db"}
        config.update(extra_keys)
        
        # Should not raise an error
        result = pg_url_from_config(config)
        assert result == "postgresql://user:pass@localhost/db"
    
    @given(
        scheme=st.sampled_from(["postgres", "postgresql", "postgresql+psycopg2"])
    )
    def test_different_postgres_schemes(self, scheme):
        """Test that different PostgreSQL URL schemes are handled."""
        from dagster_postgres.utils import get_conn_string
        
        conn_string = get_conn_string(
            username="user",
            password="pass",
            hostname="localhost",
            db_name="test",
            scheme=scheme
        )
        
        assert conn_string.startswith(f"{scheme}://")
    
    def test_postgres_db_missing_required_fields(self):
        """Test that postgres_db config validates required fields."""
        incomplete_configs = [
            {"postgres_db": {"username": "u", "password": "p", "hostname": "h"}},  # missing db_name
            {"postgres_db": {"username": "u", "password": "p", "db_name": "d"}},   # missing hostname
            {"postgres_db": {"username": "u", "hostname": "h", "db_name": "d"}},   # missing password
            {"postgres_db": {"password": "p", "hostname": "h", "db_name": "d"}},   # missing username
        ]
        
        for config in incomplete_configs:
            with pytest.raises((KeyError, TypeError)) as exc:
                pg_url_from_config(config)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])