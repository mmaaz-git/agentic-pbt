"""
Property-based tests for sqlalchemy.engine URL parsing and rendering.
"""
import string
from hypothesis import assume, given, strategies as st, settings
from sqlalchemy.engine import make_url
from sqlalchemy.engine.url import URL
import urllib.parse


# Strategy for valid database driver names
driver_names = st.sampled_from([
    'postgresql', 'mysql', 'sqlite', 'oracle', 'mssql',
    'postgresql+psycopg2', 'mysql+pymysql', 'postgresql+asyncpg'
])

# Strategy for usernames and passwords
# Based on RFC 3986, these characters need special handling in URLs
safe_chars = string.ascii_letters + string.digits + '-._~'
username_strategy = st.text(alphabet=safe_chars, min_size=1, max_size=20)
password_strategy = st.text(alphabet=safe_chars, min_size=0, max_size=20)

# Strategy for hostnames
hostname_strategy = st.one_of(
    st.just('localhost'),
    st.text(alphabet=string.ascii_lowercase + string.digits + '-', min_size=1, max_size=30).filter(
        lambda x: not x.startswith('-') and not x.endswith('-')
    )
)

# Strategy for ports
port_strategy = st.one_of(st.none(), st.integers(min_value=1, max_value=65535))

# Strategy for database names
database_strategy = st.text(alphabet=safe_chars, min_size=0, max_size=30)

# Strategy for query parameters
query_key_strategy = st.text(alphabet=safe_chars, min_size=1, max_size=10)
query_value_strategy = st.text(alphabet=safe_chars, min_size=0, max_size=20)
query_strategy = st.dictionaries(query_key_strategy, query_value_strategy, max_size=5)


@given(
    drivername=driver_names,
    username=st.one_of(st.none(), username_strategy),
    password=st.one_of(st.none(), password_strategy),
    host=st.one_of(st.none(), hostname_strategy),
    port=port_strategy,
    database=st.one_of(st.none(), database_strategy),
    query=query_strategy
)
def test_url_create_round_trip(drivername, username, password, host, port, database, query):
    """Test that URL.create components can be round-tripped."""
    # Create URL from components
    url = URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query=query
    )
    
    # Convert to string and parse back
    url_string = url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    # Check that all components match
    assert parsed_url.drivername == drivername
    assert parsed_url.username == username
    assert parsed_url.password == password
    assert parsed_url.host == host
    assert parsed_url.port == port
    assert parsed_url.database == database
    # Query comparison needs special handling due to normalization
    assert dict(parsed_url.query) == query


@given(
    drivername=driver_names,
    username=st.one_of(st.none(), username_strategy),
    password=st.one_of(st.none(), password_strategy),
    host=st.one_of(st.none(), hostname_strategy),
    port=port_strategy,
    database=st.one_of(st.none(), database_strategy),
    query=query_strategy
)
def test_url_idempotence(drivername, username, password, host, port, database, query):
    """Test that make_url is idempotent when given a URL object."""
    url = URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query=query
    )
    
    # make_url should return the same URL object when given a URL
    result = make_url(url)
    assert result is url  # Should be the exact same object


@given(
    drivername=driver_names,
    username=st.one_of(st.none(), username_strategy),
    password=st.one_of(st.none(), password_strategy),
    host=st.one_of(st.none(), hostname_strategy),
    port=port_strategy,
    database=st.one_of(st.none(), database_strategy)
)
def test_url_string_round_trip_no_query(drivername, username, password, host, port, database):
    """Test URL string round-trip without query parameters."""
    # Build URL string manually
    url_parts = [drivername, '://']
    
    if username is not None:
        url_parts.append(username)
        if password is not None:
            url_parts.append(':')
            url_parts.append(password)
        url_parts.append('@')
    
    if host is not None:
        url_parts.append(host)
        if port is not None:
            url_parts.append(':')
            url_parts.append(str(port))
    
    if database is not None:
        if host is not None:
            url_parts.append('/')
        url_parts.append(database)
    
    url_string = ''.join(url_parts)
    
    # Parse and render back
    parsed_url = make_url(url_string)
    rendered = parsed_url.render_as_string(hide_password=False)
    
    # They should match exactly for simple URLs
    assert rendered == url_string


@given(
    drivername=driver_names,
    username=st.one_of(st.none(), username_strategy),
    password=st.one_of(st.none(), password_strategy),
    host=st.one_of(st.none(), hostname_strategy),
    port=port_strategy,
    database=st.one_of(st.none(), database_strategy),
    query=query_strategy.filter(lambda q: all(v != '' for v in q.values()))
)
def test_url_create_reconstruct(drivername, username, password, host, port, database, query):
    """Test that a URL can be reconstructed from its parsed components."""
    original_url = URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query=query
    )
    
    # Reconstruct from components
    reconstructed_url = URL.create(
        drivername=original_url.drivername,
        username=original_url.username,
        password=original_url.password,
        host=original_url.host,
        port=original_url.port,
        database=original_url.database,
        query=original_url.query
    )
    
    # The rendered strings should match
    assert original_url.render_as_string(hide_password=False) == \
           reconstructed_url.render_as_string(hide_password=False)


# Test for special characters that might cause issues
@given(
    text_with_special=st.text(
        alphabet=string.ascii_letters + string.digits + ' +/@=&',
        min_size=1,
        max_size=20
    )
)
def test_query_value_special_chars(text_with_special):
    """Test that query values with special characters are handled correctly."""
    url = URL.create(
        drivername='postgresql',
        host='localhost',
        database='test',
        query={'key': text_with_special}
    )
    
    url_string = url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    # The query value should be preserved
    assert parsed_url.query.get('key') == text_with_special


@given(
    username=st.text(alphabet=string.ascii_letters + string.digits + '+@/', min_size=1, max_size=20),
    password=st.text(alphabet=string.ascii_letters + string.digits + '+@/', min_size=1, max_size=20)
)
def test_username_password_special_chars(username, password):
    """Test that usernames and passwords with special characters are preserved."""
    # Skip if username contains @ as it would be ambiguous
    assume('@' not in username)
    
    url = URL.create(
        drivername='postgresql',
        username=username,
        password=password,
        host='localhost',
        database='test'
    )
    
    url_string = url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    # Username and password should be preserved
    assert parsed_url.username == username
    assert parsed_url.password == password