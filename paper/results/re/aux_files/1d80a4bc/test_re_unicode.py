import re
from hypothesis import given, strategies as st, assume, settings, example


@given(st.text())
def test_unicode_escape_roundtrip(s):
    """Unicode strings should round-trip through escape."""
    escaped = re.escape(s)
    pattern = f"^{escaped}$"
    match = re.match(pattern, s)
    assert match is not None, f"Escaped pattern doesn't match original unicode string: {s!r}"
    assert match.group() == s, f"Match group differs from original"


@given(st.text())
def test_unicode_findall_consistency(s):
    """findall should handle unicode correctly."""
    if s:
        first_char = s[0]
        escaped_char = re.escape(first_char)
        
        matches = re.findall(escaped_char, s)
        actual_count = s.count(first_char)
        
        assert len(matches) == actual_count, f"findall found {len(matches)} but string.count found {actual_count}"


@given(st.text(), st.text())
def test_unicode_sub_preserves_encoding(pattern, string):
    """Substitution should preserve unicode string types."""
    try:
        result = re.sub(pattern, '', string)
        assert isinstance(result, str), "Result is not a string"
        
        if pattern == '':
            pass
        elif pattern not in string:
            assert result == string, "No-match substitution changed string"
    except re.error:
        pass


@given(st.text(alphabet='αβγδε', min_size=1, max_size=5))
def test_greek_letters_handling(greek_text):
    """Test handling of non-ASCII unicode (Greek letters)."""
    escaped = re.escape(greek_text)
    assert re.match(escaped, greek_text) is not None
    
    pattern = greek_text[0]
    matches = re.findall(pattern, greek_text)
    assert all(m == pattern for m in matches)


@given(st.text())
def test_null_byte_handling(s):
    """Test handling of null bytes in patterns and strings."""
    if '\x00' in s:
        escaped = re.escape(s)
        assert re.match(f"^{escaped}$", s) is not None


@given(st.one_of(
    st.just('\n'),
    st.just('\r'),
    st.just('\r\n'),
    st.just('\t'),
    st.just('\v'),
    st.just('\f')
))
def test_whitespace_escape_handling(ws):
    """Special whitespace characters should be properly escaped."""
    escaped = re.escape(ws)
    assert re.match(f"^{escaped}$", ws) is not None
    
    result = re.findall(escaped, f"a{ws}b{ws}c")
    assert len(result) == 2


@given(st.text(alphabet='🦄🐍🎯🔥💻', min_size=1, max_size=3))
def test_emoji_handling(emoji_text):
    """Test handling of emoji characters."""
    escaped = re.escape(emoji_text)
    assert re.match(f"^{escaped}$", emoji_text) is not None
    
    first_emoji = emoji_text[0]
    count = emoji_text.count(first_emoji)
    matches = re.findall(re.escape(first_emoji), emoji_text)
    assert len(matches) == count


@given(st.text())
def test_combining_characters(s):
    """Test strings with combining characters."""
    if any(ord(c) in range(0x0300, 0x036F) for c in s):
        escaped = re.escape(s)
        match = re.match(f"^{escaped}$", s)
        assert match is not None
        assert match.group() == s


@given(st.text(min_size=1))
@example('\x00')
@example('\x00abc\x00')
def test_split_with_null_bytes(s):
    """Split should handle null bytes correctly."""
    if '\x00' in s:
        parts = re.split('\x00', s)
        rejoined = '\x00'.join(parts)
        if not s.startswith('\x00') and not s.endswith('\x00'):
            assert rejoined == s, f"Split/join with null bytes failed"