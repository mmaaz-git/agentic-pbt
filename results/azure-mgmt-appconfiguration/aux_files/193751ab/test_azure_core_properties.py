#!/usr/bin/env python3
"""Property-based tests for azure.core module using Hypothesis."""

import json
import base64
from datetime import datetime, date, time, timedelta, timezone
from hypothesis import given, strategies as st, assume, settings
import pytest
from azure.core.utils import parse_connection_string, case_insensitive_dict, CaseInsensitiveDict
from azure.core.serialization import AzureJSONEncoder


# Strategy for valid connection string components
# Based on the parsing logic, keys and values cannot contain '=' or ';'
connection_key = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters='=;'),
    min_size=1,
    max_size=50
).filter(lambda s: s.strip() != '')

connection_value = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters=';'),
    min_size=1,
    max_size=100
).filter(lambda s: s.strip() != '' and '=' not in s.split('=', 1)[0])


class TestParseConnectionString:
    """Test properties of parse_connection_string function."""
    
    @given(st.dictionaries(connection_key, connection_value, min_size=1, max_size=10))
    def test_parse_connection_string_case_insensitive_access(self, conn_dict):
        """When case_sensitive_keys=False, all keys should be lowercase."""
        # Build connection string
        conn_str = ';'.join(f'{k}={v}' for k, v in conn_dict.items())
        
        # Parse with case insensitive (default)
        result = parse_connection_string(conn_str, case_sensitive_keys=False)
        
        # All keys should be lowercase
        for key in result.keys():
            assert key == key.lower(), f"Key '{key}' is not lowercase"
        
        # Values should be preserved
        for orig_key, orig_value in conn_dict.items():
            assert result[orig_key.lower()] == orig_value
    
    @given(st.dictionaries(connection_key, connection_value, min_size=1, max_size=10))
    def test_parse_connection_string_case_sensitive_preserves_case(self, conn_dict):
        """When case_sensitive_keys=True, original case should be preserved."""
        # Build connection string
        conn_str = ';'.join(f'{k}={v}' for k, v in conn_dict.items())
        
        # Parse with case sensitive
        result = parse_connection_string(conn_str, case_sensitive_keys=True)
        
        # Keys should match exactly
        assert set(result.keys()) == set(conn_dict.keys())
        
        # Values should match
        for key, value in conn_dict.items():
            assert result[key] == value
    
    @given(st.text(min_size=1).filter(lambda s: s.strip() != ''))
    def test_parse_connection_string_duplicate_case_insensitive_keys_raises(self, base_key):
        """Duplicate keys (case-insensitive) should raise ValueError."""
        # Create two keys that differ only in case
        key1 = base_key.upper()
        key2 = base_key.lower()
        
        # Skip if they're already the same
        assume(key1 != key2)
        
        # Also ensure they don't contain special chars
        assume('=' not in key1 and ';' not in key1)
        
        # Create connection string with duplicate case-insensitive keys
        conn_str = f"{key1}=value1;{key2}=value2"
        
        # This should raise ValueError when case_sensitive_keys=False
        with pytest.raises(ValueError, match="Duplicate key"):
            parse_connection_string(conn_str, case_sensitive_keys=False)
    
    @given(st.text())
    def test_parse_connection_string_malformed_raises_valueerror(self, bad_str):
        """Malformed connection strings should raise ValueError."""
        # Various malformed patterns
        assume(bad_str.strip() != '')
        
        # Test strings without '=' should fail
        if '=' not in bad_str:
            with pytest.raises(ValueError):
                parse_connection_string(bad_str)
        
        # Test strings with empty keys or values
        if bad_str.strip().startswith('=') or bad_str.strip().endswith('='):
            with pytest.raises(ValueError):
                parse_connection_string(bad_str)


