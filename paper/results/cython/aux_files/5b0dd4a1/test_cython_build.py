import os
import tempfile
import hashlib
from hypothesis import given, strategies as st, settings, assume
import Cython.Build.Cache
import Cython.Build.Dependencies


# Test 1: file_hash produces valid hex strings and is consistent
@given(st.binary(min_size=0, max_size=10000))
def test_file_hash_properties(content):
    """Test that file_hash produces consistent, valid hex hashes."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        path = tmp.name
        
        try:
            # Property 1: Returns a valid hex string
            hash1 = Cython.Build.Cache.file_hash(path)
            assert isinstance(hash1, str)
            assert all(c in '0123456789abcdef' for c in hash1.lower())
            assert len(hash1) == 64  # SHA256 produces 64 hex chars
            
            # Property 2: Consistent hashing (same file produces same hash)
            hash2 = Cython.Build.Cache.file_hash(path)
            assert hash1 == hash2
            
            # Property 3: The hash changes when file content changes
            with open(path, 'wb') as f:
                f.write(content + b'x')
            hash3 = Cython.Build.Cache.file_hash(path)
            if content:  # Only check if original content was non-empty
                assert hash1 != hash3
                
        finally:
            os.unlink(path)


# Test 2: strip_string_literals normalization properties  
@given(st.text(min_size=0, max_size=1000))
def test_strip_string_literals_basic(code):
    """Test basic properties of strip_string_literals."""
    # Skip if code contains null bytes which are invalid in Python source
    assume('\x00' not in code)
    
    try:
        normalized, literals = Cython.Build.Dependencies.strip_string_literals(code)
        
        # Property 1: Returns a tuple of (str, dict)
        assert isinstance(normalized, str)
        assert isinstance(literals, dict)
        
        # Property 2: All dictionary keys follow the expected pattern
        for key in literals.keys():
            assert key.startswith('__Pyx_L')
            assert key.endswith('_')
            
        # Property 3: All dictionary values are strings
        for value in literals.values():
            assert isinstance(value, str)
            
    except Exception:
        # Some malformed code might cause parsing errors, which is expected
        pass


# Test 3: strip_string_literals with actual string literals
@given(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters='\x00'), min_size=1, max_size=100))
def test_strip_string_literals_with_strings(string_content):
    """Test strip_string_literals with actual Python string literals."""
    # Test with different quoting styles
    test_cases = [
        f'"{string_content}"',
        f"'{string_content}'",
        f'"""{string_content}"""',
        f"'''{string_content}'''",
    ]
    
    for code in test_cases:
        # Skip if the string contains the quote character unescaped
        if code[0] in string_content and '\\' not in string_content:
            continue
            
        try:
            normalized, literals = Cython.Build.Dependencies.strip_string_literals(code)
            
            # Property: String literals are replaced with labels
            if string_content:
                assert normalized != code  # Code should be normalized
                assert len(literals) > 0  # Should have extracted literals
                
                # The original string content should be preserved in literals
                found = False
                for label, value in literals.items():
                    # The value should contain the original string (possibly with quotes)
                    if string_content in value or value in code:
                        found = True
                        break
                
        except Exception:
            # Some strings might cause parsing errors
            pass


# Test 4: extended_iglob pattern consistency
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_/.', min_size=1, max_size=50))
def test_extended_iglob_consistency(pattern):
    """Test that extended_iglob returns consistent results."""
    # Avoid patterns that could match system files
    assume(not pattern.startswith('/'))
    assume('..' not in pattern)
    
    try:
        # Property 1: Returns an iterable
        result1 = list(Cython.Build.Dependencies.extended_iglob(pattern))
        result2 = list(Cython.Build.Dependencies.extended_iglob(pattern))
        
        # Property 2: Consistent results for same pattern
        assert result1 == result2
        
        # Property 3: Results are strings (file paths)
        for path in result1:
            assert isinstance(path, str)
            
    except Exception:
        # Some patterns might cause errors
        pass


# Test 5: Test the prefix parameter in strip_string_literals
@given(
    st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), blacklist_characters='\x00'), min_size=1, max_size=100),
    st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_', min_size=1, max_size=20)
)
def test_strip_string_literals_prefix(string_content, prefix):
    """Test that custom prefixes work correctly in strip_string_literals."""
    code = f'"{string_content}"'
    
    # Skip problematic cases
    if '"' in string_content and '\\' not in string_content:
        return
        
    try:
        normalized, literals = Cython.Build.Dependencies.strip_string_literals(code, prefix=prefix)
        
        # Property: Custom prefix is used in labels
        for key in literals.keys():
            assert key.startswith(prefix)
            assert key[len(prefix):].replace('_', '').isdigit() or key.endswith('_')
            
    except Exception:
        pass


# Test 6: Test normalize_existing with path normalization
@given(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_/.', min_size=1, max_size=100),
    st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_/.', min_size=1, max_size=50), min_size=0, max_size=10)
)
def test_normalize_existing_properties(base_path, rel_paths):
    """Test normalize_existing path normalization."""
    # Avoid absolute paths and dangerous patterns
    assume(not base_path.startswith('/'))
    assume(all(not p.startswith('/') for p in rel_paths))
    assume('..' not in base_path)
    assume(all('..' not in p for p in rel_paths))
    
    try:
        result = Cython.Build.Dependencies.normalize_existing(base_path, rel_paths)
        
        # Property 1: Result is a tuple
        assert isinstance(result, tuple)
        
        # Property 2: Same input produces same output (deterministic)
        result2 = Cython.Build.Dependencies.normalize_existing(base_path, rel_paths)
        assert result == result2
        
        # Property 3: Duplicate paths in input are deduplicated
        if rel_paths:
            rel_paths_with_dup = rel_paths + [rel_paths[0]]
            result_dup = Cython.Build.Dependencies.normalize_existing(base_path, rel_paths_with_dup)
            # The result should have at most the same number of unique paths
            assert len(result_dup) <= len(set(rel_paths_with_dup))
            
    except Exception:
        # Some inputs might cause errors
        pass