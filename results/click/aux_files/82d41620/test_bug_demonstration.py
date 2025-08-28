"""Demonstrate the bug in click.termui unstyle function."""

import click.termui
from hypothesis import given, strategies as st


# Bug test: unstyle should remove ALL escape sequences
@given(
    text=st.text(alphabet=st.characters(min_codepoint=0x1b, max_codepoint=0x1b), min_size=1, max_size=3)
)
def test_unstyle_bare_escape(text):
    """Test that unstyle removes bare escape characters."""
    # Style the text (which contains escape characters)
    styled = click.termui.style(text, fg='red')
    # Unstyle it
    unstyled = click.termui.unstyle(styled)
    
    # The unstyled text should not contain escape characters
    assert '\x1b' not in unstyled, f"Bare escape character remains: {repr(unstyled)}"


@given(prefix=st.text(alphabet=st.characters(blacklist_characters='\x1b'), max_size=10))
def test_unstyle_with_incomplete_sequences(prefix):
    """Test unstyle with various incomplete ANSI sequences."""
    incomplete_sequences = [
        '\x1b',      # Just escape
        '\x1b[',     # Escape + bracket
        '\x1b[3',    # Partial color code
        '\x1b[31',   # Almost complete color code (missing 'm')
    ]
    
    for seq in incomplete_sequences:
        text = prefix + seq
        # Apply styling
        styled = click.termui.style(text, bold=True)
        unstyled = click.termui.unstyle(styled)
        
        # No escape characters should remain
        assert '\x1b' not in unstyled, f"Escape remains in {repr(unstyled)} from {repr(seq)}"


if __name__ == "__main__":
    # Demonstrate the issue directly
    print("Testing bare escape character:")
    text = '\x1b'
    styled = click.termui.style(text, fg='red')
    unstyled = click.termui.unstyle(styled)
    print(f"  Original: {repr(text)}")
    print(f"  Styled:   {repr(styled)}")
    print(f"  Unstyled: {repr(unstyled)}")
    print(f"  Bug: Escape remains = {'\x1b' in unstyled}")
    
    print("\nTesting text with embedded escape:")
    text = 'Hello\x1bWorld'
    styled = click.termui.style(text, fg='blue')
    unstyled = click.termui.unstyle(styled)
    print(f"  Original: {repr(text)}")
    print(f"  Styled:   {repr(styled)}")
    print(f"  Unstyled: {repr(unstyled)}")
    print(f"  Bug: Escape remains = {'\x1b' in unstyled}")