class TestCaseInsensitiveDict:
    """Test properties of CaseInsensitiveDict."""
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != ''),
            st.text(max_size=100),
            min_size=1,
            max_size=20
        )
    )
    def test_case_insensitive_dict_access_invariant(self, test_dict):
        """CaseInsensitiveDict should provide case-insensitive access to all keys."""
        ci_dict = case_insensitive_dict(test_dict)
        
        for key, value in test_dict.items():
            # Test various case variations
            assert ci_dict.get(key.lower()) == value
            assert ci_dict.get(key.upper()) == value
            assert ci_dict.get(key.title()) == value
            
            # Test with __getitem__ as well
            assert ci_dict[key.lower()] == value
            assert ci_dict[key.upper()] == value
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != ''),
            st.text(max_size=100),
            min_size=1,
            max_size=20
        )
    )
    def test_case_insensitive_dict_update_preserves_invariant(self, initial_dict):
        """Updates to CaseInsensitiveDict should maintain case-insensitive access."""
        ci_dict = CaseInsensitiveDict(initial_dict)
        
        # Update with different case
        for key in list(initial_dict.keys()):
            new_value = "updated_" + str(initial_dict[key])
            ci_dict[key.upper()] = new_value
            
            # All case variations should give the updated value
            assert ci_dict.get(key.lower()) == new_value
            assert ci_dict.get(key.upper()) == new_value
            assert ci_dict.get(key) == new_value
    
    @given(st.text(min_size=1, max_size=20).filter(lambda s: s.strip() != ''))
    def test_case_insensitive_dict_single_key_multiple_cases(self, key):
        """Setting the same key with different cases should update the same entry."""
        ci_dict = CaseInsensitiveDict()
        
        # Set with different cases
        ci_dict[key.lower()] = "lower"
        ci_dict[key.upper()] = "upper"
        ci_dict[key.title()] = "title"
        
        # Should only have one key
        assert len(ci_dict) == 1
        
        # All accesses should return the last value
        assert ci_dict.get(key.lower()) == "title"
        assert ci_dict.get(key.upper()) == "title"
        assert ci_dict.get(key) == "title"


class TestAzureJSONEncoder:
    """Test properties of AzureJSONEncoder."""
    
    @given(st.binary(min_size=0, max_size=1000))
    def test_azure_json_encoder_bytes_base64_property(self, byte_data):
        """Bytes should be encoded as base64 strings."""
        encoder = AzureJSONEncoder()
        
        # Encode the bytes
        result = json.dumps({'data': byte_data}, cls=AzureJSONEncoder)
        decoded = json.loads(result)
        
        # The encoded bytes should be a base64 string
        encoded_str = decoded['data']
        assert isinstance(encoded_str, str)
        
        # Should be valid base64
        try:
            decoded_bytes = base64.b64decode(encoded_str)
            assert decoded_bytes == byte_data
        except Exception as e:
            pytest.fail(f"Failed to decode base64: {e}")
    
    @given(
        st.datetimes(min_value=datetime(1900, 1, 1), max_value=datetime(2100, 12, 31))
    )
    def test_azure_json_encoder_datetime_iso_format(self, dt):
        """Datetime objects should be encoded in ISO format."""
        # Make datetime timezone-aware to match Azure's behavior
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        result = json.dumps({'dt': dt}, cls=AzureJSONEncoder)
        decoded = json.loads(result)
        
        # Should be a string in ISO format
        dt_str = decoded['dt']
        assert isinstance(dt_str, str)
        
        # Should be parseable as ISO format
        try:
            parsed = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            # Compare with second precision (microseconds might differ)
            assert parsed.replace(microsecond=0) == dt.replace(microsecond=0)
        except ValueError as e:
            pytest.fail(f"Not valid ISO format: {dt_str}, error: {e}")
    
    @given(st.timedeltas(min_value=timedelta(seconds=-1e6), max_value=timedelta(seconds=1e6)))
    def test_azure_json_encoder_timedelta_duration_format(self, td):
        """Timedelta objects should be encoded in ISO 8601 duration format."""
        result = json.dumps({'td': td}, cls=AzureJSONEncoder)
        decoded = json.loads(result)
        
        # Should be a string starting with 'P' (ISO 8601 duration format)
        td_str = decoded['td']
        assert isinstance(td_str, str)
        assert td_str.startswith('P') or td_str.startswith('-P'), f"Invalid duration format: {td_str}"
        
        # Check it contains valid duration components
        # Format should be like P1DT2H30M45S
        if 'T' in td_str:
            # Has time components
            date_part, time_part = td_str.replace('-P', 'P').split('T')
            assert date_part.startswith('P')
            # Time part should have H, M, or S
            assert any(c in time_part for c in ['H', 'M', 'S'])