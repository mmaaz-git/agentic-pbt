import collections
import math
from hypothesis import given, strategies as st, assume, settings
import pytest


# Counter Properties

@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=-100, max_value=100)))
def test_counter_addition_commutativity(d1):
    """Counter addition should be commutative"""
    c1 = collections.Counter(d1)
    c2 = collections.Counter(d1)
    assert c1 + c2 == c2 + c1


@given(
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=-100, max_value=100)),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=-100, max_value=100)),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=-100, max_value=100))
)
def test_counter_addition_associativity(d1, d2, d3):
    """Counter addition should be associative"""
    c1 = collections.Counter(d1)
    c2 = collections.Counter(d2)
    c3 = collections.Counter(d3)
    assert (c1 + c2) + c3 == c1 + (c2 + c3)


@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=-100, max_value=100)))
def test_counter_subtract_inverse(d1):
    """Subtracting a counter from itself should yield empty positive counts"""
    c1 = collections.Counter(d1)
    result = c1 - c1
    assert all(v > 0 for v in result.values())
    assert len(result) == 0


@given(
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=100)),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=100))
)
def test_counter_union_idempotence(d1, d2):
    """Union with self should be idempotent"""
    c1 = collections.Counter(d1)
    assert c1 | c1 == c1


@given(
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=100)),
    st.dictionaries(st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=100))
)
def test_counter_intersection_commutativity(d1, d2):
    """Counter intersection should be commutative"""
    c1 = collections.Counter(d1)
    c2 = collections.Counter(d2)
    assert c1 & c2 == c2 & c1


@given(st.lists(st.integers()))
def test_counter_total_sum_invariant(items):
    """Counter.total() should equal sum of values"""
    c = collections.Counter(items)
    assert c.total() == sum(c.values())
    assert c.total() == len(items)


@given(st.lists(st.text(min_size=1, max_size=5)), st.integers(min_value=0, max_value=100))
def test_counter_most_common_length(items, n):
    """most_common(n) should return at most n items"""
    c = collections.Counter(items)
    result = c.most_common(n)
    assert len(result) <= n
    assert len(result) <= len(set(items))


@given(st.lists(st.integers(min_value=-100, max_value=100)))
def test_counter_elements_preserves_positive(items):
    """elements() should only yield items with positive counts"""
    c = collections.Counter(items)
    # Manually set some negative counts
    for key in list(c.keys())[:len(c)//2]:
        c[key] = -abs(c[key]) if c[key] != 0 else -1
    
    elements_list = list(c.elements())
    # Check that negative counts are not represented
    for elem in elements_list:
        assert c[elem] > 0


# ChainMap Properties

@given(
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers()),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers()),
    st.text(min_size=1, max_size=5)
)
def test_chainmap_lookup_order(d1, d2, key):
    """ChainMap should return value from first dict containing the key"""
    cm = collections.ChainMap(d1, d2)
    if key in d1:
        assert cm.get(key) == d1[key]
    elif key in d2:
        assert cm.get(key) == d2[key]
    else:
        assert cm.get(key) is None


@given(
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers()),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers())
)
def test_chainmap_length_invariant(d1, d2):
    """ChainMap length should be number of unique keys across all maps"""
    cm = collections.ChainMap(d1, d2)
    unique_keys = set(d1.keys()) | set(d2.keys())
    assert len(cm) == len(unique_keys)


@given(
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers()),
    st.text(min_size=1, max_size=5),
    st.integers()
)
def test_chainmap_write_to_first(d1, key, value):
    """Writes should only affect the first mapping"""
    d2 = d1.copy()
    cm = collections.ChainMap({}, d2)
    original_d2 = d2.copy()
    
    cm[key] = value
    assert cm.maps[0][key] == value
    assert cm.maps[1] == original_d2


@given(st.dictionaries(st.text(min_size=1, max_size=5), st.integers()))
def test_chainmap_parents_property(d1):
    """parents should skip the first map"""
    d2 = {"unique": 999}
    cm = collections.ChainMap(d1, d2)
    parents = cm.parents
    
    assert len(parents.maps) == 1
    assert parents.maps[0] == d2
    assert "unique" in parents


@given(st.dictionaries(st.text(min_size=1, max_size=5), st.integers()))
def test_chainmap_new_child_preserves_chain(d1):
    """new_child should add a new map at the front"""
    cm = collections.ChainMap(d1)
    child = cm.new_child()
    
    assert len(child.maps) == 2
    assert child.maps[0] == {}
    assert child.maps[1] == d1


# OrderedDict Properties

@given(st.lists(st.tuples(st.text(min_size=1, max_size=5), st.integers())))
def test_ordereddict_maintains_insertion_order(items):
    """OrderedDict should maintain insertion order"""
    od = collections.OrderedDict()
    for key, value in items:
        od[key] = value
    
    # Get unique keys in order of first appearance
    seen = set()
    expected_keys = []
    for key, _ in items:
        if key not in seen:
            expected_keys.append(key)
            seen.add(key)
    
    assert list(od.keys()) == expected_keys


@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=1))
def test_ordereddict_reversed_reverses(d):
    """Reversing twice should give original order"""
    od = collections.OrderedDict(d)
    forward = list(od)
    reverse = list(reversed(od))
    double_reverse = list(reversed(reverse))
    assert forward == double_reverse


