import copy
import pytest
from hypothesis import given, strategies as st, assume, settings
from requests.cookies import (
    RequestsCookieJar, 
    cookiejar_from_dict,
    merge_cookies,
    create_cookie,
    morsel_to_cookie,
    remove_cookie_by_name,
    CookieConflictError
)
from http.cookies import SimpleCookie


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
    values=st.text(min_size=0, max_size=1000),
    min_size=0,
    max_size=20
))
def test_cookiejar_dict_roundtrip(cookie_dict):
    jar = cookiejar_from_dict(cookie_dict)
    result_dict = jar.get_dict()
    assert result_dict == cookie_dict


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
    values=st.text(min_size=0, max_size=1000),
    min_size=1,
    max_size=20
))
def test_cookiejar_items_consistency(cookie_dict):
    jar = cookiejar_from_dict(cookie_dict)
    
    items_result = dict(jar.items())
    assert items_result == cookie_dict
    
    keys_result = set(jar.keys())
    assert keys_result == set(cookie_dict.keys())
    
    values_result = list(jar.values())
    assert sorted(values_result) == sorted(cookie_dict.values())


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
    values=st.text(min_size=0, max_size=1000),
    min_size=0,
    max_size=20
))
def test_cookiejar_copy_independence(cookie_dict):
    jar1 = cookiejar_from_dict(cookie_dict)
    jar2 = jar1.copy()
    
    assert jar1.get_dict() == jar2.get_dict()
    
    if cookie_dict:
        key = list(cookie_dict.keys())[0]
        jar2.set(key, "modified_value")
        assert jar1.get(key) != "modified_value"


@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
        values=st.text(min_size=0, max_size=1000),
        min_size=0,
        max_size=10
    ),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
        values=st.text(min_size=0, max_size=1000),
        min_size=0,
        max_size=10
    )
)
def test_merge_cookies_dict_preserves_original(dict1, dict2):
    jar = cookiejar_from_dict(dict1)
    original_dict = jar.get_dict()
    
    result = merge_cookies(jar, dict2)
    
    assert result is jar
    
    for key in dict1:
        if key not in dict2:
            assert jar.get(key) == dict1[key]


@given(
    st.dictionaries(
        keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
        values=st.text(min_size=0, max_size=1000),
        min_size=0,
        max_size=10
    ),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
        values=st.text(min_size=0, max_size=1000),
        min_size=0,
        max_size=10
    )
)
def test_merge_cookies_overwrite_false(dict1, dict2):
    jar = cookiejar_from_dict(dict1)
    merge_cookies(jar, dict2)
    
    for key in dict1:
        assert jar.get(key) == dict1[key]


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
    values=st.text(min_size=0, max_size=1000),
    min_size=1,
    max_size=20
))
def test_multiple_domains_single_domain(cookie_dict):
    jar = cookiejar_from_dict(cookie_dict)
    
    assert jar.multiple_domains() == False
    
    domains = jar.list_domains()
    assert len(domains) <= 1


@given(st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
       st.text(min_size=0, max_size=1000))
def test_set_none_removes_cookie(name, value):
    jar = RequestsCookieJar()
    jar.set(name, value)
    assert jar.get(name) == value
    
    jar.set(name, None)
    assert jar.get(name) is None
    assert name not in jar


@given(st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
       st.text(min_size=0, max_size=1000))
def test_delitem_removes_cookie(name, value):
    jar = RequestsCookieJar()
    jar[name] = value
    assert jar[name] == value
    
    del jar[name]
    assert jar.get(name) is None
    with pytest.raises(KeyError):
        _ = jar[name]


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
    values=st.text(min_size=0, max_size=1000),
    min_size=0,
    max_size=20
))
def test_update_from_dict(cookie_dict):
    jar1 = RequestsCookieJar()
    jar1.update(cookie_dict)
    
    assert jar1.get_dict() == cookie_dict


@given(st.dictionaries(
    keys=st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
    values=st.text(min_size=0, max_size=1000),
    min_size=0,
    max_size=10
))
def test_update_from_cookiejar(cookie_dict):
    jar1 = cookiejar_from_dict(cookie_dict)
    jar2 = RequestsCookieJar()
    jar2.update(jar1)
    
    assert jar2.get_dict() == cookie_dict


@given(st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
       st.text(min_size=0, max_size=1000))
def test_create_cookie_domain_initial_dot(name, value):
    cookie = create_cookie(name, value, domain=".example.com")
    assert cookie.domain_initial_dot == True
    assert cookie.domain == ".example.com"
    
    cookie2 = create_cookie(name, value, domain="example.com")
    assert cookie2.domain_initial_dot == False
    assert cookie2.domain == "example.com"


@given(st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
       st.text(min_size=0, max_size=1000),
       st.integers(min_value=0, max_value=86400))
def test_morsel_to_cookie_maxage(name, value, max_age):
    morsel = SimpleCookie()
    morsel[name] = value
    morsel[name]["max-age"] = str(max_age)
    
    cookie = morsel_to_cookie(morsel[name])
    assert cookie.name == name
    assert cookie.value == value
    assert cookie.expires is not None


@given(st.text(min_size=1, max_size=100).filter(lambda x: x and not x.isspace()),
       st.text(min_size=0, max_size=1000))
def test_quoted_cookie_value_unquoting(name, value):
    jar = RequestsCookieJar()
    
    quoted_value = f'"{value}"'
    cookie = create_cookie(name, quoted_value)
    jar.set_cookie(cookie)
    
    retrieved = jar.get(name)
    assert retrieved == value or retrieved == quoted_value