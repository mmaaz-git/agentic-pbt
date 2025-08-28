import string
from hypothesis import assume, given, strategies as st, settings, seed
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.util import asbool, asint, OrderedSet


# Aggressive URL testing with all special characters
@given(st.text(min_size=1, max_size=50))
@settings(max_examples=5000)
def test_url_password_special_chars_aggressive(password):
    """Test URL parsing with passwords containing special characters."""
    # Focus on passwords that might break URL parsing
    
    # Create URL with password
    original_url = URL.create(
        drivername="postgresql",
        username="user",
        password=password,
        host="localhost", 
        database="db"
    )
    
    # Render as string
    url_string = original_url.render_as_string(hide_password=False)
    
    # Parse back
    try:
        parsed_url = make_url(url_string)
        
        # Password should match exactly
        assert parsed_url.password == original_url.password, \
            f"Password mismatch: original={repr(original_url.password)}, parsed={repr(parsed_url.password)}"
    except Exception as e:
        # If parsing fails but URL.create succeeded, that's a bug
        print(f"URL parsing failed for password {repr(password)}: {e}")
        print(f"URL string was: {url_string}")
        raise


# Test URL with @ in username
@given(st.text(alphabet=string.ascii_letters + "@", min_size=1, max_size=20).filter(lambda x: "@" in x))
def test_url_at_sign_in_username(username):
    """Test URL with @ character in username."""
    
    # Create URL with @ in username
    original_url = URL.create(
        drivername="postgresql",
        username=username,
        host="localhost",
        database="db"
    )
    
    # Render and parse back
    url_string = original_url.render_as_string(hide_password=False)
    
    try:
        parsed_url = make_url(url_string)
        assert parsed_url.username == original_url.username
    except Exception as e:
        print(f"Failed with username containing @: {repr(username)}")
        print(f"URL string: {url_string}")
        raise


# Test URL query parameter round-trip with special characters
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(min_size=0, max_size=20),
        min_size=1,
        max_size=5
    )
)
def test_url_query_params_special_chars(params):
    """Test URL query parameters with special characters."""
    
    original_url = URL.create(
        drivername="postgresql",
        host="localhost",
        database="db",
        query=params
    )
    
    url_string = original_url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    # Query params should match
    assert parsed_url.query == original_url.query, \
        f"Query mismatch: original={original_url.query}, parsed={parsed_url.query}"


# Test asint with strings that look like numbers but aren't
@given(st.text())
def test_asint_string_robustness(text):
    """Test asint with arbitrary strings."""
    try:
        result = asint(text)
        # If it succeeds, verify it's actually an integer
        assert isinstance(result, (int, type(None)))
        
        # If not None, converting back to string and parsing should work
        if result is not None:
            assert asint(str(result)) == result
    except (ValueError, TypeError, OverflowError) as e:
        # These are expected for non-numeric strings
        pass
    except Exception as e:
        print(f"Unexpected error for asint({repr(text)}): {e}")
        raise


# Test OrderedSet.union with self
@given(st.lists(st.integers(), min_size=0, max_size=20))
def test_ordered_set_union_with_self(items):
    """Test that union with self is idempotent."""
    s = OrderedSet(items)
    union_with_self = s.union(s)
    
    # Union with self should give same set
    assert list(union_with_self) == list(s)
    assert set(union_with_self) == set(s)


# Test OrderedSet operations with empty sets
@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_ordered_set_empty_operations(items):
    """Test OrderedSet operations with empty set."""
    s = OrderedSet(items)
    empty = OrderedSet([])
    
    # Union with empty should be identity
    assert list(s.union(empty)) == list(s)
    assert list(empty.union(s)) == list(s)
    
    # Intersection with empty should be empty
    assert list(s.intersection(empty)) == []
    assert list(empty.intersection(s)) == []
    
    # Difference with empty should be identity
    assert list(s.difference(empty)) == list(s)
    
    # Empty difference s should be empty
    assert list(empty.difference(s)) == []


# Test URL with numeric host (IP address)
@given(
    st.tuples(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255)
    )
)
def test_url_ip_address_host(ip_parts):
    """Test URL with IP address as host."""
    ip_address = ".".join(str(p) for p in ip_parts)
    
    url_str = f"postgresql://user@{ip_address}/db"
    url_obj = make_url(url_str)
    rendered = url_obj.render_as_string(hide_password=False)
    parsed = make_url(rendered)
    
    assert parsed.host == url_obj.host == ip_address


# Test asbool with empty and whitespace strings
@given(st.text(alphabet=" \t\n\r", min_size=0, max_size=10))
def test_asbool_whitespace_only(whitespace):
    """Test asbool with whitespace-only strings."""
    try:
        result = asbool(whitespace)
        # Empty or whitespace string should behave consistently
        assert isinstance(result, bool)
    except ValueError as e:
        # Should get clear error for invalid strings
        assert "String is not true/false" in str(e)


# Test OrderedSet with None
def test_ordered_set_with_none():
    """Test OrderedSet containing None."""
    s = OrderedSet([1, None, 2, None, 3])
    
    # Should contain only one None
    assert None in s
    assert list(s) == [1, None, 2, 3]
    
    # Operations with None
    s2 = OrderedSet([None, 4, 5])
    union = s.union(s2)
    assert None in union
    
    intersection = s.intersection(s2)
    assert None in intersection


# Test URL.create vs make_url consistency
@given(
    scheme=st.sampled_from(["postgresql", "mysql", "sqlite"]),
    username=st.one_of(st.none(), st.text(alphabet=string.ascii_letters, min_size=1, max_size=10)),
    password=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10)),
    host=st.one_of(st.none(), st.sampled_from(["localhost", "127.0.0.1", "example.com"])),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    database=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20))
)
def test_url_create_vs_make_url(scheme, username, password, host, port, database):
    """Test that URL.create and make_url produce consistent results."""
    
    # Create using URL.create
    created_url = URL.create(
        drivername=scheme,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    
    # Create using make_url from string
    url_string = created_url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    # All components should match
    assert created_url.drivername == parsed_url.drivername
    assert created_url.username == parsed_url.username
    assert created_url.password == parsed_url.password
    assert created_url.host == parsed_url.host
    assert created_url.port == parsed_url.port
    assert created_url.database == parsed_url.database