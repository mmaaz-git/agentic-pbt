import click
from hypothesis import given, strategies as st, settings, assume
import math
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


@given(
    st.text(min_size=1),
    st.integers(min_value=1, max_value=200)
)
def test_wrap_text_preserves_content(text, width):
    assume(not text.isspace())
    wrapped = click.wrap_text(text, width=width)
    unwrapped = wrapped.replace('\n', ' ')
    
    original_words = text.split()
    unwrapped_words = unwrapped.split()
    assert original_words == unwrapped_words


@given(
    st.text(min_size=1),
    st.integers(min_value=1, max_value=200)
)
def test_wrap_text_respects_width(text, width):
    wrapped = click.wrap_text(text, width=width)
    lines = wrapped.split('\n')
    
    for line in lines:
        if line:
            assert len(line) <= width


@given(st.text())
def test_wrap_text_empty_width_1(text):
    assume(text and not text.isspace())
    wrapped = click.wrap_text(text, width=1)
    for line in wrapped.split('\n'):
        if line and not line.isspace():
            assert len(line) <= max(1, min(len(w) for w in text.split()))


@given(st.text(alphabet=st.characters(blacklist_categories=['Cs'])))
def test_format_filename_round_trip(text):
    formatted = click.format_filename(text)
    assert isinstance(formatted, str)
    
    if all(ord(c) < 128 for c in text):
        assert text == formatted


@given(st.text())
def test_format_filename_idempotent(text):
    once = click.format_filename(text)
    twice = click.format_filename(once)
    assert once == twice


@given(st.text(min_size=1))
def test_wrap_text_with_initial_indent(text, width=50):
    indent = "  "
    wrapped = click.wrap_text(text, width=width, initial_indent=indent)
    lines = wrapped.split('\n')
    if lines and lines[0]:
        assert lines[0].startswith(indent) or text.startswith('\n')


@given(st.text(min_size=1))
def test_wrap_text_preserve_paragraphs(text):
    assume('\n\n' in text)
    wrapped = click.wrap_text(text, preserve_paragraphs=True)
    
    original_paragraphs = text.split('\n\n')
    wrapped_paragraphs = wrapped.split('\n\n')
    
    original_para_count = len([p for p in original_paragraphs if p.strip()])
    wrapped_para_count = len([p for p in wrapped_paragraphs if p.strip()])
    
    assert abs(original_para_count - wrapped_para_count) <= 1


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


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])