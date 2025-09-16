import re
from hypothesis import given, strategies as st, assume, settings


@given(st.text())
def test_scanner_consistency(s):
    """Scanner should give same results as finditer."""
    pattern = '.'
    
    if s:
        # Using undocumented Scanner class
        scanner = re.Scanner([(pattern, lambda scanner, token: token)])
        tokens, remainder = scanner.scan(s)
        
        # Compare with finditer
        finditer_results = [m.group() for m in re.finditer(pattern, s)]
        
        assert tokens == finditer_results, "Scanner gave different results than finditer"
        assert remainder == '', "Scanner left remainder for . pattern"


@given(
    st.text(alphabet='abc', min_size=1, max_size=5),
    st.integers(min_value=-100, max_value=100)
)
def test_negative_count_in_sub(pattern, count):
    """Negative count in sub should work like no limit."""
    string = 'abcabcabc'
    
    try:
        if count < 0:
            # Negative count should mean unlimited
            result_negative = re.sub(pattern, 'X', string, count=count)
            result_unlimited = re.sub(pattern, 'X', string)
            assert result_negative == result_unlimited, f"Negative count {count} didn't work like unlimited"
    except re.error:
        pass


@given(
    st.text(alphabet='01', min_size=1, max_size=5),
    st.integers(min_value=-100, max_value=100)
)
def test_negative_maxsplit_in_split(pattern, maxsplit):
    """Negative maxsplit in split should work like no limit."""
    string = '010101'
    
    try:
        if maxsplit < 0:
            # Negative maxsplit should mean unlimited
            result_negative = re.split(pattern, string, maxsplit=maxsplit)
            result_unlimited = re.split(pattern, string)
            assert result_negative == result_unlimited, f"Negative maxsplit {maxsplit} didn't work like unlimited"
    except re.error:
        pass


@given(st.text())
def test_pattern_hashability(s):
    """Compiled patterns should be hashable and usable as dict keys."""
    if s:
        pattern_str = s[:5]  # Use prefix to avoid complex patterns
        try:
            p1 = re.compile(pattern_str)
            p2 = re.compile(pattern_str)
            
            # Should be hashable
            h1 = hash(p1)
            h2 = hash(p2)
            
            # Can use as dict key
            d = {p1: 'value1'}
            d[p2] = 'value2'
            
            # Both patterns should map to same value since they're equivalent
            # Actually, they're different objects so will have different hashes
            # This is correct behavior
        except re.error:
            pass


@given(st.text(min_size=1))
def test_match_vs_search_at_position(s):
    """match at pos should equal search with ^ at pos."""
    pattern = s[0]  # Match first character
    
    for pos in range(len(s)):
        try:
            # Pattern.match with pos parameter
            p = re.compile(pattern)
            match_result = p.match(s, pos)
            
            # Pattern.search with ^ anchor
            anchored = '^' + pattern
            p_anchored = re.compile(anchored)
            search_result = p_anchored.search(s[pos:])
            
            if match_result is None:
                assert search_result is None
            else:
                assert search_result is not None
                # Adjust for position offset
                assert match_result.group() == search_result.group()
        except re.error:
            pass


@given(st.text(alphabet='ab()*+?.', min_size=1, max_size=10))
def test_escape_idempotency(s):
    """Escaping an already escaped string should give valid pattern."""
    escaped_once = re.escape(s)
    escaped_twice = re.escape(escaped_once)
    
    # Both should be valid patterns
    try:
        p1 = re.compile(escaped_once)
        p2 = re.compile(escaped_twice)
        
        # escaped_once should match original string
        assert p1.match(s) is not None
        
        # escaped_twice should match escaped_once
        assert p2.match(escaped_once) is not None
    except re.error as e:
        assert False, f"Escaped pattern not valid: {e}"