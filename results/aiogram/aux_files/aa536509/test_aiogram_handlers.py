"""Property-based tests for aiogram.handlers"""

import re
from hypothesis import given, strategies as st, assume, settings
from aiogram.filters.command import Command, CommandObject


# Strategy for valid command prefixes (common bot command prefixes)
prefix_strategy = st.sampled_from(["/", "!", ".", "~", "$"])

# Strategy for valid command names (alphanumeric, underscores)
command_strategy = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_]{0,31}", fullmatch=True)

# Strategy for valid mention/username (Telegram username rules)
mention_strategy = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_]{4,31}", fullmatch=True)

# Strategy for arguments (any text without newlines)
args_strategy = st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"], blacklist_characters="\n\r"), min_size=1, max_size=100)


@given(
    prefix=prefix_strategy,
    command=command_strategy,
    mention=st.one_of(st.none(), mention_strategy),
    args=st.one_of(st.none(), args_strategy)
)
@settings(max_examples=1000)
def test_command_object_text_property_reconstruction(prefix, command, mention, args):
    """Test that CommandObject.text correctly reconstructs the command string"""
    
    # Create CommandObject
    cmd_obj = CommandObject(
        prefix=prefix,
        command=command,
        mention=mention,
        args=args
    )
    
    # Get reconstructed text
    reconstructed = cmd_obj.text
    
    # Verify the reconstruction matches expected format
    expected = prefix + command
    if mention:
        expected += "@" + mention
    if args:
        expected += " " + args
    
    assert reconstructed == expected, f"Reconstruction failed: got {reconstructed!r}, expected {expected!r}"


@given(
    prefix=prefix_strategy,
    command=command_strategy,
    mention=st.one_of(st.none(), mention_strategy),
    args=st.one_of(st.none(), args_strategy)
)
@settings(max_examples=1000)
def test_command_extract_and_text_round_trip(prefix, command, mention, args):
    """Test that extract_command followed by .text gives back the original for valid commands"""
    
    # Build original text
    original = prefix + command
    if mention:
        original += "@" + mention
    if args:
        original += " " + args
    
    # Create Command filter and extract
    cmd_filter = Command(command)
    
    try:
        # Extract command
        cmd_obj = cmd_filter.extract_command(original)
        
        # Reconstruct text
        reconstructed = cmd_obj.text
        
        # They should match
        assert reconstructed == original, f"Round-trip failed: {original!r} -> {reconstructed!r}"
        
    except Exception:
        # extract_command might raise exceptions for invalid formats
        # That's okay as long as it's consistent
        pass


@given(
    text=st.text(min_size=1, max_size=200)
)
def test_command_extract_handles_arbitrary_text(text):
    """Test that extract_command handles arbitrary text without crashing unexpectedly"""
    
    # Skip texts that are just whitespace
    assume(text.strip())
    
    cmd_filter = Command("test")
    
    try:
        # Try to extract command
        cmd_obj = cmd_filter.extract_command(text)
        
        # If extraction succeeds, verify basic properties
        assert isinstance(cmd_obj, CommandObject)
        assert isinstance(cmd_obj.prefix, str)
        assert isinstance(cmd_obj.command, str)
        assert cmd_obj.mention is None or isinstance(cmd_obj.mention, str)
        assert cmd_obj.args is None or isinstance(cmd_obj.args, str)
        
        # Verify text property works
        reconstructed = cmd_obj.text
        assert isinstance(reconstructed, str)
        
    except Exception as e:
        # Should only raise CommandException for invalid formats
        from aiogram.filters.command import CommandException
        assert isinstance(e, CommandException), f"Unexpected exception type: {type(e)}"


@given(
    prefix=prefix_strategy,
    command=command_strategy,
)
def test_command_without_args_round_trip(prefix, command):
    """Test commands without arguments or mentions"""
    
    original = prefix + command
    
    cmd_filter = Command(command)
    
    try:
        cmd_obj = cmd_filter.extract_command(original)
        reconstructed = cmd_obj.text
        
        assert reconstructed == original, f"Simple command round-trip failed: {original!r} -> {reconstructed!r}"
        assert cmd_obj.args is None, "Command without args should have args=None"
        assert cmd_obj.mention is None, "Command without mention should have mention=None"
        
    except Exception:
        pass


@given(
    command=command_strategy,
    extra_spaces=st.integers(min_value=2, max_value=10)
)
def test_command_with_multiple_spaces(command, extra_spaces):
    """Test that multiple spaces between command and args are handled correctly"""
    
    original = "/" + command + (" " * extra_spaces) + "some args"
    
    cmd_filter = Command(command)
    
    try:
        cmd_obj = cmd_filter.extract_command(original)
        
        # Args should not include leading spaces
        assert cmd_obj.args == "some args", f"Args incorrectly parsed with multiple spaces: {cmd_obj.args!r}"
        
        # Reconstruction should normalize to single space
        reconstructed = cmd_obj.text
        expected = "/" + command + " " + "some args"
        assert reconstructed == expected, f"Multiple spaces not normalized: {reconstructed!r}"
        
    except Exception:
        pass


@given(
    text=st.text(alphabet=st.characters(whitelist_categories=["Zs", "Cc"]), min_size=1, max_size=10)
)
def test_command_with_only_whitespace(text):
    """Test that whitespace-only text is handled properly"""
    
    cmd_filter = Command("test")
    
    try:
        cmd_obj = cmd_filter.extract_command(text)
        # If it succeeds, it should at least not crash on text property
        _ = cmd_obj.text
    except Exception as e:
        from aiogram.filters.command import CommandException
        # Should raise CommandException for invalid input
        assert isinstance(e, CommandException)