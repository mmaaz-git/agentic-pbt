"""Focused test demonstrating str() behavior inconsistency in aiogram enums"""

from aiogram.enums import ChatType, ParseMode, BotCommandScopeType, UpdateType


def test_str_enum_substitutability():
    """
    String enums that inherit from str should behave like strings.
    This includes str() returning the string value, not the enum representation.
    """
    
    # Test multiple string enums
    test_cases = [
        (ChatType.PRIVATE, "private"),
        (ParseMode.HTML, "HTML"),
        (BotCommandScopeType.DEFAULT, "default"),
        (UpdateType.MESSAGE, "message"),
    ]
    
    for enum_member, expected_value in test_cases:
        # These pass - the enum equals its value
        assert enum_member == expected_value
        assert isinstance(enum_member, str)
        
        # This fails - str() doesn't return the value
        actual_str = str(enum_member)
        print(f"str({enum_member!r}) = {actual_str!r}, expected {expected_value!r}")
        assert actual_str == expected_value, f"str() returned {actual_str!r} instead of {expected_value!r}"


def demonstrate_practical_impact():
    """Show how this could cause real issues in code"""
    
    # Scenario: Using enum in string formatting
    chat_type = ChatType.PRIVATE
    
    # Developer expects this to produce "Chat type: private"
    message = f"Chat type: {chat_type}"
    print(f"Formatted message: {message!r}")
    
    # But it actually produces "Chat type: ChatType.PRIVATE"
    assert message == "Chat type: private", f"Got {message!r}"


def demonstrate_json_serialization():
    """Show impact on JSON serialization"""
    import json
    
    data = {
        "chat_type": ChatType.PRIVATE,
        "parse_mode": ParseMode.HTML
    }
    
    # This will fail because enums aren't JSON serializable by default
    # But if they properly acted as strings, it would work
    try:
        json_str = json.dumps(data)
        print(f"JSON: {json_str}")
    except TypeError as e:
        print(f"JSON serialization failed: {e}")
        
        # Workaround needed
        data_with_str = {
            "chat_type": str(ChatType.PRIVATE),  # Returns "ChatType.PRIVATE" not "private"!
            "parse_mode": str(ParseMode.HTML),    # Returns "ParseMode.HTML" not "HTML"!
        }
        json_str = json.dumps(data_with_str)
        print(f"JSON with str(): {json_str}")
        
        # This produces wrong values!
        assert '"chat_type": "private"' in json_str, f"Wrong value in JSON: {json_str}"


if __name__ == "__main__":
    print("Testing str() behavior of aiogram string enums...\n")
    
    try:
        test_str_enum_substitutability()
    except AssertionError as e:
        print(f"✗ String substitutability test failed: {e}\n")
    
    try:
        demonstrate_practical_impact()
    except AssertionError as e:
        print(f"✗ Practical impact demo failed: {e}\n")
    
    try:
        demonstrate_json_serialization()
    except AssertionError as e:
        print(f"✗ JSON serialization demo failed: {e}\n")