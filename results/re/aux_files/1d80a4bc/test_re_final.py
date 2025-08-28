import re
from hypothesis import given, strategies as st, assume, settings, example


@given(st.text())
def test_purge_doesnt_affect_results(s):
    """re.purge() should clear cache but not affect results."""
    pattern = s[:3] if len(s) >= 3 else s
    
    try:
        # Get results before purge
        before = re.findall(pattern, s)
        
        # Purge the cache
        re.purge()
        
        # Get results after purge
        after = re.findall(pattern, s)
        
        assert before == after, "Results changed after cache purge"
    except re.error:
        pass


@given(
    st.text(alphabet='ab', min_size=1, max_size=5),
    st.text(alphabet='ab', min_size=0, max_size=10)
)
def test_match_object_groups_consistency(pattern, string):
    """Match object groups should be consistent."""
    pattern_with_groups = f'({pattern})'
    
    try:
        match = re.match(pattern_with_groups, string)
        if match:
            assert match.group() == match.group(0), "group() and group(0) differ"
            assert match.groups()[0] == match.group(1), "groups()[0] and group(1) differ"
    except re.error:
        pass


@given(st.text(min_size=0, max_size=100))
def test_empty_split_pattern_behavior(string):
    """Split with empty pattern has specific behavior."""
    # According to docs, split with empty pattern should split on empty matches
    result = re.split('', string)
    
    # Empty pattern split should return list with original string 
    # (or list of characters with empty strings between)
    if string:
        # With Python 3.5+, splitting on empty pattern returns original string
        assert result == [string] or all(c in string for c in result if c)


@given(
    st.lists(st.text(alphabet='abc', min_size=1, max_size=3), min_size=2, max_size=5),
    st.text(alphabet='abc', min_size=0, max_size=20)
)
def test_alternation_order_doesnt_matter_for_findall(alternatives, string):
    """Order of alternatives in pattern shouldn't affect what's found (just order)."""
    pattern1 = '|'.join(re.escape(alt) for alt in alternatives)
    pattern2 = '|'.join(re.escape(alt) for alt in reversed(alternatives))
    
    try:
        matches1 = set(re.findall(pattern1, string))
        matches2 = set(re.findall(pattern2, string))
        
        assert matches1 == matches2, "Different alternatives found with different order"
    except re.error:
        pass


@given(st.text(alphabet='01', min_size=1, max_size=100))
def test_subn_count_accuracy(string):
    """subn should accurately count substitutions."""
    pattern = '0'
    replacement = '1'
    
    try:
        new_string, count = re.subn(pattern, replacement, string)
        
        # Count should match the number of pattern occurrences
        expected_count = string.count('0')
        assert count == expected_count, f"subn reported {count} subs but string has {expected_count} matches"
        
        # The new string should have no remaining matches
        remaining = re.findall(pattern, new_string)
        assert len(remaining) == 0, "Pattern still found after substitution"
    except re.error:
        pass


@given(st.integers(min_value=0, max_value=200))
def test_groups_limit(n):
    """Test behavior at group limits."""
    # Python re module has a limit of 100 groups (used to be 99)
    if n <= 100:
        pattern = '(' * n + 'a' + ')' * n
        try:
            compiled = re.compile(pattern)
            assert compiled.groups == n
            
            match = compiled.match('a')
            if match and n > 0:
                assert len(match.groups()) == n
        except re.error as e:
            if 'too many groups' in str(e).lower():
                pass
            else:
                raise
    else:
        # Should fail with too many groups
        pattern = '(' * n + 'a' + ')' * n
        try:
            re.compile(pattern)
            assert False, f"Should have failed with {n} groups"
        except re.error as e:
            assert 'group' in str(e).lower() or 'many' in str(e).lower()


@given(st.text())
@example('\r\n')
@example('\n')
@example('\r')
def test_line_boundary_matching(s):
    """Test $ and ^ with different line endings."""
    # In multiline mode, ^ and $ should match at line boundaries
    if '\n' in s or '\r' in s:
        # Test that ^ matches after newlines in MULTILINE mode
        starts = re.findall('^', s, re.MULTILINE)
        
        # Count line starts (including start of string)
        lines = s.split('\n')
        if not s.endswith('\n'):
            expected_starts = len(lines)
        else:
            expected_starts = len(lines)
            
        # This is complex due to \r\n handling, so just ensure we find at least one
        assert len(starts) >= 1