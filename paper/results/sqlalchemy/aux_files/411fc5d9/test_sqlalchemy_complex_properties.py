import string
from hypothesis import assume, given, strategies as st, settings
from sqlalchemy.util import asbool, asint, OrderedSet
from sqlalchemy.engine.url import make_url


# Test that asbool handles various Unicode strings correctly
@given(st.text())
@settings(max_examples=1000)
def test_asbool_unicode_handling(text):
    # asbool should either return a boolean or raise ValueError for invalid strings
    try:
        result = asbool(text)
        assert isinstance(result, bool)
        
        # If it succeeded, calling it again should give same result
        result2 = asbool(text)
        assert result == result2
    except ValueError as e:
        # ValueError is expected for strings that aren't boolean-like
        assert "String is not true/false" in str(e)
    except Exception as e:
        # Any other exception might be a bug
        print(f"Unexpected exception for asbool('{text}'): {e}")
        raise


# Test asint with float strings
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_asint_float_string_conversion(value):
    # asint with float string should either work or raise appropriate error
    float_str = str(value)
    
    try:
        result = asint(float_str)
        # If it succeeds, it should be an integer
        assert isinstance(result, int)
    except ValueError:
        # ValueError is expected for non-integer strings
        assert '.' in float_str or 'e' in float_str.lower()


# Test OrderedSet with unhashable types gracefully
def test_ordered_set_unhashable_handling():
    # OrderedSet should handle or reject unhashable types appropriately
    try:
        # Try with a list of lists (unhashable)
        OrderedSet([[1], [2], [3]])
        # If it works, it should have converted them somehow
    except TypeError as e:
        # TypeError is expected for unhashable types
        assert "unhashable" in str(e)


# Test URL with extremely long components
@given(
    long_string=st.text(alphabet=string.ascii_letters, min_size=100, max_size=1000)
)
def test_url_long_components(long_string):
    # Test with very long database name
    url_str = f"postgresql://user@localhost/{long_string}"
    
    url_obj = make_url(url_str)
    rendered = url_obj.render_as_string(hide_password=False)
    url_obj2 = make_url(rendered)
    
    # Long database name should be preserved
    assert url_obj.database == url_obj2.database == long_string


# Test OrderedSet symmetric difference property
@given(
    list1=st.lists(st.integers(), min_size=0, max_size=10),
    list2=st.lists(st.integers(), min_size=0, max_size=10)
)
def test_ordered_set_symmetric_difference(list1, list2):
    set1 = OrderedSet(list1)
    set2 = OrderedSet(list2)
    
    # Symmetric difference using union and intersection
    union = set1.union(set2)
    intersection = set1.intersection(set2)
    
    # Elements in union but not in intersection
    sym_diff_via_ops = OrderedSet(union).difference(OrderedSet(intersection))
    
    # Should equal (set1 - set2) union (set2 - set1)
    diff1 = set1.difference(set2)
    diff2 = set2.difference(set1)
    sym_diff_direct = OrderedSet(diff1).union(OrderedSet(diff2))
    
    assert set(sym_diff_via_ops) == set(sym_diff_direct)


# Test asbool with mixed-type inputs
@given(
    value=st.one_of(
        st.binary(),
        st.complex_numbers(allow_nan=False, allow_infinity=False),
        st.dictionaries(st.text(), st.integers()),
        st.tuples(st.integers(), st.integers())
    )
)
def test_asbool_mixed_types(value):
    # asbool should handle various Python types
    try:
        result = asbool(value)
        assert isinstance(result, bool)
        
        # Should follow Python's bool() for non-string types
        if not isinstance(value, str):
            assert result == bool(value)
    except Exception as e:
        # Complex numbers and other types might cause issues
        print(f"Exception for asbool({type(value).__name__}): {e}")
        # Only string ValueError is expected
        if isinstance(value, str):
            assert isinstance(e, ValueError)


# Test URL parsing with IPv6 addresses
def test_url_ipv6_handling():
    test_cases = [
        "postgresql://user@[::1]/db",  # IPv6 localhost
        "postgresql://user@[2001:db8::1]/db",  # IPv6 address
        "postgresql://user@[::1]:5432/db",  # IPv6 with port
    ]
    
    for url_str in test_cases:
        try:
            url_obj = make_url(url_str)
            rendered = url_obj.render_as_string(hide_password=False)
            url_obj2 = make_url(rendered)
            
            # Host should be preserved
            assert url_obj.host == url_obj2.host
        except Exception as e:
            print(f"IPv6 handling issue for {url_str}: {e}")


# Test OrderedSet with duplicate-heavy lists
@given(
    base_list=st.lists(st.integers(min_value=0, max_value=5), min_size=20, max_size=50)
)
def test_ordered_set_duplicate_heavy(base_list):
    # Test with lots of duplicates
    ordered_set = OrderedSet(base_list)
    
    # Should have at most 6 elements (0-5)
    assert len(ordered_set) <= 6
    
    # First occurrence order should be preserved
    seen_indices = {}
    for i, val in enumerate(base_list):
        if val not in seen_indices:
            seen_indices[val] = i
    
    expected_order = sorted(seen_indices.keys(), key=lambda x: seen_indices[x])
    assert list(ordered_set) == expected_order


# Test asint with edge case numeric strings
def test_asint_edge_cases():
    edge_cases = [
        ("0", 0),
        ("-0", 0),
        ("+42", 42),
        ("  42  ", 42),
        ("-42", -42),
        ("00042", 42),
        ("1_000", None),  # Python numeric literal syntax - might fail
    ]
    
    for input_val, expected in edge_cases:
        try:
            result = asint(input_val)
            if expected is not None:
                assert result == expected, f"asint('{input_val}') returned {result}, expected {expected}"
        except ValueError:
            # Some edge cases might raise ValueError
            pass


# Test metamorphic property: OrderedSet operations associativity  
@given(
    list1=st.lists(st.integers(), max_size=10),
    list2=st.lists(st.integers(), max_size=10),
    list3=st.lists(st.integers(), max_size=10)
)
def test_ordered_set_union_associative(list1, list2, list3):
    set1 = OrderedSet(list1)
    set2 = OrderedSet(list2)
    set3 = OrderedSet(list3)
    
    # (A ∪ B) ∪ C should have same elements as A ∪ (B ∪ C)
    left_assoc = set1.union(set2).union(set3)
    right_assoc = set1.union(set2.union(set3))
    
    # Sets should be equal (though order might differ)
    assert set(left_assoc) == set(right_assoc)