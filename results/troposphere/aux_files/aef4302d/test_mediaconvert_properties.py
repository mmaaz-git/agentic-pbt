#!/usr/bin/env python3
"""Property-based tests for troposphere.mediaconvert module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.mediaconvert as mc
from troposphere import AWSProperty, AWSObject

# Test 1: Required field validation property
# Evidence: JobTemplate.props shows SettingsJson is required (True flag)
# Property: Creating a JobTemplate and calling to_dict() without SettingsJson should raise ValueError
def test_required_field_validation():
    """Test that required fields are enforced during validation"""
    # JobTemplate requires SettingsJson
    jt = mc.JobTemplate("TestTemplate")
    try:
        jt.to_dict()  # This should fail
        assert False, "Should have raised ValueError for missing required field"
    except ValueError as e:
        assert "SettingsJson" in str(e)
        assert "required" in str(e)
    
    # Preset also requires SettingsJson
    preset = mc.Preset("TestPreset")  
    try:
        preset.to_dict()
        assert False, "Should have raised ValueError for missing required field"
    except ValueError as e:
        assert "SettingsJson" in str(e)
        assert "required" in str(e)
    
    # AccelerationSettings requires Mode
    acc = mc.AccelerationSettings()
    try:
        acc.to_dict()
        assert False, "Should have raised ValueError for missing required field" 
    except ValueError as e:
        assert "Mode" in str(e)
        assert "required" in str(e)

# Test 2: Integer validator property
# Evidence: Priority and WaitMinutes use integer validator from troposphere.validators
# Property: Setting integer fields to non-integer values should fail
@given(value=st.one_of(
    st.text(min_size=1),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_integer_validation(value):
    """Test that integer fields reject non-integer values"""
    assume(not isinstance(value, int))
    assume(not isinstance(value, bool))  # bool is subclass of int in Python
    
    # Try to convert to int - if it succeeds, skip this test case
    try:
        int(value)
        assume(False)  # Skip values that can be converted to int
    except (ValueError, TypeError):
        pass  # This is what we want to test
    
    # Test Priority field on JobTemplate
    jt = mc.JobTemplate("Test", SettingsJson={})
    try:
        jt.Priority = value
        assert False, f"Should reject non-integer value {value!r}"
    except (ValueError, TypeError):
        pass  # Expected
    
    # Test WaitMinutes on HopDestination  
    hop = mc.HopDestination()
    try:
        hop.WaitMinutes = value
        assert False, f"Should reject non-integer value {value!r}"
    except (ValueError, TypeError):
        pass  # Expected

# Test 3: Serialization round-trip property
# Evidence: BaseAWSObject has to_dict() and from_dict() methods
# Property: to_dict() -> from_dict() should produce equivalent object
@given(
    name=st.text(alphabet=st.characters(whitelist_categories=["L", "N"]), min_size=1, max_size=100),
    settings_json=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.text(), st.integers(), st.booleans(), st.none()),
        max_size=10
    ),
    priority=st.one_of(st.none(), st.integers(min_value=-100, max_value=100)),
    category=st.one_of(st.none(), st.text(max_size=50)),
    description=st.one_of(st.none(), st.text(max_size=200))
)
def test_jobtemplate_serialization_roundtrip(name, settings_json, priority, category, description):
    """Test that JobTemplate survives to_dict -> from_dict round trip"""
    
    # Create original object
    kwargs = {"SettingsJson": settings_json}
    if priority is not None:
        kwargs["Priority"] = priority
    if category is not None:
        kwargs["Category"] = category
    if description is not None:
        kwargs["Description"] = description
    
    original = mc.JobTemplate(name, **kwargs)
    
    # Serialize to dict
    serialized = original.to_dict()
    
    # Deserialize back
    properties = serialized.get("Properties", {})
    restored = mc.JobTemplate.from_dict(name, properties)
    
    # Compare
    assert original.title == restored.title
    assert original.to_dict() == restored.to_dict()

# Test 4: Property type consistency
# Evidence: props dict specifies expected types for each property
# Property: Properties should maintain their type after assignment  
@given(
    mode=st.text(min_size=1, max_size=50)
)
def test_acceleration_settings_mode_type(mode):
    """Test that AccelerationSettings Mode property maintains string type"""
    acc = mc.AccelerationSettings(Mode=mode)
    
    # The value should be stored as provided
    assert acc.Mode == mode
    assert isinstance(acc.Mode, str)
    
    # Should serialize correctly
    result = acc.to_dict()
    assert result["Mode"] == mode

# Test 5: List property handling
# Evidence: HopDestinations is defined as ([HopDestination], False)
# Property: List properties should properly handle list inputs
@given(
    hop_destinations=st.lists(
        st.builds(
            dict,
            Priority=st.integers(min_value=0, max_value=10),
            Queue=st.text(min_size=1, max_size=50),
            WaitMinutes=st.integers(min_value=0, max_value=60)
        ),
        max_size=5
    )
)  
def test_jobtemplate_hop_destinations(hop_destinations):
    """Test that JobTemplate properly handles HopDestinations list"""
    
    # Convert dicts to HopDestination objects
    hop_objects = []
    for hop_dict in hop_destinations:
        hop = mc.HopDestination(**hop_dict)
        hop_objects.append(hop)
    
    # Create JobTemplate with HopDestinations
    jt = mc.JobTemplate(
        "TestTemplate",
        SettingsJson={},
        HopDestinations=hop_objects
    )
    
    # Verify the list is stored correctly
    assert len(jt.HopDestinations) == len(hop_destinations)
    
    # Verify serialization
    result = jt.to_dict()
    props = result.get("Properties", {})
    
    if hop_destinations:  # Only check if we have destinations
        assert "HopDestinations" in props
        assert len(props["HopDestinations"]) == len(hop_destinations)
        
        # Verify each destination
        for i, hop_dict in enumerate(hop_destinations):
            serialized_hop = props["HopDestinations"][i]
            for key, value in hop_dict.items():
                assert serialized_hop[key] == value

if __name__ == "__main__":
    # Run the tests
    print("Testing required field validation...")
    test_required_field_validation()
    print("✓ Required field validation works correctly")
    
    print("\nTesting integer validation...")
    test_integer_validation()
    print("✓ Integer validation works correctly")
    
    print("\nTesting serialization round-trip...")
    test_jobtemplate_serialization_roundtrip()
    print("✓ Serialization round-trip works correctly")
    
    print("\nTesting acceleration settings mode type...")
    test_acceleration_settings_mode_type()
    print("✓ Mode type consistency works correctly")
    
    print("\nTesting hop destinations list handling...")
    test_jobtemplate_hop_destinations()
    print("✓ List property handling works correctly")
    
    print("\nAll tests passed!")