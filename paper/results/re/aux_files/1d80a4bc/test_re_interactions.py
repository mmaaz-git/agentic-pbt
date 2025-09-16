import re
from hypothesis import given, strategies as st, assume, settings


@given(
    st.text(alphabet='abc', min_size=1, max_size=10),
    st.text(alphabet='abc', min_size=0, max_size=20)
)
def test_compile_then_methods_consistency(pattern, string):
    """Using compiled pattern should give same results as direct calls."""
    try:
        # Direct calls
        direct_search = re.search(pattern, string)
        direct_match = re.match(pattern, string)
        direct_findall = re.findall(pattern, string)
        
        # Compiled pattern calls
        compiled = re.compile(pattern)
        compiled_search = compiled.search(string)
        compiled_match = compiled.match(string)
        compiled_findall = compiled.findall(string)
        
        # Check consistency
        if direct_search is None:
            assert compiled_search is None
        else:
            assert compiled_search is not None
            assert direct_search.group() == compiled_search.group()
            
        if direct_match is None:
            assert compiled_match is None
        else:
            assert compiled_match is not None
            assert direct_match.group() == compiled_match.group()
            
        assert direct_findall == compiled_findall
    except re.error:
        pass


@given(
    st.text(alphabet='abc', min_size=1, max_size=5),
    st.text(alphabet='abc', min_size=0, max_size=10),
    st.text(alphabet='xyz', min_size=0, max_size=5)
)
def test_sub_with_function_replacement(pattern, string, prefix):
    """Test substitution with callable replacement."""
    call_count = [0]
    
    def repl_func(match):
        call_count[0] += 1
        return prefix + match.group()
    
    try:
        # String replacement
        string_result = re.sub(pattern, prefix, string)
        
        # Function replacement
        func_result = re.sub(pattern, repl_func, string)
        
        # Count how many substitutions were made
        _, count = re.subn(pattern, prefix, string)
        
        # The function should be called exactly 'count' times
        assert call_count[0] == count, f"Function called {call_count[0]} times but {count} substitutions made"
        
        # If prefix is empty, results should match
        if prefix == '':
            assert string_result == func_result
    except re.error:
        pass


@given(
    st.text(alphabet='01', min_size=1, max_size=10),
    st.text(alphabet='01', min_size=0, max_size=20)
)
def test_match_search_fullmatch_relationship(pattern, string):
    """Test relationship between match, search, and fullmatch."""
    try:
        match_result = re.match(pattern, string)
        search_result = re.search(pattern, string)
        fullmatch_result = re.fullmatch(pattern, string)
        
        # If fullmatch succeeds, match must also succeed
        if fullmatch_result is not None:
            assert match_result is not None, "fullmatch succeeded but match failed"
            assert match_result.group() == fullmatch_result.group()
            
        # If match succeeds, search must also succeed (and find the same or earlier)
        if match_result is not None:
            assert search_result is not None, "match succeeded but search failed"
            assert search_result.start() == 0, "search didn't find match at start"
            
    except re.error:
        pass


@given(
    st.text(alphabet='abc', min_size=1, max_size=5),
    st.text(alphabet='abc', min_size=0, max_size=20),
    st.sampled_from([re.IGNORECASE, re.MULTILINE, re.DOTALL, 0])
)
def test_flags_consistency_across_functions(pattern, string, flags):
    """Flags should work consistently across all functions."""
    try:
        # Test with direct functions
        match_result = re.match(pattern, string, flags)
        search_result = re.search(pattern, string, flags)
        findall_result = re.findall(pattern, string, flags)
        
        # Test with compiled pattern
        compiled = re.compile(pattern, flags)
        compiled_match = compiled.match(string)
        compiled_search = compiled.search(string)
        compiled_findall = compiled.findall(string)
        
        # Results should be consistent
        if match_result is None:
            assert compiled_match is None
        else:
            assert compiled_match is not None
            assert match_result.group() == compiled_match.group()
            
        if search_result is None:
            assert compiled_search is None
        else:
            assert compiled_search is not None
            assert search_result.group() == compiled_search.group()
            
        assert findall_result == compiled_findall
    except re.error:
        pass


@given(
    st.text(alphabet='abc', min_size=1, max_size=5),
    st.text(alphabet='abc', min_size=0, max_size=20)
)
def test_finditer_iteration_safety(pattern, string):
    """finditer should be safe to iterate multiple times."""
    try:
        # Create iterator
        iter1 = re.finditer(pattern, string)
        results1 = [m.group() for m in iter1]
        
        # Create another iterator
        iter2 = re.finditer(pattern, string)
        results2 = [m.group() for m in iter2]
        
        # Results should be the same
        assert results1 == results2
        
        # Should also match findall
        findall_results = re.findall(pattern, string)
        assert results1 == findall_results
    except re.error:
        pass


@given(
    st.text(alphabet='()[]{}.+*?', min_size=1, max_size=3),
    st.text(alphabet='abc', min_size=0, max_size=10)
)
def test_escape_then_use(special_chars, string):
    """Escaped special characters should be treated as literals."""
    escaped = re.escape(special_chars)
    
    # The escaped pattern should only match the literal string
    matches = re.findall(escaped, special_chars + string + special_chars)
    
    # Should find exactly 2 matches (at beginning and end)
    assert len(matches) == 2
    assert all(m == special_chars for m in matches)