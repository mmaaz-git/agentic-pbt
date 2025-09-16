#!/usr/bin/env python3
"""Property-based tests for troposphere.lex module."""

import sys
import json
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.lex as lex
from troposphere import AWSProperty, AWSObject, Tags
from troposphere.validators import integer, double, boolean


# Test 1: Required field validation
@given(
    enabled=st.booleans(),
    description=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_dialog_code_hook_required_field(enabled, description):
    """Test that DialogCodeHookSetting enforces required 'Enabled' field."""
    if enabled is None:
        with pytest.raises((TypeError, ValueError)):
            hook = lex.DialogCodeHookSetting()
    else:
        hook = lex.DialogCodeHookSetting(Enabled=enabled)
        assert hook.properties['Enabled'] == enabled
        

# Test 2: Type validation for integer properties
@given(
    weight=st.one_of(
        st.integers(min_value=-2**63, max_value=2**63-1),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(alphabet='0123456789', min_size=1, max_size=20),
        st.none()
    )
)
def test_custom_vocabulary_item_weight_type(weight):
    """Test that CustomVocabularyItem.Weight validates integer types properly."""
    item = lex.CustomVocabularyItem(Phrase="test")
    
    if weight is not None:
        try:
            # Integer validator should accept integers and numeric strings
            validated = integer(weight)
            item.properties['Weight'] = validated
            assert isinstance(item.properties['Weight'], int)
        except (TypeError, ValueError):
            # Should fail for non-numeric values
            assert not isinstance(weight, (int, str)) or (isinstance(weight, str) and not weight.isdigit())


# Test 3: to_dict() round-trip property
@given(
    text=st.text(min_size=1, max_size=100),
    value=st.text(min_size=1, max_size=100)
)
def test_button_to_dict_round_trip(text, value):
    """Test that Button objects can be serialized and maintain their properties."""
    button = lex.Button(Text=text, Value=value)
    
    # Serialize to dict
    button_dict = button.to_dict()
    
    # Check that required fields are preserved
    assert button_dict['Text'] == text
    assert button_dict['Value'] == value
    
    # Create new button from dict
    button2 = lex.Button(**button_dict)
    assert button2.properties['Text'] == text
    assert button2.properties['Value'] == value


# Test 4: Boolean validator edge cases
@given(
    value=st.one_of(
        st.booleans(),
        st.integers(min_value=0, max_value=1),
        st.text(alphabet='01', min_size=1, max_size=1),
        st.sampled_from(['true', 'false', 'True', 'False', 'TRUE', 'FALSE']),
        st.sampled_from(['yes', 'no', 'on', 'off']),
        st.none()
    )
)
def test_boolean_validator_edge_cases(value):
    """Test that boolean validator handles various input types correctly."""
    if value is None:
        # None should be handled appropriately
        setting = lex.DialogCodeHookSetting(Enabled=True)
        assert setting.properties['Enabled'] is True
    else:
        try:
            validated = boolean(value)
            assert isinstance(validated, bool)
            
            # Check expected conversions
            if value in [True, 1, '1', 'true', 'True', 'TRUE']:
                assert validated is True
            elif value in [False, 0, '0', 'false', 'False', 'FALSE']:
                assert validated is False
        except (TypeError, ValueError):
            # Should fail for invalid boolean representations
            assert value not in [True, False, 0, 1, '0', '1', 'true', 'false', 'True', 'False', 'TRUE', 'FALSE']


# Test 5: Nested property structure validation
@given(
    message_value=st.text(min_size=1, max_size=1000),
    allow_interrupt=st.booleans()
)
def test_message_group_nested_structure(message_value, allow_interrupt):
    """Test that MessageGroup correctly handles nested Message objects."""
    # Create nested structure
    plain_text = lex.PlainTextMessage(Value=message_value)
    message = lex.Message(PlainTextMessage=plain_text)
    message_group = lex.MessageGroup(Message=message)
    
    # Serialize to dict
    mg_dict = message_group.to_dict()
    
    # Verify nested structure is preserved
    assert 'Message' in mg_dict
    assert 'PlainTextMessage' in mg_dict['Message']
    assert mg_dict['Message']['PlainTextMessage']['Value'] == message_value
    
    # Test with variations
    variations = [lex.Message(PlainTextMessage=lex.PlainTextMessage(Value=f"var_{i}")) for i in range(3)]
    message_group_with_vars = lex.MessageGroup(Message=message, Variations=variations)
    mg_vars_dict = message_group_with_vars.to_dict()
    
    assert len(mg_vars_dict.get('Variations', [])) == 3
    for i, var in enumerate(mg_vars_dict['Variations']):
        assert var['PlainTextMessage']['Value'] == f"var_{i}"


# Test 6: Property constraints and ranges
@given(
    priority=st.one_of(
        st.integers(min_value=-2**31, max_value=2**31-1),
        st.integers(min_value=2**31, max_value=2**63-1),
        st.integers(min_value=-2**63, max_value=-2**31-1)
    ),
    slot_name=st.text(min_size=1, max_size=100)
)
def test_slot_priority_integer_bounds(priority, slot_name):
    """Test that SlotPriority handles various integer ranges."""
    slot_priority = lex.SlotPriority(Priority=priority, SlotName=slot_name)
    
    # Should store the integer value
    assert slot_priority.properties['Priority'] == priority
    assert slot_priority.properties['SlotName'] == slot_name
    
    # to_dict should preserve the value
    sp_dict = slot_priority.to_dict()
    assert sp_dict['Priority'] == priority


# Test 7: Optional vs Required property handling
@given(
    title=st.text(min_size=1, max_size=100),
    subtitle=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    image_url=st.one_of(st.none(), st.text(min_size=1, max_size=200))
)
def test_image_response_card_optional_fields(title, subtitle, image_url):
    """Test that ImageResponseCard correctly handles optional vs required fields."""
    # Title is required
    card = lex.ImageResponseCard(Title=title)
    assert card.properties['Title'] == title
    
    # Optional fields
    if subtitle is not None:
        card.properties['Subtitle'] = subtitle
    if image_url is not None:
        card.properties['ImageUrl'] = image_url
    
    card_dict = card.to_dict()
    assert card_dict['Title'] == title
    
    # Optional fields should only be in dict if set
    if subtitle is not None:
        assert card_dict.get('Subtitle') == subtitle
    else:
        assert 'Subtitle' not in card_dict
    
    if image_url is not None:
        assert card_dict.get('ImageUrl') == image_url
    else:
        assert 'ImageUrl' not in card_dict


# Test 8: Double/float validator edge cases
@given(
    threshold=st.one_of(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        st.floats(allow_nan=True, allow_infinity=True),
        st.integers(min_value=0, max_value=1),
        st.text(alphabet='0123456789.', min_size=1, max_size=10).filter(lambda x: x.count('.') <= 1)
    )
)
def test_nlu_confidence_threshold_validation(threshold):
    """Test NluConfidenceThreshold double validation in BotLocale."""
    try:
        validated = double(threshold)
        # Should be converted to float
        assert isinstance(validated, float)
        
        # Check for special values
        if validated != validated:  # NaN check
            # NaN might be rejected by AWS
            pass
        elif validated == float('inf') or validated == float('-inf'):
            # Infinity might be rejected by AWS
            pass
    except (TypeError, ValueError):
        # Should fail for non-numeric values
        pass


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])