@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), min_size=2))
def test_ordereddict_move_to_end(d):
    """move_to_end should correctly position elements"""
    od = collections.OrderedDict(d)
    keys = list(od.keys())
    if len(keys) >= 2:
        key = keys[0]
        od.move_to_end(key, last=True)
        assert list(od.keys())[-1] == key
        
        od.move_to_end(key, last=False)
        assert list(od.keys())[0] == key


# deque Properties

@given(st.lists(st.integers()), st.integers(min_value=-100, max_value=100))
def test_deque_rotate_preserves_elements(items, n):
    """Rotating a deque should preserve all elements"""
    dq = collections.deque(items)
    original = list(dq)
    dq.rotate(n)
    rotated = list(dq)
    
    assert sorted(original) == sorted(rotated)
    assert len(original) == len(rotated)


@given(st.lists(st.integers(), min_size=1))
def test_deque_rotate_cycle(items):
    """Rotating by length should give original order"""
    dq = collections.deque(items)
    original = list(dq)
    dq.rotate(len(items))
    assert list(dq) == original


@given(st.lists(st.integers()), st.lists(st.integers()))
def test_deque_extend_extendleft_asymmetry(items1, items2):
    """extend and extendleft should have different results for non-empty items2"""
    if len(items2) > 1:  # Only test with multiple items
        dq1 = collections.deque(items1)
        dq2 = collections.deque(items1)
        
        dq1.extend(items2)
        dq2.extendleft(items2)
        
        # They should be different unless items2 is empty or has one element
        if len(items2) > 1:
            assert list(dq1) != list(dq2)


@given(st.lists(st.integers(), min_size=1))
def test_deque_appendleft_popleft_inverse(items):
    """appendleft followed by popleft should be identity"""
    dq = collections.deque(items)
    original = list(dq)
    
    test_val = 999999  # Unlikely to be in the list
    dq.appendleft(test_val)
    popped = dq.popleft()
    
    assert popped == test_val
    assert list(dq) == original


@given(st.lists(st.integers()), st.integers(min_value=1, max_value=100))
def test_deque_maxlen_invariant(items, maxlen):
    """deque with maxlen should never exceed that length"""
    dq = collections.deque(items, maxlen=maxlen)
    assert len(dq) <= maxlen
    
    # Add more items
    for i in range(maxlen * 2):
        dq.append(i)
        assert len(dq) <= maxlen


# namedtuple Properties

@given(
    st.text(min_size=1, max_size=10).filter(str.isidentifier),
    st.lists(st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier() and not x.startswith('_')), 
             min_size=1, max_size=5, unique=True)
)
def test_namedtuple_field_access(typename, fields):
    """namedtuple fields should be accessible by name and index"""
    assume(not any(f in ['__new__', '__getnewargs__', '_make', '_asdict', '_replace', '_fields'] for f in fields))
    
    NT = collections.namedtuple(typename, fields)
    values = list(range(len(fields)))
    instance = NT(*values)
    
    # Test access by index and by name
    for i, field in enumerate(fields):
        assert instance[i] == values[i]
        assert getattr(instance, field) == values[i]


@given(
    st.text(min_size=1, max_size=10).filter(str.isidentifier),
    st.lists(st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier() and not x.startswith('_')), 
             min_size=1, max_size=5, unique=True)
)
def test_namedtuple_asdict_round_trip(typename, fields):
    """Converting to dict and back should preserve values"""
    assume(not any(f in ['__new__', '__getnewargs__', '_make', '_asdict', '_replace', '_fields'] for f in fields))
    
    NT = collections.namedtuple(typename, fields)
    values = list(range(len(fields)))
    instance = NT(*values)
    
    # Round trip through dict
    d = instance._asdict()
    instance2 = NT(**d)
    
    assert instance == instance2


@given(
    st.text(min_size=1, max_size=10).filter(str.isidentifier),
    st.lists(st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier() and not x.startswith('_')), 
             min_size=2, max_size=5, unique=True)
)
def test_namedtuple_replace_preserves_others(typename, fields):
    """_replace should only change specified fields"""
    assume(not any(f in ['__new__', '__getnewargs__', '_make', '_asdict', '_replace', '_fields'] for f in fields))
    
    NT = collections.namedtuple(typename, fields)
    values = list(range(len(fields)))
    instance = NT(*values)
    
    # Replace first field
    new_val = 999
    instance2 = instance._replace(**{fields[0]: new_val})
    
    assert getattr(instance2, fields[0]) == new_val
    for field in fields[1:]:
        assert getattr(instance2, field) == getattr(instance, field)


# Edge case tests

@given(st.integers(min_value=-1000, max_value=1000))
def test_counter_unary_operations(n):
    """Test unary + and - on Counter"""
    c = collections.Counter(a=n, b=-n, c=0)
    
    # Unary + should keep only positive
    pos = +c
    assert all(v > 0 for v in pos.values())
    
    # Unary - should negate and keep only positive results
    neg = -c
    assert all(v > 0 for v in neg.values())


@given(st.dictionaries(st.text(min_size=1), st.integers(min_value=-100, max_value=100), min_size=1))
def test_counter_equality_with_zeros(d):
    """Counters should treat missing keys as zero for equality"""
    c1 = collections.Counter(d)
    c2 = collections.Counter(d)
    
    # Add a zero count to c2
    c2['nonexistent_key'] = 0
    
    # Should still be equal
    assert c1 == c2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])