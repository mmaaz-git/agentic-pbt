"""Property-based tests for click.termui module."""

import math
import re
import sys
from hypothesis import assume, given, strategies as st, settings
import click.termui
from click.termui import style, unstyle, _interpret_color, _build_prompt, _format_default
from click.types import Choice


# Property 1: Round-trip property for style/unstyle
@given(
    text=st.text(),
    fg=st.one_of(
        st.none(),
        st.sampled_from(['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
                         'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
                         'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white']),
        st.integers(min_value=0, max_value=255),
        st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255))
    ),
    bg=st.one_of(
        st.none(),
        st.sampled_from(['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
                         'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
                         'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white']),
        st.integers(min_value=0, max_value=255),
        st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255))
    ),
    bold=st.one_of(st.none(), st.booleans()),
    dim=st.one_of(st.none(), st.booleans()),
    underline=st.one_of(st.none(), st.booleans()),
    italic=st.one_of(st.none(), st.booleans()),
    blink=st.one_of(st.none(), st.booleans()),
    reverse=st.one_of(st.none(), st.booleans()),
    strikethrough=st.one_of(st.none(), st.booleans()),
    overline=st.one_of(st.none(), st.booleans())
)
@settings(max_examples=500)
def test_style_unstyle_round_trip(text, fg, bg, bold, dim, underline, italic, blink, reverse, strikethrough, overline):
    """Test that unstyle(style(text)) returns the original text."""
    styled = style(text, fg=fg, bg=bg, bold=bold, dim=dim, underline=underline,
                   italic=italic, blink=blink, reverse=reverse,
                   strikethrough=strikethrough, overline=overline)
    unstyled = unstyle(styled)
    assert unstyled == text


# Property 2: Idempotence of unstyle
@given(text=st.text())
def test_unstyle_idempotence(text):
    """Test that unstyle(unstyle(text)) == unstyle(text)."""
    once = unstyle(text)
    twice = unstyle(once)
    assert once == twice


# Property 3: Style without reset should not end with reset code
@given(
    text=st.text(min_size=1),
    fg=st.sampled_from(['red', 'green', 'blue']),
)
def test_style_reset_control(text, fg):
    """Test that reset=False doesn't add reset codes."""
    styled_with_reset = style(text, fg=fg, reset=True)
    styled_without_reset = style(text, fg=fg, reset=False)
    
    assert styled_with_reset.endswith('\033[0m')
    assert not styled_without_reset.endswith('\033[0m')


# Property 4: Style composition - multiple styles should accumulate
@given(
    text=st.text(min_size=1),
    fg=st.sampled_from(['red', 'green', 'blue']),
    bold=st.booleans()
)
def test_style_composition(text, fg, bold):
    """Test that style composition works correctly."""
    # Apply color without reset
    styled1 = style(text, fg=fg, reset=False)
    # Apply bold on top
    styled2 = style(styled1, bold=bold, reset=True)
    
    # Should contain both the color code and bold code
    if bold:
        assert '\033[1m' in styled2  # Bold code
    else:
        assert '\033[22m' in styled2  # Not bold code


# Property 5: _interpret_color should handle all valid inputs
@given(
    color=st.one_of(
        st.sampled_from(['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
                         'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
                         'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white', 'reset']),
        st.integers(min_value=0, max_value=255),
        st.tuples(st.integers(0, 255), st.integers(0, 255), st.integers(0, 255))
    ),
    offset=st.integers(min_value=0, max_value=10)
)
def test_interpret_color_valid(color, offset):
    """Test that _interpret_color handles all valid color specifications."""
    result = _interpret_color(color, offset)
    assert isinstance(result, str)
    assert result  # Should not be empty


# Property 6: Build prompt should preserve text and suffix
@given(
    text=st.text(),
    suffix=st.text(),
    show_default=st.booleans(),
    default=st.one_of(st.none(), st.text(), st.integers()),
    show_choices=st.booleans()
)
def test_build_prompt_preserves_text(text, suffix, show_default, default, show_choices):
    """Test that _build_prompt preserves the base text and suffix."""
    prompt = _build_prompt(text, suffix, show_default, default, show_choices, None)
    
    # The prompt should start with the text
    assert prompt.startswith(text)
    # The prompt should end with the suffix
    assert prompt.endswith(suffix)


# Property 7: Format default should handle file-like objects
@given(default=st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none()
))
def test_format_default_basic_types(default):
    """Test that _format_default returns the same value for basic types."""
    result = _format_default(default)
    assert result == default


