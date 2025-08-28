"""Property-based tests for SQLAlchemy using Hypothesis."""

import string
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy.engine import url
from sqlalchemy import and_, or_, not_, literal, Integer, String, Boolean, Float
from sqlalchemy import types
import pytest


# URL Testing Strategies
@st.composite
def valid_db_url_strings(draw):
    """Generate valid database URL strings."""
    # Common database drivers
    drivers = ['postgresql', 'mysql', 'sqlite', 'oracle', 'mssql', 
               'postgresql+psycopg2', 'mysql+pymysql', 'sqlite+pysqlite']
    driver = draw(st.sampled_from(drivers))
    
    # Username and password (optional)
    username = draw(st.text(alphabet=string.ascii_letters + string.digits + '_', 
                            min_size=0, max_size=20))
    password = draw(st.text(alphabet=string.ascii_letters + string.digits + '_!@#$', 
                            min_size=0, max_size=20))
    
    # Host and port
    host = draw(st.one_of(
        st.just('localhost'),
        st.just('127.0.0.1'),
        st.text(alphabet=string.ascii_lowercase + string.digits + '.', 
                min_size=1, max_size=30).filter(lambda x: x[0] != '.' and x[-1] != '.')
    ))
    port = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=65535)))
    
    # Database name
    database = draw(st.text(alphabet=string.ascii_letters + string.digits + '_', 
                            min_size=1, max_size=30))
    
    # Build URL
    if driver.startswith('sqlite'):
        # SQLite has special format
        if database:
            return f"{driver}:///{database}"
        else:
            return f"{driver}:///:memory:"
    
    url_str = f"{driver}://"
    if username:
        url_str += username
        if password:
            url_str += f":{password}"
        url_str += "@"
    
    url_str += host
    if port:
        url_str += f":{port}"
    url_str += f"/{database}"
    
    return url_str


@given(valid_db_url_strings())
@settings(max_examples=200)
def test_url_round_trip_property(url_string):
    """Test that parsing and rendering a URL preserves the original string."""
    parsed = url.make_url(url_string)
    rendered = parsed.render_as_string(hide_password=False)
    
    # The rendered URL should match the original
    assert url_string == rendered, f"URL round-trip failed: {url_string} != {rendered}"


@given(
    drivername=st.sampled_from(['postgresql', 'mysql', 'sqlite', 'oracle']),
    username=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    password=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    host=st.one_of(st.none(), st.text(min_size=1, max_size=30)),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    database=st.one_of(st.none(), st.text(min_size=1, max_size=30))
)
@settings(max_examples=200)
def test_url_create_components_preserved(drivername, username, password, host, port, database):
    """Test that URL.create preserves all components."""
    # Skip invalid combinations
    if drivername == 'sqlite' and (username or password or host or port):
        assume(False)
    
    created_url = url.URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    
    # Check all components are preserved
    assert created_url.drivername == drivername
    assert created_url.username == username
    assert created_url.password == password
    assert created_url.host == host
    assert created_url.port == port
    assert created_url.database == database


@given(
    drivername=st.text(min_size=1, max_size=20),
    username=st.text(min_size=1, max_size=20),
    password=st.text(min_size=1, max_size=20),
    host=st.text(min_size=1, max_size=30),
    port=st.integers(min_value=1, max_value=65535),
    database=st.text(min_size=1, max_size=30)
)
@settings(max_examples=200)
def test_url_create_render_round_trip(drivername, username, password, host, port, database):
    """Test URL.create followed by render_as_string and make_url round-trip."""
    created_url = url.URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    
    # Render to string
    url_string = created_url.render_as_string(hide_password=False)
    
    # Parse back
    parsed_url = url.make_url(url_string)
    
    # Components should match
    assert parsed_url.drivername == drivername
    assert parsed_url.username == username
    assert parsed_url.password == password
    assert parsed_url.host == host
    assert parsed_url.port == port
    assert parsed_url.database == database


# Type System Tests
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans(),
        st.none()
    )
)
def test_literal_value_preservation(value):
    """Test that literal() preserves the value."""
    lit = literal(value)
    # The value should be accessible
    assert lit.value == value


@given(
    type_name=st.sampled_from([
        'Integer', 'String', 'Boolean', 'Float', 'BigInteger', 
        'SmallInteger', 'Numeric', 'Text', 'Unicode'
    ])
)
def test_type_name_consistency(type_name):
    """Test that type classes have consistent naming."""
    type_class = getattr(types, type_name)
    type_instance = type_class()
    
    # The type should have a consistent string representation
    type_str = str(type_instance)
    assert type_name.upper() in type_str.upper() or type_name in type_str


# Query Parameter Tests
@given(params=st.dictionaries(
    st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10),
    st.text(min_size=0, max_size=50),
    min_size=0,
    max_size=5
))
@settings(max_examples=100)
def test_url_query_params_round_trip(params):
    """Test that URL query parameters are preserved."""
    base_url = url.URL.create(
        drivername='postgresql',
        host='localhost',
        database='testdb',
        query=params
    )
    
    # Render and parse back
    url_string = base_url.render_as_string(hide_password=False)
    parsed_url = url.make_url(url_string)
    
    # Query params should match
    for key, value in params.items():
        assert key in parsed_url.query
        assert parsed_url.query[key] == value


# Test URL update_query methods
@given(
    initial_params=st.dictionaries(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
        st.text(min_size=1, max_size=10),
        min_size=0,
        max_size=3
    ),
    update_params=st.dictionaries(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
        st.text(min_size=1, max_size=10),
        min_size=0,
        max_size=3
    )
)
def test_url_update_query_dict(initial_params, update_params):
    """Test URL.update_query_dict method."""
    base_url = url.URL.create(
        drivername='postgresql',
        host='localhost',
        database='testdb',
        query=initial_params
    )
    
    updated_url = base_url.update_query_dict(update_params)
    
    # Original URL should be unchanged
    for key, value in initial_params.items():
        assert base_url.query.get(key) == value
    
    # Updated URL should have new params
    for key, value in update_params.items():
        assert updated_url.query.get(key) == value


# Test URL difference_update_query
@given(
    initial_params=st.dictionaries(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=5),
        st.text(min_size=1, max_size=10),
        min_size=1,
        max_size=5
    )
)
def test_url_difference_update_query(initial_params):
    """Test URL.difference_update_query removes specified keys."""
    base_url = url.URL.create(
        drivername='postgresql',
        host='localhost',
        database='testdb',
        query=initial_params
    )
    
    # Remove some keys
    keys_to_remove = list(initial_params.keys())[:len(initial_params)//2]
    if keys_to_remove:
        updated_url = base_url.difference_update_query(keys_to_remove)
        
        # Removed keys should not be in updated URL
        for key in keys_to_remove:
            assert key not in updated_url.query
        
        # Remaining keys should still be there
        for key in initial_params:
            if key not in keys_to_remove:
                assert updated_url.query.get(key) == initial_params[key]