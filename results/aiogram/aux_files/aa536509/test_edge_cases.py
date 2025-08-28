"""Test specific edge cases for command parsing"""

from aiogram.filters.command import Command, CommandObject


def test_empty_command():
    """Test command with empty command name"""
    cmd_filter = Command("test")
    
    # Test with just prefix
    text = "/"
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted from '/': {cmd_obj}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
    except Exception as e:
        print(f"Failed on '/': {e}")
    
    # Test with prefix and space
    text = "/ "
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted from '/ ': {cmd_obj}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
    except Exception as e:
        print(f"Failed on '/ ': {e}")
    
    # Test with prefix and args but no command
    text = "/ args here"
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted from '/ args here': {cmd_obj}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
    except Exception as e:
        print(f"Failed on '/ args here': {e}")


def test_special_characters():
    """Test commands with special characters"""
    cmd_filter = Command("test")
    
    # Test with newline in args
    text = "/cmd arg1\narg2"
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted from '/cmd arg1\\narg2': {cmd_obj}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
        print(f"  Match: {cmd_obj.text == text}")
    except Exception as e:
        print(f"Failed on newline: {e}")
    
    # Test with tab in args  
    text = "/cmd\targs"
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted from '/cmd\\targs': {cmd_obj}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
        print(f"  Match: {cmd_obj.text == text}")
    except Exception as e:
        print(f"Failed on tab: {e}")
    
    # Test with multiple @ symbols
    text = "/cmd@user1@user2 args"
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted from '/cmd@user1@user2 args': {cmd_obj}")
        print(f"  Command: {cmd_obj.command!r}")
        print(f"  Mention: {cmd_obj.mention!r}")
        print(f"  Args: {cmd_obj.args!r}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
    except Exception as e:
        print(f"Failed on multiple @: {e}")


def test_unicode():
    """Test with unicode characters"""
    cmd_filter = Command("test")
    
    # Test with emoji in args
    text = "/cmd 😀 test"
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted emoji args: {cmd_obj}")
        print(f"  Args: {cmd_obj.args!r}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
        print(f"  Match: {cmd_obj.text == text}")
    except Exception as e:
        print(f"Failed on emoji: {e}")
    
    # Test with unicode in command
    text = "/café test"
    try:
        cmd_obj = cmd_filter.extract_command(text)
        print(f"Extracted unicode command: {cmd_obj}")
        print(f"  Command: {cmd_obj.command!r}")
        print(f"  Reconstructed: {cmd_obj.text!r}")
    except Exception as e:
        print(f"Failed on unicode command: {e}")


if __name__ == "__main__":
    print("=== Testing empty commands ===")
    test_empty_command()
    print("\n=== Testing special characters ===")
    test_special_characters()
    print("\n=== Testing unicode ===")
    test_unicode()