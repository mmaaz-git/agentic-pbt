#!/usr/bin/env python3
import sys
from urllib.parse import urlparse, unquote

sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, settings, example
from dagster_postgres.utils import get_conn_string


class TestEdgeCases:
    """Test edge cases that might break URL encoding."""
    
    def test_special_characters_in_password(self):
        """Test passwords with characters that need URL encoding."""
        test_cases = [
            "@#$%^&*()",  # Special symbols
            "pass@word:with/slash",  # URL delimiters
            "пароль",  # Cyrillic
            "密码",  # Chinese  
            "🔒🔑",  # Emojis
            " spaces in password ",  # Spaces
            "tab\there",  # Tab character
            "new\nline",  # Newline
            "",  # Empty password
            "a" * 1000,  # Very long password
        ]
        
        for password in test_cases:
            conn_string = get_conn_string(
                username="user",
                password=password,
                hostname="localhost",
                db_name="test"
            )
            
            parsed = urlparse(conn_string)
            # Password should be recoverable after URL encoding/decoding
            if parsed.password:
                recovered_password = unquote(parsed.password)
                assert recovered_password == password, f"Failed for password: {repr(password)}"
    
    def test_special_characters_in_username(self):
        """Test usernames with special characters."""
        test_cases = [
            "user@domain.com",  # Email-like
            "user:name",  # Colon
            "user/name",  # Slash
            "user name",  # Space
            "用户",  # Chinese
            "",  # Empty username
        ]
        
        for username in test_cases:
            conn_string = get_conn_string(
                username=username,
                password="pass",
                hostname="localhost",
                db_name="test"
            )
            
            parsed = urlparse(conn_string)
            if parsed.username:
                recovered_username = unquote(parsed.username)
                assert recovered_username == username, f"Failed for username: {repr(username)}"
    
    def test_special_database_names(self):
        """Test database names with special characters."""
        test_cases = [
            "my-database",  # Hyphen
            "my_database",  # Underscore
            "123database",  # Starting with number
            "database.prod",  # Dot
            "データベース",  # Japanese
        ]
        
        for db_name in test_cases:
            conn_string = get_conn_string(
                username="user",
                password="pass",
                hostname="localhost",
                db_name=db_name
            )
            
            parsed = urlparse(conn_string)
            # Remove leading slash from path
            recovered_db = parsed.path.lstrip('/')
            assert recovered_db == db_name, f"Failed for db_name: {repr(db_name)}"
    
    def test_params_with_special_characters(self):
        """Test parameters with values that need encoding."""
        params = {
            "sslmode": "verify-full",
            "option": "value with spaces",
            "param": "value&with&ampersands",
            "setting": "value=with=equals",
        }
        
        conn_string = get_conn_string(
            username="user",
            password="pass",
            hostname="localhost",
            db_name="test",
            params=params
        )
        
        parsed = urlparse(conn_string)
        # Params should be in query string
        assert parsed.query
        # Basic check that params are present
        for key in params:
            assert key in parsed.query
    
    @given(
        username=st.text(min_size=0, max_size=100),
        password=st.text(min_size=0, max_size=100)
    )
    @settings(max_examples=500)
    def test_arbitrary_text_encoding(self, username, password):
        """Property: Any text should be properly encoded in connection strings."""
        conn_string = get_conn_string(
            username=username,
            password=password,
            hostname="localhost",
            db_name="test"
        )
        
        # Should be able to parse without error
        parsed = urlparse(conn_string)
        
        # Should be able to recover original values
        if username and parsed.username:
            assert unquote(parsed.username) == username
        if password and parsed.password:
            assert unquote(parsed.password) == password


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])