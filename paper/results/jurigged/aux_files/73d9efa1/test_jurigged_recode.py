import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import linecache
from hypothesis import given, strategies as st, settings
import jurigged.recode as recode

# Test 1: virtual_file creates unique filenames
@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=1000)
)
def test_virtual_file_uniqueness(name, contents):
    """Each call to virtual_file should produce a unique filename"""
    filename1 = recode.virtual_file(name, contents)
    filename2 = recode.virtual_file(name, contents)
    
    # Even with same inputs, filenames should be different
    assert filename1 != filename2
    
    # Both should be in the format <name#number>
    assert filename1.startswith(f"<{name}#")
    assert filename2.startswith(f"<{name}#")
    assert filename1.endswith(">")
    assert filename2.endswith(">")

# Test 2: virtual_file caching property
@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=1000)
)
def test_virtual_file_caching(name, contents):
    """Content stored in linecache should match splitlines of input"""
    filename = recode.virtual_file(name, contents)
    
    # Check that file is cached
    assert filename in linecache.cache
    
    # Check cache structure
    cache_entry = linecache.cache[filename]
    assert cache_entry[0] is None  # First element should be None
    assert cache_entry[1] is None  # Second element should be None
    assert cache_entry[3] == filename  # Fourth element should be the filename
    
    # Most importantly, the cached lines should match splitlines
    expected_lines = recode.splitlines(contents)
    cached_lines = cache_entry[2]
    assert cached_lines == expected_lines

# Test 3: splitlines behavior - NOT a round-trip property but specific behavior
@given(st.text(min_size=0, max_size=1000))
def test_splitlines_preserves_line_endings(text):
    """splitlines should preserve line endings in the split strings"""
    lines = recode.splitlines(text)
    
    # splitlines always returns at least one element
    assert len(lines) >= 1
    
    # If text is empty, should return ['']
    if text == '':
        assert lines == ['']
    
    # If there are newlines, they should be preserved in the strings
    if '\n' in text:
        # All lines except possibly the last should end with a line terminator
        for line in lines[:-1]:
            if line:  # Skip empty strings
                assert line.endswith(('\n', '\r\n', '\r'))

# Test 4: Strip idempotence
@given(st.text())
def test_strip_idempotence(text):
    """Stripping should be idempotent - stripping twice equals stripping once"""
    stripped_once = text.strip()
    stripped_twice = stripped_once.strip()
    assert stripped_once == stripped_twice

# Test 5: virtual_file counter property
@given(st.text(min_size=0, max_size=100))
def test_virtual_file_counter_increments(name):
    """The counter in virtual_file should increment monotonically"""
    contents = "test"
    
    filename1 = recode.virtual_file(name, contents)
    filename2 = recode.virtual_file(name, contents)
    
    # Extract numbers from filenames
    import re
    match1 = re.search(r'#(\d+)>', filename1)
    match2 = re.search(r'#(\d+)>', filename2)
    
    assert match1 and match2, "Filenames should contain counter numbers"
    
    num1 = int(match1.group(1))
    num2 = int(match2.group(1))
    
    # Counter should increment
    assert num2 > num1

# Test 6: OutOfSyncException is properly an Exception
def test_out_of_sync_exception():
    """OutOfSyncException should be a proper Exception subclass"""
    exc = recode.OutOfSyncException("test message")
    assert isinstance(exc, Exception)
    assert str(exc) == "test message"
    assert exc.args == ("test message",)

# Test 7: make_recoder with invalid input
@given(st.one_of(
    st.none(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.lists(st.integers())
))
def test_make_recoder_handles_invalid_objects(obj):
    """make_recoder should handle invalid objects gracefully"""
    # make_recoder uses registry.find which might not find arbitrary objects
    result = recode.make_recoder(obj)
    
    # For objects not in registry, it should return a falsy value (likely None or False)
    # Based on the code: return (cf and defn and Recoder(...))
    # If cf or defn is None/False, the whole expression evaluates to that falsy value
    assert result is None or result is False or isinstance(result, recode.Recoder)

# Test 8: virtual_file name escaping
@given(st.text())
def test_virtual_file_name_in_filename(name):
    """The name should appear in the generated filename"""
    contents = "test"
    filename = recode.virtual_file(name, contents)
    
    # Filename format is <name#number>
    assert filename.startswith("<")
    assert filename.endswith(">")
    assert f"{name}#" in filename

if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v"])