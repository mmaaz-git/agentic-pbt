import copy
import random
import string
from hypothesis import given, strategies as st, assume, settings
import requests.cookies
from requests.cookies import (
    RequestsCookieJar,
    cookiejar_from_dict,
    merge_cookies,
    create_cookie,
    CookieConflictError
)


# Strategy for valid cookie names (no special chars that break cookies)
cookie_name = st.text(
    alphabet=string.ascii_letters + string.digits + '-_',
    min_size=1,
    max_size=100
).filter(lambda x: not x.startswith('__'))

# Strategy for cookie values
cookie_value = st.text(
    alphabet=string.ascii_letters + string.digits + '-_.~',
    min_size=0,
    max_size=1000
)

# Strategy for domain names
domain_name = st.text(
    alphabet=string.ascii_lowercase + string.digits + '.-',
    min_size=1,
    max_size=100
).filter(lambda x: x and not x.startswith('.') and not x.endswith('.'))

# Strategy for paths
path_name = st.text(
    alphabet=string.ascii_letters + string.digits + '/-_',
    min_size=1,
    max_size=100
).filter(lambda x: x.startswith('/'))


# Property 1: Round-trip cookiejar_from_dict
@given(st.dictionaries(cookie_name, cookie_value, min_size=0, max_size=20))
def test_cookiejar_from_dict_roundtrip(cookie_dict):
    """Converting dict to CookieJar and back should preserve data."""
    jar = cookiejar_from_dict(cookie_dict)
    
    # Extract cookies back to dict using the jar's methods
    result_dict = {}
    for cookie in jar:
        # Only use the name/value since that's what cookiejar_from_dict sets
        result_dict[cookie.name] = cookie.value
    
    assert result_dict == cookie_dict


# Property 2: Set/Get consistency in RequestsCookieJar
@given(
    cookie_name,
    cookie_value,
    st.one_of(st.none(), domain_name),
    st.one_of(st.none(), path_name)
)
def test_set_get_consistency(name, value, domain, path):
    """Setting a cookie and getting it should return the same value."""
    jar = RequestsCookieJar()
    
    # Set the cookie
    jar.set(name, value, domain=domain, path=path)
    
    # Get it back
    retrieved = jar.get(name, domain=domain, path=path)
    
    assert retrieved == value


# Property 3: Dict-like operations
@given(cookie_name, cookie_value)
def test_dict_like_operations(name, value):
    """RequestsCookieJar should support dict-like operations as documented."""
    jar = RequestsCookieJar()
    
    # Test __setitem__ and __getitem__
    jar[name] = value
    assert jar[name] == value
    
    # Test 'in' operator
    assert name in jar
    
    # Test keys()
    assert name in jar.keys()
    
    # Test values()  
    assert value in jar.values()
    
    # Test items()
    assert (name, value) in jar.items()
    
    # Test get() with default
    assert jar.get(name) == value
    assert jar.get(name + '_nonexistent', 'default') == 'default'


# Property 4: Merge cookies preserves all cookies
@given(
    st.dictionaries(cookie_name, cookie_value, min_size=0, max_size=10),
    st.dictionaries(cookie_name, cookie_value, min_size=0, max_size=10)
)
def test_merge_cookies(dict1, dict2):
    """Merging cookies should include all cookies from both sources."""
    jar1 = cookiejar_from_dict(dict1)
    jar2 = cookiejar_from_dict(dict2)
    
    # Merge jar2 into jar1
    result = merge_cookies(jar1, jar2)
    
    # All cookies from dict2 should be in result
    for name, value in dict2.items():
        assert result.get(name) == value
    
    # Cookies from dict1 that aren't overwritten should remain
    for name, value in dict1.items():
        if name not in dict2:
            assert result.get(name) == value


# Property 5: Cookie conflicts with same name but different domains
@given(
    cookie_name,
    cookie_value,
    cookie_value,
    domain_name,
    domain_name
)
def test_cookie_conflicts(name, value1, value2, domain1, domain2):
    """Multiple cookies with same name but different domains should be allowed."""
    assume(domain1 != domain2)  # Need different domains
    
    jar = RequestsCookieJar()
    
    # Set cookies with same name but different domains
    jar.set(name, value1, domain=domain1)
    jar.set(name, value2, domain=domain2)
    
    # Should be able to get each one specifically
    assert jar.get(name, domain=domain1) == value1
    assert jar.get(name, domain=domain2) == value2
    
    # Getting without domain should raise CookieConflictError
    # according to _find_no_duplicates documentation
    try:
        jar[name]  # This uses _find_no_duplicates without domain
        # If we get here, there might be a bug - it should conflict
        assert False, "Expected CookieConflictError but none was raised"
    except CookieConflictError:
        pass  # Expected behavior
    except KeyError:
        # This happens if no cookies match, which shouldn't happen
        pass


# Property 6: Update operation
@given(
    st.dictionaries(cookie_name, cookie_value, min_size=0, max_size=10),
    st.dictionaries(cookie_name, cookie_value, min_size=0, max_size=10)
)
def test_update_operation(dict1, dict2):
    """Update should work like dict update - later values override earlier."""
    jar1 = RequestsCookieJar()
    jar2 = RequestsCookieJar()
    
    # Set up the jars
    for name, value in dict1.items():
        jar1[name] = value
    for name, value in dict2.items():
        jar2[name] = value
    
    # Update jar1 with jar2
    jar1.update(jar2)
    
    # Check all values from dict2 are in jar1
    for name, value in dict2.items():
        assert jar1[name] == value
    
    # Check values from dict1 that weren't overridden
    for name, value in dict1.items():
        if name not in dict2:
            assert jar1[name] == value


# Property 7: Setting None should remove cookie
@given(cookie_name, cookie_value)
def test_set_none_removes_cookie(name, value):
    """Setting a cookie value to None should remove it."""
    jar = RequestsCookieJar()
    
    # Set a cookie
    jar.set(name, value)
    assert jar.get(name) == value
    
    # Set to None should remove it
    jar.set(name, None)
    assert jar.get(name) is None
    assert name not in jar


# Property 8: Copy operation
@given(st.dictionaries(cookie_name, cookie_value, min_size=0, max_size=10))
def test_copy_operation(cookie_dict):
    """Copy should create independent jar with same cookies."""
    jar1 = cookiejar_from_dict(cookie_dict)
    jar2 = jar1.copy()
    
    # Should have same cookies
    for name, value in cookie_dict.items():
        assert jar2.get(name) == value
    
    # But should be independent - modifying one shouldn't affect other
    if cookie_dict:
        first_name = list(cookie_dict.keys())[0]
        jar2.set(first_name, "modified")
        assert jar1.get(first_name) == cookie_dict[first_name]
        assert jar2.get(first_name) == "modified"