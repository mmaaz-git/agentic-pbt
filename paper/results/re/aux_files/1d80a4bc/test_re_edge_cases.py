import re
from hypothesis import given, strategies as st, assume, settings, example
import sys


@given(st.integers(min_value=1, max_value=10))
def test_backreference_substitution(n):
    """Test backreference behavior in substitutions."""
    pattern = r'(\d+)'
    string = '123 456 789'
    
    if n <= 9:
        repl = f'\\{n}'
        try:
            result = re.sub(pattern, repl, string, count=1)
        except re.error as e:
            if 'invalid group reference' in str(e):
                pass
            else:
                raise


@given(st.text(alphabet='ab()', min_size=1, max_size=10))
def test_unbalanced_parentheses(pattern):
    """Test handling of unbalanced parentheses in patterns."""
    try:
        re.compile(pattern)
        re.findall(pattern, 'test')
    except re.error as e:
        if 'unbalanced parenthesis' in str(e) or 'unterminated group' in str(e):
            pass
        else:
            # Re-raise if it's a different error
            raise


@given(st.integers(min_value=0, max_value=1000))
def test_group_reference_limits(n):
    """Test limits of group references."""
    pattern = '()' * min(n, 100)  # Limit to avoid memory issues
    try:
        compiled = re.compile(pattern)
        if n <= 100:
            assert compiled.groups == min(n, 100)
    except re.error:
        pass


@given(st.text(min_size=1, max_size=3))
def test_recursive_pattern_edge_cases(s):
    """Test potentially recursive or complex patterns."""
    patterns_to_test = [
        s + '*',
        s + '+',
        s + '?',
        '(' + s + ')*',
        s + '{0,10}',
    ]
    
    for pattern in patterns_to_test:
        try:
            re.findall(pattern, s * 3)
        except re.error:
            pass


@given(st.text())
def test_finditer_vs_findall_consistency(string):
    """finditer should find the same matches as findall."""
    pattern = '.'
    
    if string:
        findall_results = re.findall(pattern, string)
        finditer_results = [m.group() for m in re.finditer(pattern, string)]
        
        assert findall_results == finditer_results, "findall and finditer gave different results"


@given(st.text(alphabet='01', min_size=0, max_size=5))
def test_fullmatch_vs_match_with_anchors(string):
    """fullmatch should be equivalent to match with ^ and $ anchors."""
    patterns = ['0*', '1*', '01', '10', '.*', '0+1*']
    
    for pattern in patterns:
        try:
            fullmatch_result = re.fullmatch(pattern, string)
            anchored_pattern = f'^{pattern}$'
            match_result = re.match(anchored_pattern, string)
            
            if fullmatch_result is None:
                assert match_result is None
            else:
                assert match_result is not None
                assert fullmatch_result.group() == match_result.group()
        except re.error:
            pass


@given(
    st.text(min_size=1, max_size=5),
    st.integers(min_value=-10, max_value=10)
)
def test_negative_lookahead_assertions(text, n):
    """Test negative lookahead assertions."""
    if n >= 0 and n < len(text):
        pattern = f'(?!{re.escape(text[n])})'
        try:
            matches = re.findall(pattern, text)
        except re.error:
            pass


@given(st.text(alphabet='abc', min_size=1, max_size=100))
def test_pattern_cache_consistency(s):
    """Test that pattern caching doesn't cause issues."""
    # Force many different patterns to potentially overflow cache
    patterns = [s[i:i+2] for i in range(min(len(s)-1, 50))]
    
    for pattern in patterns:
        try:
            re.compile(pattern)
            re.findall(pattern, s)
        except re.error:
            pass
    
    # Now re-test first pattern to ensure cache doesn't affect results
    if patterns:
        first_pattern = patterns[0]
        try:
            result1 = re.findall(first_pattern, s)
            result2 = re.findall(first_pattern, s)
            assert result1 == result2, "Same pattern gave different results after cache operations"
        except re.error:
            pass


@given(st.lists(st.text(min_size=1, max_size=3), min_size=1, max_size=5))
def test_alternation_patterns(alternatives):
    """Test alternation patterns with |."""
    pattern = '|'.join(re.escape(alt) for alt in alternatives)
    test_string = ''.join(alternatives)
    
    try:
        matches = re.findall(pattern, test_string)
        # At minimum, each alternative should match itself
        for alt in alternatives:
            if alt in test_string:
                assert any(m == alt for m in matches), f"Alternative {alt!r} not found in matches"
    except re.error:
        pass


@given(st.text())
@example('')
@example('\n')
@example('\r\n')
def test_multiline_mode_edge_cases(s):
    """Test edge cases with multiline mode."""
    patterns_flags = [
        ('^', re.MULTILINE),
        ('$', re.MULTILINE),
        ('^$', re.MULTILINE),
        ('.*', re.DOTALL),
        ('^.*$', re.MULTILINE | re.DOTALL)
    ]
    
    for pattern, flags in patterns_flags:
        try:
            matches = re.findall(pattern, s, flags=flags)
        except re.error:
            pass