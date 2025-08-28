"""Verify tab character handling bug"""

from aiogram.filters.command import Command, CommandObject


def test_tab_normalization():
    """Test that tabs are handled correctly in command parsing"""
    
    cmd_filter = Command("test")
    
    # Test various whitespace between command and args
    test_cases = [
        ("/cmd args", "single space"),
        ("/cmd  args", "double space"),
        ("/cmd\targs", "tab character"),
        ("/cmd\t\targs", "double tab"),
        ("/cmd \t args", "mixed space and tab"),
    ]
    
    for text, description in test_cases:
        try:
            cmd_obj = cmd_filter.extract_command(text)
            reconstructed = cmd_obj.text
            
            print(f"Test case: {description}")
            print(f"  Original:      {text!r}")
            print(f"  Command:       {cmd_obj.command!r}")
            print(f"  Args:          {cmd_obj.args!r}")
            print(f"  Reconstructed: {reconstructed!r}")
            print(f"  Match:         {reconstructed == text}")
            
            # Check if semantic meaning is preserved
            # (command and args are the same, only whitespace differs)
            if cmd_obj.command == "cmd" and cmd_obj.args == "args":
                print(f"  Semantic:      ✓ Preserves meaning")
            else:
                print(f"  Semantic:      ✗ Different meaning!")
            print()
            
        except Exception as e:
            print(f"Failed on {description}: {e}")
            print()


def test_real_world_scenario():
    """Test a realistic scenario where users might use tabs"""
    
    # Simulate a user copying command from a document with tabs
    user_input = "/start\tJohn Doe"
    
    cmd_filter = Command("start")
    cmd_obj = cmd_filter.extract_command(user_input)
    
    print("Real-world scenario: User copies command with tab")
    print(f"  User input:    {user_input!r}")
    print(f"  Parsed args:   {cmd_obj.args!r}")
    print(f"  Reconstructed: {cmd_obj.text!r}")
    
    # The semantic meaning is preserved (args = "John Doe")
    # but the exact formatting is lost
    assert cmd_obj.args == "John Doe"
    assert cmd_obj.text == "/start John Doe"
    
    print(f"  Args match:    {cmd_obj.args == 'John Doe'}")
    print(f"  Whitespace normalized: tab -> space")


if __name__ == "__main__":
    test_tab_normalization()
    print("=" * 50)
    test_real_world_scenario()