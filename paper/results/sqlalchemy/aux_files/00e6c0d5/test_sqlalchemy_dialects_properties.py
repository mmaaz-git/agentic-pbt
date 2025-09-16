"""Property-based tests for SQLAlchemy dialects using Hypothesis."""

import json
from hypothesis import given, assume, strategies as st, settings
from sqlalchemy.dialects import postgresql, mysql, sqlite
from sqlalchemy.dialects.postgresql import psycopg2 as pg_dialect
from sqlalchemy.dialects.mysql import mysqldb as my_dialect


# JSON strategies that generate valid JSON data
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1e10, max_value=1e10),
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    st.text(min_size=0, max_size=100),
)

# Recursive JSON structure (limited depth to prevent excessive memory usage)
json_value = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(
            st.text(min_size=1, max_size=50),
            children,
            max_size=10
        )
    ),
    max_leaves=50
)


@given(json_value)
@settings(max_examples=500)
def test_postgresql_json_round_trip(data):
    """Test that PostgreSQL JSON type preserves data through bind/result processing."""
    pg_json = postgresql.JSON()
    dialect = pg_dialect.dialect()
    
    bind_processor = pg_json.bind_processor(dialect)
    result_processor = pg_json.result_processor(dialect, None)
    
    # Skip if processors don't exist
    if not bind_processor or not result_processor:
        assume(False)
    
    # Process through bind (Python -> DB format)
    bound_value = bind_processor(data)
    
    # Process through result (DB format -> Python)
    result_value = result_processor(bound_value)
    
    # Check round-trip property
    assert result_value == data, f"Round-trip failed: {data} -> {bound_value} -> {result_value}"


@given(json_value)
@settings(max_examples=500)
def test_mysql_json_round_trip(data):
    """Test that MySQL JSON type preserves data through bind/result processing."""
    my_json = mysql.JSON()
    dialect = my_dialect.dialect()
    
    bind_processor = my_json.bind_processor(dialect)
    result_processor = my_json.result_processor(dialect, None)
    
    # Skip if processors don't exist
    if not bind_processor or not result_processor:
        assume(False)
    
    # Process through bind (Python -> DB format)
    bound_value = bind_processor(data)
    
    # Process through result (DB format -> Python)
    result_value = result_processor(bound_value)
    
    # Check round-trip property
    assert result_value == data, f"Round-trip failed: {data} -> {bound_value} -> {result_value}"


# Array strategies for PostgreSQL
array_integers = st.lists(
    st.integers(min_value=-1e9, max_value=1e9),
    min_size=0,
    max_size=100
)

array_floats = st.lists(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
    min_size=0,
    max_size=100
)

array_strings = st.lists(
    st.text(min_size=0, max_size=50),
    min_size=0,
    max_size=50
)


@given(array_integers)
@settings(max_examples=500)
def test_postgresql_array_integers_round_trip(data):
    """Test that PostgreSQL ARRAY(INTEGER) preserves integer lists."""
    array_type = postgresql.ARRAY(postgresql.INTEGER)
    dialect = pg_dialect.dialect()
    
    bind_processor = array_type.bind_processor(dialect)
    result_processor = array_type.result_processor(dialect, None)
    
    if not bind_processor or not result_processor:
        assume(False)
    
    bound_value = bind_processor(data)
    result_value = result_processor(bound_value)
    
    assert result_value == data, f"Array round-trip failed: {data} -> {result_value}"


@given(array_floats)
@settings(max_examples=500)
def test_postgresql_array_floats_round_trip(data):
    """Test that PostgreSQL ARRAY(FLOAT) preserves float lists."""
    array_type = postgresql.ARRAY(postgresql.FLOAT)
    dialect = pg_dialect.dialect()
    
    bind_processor = array_type.bind_processor(dialect)
    result_processor = array_type.result_processor(dialect, None)
    
    if not bind_processor or not result_processor:
        assume(False)
    
    bound_value = bind_processor(data)
    result_value = result_processor(bound_value)
    
    # For floats, we need to handle potential precision issues
    assert len(result_value) == len(data)
    for original, result in zip(data, result_value):
        # Using approximate equality for floats
        if original is not None and result is not None:
            assert abs(original - result) < 1e-6, f"Float mismatch: {original} != {result}"
        else:
            assert original == result


