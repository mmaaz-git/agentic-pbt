"""Property-based tests for Cython.TestUtils"""

import os
import tempfile
import time
from hypothesis import given, strategies as st, assume, settings
import Cython.TestUtils


# Test 1: strip_common_indent properties
@given(st.lists(st.text(alphabet=' \t', min_size=0, max_size=20)))
def test_strip_common_indent_empty_lines_removed(indents):
    """Empty lines should be completely removed"""
    # Create lines with just whitespace
    lines = [indent for indent in indents]
    result = Cython.TestUtils.strip_common_indent(lines)
    # All empty/whitespace-only lines should be removed
    for line in result:
        assert line.strip() != "", f"Empty line not removed: repr={repr(line)}"


@given(
    common_indent=st.text(alphabet=' \t', min_size=1, max_size=10),
    suffixes=st.lists(st.text(min_size=1), min_size=1, max_size=10)
)
def test_strip_common_indent_removes_common_prefix(common_indent, suffixes):
    """Common indentation should be completely removed"""
    # Create lines with common indentation
    lines = [common_indent + suffix for suffix in suffixes]
    result = Cython.TestUtils.strip_common_indent(lines)
    
    # The common indent should be gone
    for i, line in enumerate(result):
        assert not line.startswith(common_indent) or suffixes[i].startswith(common_indent), \
            f"Common indent not fully removed: {repr(line)}"


@given(
    indents=st.lists(
        st.integers(min_value=0, max_value=20),
        min_size=1,
        max_size=10
    ),
    content=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10)
)
def test_strip_common_indent_preserves_relative_indentation(indents, content):
    """Relative indentation between lines should be preserved"""
    # Create lines with different indentation levels
    lines = [' ' * indent + content for indent in indents]
    
    # Filter out empty content lines as strip_common_indent would
    non_empty_lines = [line for line in lines if line.strip()]
    if not non_empty_lines:
        return  # No testable content
    
    result = Cython.TestUtils.strip_common_indent(lines)
    
    if len(result) >= 2:
        # Check relative indentation is preserved
        for i in range(1, len(result)):
            original_diff = len(lines[i]) - len(lines[i].lstrip()) - (len(lines[0]) - len(lines[0].lstrip()))
            result_diff = len(result[i]) - len(result[i].lstrip()) - (len(result[0]) - len(result[0].lstrip()))
            # The difference in indentation should be preserved
            assert abs(original_diff - result_diff) <= len(lines[0]) - len(lines[0].lstrip()), \
                f"Relative indentation not preserved"


# Test 2: write_file round-trip property
@given(
    content=st.text(min_size=0, max_size=1000),
    dedent=st.booleans()
)
@settings(max_examples=100)
def test_write_file_round_trip_text(content, dedent):
    """What we write should be what we read back (for text)"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        temp_path = f.name
    
    try:
        # Apply dedent if needed to match what write_file would do
        import textwrap
        expected_content = textwrap.dedent(content) if dedent else content
        
        Cython.TestUtils.write_file(temp_path, content, dedent=dedent)
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            read_content = f.read()
        
        assert read_content == expected_content, \
            f"Round-trip failed: wrote {repr(expected_content[:50])}... but read {repr(read_content[:50])}..."
    finally:
        os.unlink(temp_path)


@given(content=st.binary(min_size=0, max_size=1000))
def test_write_file_round_trip_binary(content):
    """What we write should be what we read back (for binary)"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    
    try:
        Cython.TestUtils.write_file(temp_path, content)
        
        with open(temp_path, 'rb') as f:
            read_content = f.read()
        
        assert read_content == content, "Binary round-trip failed"
    finally:
        os.unlink(temp_path)


# Test 3: write_newer_file timestamp property
@given(
    content1=st.text(min_size=1, max_size=100),
    content2=st.text(min_size=1, max_size=100)
)
def test_write_newer_file_timestamp_property(content1, content2):
    """write_newer_file should always create a file newer than the reference"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ref_file = os.path.join(tmpdir, 'reference.txt')
        new_file = os.path.join(tmpdir, 'newer.txt')
        
        # Create reference file
        Cython.TestUtils.write_file(ref_file, content1)
        ref_time = os.path.getmtime(ref_file)
        
        # Small delay to ensure filesystem timestamp resolution
        time.sleep(0.001)
        
        # Create newer file
        Cython.TestUtils.write_newer_file(new_file, ref_file, content2)
        new_time = os.path.getmtime(new_file)
        
        assert new_time >= ref_time, f"File not newer: {new_time} <= {ref_time}"
        
        # Also check content is correct
        with open(new_file, 'r', encoding='utf-8') as f:
            assert f.read() == content2


# Test 4: Encoding preservation
@given(
    content=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \n\t',
        min_size=0,
        max_size=100
    ),
    encoding=st.sampled_from(['utf-8', 'ascii', 'latin-1'])
)
def test_write_file_encoding_preservation(content, encoding):
    """Content should be preserved when using different encodings (for compatible chars)"""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    
    try:
        # Only test if content is encodable
        try:
            content.encode(encoding)
        except UnicodeEncodeError:
            assume(False)  # Skip this test case
        
        Cython.TestUtils.write_file(temp_path, content, encoding=encoding)
        
        with open(temp_path, 'r', encoding=encoding) as f:
            read_content = f.read()
        
        assert read_content == content, f"Encoding {encoding} didn't preserve content"
    finally:
        os.unlink(temp_path)


# Test 5: Edge case - mixed whitespace in strip_common_indent
@given(
    spaces=st.integers(min_value=0, max_value=10),
    tabs=st.integers(min_value=0, max_value=5),
    content_lines=st.lists(
        st.text(alphabet='abcdef', min_size=1, max_size=10),
        min_size=1,
        max_size=5
    )
)
def test_strip_common_indent_mixed_whitespace(spaces, tabs, content_lines):
    """Test with mixed spaces and tabs"""
    # Create lines with mixed indentation
    indent = ' ' * spaces + '\t' * tabs
    lines = [indent + content for content in content_lines]
    
    result = Cython.TestUtils.strip_common_indent(lines)
    
    # All lines should have the common indent removed
    for line in result:
        assert not line.startswith(indent) or all(c.startswith(indent) for c in content_lines), \
            f"Mixed whitespace indent not handled correctly"


if __name__ == "__main__":
    import pytest
    import sys
    
    # Run the tests
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))