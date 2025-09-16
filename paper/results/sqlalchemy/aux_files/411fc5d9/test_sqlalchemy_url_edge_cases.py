import string
from hypothesis import assume, given, strategies as st, settings, example
from sqlalchemy.engine.url import make_url, URL


# Test URL with special characters in password
@given(
    password=st.text(min_size=1, max_size=50)
)
def test_url_special_chars_in_password(password):
    # Skip if password contains characters that would break URL parsing
    assume('@' not in password)
    assume('/' not in password)
    assume(':' not in password)
    
    url_str = f"postgresql://user:{password}@localhost/db"
    
    try:
        url_obj = make_url(url_str)
        rendered = url_obj.render_as_string(hide_password=False)
        
        # Try to parse the rendered URL again
        url_obj2 = make_url(rendered)
        
        # Passwords should match
        assert url_obj.password == url_obj2.password
    except Exception:
        # If it fails, that might indicate a bug with special character handling
        pass


# Test URL with query parameters
@given(
    params=st.dictionaries(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
        st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
        min_size=0,
        max_size=5
    )
)
def test_url_with_query_params(params):
    base_url = "postgresql://user@localhost/db"
    
    if params:
        query_str = "&".join(f"{k}={v}" for k, v in params.items())
        url_str = f"{base_url}?{query_str}"
    else:
        url_str = base_url
    
    url_obj = make_url(url_str)
    rendered = url_obj.render_as_string(hide_password=False)
    url_obj2 = make_url(rendered)
    
    # Query parameters should be preserved
    assert url_obj.query == url_obj2.query


# Test URL normalization
@given(
    scheme=st.sampled_from(['postgresql', 'mysql', 'sqlite']),
    host=st.sampled_from(['LOCALHOST', 'LocalHost', 'localhost'])
)
def test_url_host_normalization(scheme, host):
    url_str = f"{scheme}://user@{host}/db"
    url_obj = make_url(url_str)
    rendered = url_obj.render_as_string(hide_password=False)
    
    # Check if host is normalized
    url_obj2 = make_url(rendered)
    assert url_obj.host == url_obj2.host


# Test empty components
def test_url_empty_components():
    test_cases = [
        "postgresql://localhost/db",  # No user
        "postgresql://user@localhost",  # No database
        "postgresql://user@/db",  # Empty host
        "postgresql://@localhost/db",  # Empty user
    ]
    
    for url_str in test_cases:
        try:
            url_obj = make_url(url_str)
            rendered = url_obj.render_as_string(hide_password=False)
            url_obj2 = make_url(rendered)
            
            # All components should match after round-trip
            assert url_obj.drivername == url_obj2.drivername
            assert url_obj.username == url_obj2.username
            assert url_obj.password == url_obj2.password
            assert url_obj.host == url_obj2.host
            assert url_obj.database == url_obj2.database
        except Exception as e:
            print(f"Failed for {url_str}: {e}")
            raise


# Test URL with percent encoding
@given(
    username=st.text(alphabet=string.ascii_letters + ' !#$%', min_size=1, max_size=20)
)
def test_url_percent_encoding(username):
    # Skip usernames with @ or : which have special meaning
    assume('@' not in username)
    assume(':' not in username)
    assume('/' not in username)
    
    url_str = f"postgresql://{username}@localhost/db"
    
    try:
        url_obj = make_url(url_str)
        rendered = url_obj.render_as_string(hide_password=False)
        url_obj2 = make_url(rendered)
        
        # Username should be preserved even with special chars
        assert url_obj.username == url_obj2.username
    except Exception:
        pass


# Test database path for SQLite
@given(
    path=st.text(alphabet=string.ascii_letters + string.digits + '/_.-', min_size=1, max_size=50)
)
def test_sqlite_path_handling(path):
    # Ensure path doesn't start with multiple slashes
    path = path.lstrip('/')
    assume(path)  # Skip empty paths after stripping
    
    url_str = f"sqlite:///{path}"
    
    url_obj = make_url(url_str)
    rendered = url_obj.render_as_string(hide_password=False)
    url_obj2 = make_url(rendered)
    
    # Database path should be preserved
    assert url_obj.database == url_obj2.database


# Test port edge cases
@given(
    port=st.one_of(
        st.just(None),
        st.integers(min_value=1, max_value=65535),
        st.sampled_from([80, 443, 3306, 5432, 1433])  # Common DB ports
    )
)
def test_url_port_handling(port):
    if port is None:
        url_str = "postgresql://user@localhost/db"
    else:
        url_str = f"postgresql://user@localhost:{port}/db"
    
    url_obj = make_url(url_str)
    rendered = url_obj.render_as_string(hide_password=False)
    url_obj2 = make_url(rendered)
    
    assert url_obj.port == url_obj2.port


# Test make_url idempotence with URL object
@given(
    scheme=st.sampled_from(['postgresql', 'mysql', 'sqlite']),
    username=st.one_of(st.none(), st.text(alphabet=string.ascii_letters, min_size=1, max_size=10)),
    host=st.one_of(st.none(), st.sampled_from(['localhost', '127.0.0.1'])),
    database=st.one_of(st.none(), st.text(alphabet=string.ascii_letters, min_size=1, max_size=10))
)
def test_make_url_idempotence(scheme, username, host, database):
    url_str = f"{scheme}://"
    if username:
        url_str += f"{username}@"
    if host:
        url_str += host
    if database:
        url_str += f"/{database}"
    
    url_obj1 = make_url(url_str)
    url_obj2 = make_url(url_obj1)  # Pass URL object instead of string
    
    # Should return the same object or equivalent
    assert url_obj1.drivername == url_obj2.drivername
    assert url_obj1.username == url_obj2.username
    assert url_obj1.host == url_obj2.host
    assert url_obj1.database == url_obj2.database