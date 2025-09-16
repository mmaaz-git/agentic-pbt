import math
import random
from hypothesis import assume, given, strategies as st, settings
import pytest
from sqlalchemy.ext.mutable import MutableList, MutableDict, MutableSet
from sqlalchemy.ext.orderinglist import OrderingList, ordering_list, count_from_0


# MutableList tests
@given(st.lists(st.integers()))
def test_mutablelist_append_pop_roundtrip(items):
    """Test that MutableList maintains list semantics for append/pop operations"""
    mlist = MutableList(items.copy())
    original = items.copy()
    
    # Append then pop should return to original
    if len(items) > 0:
        value = 42
        mlist.append(value)
        assert len(mlist) == len(original) + 1
        assert mlist[-1] == value
        popped = mlist.pop()
        assert popped == value
        assert list(mlist) == original


@given(st.lists(st.integers()))
def test_mutablelist_extend_maintains_order(items):
    """Test that extend maintains the order of elements"""
    mlist = MutableList()
    mlist.extend(items)
    assert list(mlist) == items
    
    # Double extend should concatenate
    mlist2 = MutableList()
    mlist2.extend(items)
    mlist2.extend(items)
    assert list(mlist2) == items + items


@given(st.lists(st.integers(), min_size=1))
def test_mutablelist_reverse_twice_identity(items):
    """Test that reversing twice returns to original"""
    mlist = MutableList(items.copy())
    original = items.copy()
    mlist.reverse()
    mlist.reverse()
    assert list(mlist) == original


@given(st.lists(st.integers()))
def test_mutablelist_clear_empties_list(items):
    """Test that clear() empties the list"""
    mlist = MutableList(items)
    mlist.clear()
    assert len(mlist) == 0
    assert list(mlist) == []


# MutableDict tests
@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_mutabledict_setitem_getitem_consistency(items):
    """Test that MutableDict maintains dict semantics"""
    mdict = MutableDict(items)
    
    # All items should be retrievable
    for key, value in items.items():
        assert mdict[key] == value
        assert mdict.get(key) == value
    
    # Setting and getting should be consistent
    if items:
        key = list(items.keys())[0]
        new_value = 999
        mdict[key] = new_value
        assert mdict[key] == new_value


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_mutabledict_pop_removes_key(items):
    """Test that pop removes the key and returns the value"""
    assume(len(items) > 0)
    mdict = MutableDict(items.copy())
    
    key = list(items.keys())[0]
    value = items[key]
    
    popped = mdict.pop(key)
    assert popped == value
    assert key not in mdict
    
    # Pop with default for non-existent key
    default = -999
    assert mdict.pop("nonexistent_key", default) == default


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_mutabledict_clear_empties_dict(items):
    """Test that clear() empties the dict"""
    mdict = MutableDict(items)
    mdict.clear()
    assert len(mdict) == 0
    assert dict(mdict) == {}


@given(st.dictionaries(st.text(min_size=1), st.integers()))
def test_mutabledict_copy_independence(items):
    """Test that copy creates independent dict"""
    mdict1 = MutableDict(items)
    mdict2 = mdict1.copy()
    
    # They should be equal but not the same object
    assert dict(mdict1) == dict(mdict2)
    assert mdict1 is not mdict2
    
    # Modifying one shouldn't affect the other
    if items:
        key = list(items.keys())[0]
        mdict1[key] = -999
        assert mdict1[key] != mdict2[key]


# MutableSet tests
@given(st.sets(st.integers()))
def test_mutableset_add_remove_invariants(items):
    """Test that MutableSet maintains set semantics"""
    mset = MutableSet(items)
    
    # Adding existing element shouldn't change size
    if items:
        elem = list(items)[0]
        original_len = len(mset)
        mset.add(elem)
        assert len(mset) == original_len
        assert elem in mset
    
    # Adding new element should increase size
    new_elem = max(items) + 1 if items else 0
    original_len = len(mset)
    mset.add(new_elem)
    assert len(mset) == original_len + 1
    assert new_elem in mset
    
    # Removing element should decrease size
    mset.remove(new_elem)
    assert len(mset) == original_len
    assert new_elem not in mset


@given(st.sets(st.integers()), st.sets(st.integers()))
def test_mutableset_union_commutativity(set1, set2):
    """Test that union is commutative"""
    mset1 = MutableSet(set1)
    mset2 = MutableSet(set2)
    
    union1 = mset1.union(mset2)
    union2 = mset2.union(mset1)
    
    assert union1 == union2


@given(st.sets(st.integers()), st.sets(st.integers()))
def test_mutableset_intersection_commutativity(set1, set2):
    """Test that intersection is commutative"""
    mset1 = MutableSet(set1)
    mset2 = MutableSet(set2)
    
    inter1 = mset1.intersection(mset2)
    inter2 = mset2.intersection(mset1)
    
    assert inter1 == inter2


@given(st.sets(st.integers()))
def test_mutableset_clear_empties_set(items):
    """Test that clear() empties the set"""
    mset = MutableSet(items)
    mset.clear()
    assert len(mset) == 0
    assert set(mset) == set()


# OrderingList tests
@given(st.lists(st.integers(), min_size=1, max_size=20))
def test_orderinglist_maintains_position_attribute(items):
    """Test that OrderingList maintains position attributes correctly"""
    # Create mock objects with position attribute
    class Item:
        def __init__(self, value):
            self.value = value
            self.position = None
    
    # Create items
    objects = [Item(v) for v in items]
    
    # Create ordering list with position attribute
    olist = OrderingList('position', count_from_0)
    olist.extend(objects)
    
    # Check that positions are set correctly
    for i, obj in enumerate(olist):
        assert obj.position == i


@given(st.lists(st.integers(), min_size=2, max_size=20))
def test_orderinglist_reorder_on_append(items):
    """Test that OrderingList with reorder_on_append maintains order"""
    class Item:
        def __init__(self, value):
            self.value = value
            self.position = None
        def __repr__(self):
            return f"Item({self.value}, pos={self.position})"
    
    objects = [Item(v) for v in items]
    
    # Create ordering list with reorder_on_append
    olist = OrderingList('position', count_from_0, reorder_on_append=True)
    
    # Add items one by one
    for obj in objects:
        olist.append(obj)
    
    # Positions should be consecutive
    for i, obj in enumerate(olist):
        assert obj.position == i


@given(st.lists(st.integers(), min_size=3, max_size=20))
def test_orderinglist_insert_updates_positions(items):
    """Test that inserting into OrderingList updates positions correctly"""
    class Item:
        def __init__(self, value):
            self.value = value
            self.position = None
    
    objects = [Item(v) for v in items]
    
    olist = OrderingList('position', count_from_0)
    olist.extend(objects[:-1])
    
    # Insert at position 1
    new_item = objects[-1]
    olist.insert(1, new_item)
    
    # Check all positions are still consecutive
    for i, obj in enumerate(olist):
        assert obj.position == i


@given(st.lists(st.integers(), min_size=2, max_size=20))
def test_orderinglist_pop_updates_positions(items):
    """Test that popping from OrderingList updates positions correctly"""
    class Item:
        def __init__(self, value):
            self.value = value
            self.position = None
    
    objects = [Item(v) for v in items]
    
    olist = OrderingList('position', count_from_0)
    olist.extend(objects)
    
    # Pop middle element if possible
    if len(olist) > 2:
        olist.pop(1)
    else:
        olist.pop()
    
    # Check all positions are still consecutive
    for i, obj in enumerate(olist):
        assert obj.position == i