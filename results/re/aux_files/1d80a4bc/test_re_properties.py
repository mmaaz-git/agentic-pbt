import re
from hypothesis import given, strategies as st, assume, settings


@given(st.text())
def test_escape_round_trip(s):
    """An escaped pattern should match the literal string exactly."""
    escaped = re.escape(s)
    pattern = f"^{escaped}$"
    assert re.match(pattern, s) is not None, f"Escaped pattern doesn't match original string: {s!r}"


@given(
    st.text(min_size=1),
    st.text(),
    st.text(),
    st.integers(min_value=0, max_value=100)
)
def test_sub_subn_consistency(pattern, repl, string, count):
    """subn should return the same string as sub, plus the count."""
    try:
        sub_result = re.sub(pattern, repl, string, count=count)
        subn_result, num_subs = re.subn(pattern, repl, string, count=count)
        assert sub_result == subn_result, f"sub and subn gave different results for pattern={pattern!r}"
    except re.error:
        pass


@given(
    st.text(min_size=1),
    st.text(),
    st.integers(min_value=0, max_value=10)
)
def test_split_maxsplit_constraint(pattern, string, maxsplit):
    """split with maxsplit should return at most maxsplit+1 parts."""
    try:
        result = re.split(pattern, string, maxsplit=maxsplit)
        assert len(result) <= maxsplit + 1, f"Split returned {len(result)} parts, expected <= {maxsplit + 1}"
    except re.error:
        pass


@given(
    st.text(min_size=1),
    st.text(),
    st.text()
)
def test_sub_count_zero_invariant(pattern, repl, string):
    """sub with count=0 should return the original string unchanged."""
    try:
        result = re.sub(pattern, repl, string, count=0)
        assert result == string, f"sub with count=0 changed the string"
    except re.error:
        pass


@given(st.text())
def test_escape_produces_valid_pattern(s):
    """Escaped strings should always be valid regex patterns."""
    escaped = re.escape(s)
    try:
        re.compile(escaped)
    except re.error as e:
        assert False, f"re.escape produced invalid pattern for {s!r}: {e}"


@given(
    st.text(min_size=1),
    st.text()
)
def test_findall_length_constraint(pattern, string):
    """For single char patterns, findall results should be <= string length."""
    if len(pattern) == 1 and not re.escape(pattern) != pattern:
        try:
            matches = re.findall(pattern, string)
            assert len(matches) <= len(string), f"More matches than characters in string"
        except re.error:
            pass


@given(
    st.text(),
    st.text(),
    st.sampled_from([re.IGNORECASE, re.MULTILINE, re.DOTALL, 0])
)
def test_compile_consistency(pattern, string, flags):
    """Compiled patterns should give same results as direct pattern use."""
    try:
        compiled = re.compile(pattern, flags)
        
        direct_match = re.match(pattern, string, flags)
        compiled_match = compiled.match(string)
        
        if direct_match is None:
            assert compiled_match is None
        else:
            assert compiled_match is not None
            assert direct_match.group() == compiled_match.group()
    except re.error:
        pass