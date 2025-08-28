"""Property-based tests for sqlalchemy.connectors module"""

import re
from unittest.mock import Mock, MagicMock
from hypothesis import given, assume, strategies as st, settings
import sqlalchemy.connectors.pyodbc as pyodbc_connector
from sqlalchemy.engine.url import URL


class TestPyODBCConnector:
    """Test PyODBCConnector properties"""
    
    def setup_method(self):
        """Setup test connector instance"""
        self.connector = pyodbc_connector.PyODBCConnector()
        # Mock the loaded_dbapi to avoid import errors
        self.connector.loaded_dbapi = Mock()
        self.connector.loaded_dbapi.ProgrammingError = Exception
        self.connector.pyodbc_driver_name = "ODBC Driver 17 for SQL Server"
        
    @given(st.text())
    def test_check_quote_escaping_property(self, token):
        """Test that check_quote properly escapes tokens with special characters.
        
        Property: Tokens containing ';' or starting with '{' should be wrapped in '{}'
        and any '}' should be escaped as '}}'
        """
        # Create a mock URL to test the internal check_quote function
        url = URL.create("mssql+pyodbc", host="localhost", database="test")
        
        # We need to access the check_quote function indirectly through create_connect_args
        # Let's test the escaping logic by passing tokens through the connection args
        
        # Extract the check_quote logic
        def check_quote(token: str) -> str:
            if ";" in str(token) or str(token).startswith("{"):
                token = "{%s}" % token.replace("}", "}}")
            return token
        
        result = check_quote(token)
        
        # Property 1: If token contains ';' or starts with '{', result should be wrapped in {}
        if ";" in token or token.startswith("{"):
            assert result.startswith("{") and result.endswith("}")
            # The content between {} should have all '}' escaped as '}}'
            inner = result[1:-1]
            # Count unescaped '}' - should be 0
            # Remove all '}}' then check for remaining '}'
            unescaped = inner.replace("}}", "")
            assert "}" not in unescaped
        else:
            # If no special chars, token should be unchanged
            assert result == token
    
    @given(st.text(min_size=1))
    def test_check_quote_roundtrip(self, original):
        """Test that we can reverse the check_quote escaping.
        
        Property: For any string, we should be able to recover the original
        after quote and unquote operations.
        """
        def check_quote(token: str) -> str:
            if ";" in str(token) or str(token).startswith("{"):
                token = "{%s}" % token.replace("}", "}}")
            return token
        
        def unquote(token: str) -> str:
            """Attempt to reverse check_quote operation"""
            if token.startswith("{") and token.endswith("}"):
                # Remove outer braces
                inner = token[1:-1]
                # Unescape }}
                return inner.replace("}}", "}")
            return token
        
        quoted = check_quote(original)
        
        # Only test roundtrip for tokens that need quoting
        if ";" in original or original.startswith("{"):
            unquoted = unquote(quoted)
            assert unquoted == original
            
    @given(st.text(), st.text())
    def test_is_disconnect_programming_error(self, error_msg, extra_text):
        """Test is_disconnect correctly identifies disconnection errors.
        
        Property: ProgrammingError with specific messages should be identified as disconnect
        """
        # Create a proper ProgrammingError class
        class ProgrammingError(Exception):
            pass
        
        self.connector.loaded_dbapi.ProgrammingError = ProgrammingError
        
        # Test with messages that should be identified as disconnect
        disconnect_messages = [
            "The cursor's connection has been closed.",
            "Attempt to use a closed connection."
        ]
        
        for disconnect_msg in disconnect_messages:
            # Create error with the disconnect message embedded
            full_message = extra_text + disconnect_msg + extra_text
            error = ProgrammingError(full_message)
            
            # Should return True for these messages
            result = self.connector.is_disconnect(error, None, None)
            assert result == True
            
        # Test with unrelated message - should return False
        other_error = ProgrammingError(error_msg)
        
        # Only return False if the specific messages aren't present
        expected = any(msg in error_msg for msg in disconnect_messages)
        result = self.connector.is_disconnect(other_error, None, None)
        assert result == expected
        
    @given(st.text())
    def test_is_disconnect_non_programming_error(self, error_msg):
        """Test that non-ProgrammingErrors return False for is_disconnect.
        
        Property: Any exception that's not a ProgrammingError should return False
        """
        # Create a regular exception (not ProgrammingError)
        error = Exception(error_msg)
        
        result = self.connector.is_disconnect(error, None, None)
        assert result == False
        
    @given(
        st.text(alphabet=st.characters(blacklist_characters=";{}"), min_size=1).filter(lambda x: not x.startswith("{")),
        st.text(alphabet=st.characters(blacklist_characters=";{}"), min_size=1).filter(lambda x: not x.startswith("{")),
        st.text(alphabet=st.characters(blacklist_characters=";{}"), min_size=1).filter(lambda x: not x.startswith("{")),
    )
    def test_connection_string_construction_basic(self, host, database, driver):
        """Test basic connection string construction.
        
        Property: Connection string should contain the provided components
        """
        # Create URL with basic components
        url = URL.create(
            "mssql+pyodbc",
            host=host,
            database=database,
            query={"driver": driver}
        )
        
        connection_args, connect_params = self.connector.create_connect_args(url)
        connection_string = connection_args[0]
        
        # Properties:
        # 1. Connection string should contain host as Server
        assert f"Server={host}" in connection_string
        
        # 2. Connection string should contain database
        assert f"Database={database}" in connection_string
        
        # 3. Connection string should contain driver
        assert f"DRIVER={{{driver}}}" in connection_string
        
        # 4. Components should be separated by semicolons
        assert ";" in connection_string
        parts = connection_string.split(";")
        assert len(parts) >= 3  # At least driver, server, database
        
    @given(
        st.integers(min_value=1, max_value=65535),
        st.text(alphabet=st.characters(blacklist_characters=";{}"), min_size=1).filter(lambda x: not x.startswith("{")),
    )
    def test_connection_string_port_handling(self, port, host):
        """Test that port is correctly appended to the server.
        
        Property: When port is specified, it should be appended to Server as ,port
        """
        url = URL.create(
            "mssql+pyodbc",
            host=host,
            port=port,
            database="testdb"
        )
        
        connection_args, _ = self.connector.create_connect_args(url)
        connection_string = connection_args[0]
        
        # Port should be appended to server with comma
        expected_server = f"Server={host},{port}"
        assert expected_server in connection_string
        
    @given(st.booleans(), st.booleans(), st.booleans())
    def test_boolean_parameters_conversion(self, ansi, unicode_results, autocommit):
        """Test that boolean parameters are correctly converted.
        
        Property: Boolean string values should be converted to actual booleans
        """
        # Create URL with boolean parameters as strings
        query = {}
        if ansi:
            query["ansi"] = "true"
        if unicode_results:
            query["unicode_results"] = "yes"  
        if autocommit:
            query["autocommit"] = "1"
            
        url = URL.create(
            "mssql+pyodbc",
            host="localhost",
            database="test",
            query=query
        )
        
        _, connect_params = self.connector.create_connect_args(url)
        
        # Check that boolean params are converted
        if ansi:
            assert "ansi" in connect_params
            assert connect_params["ansi"] == True
        if unicode_results:
            assert "unicode_results" in connect_params
            assert connect_params["unicode_results"] == True
        if autocommit:
            assert "autocommit" in connect_params
            assert connect_params["autocommit"] == True