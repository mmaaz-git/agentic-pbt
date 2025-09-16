"""Property-based tests for aiogram.enums"""

import enum
from hypothesis import given, strategies as st, assume
import pytest
from aiogram.enums import (
    ChatType, ParseMode, ContentType, UpdateType, 
    ChatAction, TopicIconColor, DiceEmoji, Currency,
    PollType, StickerFormat, ChatMemberStatus
)


# Get all string-based enums and int-based enums
def get_all_enums():
    """Get all enum classes from aiogram.enums"""
    import aiogram.enums
    import inspect
    
    str_enums = []
    int_enums = []
    
    for name in dir(aiogram.enums):
        obj = getattr(aiogram.enums, name)
        if inspect.isclass(obj) and issubclass(obj, enum.Enum):
            if issubclass(obj, str):
                str_enums.append(obj)
            elif issubclass(obj, int):
                int_enums.append(obj)
    
    return str_enums, int_enums


str_enums, int_enums = get_all_enums()


# Property 1: String enum members equal their string values
@given(st.sampled_from(str_enums))
def test_str_enum_value_equality(enum_class):
    """String enum members should equal their string values"""
    for member in enum_class:
        # The member should be equal to its value as a string
        assert member == member.value
        assert str(member) == member.value
        assert isinstance(member, str)
        assert isinstance(member.value, str)


# Property 2: String operations preserve value
@given(st.sampled_from(str_enums))
def test_str_enum_string_operations(enum_class):
    """String operations on enum members should work like normal strings"""
    for member in enum_class:
        # Upper/lower operations
        assert member.upper() == member.value.upper()
        assert member.lower() == member.value.lower()
        
        # String methods return correct types
        assert isinstance(member.upper(), str)
        assert isinstance(member.lower(), str)
        
        # Length should match
        assert len(member) == len(member.value)
        
        # Slicing should work
        if len(member) > 0:
            assert member[0] == member.value[0]
            assert member[-1] == member.value[-1]
            assert member[:2] == member.value[:2]


# Property 3: Round-trip from value to enum
@given(st.sampled_from(str_enums))
def test_str_enum_round_trip_from_value(enum_class):
    """Should be able to get enum member from its value"""
    for member in enum_class:
        # Should be able to get member from value using functional call
        retrieved = enum_class(member.value)
        assert retrieved == member
        assert retrieved is member  # Should be the same object


# Property 4: Integer enum members equal their int values
@given(st.sampled_from(int_enums))
def test_int_enum_value_equality(enum_class):
    """Integer enum members should equal their integer values"""
    for member in enum_class:
        assert member == member.value
        assert int(member) == member.value
        assert isinstance(member, int)
        assert isinstance(member.value, int)


# Property 5: Integer operations on int enums
@given(st.sampled_from(int_enums))
def test_int_enum_integer_operations(enum_class):
    """Integer operations on int enum members should work"""
    for member in enum_class:
        # Basic arithmetic should work
        assert member + 0 == member.value
        assert member * 1 == member.value
        assert member - 0 == member.value
        
        # Bitwise operations
        assert member & member == member.value
        assert member | 0 == member.value
        assert member ^ 0 == member.value


# Property 6: TopicIconColor values are valid RGB colors
def test_topic_icon_color_valid_rgb():
    """TopicIconColor values should be valid RGB hex colors"""
    for color in TopicIconColor:
        # RGB values should be in range 0x000000 to 0xFFFFFF
        assert 0x000000 <= color.value <= 0xFFFFFF
        assert isinstance(color.value, int)
        
        # Check individual RGB components
        red = (color.value >> 16) & 0xFF
        green = (color.value >> 8) & 0xFF
        blue = color.value & 0xFF
        
        assert 0 <= red <= 255
        assert 0 <= green <= 255
        assert 0 <= blue <= 255


# Property 7: Enum members are hashable
@given(st.sampled_from(str_enums + int_enums))
def test_enum_hashability(enum_class):
    """All enum members should be hashable"""
    for member in enum_class:
        # Should be able to hash
        hash_val = hash(member)
        assert isinstance(hash_val, int)
        
        # Should be usable in sets and dicts
        test_set = {member}
        assert member in test_set
        
        test_dict = {member: "value"}
        assert member in test_dict


# Property 8: Unique values within each enum
@given(st.sampled_from(str_enums + int_enums))
def test_unique_values_in_enum(enum_class):
    """All values within an enum should be unique"""
    values = [member.value for member in enum_class]
    assert len(values) == len(set(values))


# Property 9: Unique names within each enum
@given(st.sampled_from(str_enums + int_enums))
def test_unique_names_in_enum(enum_class):
    """All names within an enum should be unique"""
    names = [member.name for member in enum_class]
    assert len(names) == len(set(names))


# Property 10: Enum comparison with wrong types
@given(st.sampled_from(str_enums))
def test_str_enum_comparison_with_wrong_case(enum_class):
    """Test that string enums are case-sensitive in comparisons"""
    for member in enum_class:
        # Should not equal different case versions
        if member.value != member.value.upper():
            assert member != member.value.upper()
        if member.value != member.value.lower():
            assert member != member.value.lower()


# Property 11: ParseMode special case - mixed case preservation
def test_parse_mode_case_preservation():
    """ParseMode should preserve specific case patterns"""
    assert ParseMode.MARKDOWN_V2.value == "MarkdownV2"
    assert ParseMode.MARKDOWN.value == "Markdown"
    assert ParseMode.HTML.value == "HTML"
    
    # These should not equal lowercase versions
    assert ParseMode.MARKDOWN_V2 != "markdownv2"
    assert ParseMode.MARKDOWN != "markdown"
    assert ParseMode.HTML != "html"


# Property 12: Test enum membership operations
@given(st.sampled_from(str_enums + int_enums))
def test_enum_membership(enum_class):
    """Test 'in' operator and membership checks"""
    all_members = list(enum_class)
    
    for member in all_members:
        # Member should be in the enum
        assert member in enum_class
        
        # Value lookup should work
        found = False
        for m in enum_class:
            if m.value == member.value:
                found = True
                break
        assert found


# Property 13: String enum concatenation
@given(st.sampled_from(str_enums))
def test_str_enum_concatenation(enum_class):
    """String concatenation should work for string enums"""
    for member in enum_class:
        # Should be able to concatenate
        result = member + "_suffix"
        assert result == member.value + "_suffix"
        assert isinstance(result, str)
        
        result = "prefix_" + member
        assert result == "prefix_" + member.value
        assert isinstance(result, str)


# Property 14: Immutability test
@given(st.sampled_from(str_enums + int_enums))
def test_enum_immutability(enum_class):
    """Enum values should be immutable"""
    for member in enum_class:
        original_value = member.value
        original_name = member.name
        
        # Try to verify immutability (can't directly modify)
        # Value and name should remain the same
        assert member.value == original_value
        assert member.name == original_name