"""Property-based test that reveals the whitespace normalization bug"""

from hypothesis import given, strategies as st, settings
from aiogram.filters.command import Command


@given(
    whitespace=st.sampled_from([" ", "  ", "\t", "\t\t", " \t", "\t "]),
    command=st.from_regex(r"[a-zA-Z][a-zA-Z0-9_]{0,10}", fullmatch=True),
    args=st.text(min_size=1, max_size=20).filter(lambda x: x.strip())
)
@settings(max_examples=100)
def test_whitespace_preservation_in_round_trip(whitespace, command, args):
    """
    Test that the round-trip property holds: parse then format should give back the original.
    
    The CommandObject.text property claims to "Generate original text from object"
    but this test reveals it doesn't preserve whitespace formatting.
    """
    
    # Create original command with specific whitespace
    original = f"/{command}{whitespace}{args}"
    
    # Parse the command
    cmd_filter = Command(command)
    cmd_obj = cmd_filter.extract_command(original)
    
    # Reconstruct using the text property
    reconstructed = cmd_obj.text
    
    # Check if round-trip preserves the original
    assert reconstructed == original, (
        f"Round-trip failed to preserve whitespace!\n"
        f"  Original:      {original!r}\n"
        f"  Reconstructed: {reconstructed!r}\n"
        f"  Whitespace '{whitespace!r}' was normalized to single space"
    )


if __name__ == "__main__":
    # Run the test
    test_whitespace_preservation_in_round_trip()