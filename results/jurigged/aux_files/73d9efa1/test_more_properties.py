import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import linecache
from hypothesis import given, strategies as st, settings, assume
import jurigged.recode as recode
import re

# Test for potential race conditions or edge cases with virtual_file

# Test 1: virtual_file with special characters in name
@given(st.text())
def test_virtual_file_special_chars_in_name(name):
    """virtual_file should handle any characters in the name"""
    contents = "test content"
    filename = recode.virtual_file(name, contents)
    
    # Should always produce a valid filename format
    assert filename.startswith("<")
    assert filename.endswith(">")
    
    # The name should be preserved exactly in the filename
    # Extract the name part before the #
    match = re.match(r'^<(.*)#\d+>$', filename)
    assert match is not None
    extracted_name = match.group(1)
    assert extracted_name == name

# Test 2: Check for potential overflow in counter
def test_virtual_file_counter_large_numbers():
    """Test that the counter doesn't have issues with large numbers of calls"""
    # Create many virtual files to stress test the counter
    filenames = set()
    for i in range(1000):
        filename = recode.virtual_file(f"test{i}", f"content{i}")
        filenames.add(filename)
    
    # All filenames should be unique
    assert len(filenames) == 1000

# Test 3: virtual_file with empty name
@given(st.just(""))
def test_virtual_file_empty_name(name):
    """virtual_file should handle empty names"""
    contents = "test"
    filename = recode.virtual_file(name, contents)
    
    # Should produce filename like <#number>
    assert re.match(r'^<#\d+>$', filename)

# Test 4: Check linecache pollution
@given(st.text(min_size=0, max_size=100), st.text())
def test_virtual_file_linecache_isolation(name1, contents1):
    """Each virtual file should have its own cache entry without affecting others"""
    # Create first file
    filename1 = recode.virtual_file(name1, contents1)
    cache1 = linecache.cache[filename1]
    
    # Create second file with same name but different content
    contents2 = contents1 + " modified"
    filename2 = recode.virtual_file(name1, contents2)
    cache2 = linecache.cache[filename2]
    
    # Both should exist in cache
    assert filename1 in linecache.cache
    assert filename2 in linecache.cache
    
    # They should have different cached contents
    assert cache1[2] == recode.splitlines(contents1)
    assert cache2[2] == recode.splitlines(contents2)
    
    # First file's cache should not be modified
    assert linecache.cache[filename1][2] == recode.splitlines(contents1)

# Test 5: Test with Unicode and special characters
@given(st.text(alphabet=st.characters(min_codepoint=0x1F300, max_codepoint=0x1F6FF)))
def test_virtual_file_unicode(name):
    """virtual_file should handle Unicode characters including emojis"""
    contents = "def test(): pass"
    filename = recode.virtual_file(name, contents)
    
    # Should create valid filename
    assert filename.startswith("<")
    assert filename.endswith(">")
    
    # Cache should work correctly
    assert filename in linecache.cache
    assert linecache.cache[filename][2] == recode.splitlines(contents)

# Test 6: Check for filename injection vulnerabilities
@given(st.text())
def test_virtual_file_no_injection(name):
    """Names with special characters shouldn't break the filename format"""
    # Try names that might break the format
    evil_names = [
        name,
        name + ">",
        "<" + name,
        name + "#999>",
        "#" + name,
    ]
    
    for evil_name in evil_names:
        filename = recode.virtual_file(evil_name, "content")
        
        # Should always maintain the <name#number> format
        assert filename.startswith("<")
        assert filename.endswith(">")
        assert filename.count("<") == 1
        assert filename.count(">") == 1
        
        # Should have exactly one # followed by digits before the >
        match = re.search(r'#(\d+)>$', filename)
        assert match is not None

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])