import click
from hypothesis import given, strategies as st, settings, assume, HealthCheck
import re


@given(st.text())
def test_style_unstyle_round_trip(text):
    styled = click.style(text, fg='red', bold=True)
    unstyled = click.unstyle(styled)
    assert text == unstyled


@given(
    st.text(),
    st.sampled_from([None, 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'white', 'black']),
    st.sampled_from([None, 'red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'white', 'black']),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans(),
)
def test_style_unstyle_with_all_params(text, fg, bg, bold, dim, underline, italic, blink):
    styled = click.style(text, fg=fg, bg=bg, bold=bold, dim=dim, 
                        underline=underline, italic=italic, blink=blink)
    unstyled = click.unstyle(styled)
    assert text == unstyled


@given(st.text())
def test_unstyle_idempotent(text):
    once = click.unstyle(text)
    twice = click.unstyle(once)
    assert once == twice


@given(st.text(), st.text())
def test_style_concatenation(text1, text2):
    styled1 = click.style(text1, fg='red')
    styled2 = click.style(text2, fg='blue')
    combined = styled1 + styled2
    unstyled = click.unstyle(combined)
    assert unstyled == text1 + text2


@given(st.text())
def test_double_style_preserves_text(text):
    styled_once = click.style(text, fg='red')
    styled_twice = click.style(styled_once, fg='blue')
    unstyled = click.unstyle(styled_twice)
    assert text in unstyled


@given(st.text())
def test_format_filename_idempotent(text):
    once = click.format_filename(text)
    twice = click.format_filename(once)
    assert once == twice


@given(st.text())
def test_style_reset_parameter(text):
    styled_with_reset = click.style(text, fg='red', reset=True)
    styled_without_reset = click.style(text, fg='red', reset=False)
    
    if text:
        assert styled_with_reset.endswith('\x1b[0m') or '\x1b[0m' in styled_with_reset
        assert not styled_without_reset.endswith('\x1b[0m') or text.endswith('\x1b[0m')
    
    assert click.unstyle(styled_with_reset) == text
    assert click.unstyle(styled_without_reset) == text


@given(st.text())
def test_nested_style_unwrapping(text):
    styled1 = click.style(text, fg='red')
    styled2 = click.style(styled1, bold=True)
    styled3 = click.style(styled2, underline=True)
    
    unstyled = click.unstyle(styled3)
    
    assert text in unstyled


@given(st.integers(min_value=0, max_value=255))
def test_style_with_numeric_colors(text_int):
    text = str(text_int)
    
    styled = click.style(text, fg=text_int)
    unstyled = click.unstyle(styled)
    assert unstyled == text
    
    styled_bg = click.style(text, bg=text_int)
    unstyled_bg = click.unstyle(styled_bg)
    assert unstyled_bg == text


@given(
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255)
)
def test_style_with_rgb_colors(r, g, b):
    text = f"RGB({r},{g},{b})"
    
    styled = click.style(text, fg=(r, g, b))
    unstyled = click.unstyle(styled)
    assert unstyled == text
    
    styled_bg = click.style(text, bg=(r, g, b))
    unstyled_bg = click.unstyle(styled_bg)
    assert unstyled_bg == text


@given(st.text())
def test_multiple_unstyle_on_already_styled(text):
    already_styled = f"\x1b[31m{text}\x1b[0m"
    
    unstyled = click.unstyle(already_styled)
    assert unstyled == text
    
    double_unstyled = click.unstyle(unstyled)
    assert double_unstyled == text


@given(st.text())
def test_style_empty_string_with_params(text):
    if not text:
        styled = click.style(text, fg='red', bg='blue', bold=True)
        assert styled == ''
        
        unstyled = click.unstyle(styled)
        assert unstyled == text


@given(st.text(min_size=1))
def test_complex_ansi_patterns(text):
    patterns = [
        f"\x1b[0m{text}\x1b[0m",
        f"\x1b[31m\x1b[1m{text}\x1b[0m\x1b[0m",
        f"\x1b[38;5;123m{text}\x1b[0m",
        f"\x1b[38;2;100;200;150m{text}\x1b[0m",
    ]
    
    for pattern in patterns:
        unstyled = click.unstyle(pattern)
        assert text in unstyled or unstyled == text


@given(st.lists(st.text(), min_size=1, max_size=10))
def test_style_list_concatenation(texts):
    styled_parts = [click.style(t, fg='red') for t in texts]
    combined = ''.join(styled_parts)
    
    unstyled = click.unstyle(combined)
    expected = ''.join(texts)
    
    assert unstyled == expected


@given(st.text())
def test_format_filename_with_path_separators(text):
    if '/' in text or '\\' in text:
        formatted = click.format_filename(text)
        assert isinstance(formatted, str)
        
        formatted_shorten = click.format_filename(text, shorten=True)
        assert isinstance(formatted_shorten, str)
        
        if '/' in text:
            assert len(formatted_shorten) <= len(formatted)


@given(st.text(alphabet=st.characters(min_codepoint=0xD800, max_codepoint=0xDFFF)))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_format_filename_with_surrogates(text):
    assume(text)
    
    formatted = click.format_filename(text)
    assert isinstance(formatted, str)
    
    for char in formatted:
        assert ord(char) < 0xD800 or ord(char) > 0xDFFF or char == '�'


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])