# Property 8: Style should handle non-string inputs by converting them
@given(
    text=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.integers(), max_size=5)
    ),
    fg=st.sampled_from(['red', 'green', 'blue'])
)
def test_style_non_string_conversion(text, fg):
    """Test that style converts non-string inputs to strings."""
    styled = style(text, fg=fg)
    unstyled = unstyle(styled)
    assert unstyled == str(text)


# Property 9: ANSI escape codes should follow expected pattern
@given(
    text=st.text(min_size=1),
    fg=st.sampled_from(['red', 'green', 'blue']),
    bg=st.sampled_from(['black', 'white', 'yellow'])
)
def test_ansi_escape_pattern(text, fg, bg):
    """Test that generated ANSI codes follow the expected pattern."""
    styled = style(text, fg=fg, bg=bg)
    
    # Should contain escape sequences
    assert '\033[' in styled
    # Should end with reset if not disabled
    assert styled.endswith('\033[0m')
    
    # After unstyle, no escape sequences should remain
    unstyled = unstyle(styled)
    assert '\033[' not in unstyled


# Property 10: Multiple styling attributes in combination
@given(
    text=st.text(min_size=1, max_size=100),
    styles=st.fixed_dictionaries({
        'fg': st.one_of(st.none(), st.sampled_from(['red', 'green', 'blue'])),
        'bg': st.one_of(st.none(), st.sampled_from(['black', 'white'])),
        'bold': st.one_of(st.none(), st.booleans()),
        'dim': st.one_of(st.none(), st.booleans()),
        'underline': st.one_of(st.none(), st.booleans()),
        'italic': st.one_of(st.none(), st.booleans()),
        'blink': st.one_of(st.none(), st.booleans()),
        'reverse': st.one_of(st.none(), st.booleans()),
        'strikethrough': st.one_of(st.none(), st.booleans()),
        'overline': st.one_of(st.none(), st.booleans()),
    })
)
def test_multiple_styles_combination(text, styles):
    """Test that multiple style attributes can be combined."""
    styled = style(text, **styles)
    unstyled = unstyle(styled)
    
    # Core property: unstyle should always recover the original text
    assert unstyled == text
    
    # If any style is applied, there should be escape codes
    if any(v is not None for v in styles.values()):
        assert '\033[' in styled


# Property 11: Chained styling operations
@given(
    text=st.text(min_size=1, max_size=50),
    fg1=st.sampled_from(['red', 'green', 'blue']),
    fg2=st.sampled_from(['yellow', 'magenta', 'cyan']),
)
def test_chained_styling(text, fg1, fg2):
    """Test chaining style operations."""
    # First style
    styled1 = style(text, fg=fg1)
    # Unstyle and restyle
    unstyled = unstyle(styled1)
    styled2 = style(unstyled, fg=fg2)
    
    # Final unstyle should give original text
    final = unstyle(styled2)
    assert final == text


# Property 12: Edge case - empty text
@given(
    fg=st.sampled_from(['red', 'green', 'blue']),
    bold=st.booleans()
)
def test_empty_text_styling(fg, bold):
    """Test styling empty text."""
    styled = style('', fg=fg, bold=bold)
    unstyled = unstyle(styled)
    assert unstyled == ''


# Property 13: RGB color values validation
@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)
def test_rgb_color_bounds(r, g, b):
    """Test RGB color interpretation with various values."""
    result = _interpret_color((r, g, b))
    # Should produce a valid ANSI color code string
    assert isinstance(result, str)
    assert f'{r:d}' in result
    assert f'{g:d}' in result
    assert f'{b:d}' in result


# Property 14: 256-color palette validation
@given(color_num=st.integers(min_value=0, max_value=255))
def test_256_color_palette(color_num):
    """Test 256-color palette interpretation."""
    result = _interpret_color(color_num)
    assert isinstance(result, str)
    assert f'{color_num:d}' in result


# Property 15: Test strip_ansi removes all ANSI codes
@given(
    text=st.text(),
    num_styles=st.integers(min_value=1, max_value=5)
)
def test_strip_ansi_comprehensive(text, num_styles):
    """Test that strip_ansi/unstyle removes all ANSI escape codes."""
    styled = text
    # Apply multiple random styles
    for _ in range(num_styles):
        styled = style(styled, fg='red', reset=False)
        styled = style(styled, bold=True, reset=False)
    
    # Add final reset
    styled = styled + '\033[0m'
    
    # Unstyle should remove all ANSI codes
    unstyled = unstyle(styled)
    
    # No ANSI escape sequences should remain
    assert '\033' not in unstyled
    assert unstyled == text