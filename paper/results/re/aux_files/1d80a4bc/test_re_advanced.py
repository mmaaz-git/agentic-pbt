import re
from hypothesis import given, strategies as st, assume, settings


@given(st.text())
def test_escape_metamorphic_property(s):
    """Double escaping should produce a pattern that matches the escaped string."""
    escaped_once = re.escape(s)
    escaped_twice = re.escape(escaped_once)
    
    if re.match(f"^{escaped_twice}$", escaped_once):
        pass
    else:
        assert False, f"Double escape failed for {s!r}"


@given(st.text(), st.text())  
def test_sub_empty_pattern_edge_case(repl, string):
    """Substituting empty pattern should insert replacement between every character."""
    result = re.sub('', repl, string)
    if string == '':
        assert result == repl
    else:
        expected_parts = len(string) + 1
        parts = result.split(repl)
        if repl != '' and repl not in string:
            assert len(parts) == expected_parts, f"Empty pattern substitution incorrect"


@given(st.text(alphabet='abc', min_size=1, max_size=10))
def test_split_empty_pattern(string):
    """Splitting by empty pattern should have specific behavior."""
    result = re.split('', string)
    
    if string:
        assert result[0] == '' or result[0] == string[0]
        assert result[-1] == '' or result[-1] == string[-1]


@given(st.text())
def test_findall_empty_pattern(string):
    """findall with empty pattern should find len(string)+1 matches."""
    matches = re.findall('', string)
    assert len(matches) == len(string) + 1, f"Empty pattern findall count wrong"


@given(
    st.text(alphabet='01', min_size=1, max_size=10),
    st.text(alphabet='01', min_size=0, max_size=10)
)
def test_search_vs_match_consistency(pattern, string):
    """If match succeeds, search should also succeed and find the same or earlier match."""
    try:
        match_result = re.match(pattern, string)
        search_result = re.search(pattern, string)
        
        if match_result is not None:
            assert search_result is not None, "match succeeded but search failed"
            assert search_result.start() == 0, "search should find match at start when match succeeds"
            assert search_result.group() == match_result.group(), "search and match found different matches"
    except re.error:
        pass


@given(st.text(min_size=1, max_size=5))
def test_compile_cache_behavior(pattern):
    """Test potential issues with regex compilation and caching."""
    try:
        p1 = re.compile(pattern)
        p2 = re.compile(pattern)
        
        test_string = pattern
        
        r1 = p1.findall(test_string)
        r2 = p2.findall(test_string)
        
        assert r1 == r2, "Same pattern compiled twice gives different results"
    except re.error:
        pass


@given(
    st.text(alphabet='abc', min_size=1, max_size=5),
    st.text(alphabet='abc', min_size=0, max_size=10),
    st.integers(min_value=1, max_value=5)
)  
def test_split_count_relationship(pattern, string, maxsplit):
    """The actual number of splits should be min(possible_splits, maxsplit)."""
    try:
        unlimited = re.split(pattern, string)
        limited = re.split(pattern, string, maxsplit=maxsplit)
        
        if len(unlimited) > 1:
            actual_splits_unlimited = len(unlimited) - 1
            actual_splits_limited = len(limited) - 1
            
            assert actual_splits_limited <= maxsplit, f"Made more splits than maxsplit"
            assert actual_splits_limited <= actual_splits_unlimited, f"Limited split made more splits than unlimited"
    except re.error:
        pass


@given(st.text(alphabet='()[]{}.+*?\\|^$', min_size=1, max_size=3))
def test_escape_special_chars_comprehensive(special_chars):
    """Test escaping of regex special characters."""
    escaped = re.escape(special_chars)
    
    assert re.match(f"^{escaped}$", special_chars) is not None
    
    for char in special_chars:
        if char in '.^$*+?{}[]\\|()':
            assert '\\' + char in escaped or (char == '\\' and '\\\\' in escaped)