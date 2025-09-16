#!/usr/bin/env python3
"""Focused bug hunting tests for isort.wrap module"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

from hypothesis import given, strategies as st, settings, assume
from isort import wrap
from isort.settings import Config

# Test 1: Content with existing newlines
@given(
    prefix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=50),
    suffix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=50),
    line_length=st.integers(min_value=10, max_value=100),
)
@settings(max_examples=1000)
def test_content_with_embedded_newlines(prefix, suffix, line_length):
    """Test how the function handles content that already contains newlines."""
    
    # Create content with embedded newline
    content = prefix + '\n' + suffix
    
    config = Config(line_length=line_length)
    
    # The line() function is supposed to wrap single lines
    # What happens when content already has newlines?
    result = wrap.line(content, "\n", config)
    
    assert isinstance(result, str)
    
    # This might reveal unexpected behavior
    # The function seems to return content as-is when it has newlines
    print(f"Input with newline: {repr(content[:50])}")
    print(f"Result: {repr(result[:50])}")


# Test 2: Testing split behavior with special regex characters
@given(
    prefix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=20),
    suffix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=20),
)
@settings(max_examples=1000)
def test_regex_special_chars_in_splitter(prefix, suffix):
    """Test if regex special characters in content cause issues."""
    
    # The code uses re.escape but let's test edge cases
    # Add content that looks like the splitters but isn't
    content = prefix + "import" + suffix  # Not "import " with space
    
    config = Config(line_length=20, use_parentheses=True)
    
    result = wrap.line(content, "\n", config)
    assert isinstance(result, str)
    
    # The regex looks for \bimport \b (word boundaries)
    # So "import" without space shouldn't trigger splitting
    

# Test 3: Testing minimum_length calculation edge case
@given(
    imports_count=st.integers(min_value=2, max_value=5),
    import_length=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=500)
def test_minimum_length_calculation(imports_count, import_length):
    """Test the minimum_length calculation in balanced wrapping."""
    
    # Create imports of specific length
    from_imports = [f"{'a' * import_length}{i}" for i in range(imports_count)]
    
    config = Config(
        line_length=50,
        balanced_wrapping=True,
        use_parentheses=True,
    )
    
    import_start = "from module import "
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports.copy(),
        config=config
    )
    
    assert isinstance(result, str)
    
    # Check the balanced wrapping logic
    lines = result.split('\n')
    if len(lines) > 1:
        # According to the code, it calculates minimum_length from lines[:-1]
        # This excludes the last line
        line_lengths = [len(line) for line in lines[:-1]]
        if line_lengths:
            min_length = min(line_lengths)
            # The algorithm tries to balance so last line isn't too short
            # But there's a potential issue if lines list is exactly 1 element
            

# Test 4: Testing the pop() operations on empty lists
@given(
    explode=st.booleans(),
)
@settings(max_examples=500)
def test_empty_from_imports_edge_case(explode):
    """Specifically test empty from_imports list."""
    
    config = Config(line_length=50)
    import_start = "from module import "
    
    # Empty list - the code does from_imports.pop(0)
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=[],  # Empty!
        config=config,
        explode=explode
    )
    
    assert isinstance(result, str)
    # Should handle empty list gracefully
    

# Test 5: Line without comment but with # in middle
@given(
    prefix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=10, max_size=30),
    middle=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=20),
    suffix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=20),
)
@settings(max_examples=500)
def test_hash_in_middle_of_content(prefix, middle, suffix):
    """Test content with # that's not a comment."""
    
    # Create content with # in the middle (not a comment)
    content = f"{prefix}#{middle}#{suffix}"
    
    config = Config(line_length=30, use_parentheses=True)
    
    result = wrap.line(content, "\n", config)
    
    assert isinstance(result, str)
    
    # The code splits on "#" to find comments
    # With multiple #, it might behave unexpectedly
    parts = content.split("#", 1)
    # The code assumes the second part is a comment
    

# Test 6: Testing line_parts pop with empty list
@given(
    content_length=st.integers(min_value=100, max_value=200),
)
@settings(max_examples=500)
def test_line_parts_exhaustion(content_length):
    """Test when line_parts list gets exhausted in the while loop."""
    
    # Create very long content with a splitter
    content = "a" * content_length + " import " + "b" * 10
    
    config = Config(
        line_length=10,  # Very small to force many pops
        wrap_length=8,   # Even smaller
        use_parentheses=False,
    )
    
    result = wrap.line(content, "\n", config)
    
    assert isinstance(result, str)
    
    # The while loop pops from line_parts until content fits
    # Edge case: what if all parts are popped?
    

# Test 7: Testing with only whitespace between parts
@given(
    num_spaces=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=500)
def test_whitespace_only_parts(num_spaces):
    """Test with parts that are only whitespace."""
    
    # Create content with varying whitespace
    content = "from" + " " * num_spaces + "import" + " " * num_spaces + "something"
    
    config = Config(line_length=20, use_parentheses=True)
    
    result = wrap.line(content, "\n", config)
    
    assert isinstance(result, str)
    

# Test 8: Searching for actual bugs - comment edge case
@given(
    base=st.text(alphabet='abcdefghijklmnopqrstuvwxyz. ', min_size=50, max_size=100),
)
@settings(max_examples=1000)
def test_comment_split_bug(base):
    """Look for bugs in comment splitting logic."""
    
    # Add multiple # symbols
    content = base[:20] + " # comment1 # comment2"
    
    config = Config(
        line_length=30,
        use_parentheses=True,
        include_trailing_comma=True,
    )
    
    result = wrap.line(content, "\n", config)
    
    assert isinstance(result, str)
    
    # With multiple #, the split might not work as expected
    # line 78: line_without_comment, comment = content.split("#", 1)
    # This takes everything after first # as comment
    

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=long", "-s"])