"""Edge case tests for Cython.StringIOTree to find bugs"""

import io
import sys
from hypothesis import given, strategies as st, assume, settings
from Cython.StringIOTree import StringIOTree


@settings(max_examples=500)
@given(st.text(alphabet=st.characters(codec='utf-8')))
def test_unicode_handling(text):
    """Test handling of various Unicode characters"""
    tree = StringIOTree()
    written = tree.write(text)
    assert written == len(text)
    assert tree.getvalue() == text


@given(st.binary())
def test_binary_strings_rejected(data):
    """StringIOTree should only handle text, not binary"""
    tree = StringIOTree()
    if not isinstance(data, str):
        # Should either convert or raise error
        try:
            tree.write(data)
            # If it accepts it, it should be able to get value
            result = tree.getvalue()
            assert isinstance(result, (str, bytes))
        except (TypeError, AttributeError) as e:
            # Expected for binary data
            pass


@given(st.text(alphabet=['\0', '\n', '\r', '\t', '\x00', '\xff']))
def test_special_characters(text):
    """Test handling of null bytes and special characters"""
    tree = StringIOTree()
    written = tree.write(text)
    assert written == len(text)
    result = tree.getvalue()
    assert result == text


@given(st.text())
def test_reset_with_insertion_points(text):
    """Test reset() behavior when insertion points exist"""
    main = StringIOTree()
    main.write("BEFORE")
    insertion = main.insertion_point()
    main.write("AFTER")
    insertion.write(text)
    
    # Reset main tree
    main.reset()
    assert main.getvalue() == ""
    assert main.empty()
    
    # What happens to the insertion point?
    # It might still have its content or might be affected
    insertion_value = insertion.getvalue()
    # Just verify it doesn't crash
    assert isinstance(insertion_value, str)


@given(st.text(), st.text())
def test_insert_after_reset(text1, text2):
    """Test insert() after reset()"""
    tree1 = StringIOTree()
    tree2 = StringIOTree()
    
    tree1.write(text1)
    tree2.write(text2)
    
    tree1.reset()
    tree1.insert(tree2)
    
    assert tree1.getvalue() == text2


@given(st.text())
def test_copyto_with_closed_stream(text):
    """Test copyto() with various stream states"""
    tree = StringIOTree()
    tree.write(text)
    
    # Test with closed stream
    stream = io.StringIO()
    stream.close()
    
    try:
        tree.copyto(stream)
        # If it succeeds, that's unexpected for a closed stream
        assert False, "Should not write to closed stream"
    except (ValueError, IOError) as e:
        # Expected
        pass


@given(st.lists(st.text()))
def test_insertion_point_after_reset(texts):
    """Test creating insertion points after reset"""
    tree = StringIOTree()
    
    for i, text in enumerate(texts):
        tree.write(text)
        if i % 2 == 0:
            tree.reset()
            insertion = tree.insertion_point()
            insertion.write("INSERTED")
    
    # Just check it doesn't crash
    result = tree.getvalue()
    assert isinstance(result, str)


@given(st.text())
def test_double_reset(text):
    """Test calling reset() twice"""
    tree = StringIOTree()
    tree.write(text)
    tree.reset()
    tree.reset()  # Second reset on already empty tree
    assert tree.empty()
    assert tree.getvalue() == ""


@given(st.text())
def test_self_insert(text):
    """Test inserting a tree into itself"""
    tree = StringIOTree()
    tree.write(text)
    
    # Try to insert tree into itself - this could cause infinite recursion
    try:
        tree.insert(tree)
        # If it doesn't crash, check the result
        result = tree.getvalue()
        # The behavior here is interesting - what should happen?
        assert isinstance(result, str)
    except (RuntimeError, RecursionError, ValueError) as e:
        # Might protect against self-insertion
        pass


@given(st.text(min_size=1000, max_size=10000))
def test_large_strings(text):
    """Test with larger strings"""
    tree = StringIOTree()
    written = tree.write(text)
    assert written == len(text)
    assert tree.getvalue() == text
    
    # Test with insertion points on large strings
    mid = len(text) // 2
    tree2 = StringIOTree()
    tree2.write(text[:mid])
    insertion = tree2.insertion_point()
    tree2.write(text[mid:])
    insertion.write("INSERTED")
    
    result = tree2.getvalue()
    assert result == text[:mid] + "INSERTED" + text[mid:]


@given(st.lists(st.text()))
def test_markers_property(texts):
    """Test the markers property"""
    tree = StringIOTree()
    
    for text in texts:
        tree.write(text)
        # Access markers property
        try:
            markers = tree.markers
            # It's a property, let's see what it returns
            if markers is not None:
                # Try to understand what markers are
                pass
        except Exception as e:
            # Might not be readable
            pass
    
    # Also test allmarkers()
    all_markers = tree.allmarkers()
    assert isinstance(all_markers, list)


@given(st.text())
def test_stream_property(text):
    """Test the stream property"""
    tree = StringIOTree()
    tree.write(text)
    
    try:
        stream = tree.stream
        if stream is not None:
            # The stream property exists, what is it?
            assert hasattr(stream, 'write') or hasattr(stream, 'getvalue')
    except Exception:
        # Might not be directly accessible
        pass


@given(st.text())
def test_prepended_children_property(text):
    """Test the prepended_children property"""
    tree = StringIOTree()
    tree.write(text)
    insertion = tree.insertion_point()
    
    try:
        children = tree.prepended_children
        # What type is this?
        if children is not None:
            assert isinstance(children, (list, tuple, dict))
    except Exception:
        pass


@given(st.integers(min_value=0, max_value=100))
def test_multiple_commits(n):
    """Test calling commit() multiple times"""
    tree = StringIOTree()
    
    for i in range(n):
        tree.write(str(i))
        tree.commit()
    
    expected = "".join(str(i) for i in range(n))
    assert tree.getvalue() == expected


@given(st.text(), st.text())
def test_insertion_point_of_insertion_point(text1, text2):
    """Test creating insertion points from insertion points"""
    root = StringIOTree()
    root.write("ROOT")
    
    level1 = root.insertion_point()
    level1.write(text1)
    
    level2 = level1.insertion_point()
    level2.write(text2)
    
    # Verify the nesting works correctly
    assert level2.getvalue() == text2
    assert level1.getvalue() == text1 + text2
    assert root.getvalue() == "ROOT" + text1 + text2