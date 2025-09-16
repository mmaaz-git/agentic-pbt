"""Edge case testing for sqlalchemy.connectors - looking for bugs in escaping logic"""

from hypothesis import given, strategies as st, settings, example
import sqlalchemy.connectors.pyodbc as pyodbc_connector
from sqlalchemy.engine.url import URL


class TestEdgeCases:
    """Test edge cases more aggressively"""
    
    def setup_method(self):
        """Setup test connector instance"""
        self.connector = pyodbc_connector.PyODBCConnector()
        self.connector.pyodbc_driver_name = "ODBC Driver 17 for SQL Server"
    
    @given(st.text())
    @example("}}")  # Double closing brace
    @example("{}}")  # Mixed braces
    @example("{{}")  # Mixed braces
    @example("{;}")  # Semicolon inside braces
    @example("};{")  # Complex pattern
    @example("{{{}}}")  # Nested-like braces
    @example("}}{{{")  # Complex mixed
    @settings(max_examples=500)
    def test_check_quote_edge_cases(self, token):
        """Aggressively test the check_quote escaping with edge cases"""
        
        def check_quote(token: str) -> str:
            if ";" in str(token) or str(token).startswith("{"):
                token = "{%s}" % token.replace("}", "}}")
            return token
        
        result = check_quote(token)
        
        # Validate the escaping logic
        if ";" in token or token.startswith("{"):
            # Should be wrapped
            assert result.startswith("{") and result.endswith("}")
            
            # Check that escaping is correct
            inner = result[1:-1]  # Remove outer braces
            
            # Count braces in inner content
            # After escaping, every original '}' should become '}}'
            # So we should have an even number of '}' characters
            brace_count = inner.count("}")
            
            # The number of '}' should be even (pairs of }})
            if brace_count > 0:
                # Check that all '}' appear in pairs
                i = 0
                while i < len(inner):
                    if inner[i] == "}":
                        # Must be followed by another '}'
                        assert i + 1 < len(inner) and inner[i + 1] == "}", \
                            f"Unescaped }} at position {i} in '{inner}'"
                        i += 2  # Skip the pair
                    else:
                        i += 1
    
    @given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"])))
    @settings(max_examples=500)
    def test_malformed_escaping_patterns(self, text):
        """Test with various Unicode and special characters"""
        
        def check_quote(token: str) -> str:
            if ";" in str(token) or str(token).startswith("{"):
                token = "{%s}" % token.replace("}", "}}")
            return token
        
        def unquote(token: str) -> str:
            """Reverse the check_quote operation"""
            if token.startswith("{") and token.endswith("}"):
                inner = token[1:-1]
                return inner.replace("}}", "}")
            return token
        
        # Test roundtrip
        quoted = check_quote(text)
        
        if ";" in text or text.startswith("{"):
            # Should be able to recover original
            unquoted = unquote(quoted)
            assert unquoted == text, f"Roundtrip failed: {text!r} -> {quoted!r} -> {unquoted!r}"
    
    @given(
        st.lists(st.text(alphabet="};{", min_size=1, max_size=3), min_size=1, max_size=5)
    )
    def test_connection_string_with_special_chars(self, tokens):
        """Test connection string construction with tokens containing special characters"""
        
        # Build parameters with our special tokens
        params = {}
        for i, token in enumerate(tokens):
            params[f"param{i}"] = token
        
        # Create URL with these parameters
        url = URL.create(
            "mssql+pyodbc",
            host="localhost",
            database="test",
            query=params
        )
        
        try:
            connection_args, _ = self.connector.create_connect_args(url)
            connection_string = connection_args[0]
            
            # Connection string should be parseable (contain proper structure)
            assert ";" in connection_string
            
            # All parameters should be present (though possibly escaped)
            for key in params:
                assert key in connection_string
                
        except Exception as e:
            # If this causes an actual error, that might be a bug
            print(f"Exception with tokens {tokens}: {e}")
            raise
    
    @given(st.text())
    @settings(max_examples=200)
    def test_escaping_idempotence(self, text):
        """Test that escaping is idempotent when already escaped"""
        
        def check_quote(token: str) -> str:
            if ";" in str(token) or str(token).startswith("{"):
                token = "{%s}" % token.replace("}", "}}")
            return token
        
        # First escape
        escaped_once = check_quote(text)
        
        # If it was escaped, escaping again should escape the escaped version
        if escaped_once != text:
            escaped_twice = check_quote(escaped_once)
            # The twice-escaped version should be different (it would escape the outer braces)
            assert escaped_twice != escaped_once
            # And it should start with {{ since the first char is {
            assert escaped_twice.startswith("{{")