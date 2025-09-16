"""Property-based tests for aiogram.filters"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from aiogram.filters.command import Command, CommandObject, CommandException
from aiogram import Bot
import re
import asyncio


# Strategy for valid command names
command_names = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), 
                          whitelist_characters="_"),
    min_size=1,
    max_size=32
).filter(lambda x: x[0].isalpha())

# Strategy for command prefixes  
command_prefixes = st.sampled_from(["/", "!", ".", "#", "$"])

# Strategy for mentions (bot usernames)
mentions = st.one_of(
    st.none(),
    st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), 
                                   whitelist_characters="_"),
            min_size=5, max_size=32)
)

# Strategy for command arguments
arguments = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
)


class TestCommandExtraction:
    """Test properties of Command.extract_command parsing"""
    
    @given(
        prefix=command_prefixes,
        command=command_names,
        mention=mentions,
        args=arguments
    )
    def test_extract_command_structure_preservation(self, prefix, command, mention, args):
        """Test that extract_command preserves command structure"""
        cmd_filter = Command("test")
        
        # Build the text
        text = prefix + command
        if mention:
            text += "@" + mention
        if args:
            text += " " + args
            
        try:
            result = cmd_filter.extract_command(text)
            
            # Verify structure preservation
            assert result.prefix == prefix
            assert result.command == command
            assert result.mention == mention
            assert result.args == args
            
        except CommandException:
            # Should only fail if text doesn't have the right structure
            # Let's verify this is a legitimate failure
            assert " " not in text or args is not None
    
    @given(st.text(min_size=1, max_size=200))
    def test_extract_command_no_crash(self, text):
        """Test that extract_command doesn't crash on arbitrary input"""
        cmd_filter = Command("test")
        
        try:
            result = cmd_filter.extract_command(text)
            # If successful, verify basic invariants
            assert isinstance(result, CommandObject)
            assert result.prefix is not None
            assert result.command is not None
            assert len(result.prefix) == 1
            
        except CommandException:
            # Expected for malformed commands
            pass
    
    @given(
        command=command_names,
        args=st.text(min_size=1, max_size=100)
    )
    def test_extract_command_args_preservation(self, command, args):
        """Test that arguments are preserved correctly"""
        cmd_filter = Command("test")
        
        # Create text with arguments containing spaces
        text = f"/{command} {args}"
        
        result = cmd_filter.extract_command(text)
        
        # Arguments should be preserved exactly
        assert result.args == args
        assert result.command == command


class TestCommandValidation:
    """Test command validation methods"""
    
    @given(
        commands=st.lists(command_names, min_size=1, max_size=5, unique=True),
        test_command=command_names,
        ignore_case=st.booleans()
    )
    def test_validate_command_case_sensitivity(self, commands, test_command, ignore_case):
        """Test case sensitivity in command validation"""
        cmd_filter = Command(*commands, ignore_case=ignore_case)
        
        # Create a command object
        cmd_obj = CommandObject(
            prefix="/",
            command=test_command,
            mention=None,
            args=None
        )
        
        try:
            result = cmd_filter.validate_command(cmd_obj)
            
            # Should succeed if command matches
            if ignore_case:
                assert any(test_command.casefold() == cmd.casefold() for cmd in commands)
            else:
                assert test_command in commands
                
        except CommandException:
            # Should fail if command doesn't match
            if ignore_case:
                assert all(test_command.casefold() != cmd.casefold() for cmd in commands)
            else:
                assert test_command not in commands
    
    @given(
        prefix=command_prefixes,
        allowed_prefixes=st.text(min_size=1, max_size=5)
    )
    def test_validate_prefix(self, prefix, allowed_prefixes):
        """Test prefix validation"""
        cmd_filter = Command("test", prefix=allowed_prefixes)
        
        cmd_obj = CommandObject(
            prefix=prefix,
            command="test",
            mention=None,
            args=None
        )
        
        try:
            cmd_filter.validate_prefix(cmd_obj)
            # Should succeed only if prefix is in allowed
            assert prefix in allowed_prefixes
        except CommandException:
            # Should fail if prefix not allowed
            assert prefix not in allowed_prefixes


class TestCommandObjectInvariants:
    """Test CommandObject structure invariants"""
    
    @given(
        prefix=st.text(min_size=1, max_size=10),
        command=st.text(min_size=1, max_size=50),
        mention=st.one_of(st.none(), st.text(min_size=1, max_size=50)),
        args=st.one_of(st.none(), st.text(min_size=1, max_size=200))
    )
    def test_command_object_creation(self, prefix, command, mention, args):
        """Test CommandObject maintains its structure"""
        
        cmd_obj = CommandObject(
            prefix=prefix,
            command=command,
            mention=mention,
            args=args
        )
        
        # Verify all fields are preserved
        assert cmd_obj.prefix == prefix
        assert cmd_obj.command == command  
        assert cmd_obj.mention == mention
        assert cmd_obj.args == args
        
        # Test the magic property
        if mention:
            assert cmd_obj.magic == command + "@" + mention
        else:
            assert cmd_obj.magic == command


class TestCommandRegexpPatterns:
    """Test Command filter with regexp patterns"""
    
    @given(
        pattern_str=st.from_regex(r"[a-z]+", fullmatch=True),
        test_command=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20)
    )
    def test_regexp_command_matching(self, pattern_str, test_command):
        """Test that regexp patterns work correctly"""
        import re
        
        pattern = re.compile(pattern_str)
        cmd_filter = Command(pattern)
        
        cmd_obj = CommandObject(
            prefix="/",
            command=test_command,
            mention=None,
            args=None
        )
        
        try:
            result = cmd_filter.validate_command(cmd_obj)
            # Should succeed if pattern matches
            assert pattern.match(test_command) is not None
            # Should have regexp_match set
            assert result.regexp_match is not None
            
        except CommandException:
            # Should fail if pattern doesn't match
            assert pattern.match(test_command) is None


class TestCommandRoundTrip:
    """Test round-trip properties of command parsing"""
    
    @given(
        prefix=command_prefixes,
        command=command_names,
        mention=st.one_of(
            st.none(),
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", 
                   min_size=5, max_size=20)
        ),
        args=st.one_of(
            st.none(),
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and "\n" not in x)
        )
    )
    def test_command_reconstruction(self, prefix, command, mention, args):
        """Test that we can reconstruct the original text from parsed command"""
        cmd_filter = Command("test")
        
        # Build original text
        original = prefix + command
        if mention:
            original += "@" + mention
        if args:
            original += " " + args
            
        # Parse it
        parsed = cmd_filter.extract_command(original)
        
        # Reconstruct
        reconstructed = parsed.prefix + parsed.command
        if parsed.mention:
            reconstructed += "@" + parsed.mention
        if parsed.args:
            reconstructed += " " + parsed.args
            
        # Should match original
        assert reconstructed == original