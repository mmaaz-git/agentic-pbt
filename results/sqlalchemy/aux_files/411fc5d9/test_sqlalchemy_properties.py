import math
import string
from hypothesis import assume, given, strategies as st, settings
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.util import asbool, asint, OrderedSet


# URL round-trip property tests
@given(
    scheme=st.sampled_from(['postgresql', 'mysql', 'sqlite', 'oracle', 'mssql']),
    driver=st.one_of(st.none(), st.sampled_from(['', 'pymysql', 'psycopg2', 'cx_oracle'])),
    username=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=1, max_size=20)),
    password=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits + '_!@#$', min_size=1, max_size=20)),
    host=st.one_of(st.none(), st.sampled_from(['localhost', '127.0.0.1', 'db.example.com'])),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    database=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=1, max_size=30))
)
def test_url_round_trip(scheme, driver, username, password, host, port, database):
    # Build URL string
    if driver:
        scheme_part = f"{scheme}+{driver}" if driver else scheme
    else:
        scheme_part = scheme
    
    url_str = f"{scheme_part}://"
    
    if username:
        url_str += username
        if password:
            url_str += f":{password}"
        url_str += "@"
    
    if host:
        url_str += host
        if port:
            url_str += f":{port}"
    
    if database:
        url_str += f"/{database}"
    
    # Test round-trip
    url_obj = make_url(url_str)
    rendered = url_obj.render_as_string(hide_password=False)
    
    # The rendered string should be parseable and produce equivalent URL
    url_obj2 = make_url(rendered)
    assert url_obj.drivername == url_obj2.drivername
    assert url_obj.username == url_obj2.username
    assert url_obj.password == url_obj2.password
    assert url_obj.host == url_obj2.host
    assert url_obj.port == url_obj2.port
    assert url_obj.database == url_obj2.database


# asbool idempotence property
@given(st.one_of(
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.integers()),
    st.text(),
    st.sampled_from(['true', 'false', 'yes', 'no', 'on', 'off', '1', '0', 't', 'f', 'y', 'n'])
))
def test_asbool_idempotence(value):
    try:
        result1 = asbool(value)
        result2 = asbool(result1)
        assert result1 == result2, f"asbool not idempotent for {value}"
    except ValueError:
        # If it raises ValueError for invalid string, that's expected
        pass


# asbool case insensitivity for valid boolean strings
@given(st.sampled_from(['true', 'false', 'yes', 'no', 'on', 'off', 't', 'f', 'y', 'n']))
def test_asbool_case_insensitive(bool_str):
    lower_result = asbool(bool_str.lower())
    upper_result = asbool(bool_str.upper())
    mixed_result = asbool(bool_str.title())
    
    assert lower_result == upper_result == mixed_result


# asbool whitespace handling
@given(
    bool_str=st.sampled_from(['true', 'false', 'yes', 'no', 'on', 'off', '1', '0']),
    leading_space=st.text(alphabet=' \t', max_size=10),
    trailing_space=st.text(alphabet=' \t', max_size=10)
)
def test_asbool_whitespace_handling(bool_str, leading_space, trailing_space):
    spaced_str = leading_space + bool_str + trailing_space
    
    result_with_space = asbool(spaced_str)
    result_without_space = asbool(bool_str)
    
    assert result_with_space == result_without_space


# asint property - None preservation
def test_asint_none_preservation():
    assert asint(None) is None


# asint round-trip for integers
@given(st.integers())
def test_asint_integer_round_trip(value):
    result = asint(value)
    assert result == value


# asint string conversion
@given(st.integers().map(str))
def test_asint_string_conversion(value_str):
    result = asint(value_str)
    assert result == int(value_str)


# OrderedSet preserves order
@given(st.lists(st.integers(), min_size=0, max_size=20))
def test_ordered_set_preserves_order(items):
    ordered_set = OrderedSet(items)
    
    # Get unique items in order of first appearance
    seen = set()
    expected = []
    for item in items:
        if item not in seen:
            expected.append(item)
            seen.add(item)
    
    assert list(ordered_set) == expected


# OrderedSet union preserves order
@given(
    list1=st.lists(st.integers(), min_size=0, max_size=10),
    list2=st.lists(st.integers(), min_size=0, max_size=10)
)
def test_ordered_set_union_order(list1, list2):
    set1 = OrderedSet(list1)
    set2 = OrderedSet(list2)
    
    union_result = set1.union(set2)
    
    # Union should contain all elements from both sets
    assert set(union_result) == set(set1) | set(set2)
    
    # Elements from set1 should come before new elements from set2
    union_list = list(union_result)
    set1_list = list(set1)
    
    # Check that all elements from set1 appear in same order
    set1_positions = [union_list.index(x) for x in set1_list if x in union_list]
    assert set1_positions == sorted(set1_positions)


# OrderedSet intersection maintains set semantics
@given(
    list1=st.lists(st.integers(), min_size=0, max_size=10),
    list2=st.lists(st.integers(), min_size=0, max_size=10)
)
def test_ordered_set_intersection(list1, list2):
    set1 = OrderedSet(list1)
    set2 = OrderedSet(list2)
    
    intersection = set1.intersection(set2)
    
    # Intersection should contain only common elements
    assert set(intersection) == set(set1) & set(set2)
    
    # Order should be preserved from set1
    intersection_list = list(intersection)
    set1_list = list(set1)
    
    # Elements in intersection should maintain relative order from set1
    for i in range(len(intersection_list) - 1):
        elem1 = intersection_list[i]
        elem2 = intersection_list[i + 1]
        idx1 = set1_list.index(elem1)
        idx2 = set1_list.index(elem2)
        assert idx1 < idx2


# OrderedSet difference operation
@given(
    list1=st.lists(st.integers(), min_size=0, max_size=10),
    list2=st.lists(st.integers(), min_size=0, max_size=10)
)
def test_ordered_set_difference(list1, list2):
    set1 = OrderedSet(list1)
    set2 = OrderedSet(list2)
    
    difference = set1.difference(set2)
    
    # Difference should contain elements in set1 but not in set2
    assert set(difference) == set(set1) - set(set2)
    
    # Order should be preserved from set1
    diff_list = list(difference)
    set1_list = list(set1)
    
    # Elements should maintain relative order from set1
    for i in range(len(diff_list) - 1):
        elem1 = diff_list[i]
        elem2 = diff_list[i + 1]
        idx1 = set1_list.index(elem1)
        idx2 = set1_list.index(elem2)
        assert idx1 < idx2


# OrderedSet initialization is idempotent
@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_ordered_set_idempotent_init(items):
    set1 = OrderedSet(items)
    set2 = OrderedSet(set1)
    
    assert list(set1) == list(set2)
    assert set(set1) == set(set2)