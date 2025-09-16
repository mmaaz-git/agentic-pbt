"""Property-based tests for Cython.StringIOTree"""

import io
from hypothesis import given, strategies as st, assume, settings
from Cython.StringIOTree import StringIOTree

# Use more examples for thorough testing
test_settings = settings(max_examples=500)


@given(st.text())
def test_write_returns_length(text):
    """write() should return the number of characters written"""
    tree = StringIOTree()
    result = tree.write(text)
    assert result == len(text)
    assert tree.getvalue() == text


@given(st.text())
def test_empty_property(text):
    """empty() should return True iff getvalue() is empty string"""
    tree = StringIOTree()
    assert tree.empty() == (tree.getvalue() == "")
    
    if text:
        tree.write(text)
        assert tree.empty() == (tree.getvalue() == "")
    else:
        assert tree.empty()


@given(st.lists(st.text()))
def test_multiple_writes_concatenate(texts):
    """Multiple writes should concatenate in order"""
    tree = StringIOTree()
    expected = ""
    for text in texts:
        result = tree.write(text)
        assert result == len(text)
        expected += text
    assert tree.getvalue() == expected


@given(st.text(), st.text(), st.text())
def test_insertion_point_ordering(text1, text2, text3):
    """Insertion points should maintain documented order: before->insertion->after"""
    tree = StringIOTree()
    tree.write(text1)
    insertion = tree.insertion_point()
    tree.write(text3)
    insertion.write(text2)
    assert tree.getvalue() == text1 + text2 + text3


@settings(max_examples=500)
@given(st.lists(st.tuples(st.text(), st.integers(min_value=0, max_value=10))))
def test_nested_insertion_points(writes):
    """Test complex nested insertion point scenarios"""
    if not writes:
        return
    
    tree = StringIOTree()
    insertions = [tree]
    results = []
    
    for text, parent_idx in writes:
        parent_idx = parent_idx % len(insertions)
        parent = insertions[parent_idx]
        
        if text:
            parent.write(text[:len(text)//2])
            new_insertion = parent.insertion_point()
            parent.write(text[len(text)//2:])
            insertions.append(new_insertion)
    
    # Just verify it doesn't crash and produces some result
    result = tree.getvalue()
    assert isinstance(result, str)


@given(st.text())
def test_copyto_equals_getvalue(text):
    """copyto() should produce same content as getvalue()"""
    tree = StringIOTree()
    tree.write(text)
    
    buffer = io.StringIO()
    tree.copyto(buffer)
    assert buffer.getvalue() == tree.getvalue()


@given(st.text(), st.text())
def test_reset_makes_empty(text1, text2):
    """reset() should make the tree empty"""
    tree = StringIOTree()
    tree.write(text1)
    assert tree.getvalue() == text1
    
    tree.reset()
    assert tree.empty()
    assert tree.getvalue() == ""
    
    # Should be able to write after reset
    tree.write(text2)
    assert tree.getvalue() == text2


@given(st.text(), st.text())
def test_insert_method(text1, text2):
    """insert() should place another tree's contents at current position"""
    tree1 = StringIOTree()
    tree2 = StringIOTree()
    
    tree1.write(text1[:len(text1)//2])
    tree2.write(text2)
    tree1.insert(tree2)
    tree1.write(text1[len(text1)//2:])
    
    expected = text1[:len(text1)//2] + text2 + text1[len(text1)//2:]
    assert tree1.getvalue() == expected


@given(st.text())
def test_insertion_point_isolation(text):
    """Insertion point's getvalue() should only return its own content"""
    main = StringIOTree()
    main.write("BEFORE")
    insertion = main.insertion_point()
    main.write("AFTER")
    insertion.write(text)
    
    # Insertion point should only show its own content
    assert insertion.getvalue() == text
    # Main tree should show everything
    assert main.getvalue() == "BEFORE" + text + "AFTER"


@given(st.lists(st.text()), st.integers(min_value=0, max_value=100))
def test_complex_insertion_scenario(texts, seed):
    """Test a complex scenario with multiple insertion points"""
    if not texts:
        return
        
    import random
    random.seed(seed)
    
    root = StringIOTree()
    trees = [root]
    expected_positions = {root: 0}
    content_parts = []
    
    for text in texts:
        # Pick a random tree to write to
        tree = random.choice(trees)
        tree.write(text)
        
        # Sometimes create an insertion point
        if random.random() < 0.5:
            new_tree = tree.insertion_point()
            trees.append(new_tree)
    
    # Just verify it doesn't crash
    result = root.getvalue()
    assert isinstance(result, str)


@given(st.text())
def test_allmarkers_returns_list(text):
    """allmarkers() should return a list"""
    tree = StringIOTree()
    tree.write(text)
    markers = tree.allmarkers()
    assert isinstance(markers, list)


@given(st.lists(st.text(min_size=1)))
def test_multiple_insertions_same_point(texts):
    """Multiple insertion points at the same location should work correctly"""
    if not texts or len(texts) < 3:
        return
        
    root = StringIOTree()
    root.write(texts[0])
    
    # Create insertion points for middle texts
    insertions = []
    for i in range(1, len(texts) - 1):
        insertions.append(root.insertion_point())
    
    root.write(texts[-1])
    
    # Write to insertion points in order
    for i, insertion in enumerate(insertions):
        insertion.write(texts[i + 1])
    
    # Verify the order is maintained
    result = root.getvalue()
    expected = texts[0] + "".join(texts[1:-1]) + texts[-1]
    assert result == expected


@given(st.text())
def test_write_empty_string(text):
    """Writing empty string should work and return 0"""
    tree = StringIOTree()
    tree.write(text)
    result = tree.write("")
    assert result == 0
    assert tree.getvalue() == text


@given(st.lists(st.text()))
def test_commit_method(texts):
    """Test that commit() doesn't crash and tree still works after"""
    tree = StringIOTree()
    for text in texts:
        tree.write(text)
        tree.commit()
    
    expected = "".join(texts)
    assert tree.getvalue() == expected