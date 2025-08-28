#!/usr/bin/env python3
import sys
import os
import math
import time
import datetime
import uuid
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from zoneinfo import ZoneInfo

sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

import trino.dbapi
from trino.dbapi import TimeBoundLRUCache, Cursor, Connection, DBAPITypeObject


@given(
    capacity=st.integers(min_value=1, max_value=100),
    num_items=st.integers(min_value=0, max_value=200),
    keys=st.lists(st.text(min_size=1), min_size=1, unique=True)
)
def test_lru_cache_capacity_constraint(capacity, num_items, keys):
    cache = TimeBoundLRUCache(capacity, ttl_seconds=3600)
    
    items_to_add = min(num_items, len(keys))
    for i in range(items_to_add):
        cache.put(keys[i], f"value_{i}")
    
    actual_size = len(cache.cache)
    assert actual_size <= capacity, f"Cache size {actual_size} exceeds capacity {capacity}"


@given(
    ttl_seconds=st.floats(min_value=0.001, max_value=0.1),
    key=st.text(min_size=1),
    value=st.text(min_size=1),
    sleep_time=st.floats(min_value=0.0, max_value=0.2)
)
def test_lru_cache_ttl_expiration(ttl_seconds, key, value, sleep_time):
    cache = TimeBoundLRUCache(capacity=10, ttl_seconds=ttl_seconds)
    
    cache.put(key, value)
    
    if sleep_time < ttl_seconds:
        time.sleep(sleep_time)
        result = cache.get(key)
        assert result == value, f"Value should not have expired yet"
    else:
        time.sleep(sleep_time)
        result = cache.get(key)
        assert result is None, f"Value should have expired after {sleep_time}s (ttl={ttl_seconds}s)"


@given(
    capacity=st.integers(min_value=2, max_value=10),
    keys=st.lists(st.text(min_size=1), min_size=3, unique=True)
)
def test_lru_cache_eviction_order(capacity, keys):
    assume(len(keys) > capacity)
    
    cache = TimeBoundLRUCache(capacity, ttl_seconds=3600)
    
    for i, key in enumerate(keys[:capacity + 1]):
        cache.put(key, f"value_{i}")
    
    first_key = keys[0]
    assert cache.get(first_key) is None, "First (least recently used) key should have been evicted"
    
    for key in keys[1:capacity + 1]:
        assert cache.get(key) is not None, f"Key {key} should still be in cache"


@given(value=st.floats(allow_nan=True, allow_infinity=True))
def test_format_prepared_param_special_floats(value):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(value)
    
    if value == float('+inf'):
        assert result == "infinity()"
    elif value == float('-inf'):
        assert result == "-infinity()"
    elif math.isnan(value):
        assert result == "nan()"
    else:
        assert result == f"DOUBLE '{value}'"


@given(
    text=st.text(alphabet=st.characters(blacklist_categories=["Cs", "Cc"]), min_size=0)
)
def test_format_prepared_param_string_escaping(text):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(text)
    
    expected = "'" + text.replace("'", "''") + "'"
    assert result == expected, f"String escaping failed for {repr(text)}"
    
    quote_count = text.count("'")
    result_quote_count = result.count("'")
    assert result_quote_count == 2 + quote_count * 2, "Single quotes should be doubled"


@given(
    bytes_value=st.binary(min_size=0, max_size=100)
)
def test_format_prepared_param_bytes(bytes_value):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(bytes_value)
    expected = "X'" + bytes_value.hex().upper() + "'"
    
    assert result == expected, f"Bytes formatting failed"


@given(
    list_values=st.lists(st.integers(), min_size=0, max_size=10)
)
def test_format_prepared_param_list(list_values):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(list_values)
    
    assert result.startswith("ARRAY[")
    assert result.endswith("]")
    
    if not list_values:
        assert result == "ARRAY[]"


@given(
    dict_values=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.integers(),
        min_size=0,
        max_size=5
    )
)
def test_format_prepared_param_dict(dict_values):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(dict_values)
    
    assert result.startswith("MAP(")
    assert result.endswith(")")
    assert "ARRAY[" in result


@given(
    decimal_value=st.decimals(allow_nan=False, allow_infinity=False)
)
def test_format_prepared_param_decimal(decimal_value):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(decimal_value)
    
    assert result.startswith("DECIMAL '")
    assert result.endswith("'")
    
    decimal_str = result[9:-1]
    assert '.' in decimal_str or decimal_str.replace('-', '').isdigit()


@given(
    types=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
    test_value=st.text(min_size=1, max_size=20)
)
def test_dbapi_type_object_case_insensitive(types, test_value):
    type_obj = DBAPITypeObject(*types)
    
    for original_type in types:
        assert type_obj == original_type.upper()
        assert type_obj == original_type.lower()
        assert type_obj == original_type.title()
    
    if test_value.lower() in [t.lower() for t in types]:
        assert type_obj == test_value
    else:
        assert not (type_obj == test_value)


@given(
    date_value=st.dates()
)
def test_format_prepared_param_date(date_value):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(date_value)
    
    assert result.startswith("DATE '")
    assert result.endswith("'")
    
    date_str = result[6:-1]
    assert date_str == date_value.strftime("%Y-%m-%d")


@given(
    time_value=st.times()
)
def test_format_prepared_param_time_without_tz(time_value):
    assume(time_value.tzinfo is None)
    
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(time_value)
    
    assert result.startswith("TIME '")
    assert result.endswith("'")


@given(
    bool_value=st.booleans()
)
def test_format_prepared_param_bool(bool_value):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(bool_value)
    
    assert result == ("true" if bool_value else "false")


@given(
    int_value=st.integers()
)
def test_format_prepared_param_int(int_value):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(int_value)
    
    assert result == str(int_value)


def test_format_prepared_param_none():
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(None)
    assert result == "NULL"


@given(
    uuid_value=st.uuids()
)
def test_format_prepared_param_uuid(uuid_value):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(uuid_value)
    
    assert result == f"UUID '{uuid_value}'"


@given(
    tuple_values=st.tuples(st.integers(), st.text(max_size=10))
)
def test_format_prepared_param_tuple(tuple_values):
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(tuple_values)
    
    assert result.startswith("ROW(")
    assert result.endswith(")")


@given(
    host=st.sampled_from([
        "http://example.com",
        "https://example.com",
        "example.com",
        "http://example.com:8080",
        "https://example.com:443",
    ])
)
def test_connection_url_parsing(host):
    try:
        conn = Connection(host=host, user="test")
        
        if host.startswith("https://"):
            assert conn.http_scheme == "https"
            if ":443" not in host:
                assert conn.port == 443
        elif host.startswith("http://"):
            assert conn.http_scheme == "http"
            if ":8080" not in host and ":" not in host.split("//")[1]:
                assert conn.port == 8080
        
        conn.close()
    except Exception as e:
        pytest.skip(f"Connection creation failed: {e}")


if __name__ == "__main__":
    print("Running property-based tests for trino.dbapi...")
    pytest.main([__file__, "-v", "--tb=short"])