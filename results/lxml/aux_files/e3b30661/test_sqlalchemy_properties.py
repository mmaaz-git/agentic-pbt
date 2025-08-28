import math
import re
from hypothesis import assume, given, strategies as st, settings
import pytest
from sqlalchemy.engine.url import make_url, URL
from sqlalchemy.util import OrderedSet
from sqlalchemy import text, and_, or_, not_
from sqlalchemy.sql import operators
from sqlalchemy.types import Boolean, Integer, String, JSON


@given(
    drivername=st.text(min_size=1, max_size=50).filter(lambda x: not any(c in x for c in ':/\\@#?=')),
    username=st.one_of(st.none(), st.text(min_size=1, max_size=50).filter(lambda x: ':' not in x and '@' not in x)),
    password=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
    host=st.one_of(st.none(), st.text(min_size=1, max_size=50).filter(lambda x: not any(c in x for c in ':/\\@#?='))),
    port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
    database=st.one_of(st.none(), st.text(min_size=1, max_size=50).filter(lambda x: not any(c in x for c in '?#')))
)
def test_url_create_render_roundtrip(drivername, username, password, host, port, database):
    """Test that URL.create and render_as_string maintain data integrity"""
    url = URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database
    )
    
    # Check that attributes are preserved
    assert url.drivername == drivername
    assert url.username == username
    assert url.password == password
    assert url.host == host
    assert url.port == port
    assert url.database == database
    
    # Test that rendering and parsing maintains the URL
    if username is not None or host is not None:
        url_string = url.render_as_string(hide_password=False)
        parsed = make_url(url_string)
        
        assert parsed.drivername == drivername
        assert parsed.username == username
        assert parsed.password == password
        assert parsed.host == host
        assert parsed.port == port
        assert parsed.database == database


@given(
    elements=st.lists(st.integers(), min_size=0, max_size=100)
)
def test_ordered_set_invariants(elements):
    """Test OrderedSet maintains set properties while preserving order"""
    ordered_set = OrderedSet(elements)
    
    # Set property: no duplicates
    assert len(ordered_set) <= len(elements)
    assert len(ordered_set) == len(set(elements))
    
    # Order property: first occurrence order is preserved
    seen = set()
    expected_order = []
    for elem in elements:
        if elem not in seen:
            expected_order.append(elem)
            seen.add(elem)
    
    assert list(ordered_set) == expected_order
    
    # Set operations maintain cardinality invariants
    copy_set = ordered_set.copy()
    assert len(copy_set) == len(ordered_set)
    assert list(copy_set) == list(ordered_set)


@given(
    elements1=st.lists(st.integers(), min_size=0, max_size=50),
    elements2=st.lists(st.integers(), min_size=0, max_size=50)
)
def test_ordered_set_operations(elements1, elements2):
    """Test OrderedSet set operations maintain mathematical properties"""
    set1 = OrderedSet(elements1)
    set2 = OrderedSet(elements2)
    
    # Union cardinality
    union = set1 | set2
    assert len(union) <= len(set1) + len(set2)
    assert len(union) >= max(len(set1), len(set2))
    
    # Intersection cardinality
    intersection = set1 & set2
    assert len(intersection) <= min(len(set1), len(set2))
    assert all(elem in set1 for elem in intersection)
    assert all(elem in set2 for elem in intersection)
    
    # Difference cardinality
    diff = set1 - set2
    assert len(diff) <= len(set1)
    assert all(elem in set1 for elem in diff)
    assert all(elem not in set2 for elem in diff)
    
    # Symmetric difference
    sym_diff = set1.symmetric_difference(set2)
    assert len(sym_diff) == len((set1 - set2) | (set2 - set1))


@given(
    sql=st.text(min_size=1, max_size=1000)
)
def test_text_clause_preserves_sql(sql):
    """Test that text() preserves the SQL string exactly"""
    clause = text(sql)
    # The text should be preserved exactly
    assert str(clause) == sql


@given(
    elements=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=20)
)
def test_ordered_set_add_remove_invariants(elements):
    """Test add/remove operations on OrderedSet"""
    ordered_set = OrderedSet()
    
    for elem in elements:
        size_before = len(ordered_set)
        ordered_set.add(elem)
        size_after = len(ordered_set)
        
        # Adding an element increases size by at most 1
        assert size_after - size_before in [0, 1]
        
        # Element is now in the set
        assert elem in ordered_set
    
    # Remove all elements
    for elem in set(elements):
        if elem in ordered_set:
            size_before = len(ordered_set)
            ordered_set.remove(elem)
            size_after = len(ordered_set)
            
            # Removing decreases size by exactly 1
            assert size_before - size_after == 1
            
            # Element is no longer in set
            assert elem not in ordered_set