@given(array_strings)
@settings(max_examples=500)
def test_postgresql_array_strings_round_trip(data):
    """Test that PostgreSQL ARRAY(VARCHAR) preserves string lists."""
    array_type = postgresql.ARRAY(postgresql.VARCHAR)
    dialect = pg_dialect.dialect()
    
    bind_processor = array_type.bind_processor(dialect)
    result_processor = array_type.result_processor(dialect, None)
    
    if not bind_processor or not result_processor:
        assume(False)
    
    bound_value = bind_processor(data)
    result_value = result_processor(bound_value)
    
    assert result_value == data, f"String array round-trip failed: {data} -> {result_value}"


# Test nested arrays (2D arrays)
nested_array_integers = st.lists(
    st.lists(
        st.integers(min_value=-1e6, max_value=1e6),
        min_size=0,
        max_size=20
    ),
    min_size=0,
    max_size=20
)


@given(nested_array_integers)
@settings(max_examples=500)
def test_postgresql_nested_array_round_trip(data):
    """Test that PostgreSQL ARRAY(INTEGER, dimensions=2) preserves 2D arrays."""
    array_type = postgresql.ARRAY(postgresql.INTEGER, dimensions=2)
    dialect = pg_dialect.dialect()
    
    bind_processor = array_type.bind_processor(dialect)
    result_processor = array_type.result_processor(dialect, None)
    
    if not bind_processor or not result_processor:
        assume(False)
    
    # PostgreSQL requires rectangular arrays (all rows same length)
    if data and len(set(len(row) for row in data)) > 1:
        # Skip non-rectangular arrays
        assume(False)
    
    bound_value = bind_processor(data)
    result_value = result_processor(bound_value)
    
    assert result_value == data, f"Nested array round-trip failed: {data} -> {result_value}"


# Test edge cases with None values
json_with_none = st.one_of(
    st.none(),
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.none(), st.integers(), st.text()),
        min_size=1,
        max_size=5
    )
)


@given(json_with_none)
@settings(max_examples=500)
def test_postgresql_json_none_handling(data):
    """Test PostgreSQL JSON handling of None values with none_as_null=True."""
    pg_json = postgresql.JSON(none_as_null=True)
    dialect = pg_dialect.dialect()
    
    bind_processor = pg_json.bind_processor(dialect)
    result_processor = pg_json.result_processor(dialect, None)
    
    if not bind_processor or not result_processor:
        assume(False)
    
    bound_value = bind_processor(data)
    result_value = result_processor(bound_value)
    
    # With none_as_null=True, None should be preserved
    assert result_value == data, f"None handling failed: {data} -> {result_value}"


# Test arrays with None values
array_with_nulls = st.lists(
    st.one_of(st.none(), st.integers(min_value=-1000, max_value=1000)),
    min_size=0,
    max_size=50
)


@given(array_with_nulls)
@settings(max_examples=500)
def test_postgresql_array_null_handling(data):
    """Test PostgreSQL ARRAY handling of None/NULL values."""
    array_type = postgresql.ARRAY(postgresql.INTEGER)
    dialect = pg_dialect.dialect()
    
    bind_processor = array_type.bind_processor(dialect)
    result_processor = array_type.result_processor(dialect, None)
    
    if not bind_processor or not result_processor:
        assume(False)
    
    bound_value = bind_processor(data)
    result_value = result_processor(bound_value)
    
    assert result_value == data, f"Array with nulls failed: {data} -> {result_value}"