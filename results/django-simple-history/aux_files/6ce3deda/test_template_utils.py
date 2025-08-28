import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
from django.utils.safestring import SafeString, mark_safe
from simple_history.template_utils import (
    conditional_str,
    is_safe_str,
    ObjDiffDisplay,
)


@given(st.text())
def test_conditional_str_identity_for_strings(s):
    """If input is already a string, output should be the same string."""
    result = conditional_str(s)
    assert result == s
    assert result is s


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
))
def test_conditional_str_converts_non_strings(obj):
    """Non-strings should be converted to strings."""
    result = conditional_str(obj)
    assert isinstance(result, str)
    assert result == str(obj)


class HasHtmlMethod:
    def __html__(self):
        return "<div>test</div>"

class NoHtmlMethod:
    pass


@given(st.one_of(
    st.text(),
    st.integers(),
    st.none(),
    st.builds(HasHtmlMethod),
    st.builds(NoHtmlMethod),
))
def test_is_safe_str_checks_html_attribute(obj):
    """Should return True if and only if object has __html__ attribute."""
    result = is_safe_str(obj)
    assert result == hasattr(obj, "__html__")


@given(st.text())
def test_is_safe_str_with_safestring(s):
    """SafeString objects should be detected as safe."""
    safe_s = mark_safe(s)
    assert is_safe_str(safe_s) == True
    assert is_safe_str(s) == False


@given(
    st.lists(st.text(), min_size=1, max_size=10),
    st.integers(min_value=10, max_value=1000),
)
def test_common_shorten_repr_unchanged_when_short(strings, max_length):
    """If all strings are <= max_length, they should be returned unchanged."""
    assume(all(len(s) <= max_length for s in strings))
    
    display = ObjDiffDisplay(max_length=max_length)
    result = display.common_shorten_repr(*strings)
    
    assert result == tuple(strings)


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
)
def test_common_shorten_repr_returns_strings(strings):
    """Output should always be strings."""
    display = ObjDiffDisplay(max_length=80)
    result = display.common_shorten_repr(*strings)
    
    assert isinstance(result, tuple)
    assert len(result) == len(strings)
    assert all(isinstance(s, str) for s in result)


@given(
    st.text(min_size=1, max_size=50),
    st.lists(st.text(min_size=0, max_size=50), min_size=2, max_size=5),
    st.integers(min_value=30, max_value=100),
)
def test_common_shorten_repr_preserves_common_prefix(prefix, suffixes, max_length):
    """Common prefix should be preserved in shortened output."""
    strings = [prefix + suffix for suffix in suffixes]
    
    display = ObjDiffDisplay(max_length=max_length)
    result = display.common_shorten_repr(*strings)
    
    if any(len(s) > max_length for s in strings):
        for res_str, orig_str in zip(result, strings):
            if "[" in res_str and "chars]" in res_str:
                assert res_str.startswith(prefix[:display.min_begin_len]) or res_str.startswith(prefix)


@given(
    st.text(min_size=1),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=1, max_value=20),
)
def test_shorten_property(s, prefix_len, suffix_len, placeholder_len):
    """If skip > placeholder_len, string should be shortened, otherwise unchanged."""
    assume(prefix_len >= 0)
    assume(suffix_len >= 0)
    assume(placeholder_len > 0)
    
    display = ObjDiffDisplay(placeholder_len=placeholder_len)
    skip = len(s) - prefix_len - suffix_len
    
    result = display.shorten(s, prefix_len, suffix_len)
    
    if skip > placeholder_len and prefix_len + suffix_len <= len(s):
        assert "[" in result and "chars]" in result
        assert result != s
    else:
        assert result == s


@given(
    st.text(min_size=50, max_size=200),
    st.integers(min_value=5, max_value=20),
    st.integers(min_value=5, max_value=20),
)
def test_shortened_str_format(s, prefix_len, suffix_len):
    """shortened_str should produce correct format with char count."""
    assume(prefix_len + suffix_len < len(s))
    
    display = ObjDiffDisplay()
    num_skipped = len(s) - prefix_len - suffix_len
    
    result = display.shortened_str(s[:prefix_len], num_skipped, s[-suffix_len:])
    
    assert result == f"{s[:prefix_len]}[{num_skipped:d} chars]{s[-suffix_len:]}"
    assert f"[{num_skipped:d} chars]" in result


@given(
    st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=100, max_size=200), min_size=2, max_size=3),
    st.integers(min_value=20, max_value=80),
)
def test_common_shorten_repr_with_long_strings(strings, max_length):
    """When strings are longer than max_length, they should be shortened."""
    assume(all(len(s) > max_length for s in strings))
    
    display = ObjDiffDisplay(max_length=max_length)
    result = display.common_shorten_repr(*strings)
    
    assert all(len(r) <= max_length * 2 for r in result)


@given(st.integers(), st.floats(allow_nan=False), st.booleans())
def test_common_shorten_repr_handles_non_strings(i, f, b):
    """common_shorten_repr should handle non-string arguments by converting them."""
    display = ObjDiffDisplay(max_length=80)
    result = display.common_shorten_repr(i, f, b)
    
    assert result == (str(i), str(f), str(b))
    assert all(isinstance(s, str) for s in result)