@given(
    sql_parts=st.lists(
        st.text(min_size=1, max_size=100).filter(lambda x: '\0' not in x),
        min_size=2,
        max_size=10
    )
)
def test_and_or_clause_combination(sql_parts):
    """Test that and_/or_ clause builders handle multiple clauses correctly"""
    clauses = [text(part) for part in sql_parts]
    
    # Test and_ combination
    and_clause = and_(*clauses)
    assert and_clause is not None
    
    # Test or_ combination
    or_clause = or_(*clauses)
    assert or_clause is not None
    
    # Test not_ on a single clause
    if clauses:
        not_clause = not_(clauses[0])
        assert not_clause is not None


@given(
    elements=st.lists(st.integers(), min_size=0, max_size=50),
    insert_positions=st.lists(st.integers(min_value=0, max_value=100), min_size=0, max_size=20)
)
def test_ordered_set_insert_method(elements, insert_positions):
    """Test OrderedSet.insert() method maintains order correctly"""
    ordered_set = OrderedSet()
    
    for i, elem in enumerate(elements):
        if i < len(insert_positions):
            pos = insert_positions[i] % (len(ordered_set) + 1)
            ordered_set.insert(pos, elem)
        else:
            ordered_set.add(elem)
    
    # Check no duplicates
    assert len(ordered_set) == len(set(ordered_set))
    
    # Check all elements are present
    for elem in set(elements):
        assert elem in ordered_set


@given(
    valid_drivers=st.sampled_from(['postgresql', 'mysql', 'sqlite', 'oracle', 'mssql']),
    username=st.text(min_size=1, max_size=30).filter(lambda x: not any(c in x for c in ':@/')),
    password=st.text(min_size=0, max_size=30),
    host=st.text(min_size=1, max_size=50).filter(lambda x: not any(c in x for c in ':@/')),
    port=st.integers(min_value=1, max_value=65535),
    database=st.text(min_size=1, max_size=30).filter(lambda x: '/' not in x)
)
def test_url_parsing_roundtrip(valid_drivers, username, password, host, port, database):
    """Test make_url parsing and URL rendering round-trip"""
    # Build URL string manually
    if password:
        url_str = f"{valid_drivers}://{username}:{password}@{host}:{port}/{database}"
    else:
        url_str = f"{valid_drivers}://{username}@{host}:{port}/{database}"
    
    # Parse it
    parsed = make_url(url_str)
    
    # Check components
    assert parsed.drivername == valid_drivers
    assert parsed.username == username
    assert parsed.password == password if password else None
    assert parsed.host == host
    assert parsed.port == port
    assert parsed.database == database
    
    # Round-trip through string
    rendered = parsed.render_as_string(hide_password=False)
    reparsed = make_url(rendered)
    
    assert reparsed.drivername == valid_drivers
    assert reparsed.username == username
    assert reparsed.password == password if password else None
    assert reparsed.host == host
    assert reparsed.port == port
    assert reparsed.database == database


@given(
    elements=st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=100)
)
def test_ordered_set_pop_lifo(elements):
    """Test that OrderedSet.pop() follows LIFO order"""
    ordered_set = OrderedSet(elements)
    original_length = len(ordered_set)
    
    # Pop should remove and return the last element
    if original_length > 0:
        last_elem = list(ordered_set)[-1]
        popped = ordered_set.pop()
        
        assert popped == last_elem
        assert len(ordered_set) == original_length - 1
        assert popped not in ordered_set


@given(
    set1_elements=st.lists(st.integers(), min_size=0, max_size=50),
    set2_elements=st.lists(st.integers(), min_size=0, max_size=50)
)
def test_ordered_set_subset_superset_relations(set1_elements, set2_elements):
    """Test subset/superset relations are consistent"""
    set1 = OrderedSet(set1_elements)
    set2 = OrderedSet(set2_elements)
    
    # A set is always a subset and superset of itself
    assert set1.issubset(set1)
    assert set1.issuperset(set1)
    
    # If A is subset of B, then B is superset of A
    if set1.issubset(set2):
        assert set2.issuperset(set1)
    
    if set2.issubset(set1):
        assert set1.issuperset(set2)
    
    # Empty set is subset of any set
    empty = OrderedSet()
    assert empty.issubset(set1)
    assert empty.issubset(set2)
    
    # Any set is superset of empty set
    assert set1.issuperset(empty)
    assert set2.issuperset(empty)