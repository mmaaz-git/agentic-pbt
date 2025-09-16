"""
Property-based tests for Cython module components using Hypothesis.
"""
import math
from hypothesis import given, strategies as st, assume
import Cython.Shadow as Shadow
import Cython.StringIOTree as StringIOTree


# Test 1: StringIOTree properties

@given(st.text())
def test_stringiotree_write_getvalue_roundtrip(text):
    """Property: Writing text to StringIOTree and getting value should preserve the text."""
    tree = StringIOTree.StringIOTree()
    tree.write(text)
    assert tree.getvalue() == text


@given(st.lists(st.text(), min_size=1, max_size=10))
def test_stringiotree_concatenation(texts):
    """Property: Writing multiple texts should concatenate them in order."""
    tree = StringIOTree.StringIOTree()
    for text in texts:
        tree.write(text)
    assert tree.getvalue() == ''.join(texts)


@given(st.text(), st.text(), st.text())
def test_stringiotree_insertion_point(before, inserted, after):
    """Property: Insertion points should preserve the order of text."""
    tree = StringIOTree.StringIOTree()
    tree.write(before)
    insertion = tree.insertion_point()
    tree.write(after)
    insertion.write(inserted)
    expected = before + inserted + after
    assert tree.getvalue() == expected


@given(st.text())
def test_stringiotree_reset_makes_empty(text):
    """Property: reset() should make the tree empty."""
    tree = StringIOTree.StringIOTree()
    tree.write(text)
    tree.reset()
    assert tree.empty() == True
    assert tree.getvalue() == ''


@given(st.text())
def test_stringiotree_empty_reflects_content(text):
    """Property: empty() should return True iff getvalue() returns empty string."""
    tree = StringIOTree.StringIOTree()
    assert tree.empty() == (tree.getvalue() == '')
    
    if text:  # Only write non-empty text
        tree.write(text)
        assert tree.empty() == (tree.getvalue() == '')


# Test 2: cdiv/cmod mathematical properties

@given(st.integers(min_value=-10000, max_value=10000),
       st.integers(min_value=-10000, max_value=10000))
def test_cdiv_cmod_relationship(a, b):
    """Property: a = cdiv(a, b) * b + cmod(a, b) (fundamental division property)."""
    assume(b != 0)  # Division by zero is undefined
    
    quotient = Shadow.cdiv(a, b)
    remainder = Shadow.cmod(a, b)
    
    # The fundamental property of division
    assert a == quotient * b + remainder


@given(st.integers(min_value=-10000, max_value=10000),
       st.integers(min_value=1, max_value=10000))
def test_cmod_sign_property(a, b):
    """Property: The sign of cmod(a, b) should match the sign of a (C-style)."""
    remainder = Shadow.cmod(a, b)
    
    if a > 0:
        assert remainder >= 0
    elif a < 0:
        assert remainder <= 0
    else:  # a == 0
        assert remainder == 0


@given(st.integers(min_value=-10000, max_value=10000),
       st.integers(min_value=1, max_value=10000))
def test_cmod_magnitude_bound(a, b):
    """Property: |cmod(a, b)| < |b|."""
    remainder = Shadow.cmod(a, b)
    assert abs(remainder) < abs(b)


@given(st.integers(min_value=-10000, max_value=10000),
       st.integers(min_value=-10000, max_value=10000))
def test_cdiv_truncates_toward_zero(a, b):
    """Property: cdiv truncates toward zero (unlike Python's //)."""
    assume(b != 0)
    
    quotient = Shadow.cdiv(a, b)
    exact_division = a / b
    
    # cdiv should truncate toward zero
    if exact_division >= 0:
        assert quotient == int(exact_division)  # Truncate positive toward zero
    else:
        assert quotient == int(exact_division) if exact_division == int(exact_division) else int(exact_division) + 1


# Test 3: typeof properties

@given(st.integers())
def test_typeof_integer(value):
    """Property: typeof should return the correct Python type for integers."""
    assert Shadow.typeof(value) == int


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_typeof_float(value):
    """Property: typeof should return the correct Python type for floats."""
    assert Shadow.typeof(value) == float


@given(st.text())
def test_typeof_string(value):
    """Property: typeof should return the correct Python type for strings."""
    assert Shadow.typeof(value) == str


@given(st.lists(st.integers()))
def test_typeof_list(value):
    """Property: typeof should return the correct Python type for lists."""
    assert Shadow.typeof(value) == list


@given(st.dictionaries(st.text(), st.integers()))
def test_typeof_dict(value):
    """Property: typeof should return the correct Python type for dictionaries."""
    assert Shadow.typeof(value) == dict


# Test 4: Additional StringIOTree properties

@given(st.lists(st.text(), min_size=2, max_size=5))
def test_stringiotree_multiple_insertion_points(texts):
    """Property: Multiple insertion points should work correctly."""
    assume(len(texts) >= 3)  # Need at least 3 texts
    
    tree = StringIOTree.StringIOTree()
    tree.write(texts[0])
    
    insertion1 = tree.insertion_point()
    tree.write(texts[1])
    
    insertion2 = tree.insertion_point()
    tree.write(texts[2])
    
    # Write to insertion points
    if len(texts) > 3:
        insertion1.write(texts[3])
    if len(texts) > 4:
        insertion2.write(texts[4])
    
    # Build expected result
    expected = texts[0]
    if len(texts) > 3:
        expected += texts[3]
    expected += texts[1]
    if len(texts) > 4:
        expected += texts[4]
    expected += texts[2]
    
    assert tree.getvalue() == expected


@given(st.text(), st.text())
def test_stringiotree_insert_method(text1, text2):
    """Property: insert() method should insert another StringIOTree at current position."""
    tree1 = StringIOTree.StringIOTree()
    tree1.write(text1)
    
    tree2 = StringIOTree.StringIOTree()
    tree2.write(text2)
    
    tree1.insert(tree2)
    
    # tree2 should be inserted at the end of tree1
    assert tree1.getvalue() == text1 + text2