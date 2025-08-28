"""
Property-based tests for troposphere.controltower module
Testing properties that the code explicitly claims to have:
1. Round-trip property: from_dict/to_dict should be inverse operations
2. Title validation: Titles must be alphanumeric (regex validation)
3. Required field validation: Missing required fields should raise ValueError
4. Type validation: Wrong types should raise TypeError
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import re
from hypothesis import given, strategies as st, assume
from troposphere.controltower import (
    EnabledBaseline, EnabledControl, EnabledControlParameter,
    LandingZone, Parameter
)
from troposphere import Tags


# Strategies for generating valid data
def valid_title_strategy():
    """Generate valid titles that match the alphanumeric regex from the code"""
    return st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), 
                   min_size=1, max_size=255)

def valid_string_strategy():
    """Generate reasonable strings for AWS identifiers"""
    return st.text(min_size=1, max_size=100)

def valid_dict_strategy():
    """Generate simple dictionaries for Manifest property"""
    return st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=0,
        max_size=10
    )


# Test 1: Round-trip property for Parameter class
@given(
    key=st.one_of(st.none(), valid_string_strategy()),
    value=st.one_of(st.none(), valid_string_strategy())
)
def test_parameter_round_trip(key, value):
    """Test that Parameter survives from_dict -> to_dict round trip"""
    # Create parameter with optional fields
    kwargs = {}
    if key is not None:
        kwargs['Key'] = key
    if value is not None:
        kwargs['Value'] = value
    
    # Create the parameter
    param = Parameter(**kwargs)
    
    # Convert to dict and back
    param_dict = param.to_dict()
    reconstructed = Parameter.from_dict(None, param_dict)
    
    # Check equality via to_dict since objects don't implement __eq__ properly
    assert reconstructed.to_dict() == param_dict


# Test 2: Round-trip property for EnabledControlParameter
@given(
    key=valid_string_strategy(),
    value=st.one_of(
        st.text(),
        st.integers(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(min_size=1), st.text())
    )
)
def test_enabled_control_parameter_round_trip(key, value):
    """Test EnabledControlParameter round-trip with required fields"""
    param = EnabledControlParameter(Key=key, Value=value)
    param_dict = param.to_dict()
    reconstructed = EnabledControlParameter.from_dict(None, param_dict)
    assert reconstructed.to_dict() == param_dict


# Test 3: Title validation property
@given(title=st.text())
def test_title_validation(title):
    """Test that title validation works as documented"""
    # The code states titles must be alphanumeric
    valid_pattern = re.compile(r"^[a-zA-Z0-9]+$")
    
    if valid_pattern.match(title):
        # Should not raise
        try:
            baseline = EnabledBaseline(
                title,
                BaselineIdentifier="id",
                BaselineVersion="1.0",
                TargetIdentifier="target"
            )
            assert baseline.title == title
        except ValueError as e:
            # This would be a bug - valid title rejected
            assert False, f"Valid title '{title}' was rejected: {e}"
    else:
        # Should raise ValueError for invalid titles
        try:
            baseline = EnabledBaseline(
                title,
                BaselineIdentifier="id", 
                BaselineVersion="1.0",
                TargetIdentifier="target"
            )
            # This is a bug - invalid title was accepted
            assert False, f"Invalid title '{title}' was accepted but should have been rejected"
        except ValueError:
            # Expected behavior
            pass


# Test 4: Required field validation for EnabledBaseline
@given(
    baseline_id=st.one_of(st.none(), valid_string_strategy()),
    baseline_version=st.one_of(st.none(), valid_string_strategy()),
    target_id=st.one_of(st.none(), valid_string_strategy()),
    include_optional=st.booleans()
)
def test_enabled_baseline_required_fields(baseline_id, baseline_version, target_id, include_optional):
    """Test that required fields are enforced as documented"""
    kwargs = {}
    
    # Add fields if provided
    if baseline_id is not None:
        kwargs['BaselineIdentifier'] = baseline_id
    if baseline_version is not None:
        kwargs['BaselineVersion'] = baseline_version  
    if target_id is not None:
        kwargs['TargetIdentifier'] = target_id
    
    # All three fields are required according to props definition
    all_required_present = (baseline_id is not None and 
                           baseline_version is not None and
                           target_id is not None)
    
    baseline = EnabledBaseline("TestBaseline", validation=False, **kwargs)
    
    if all_required_present:
        # Should successfully convert to dict with validation
        try:
            result = baseline.to_dict(validation=True)
            assert 'Properties' in result
        except ValueError as e:
            # This would be a bug - all required fields present but validation failed
            assert False, f"All required fields present but validation failed: {e}"
    else:
        # Should raise ValueError when validation is enabled
        try:
            baseline.to_dict(validation=True)
            # This is a bug - validation should have failed
            assert False, "Missing required fields but validation passed"
        except ValueError as e:
            # Expected - should mention the missing required field
            assert "required" in str(e).lower()


# Test 5: LandingZone manifest and version are required
@given(
    manifest=st.one_of(st.none(), valid_dict_strategy()),
    version=st.one_of(st.none(), valid_string_strategy())
)
def test_landing_zone_required_fields(manifest, version):
    """Test LandingZone required field validation"""
    kwargs = {}
    if manifest is not None:
        kwargs['Manifest'] = manifest
    if version is not None:
        kwargs['Version'] = version
    
    lz = LandingZone("TestLZ", validation=False, **kwargs)
    
    all_required = manifest is not None and version is not None
    
    if all_required:
        try:
            result = lz.to_dict(validation=True)
            assert 'Properties' in result
        except ValueError:
            assert False, "All required fields present but validation failed"
    else:
        try:
            lz.to_dict(validation=True)
            assert False, "Missing required fields but validation passed"
        except ValueError as e:
            assert "required" in str(e).lower()


# Test 6: JSON serialization round-trip
@given(
    baseline_id=valid_string_strategy(),
    baseline_version=valid_string_strategy(),
    target_id=valid_string_strategy()
)
def test_json_serialization_round_trip(baseline_id, baseline_version, target_id):
    """Test that JSON serialization preserves all data"""
    baseline = EnabledBaseline(
        "TestBaseline",
        BaselineIdentifier=baseline_id,
        BaselineVersion=baseline_version,
        TargetIdentifier=target_id
    )
    
    # Convert to JSON and parse back
    json_str = baseline.to_json(validation=False)
    parsed = json.loads(json_str)
    
    # Reconstruct from parsed dict
    properties = parsed.get('Properties', {})
    reconstructed = EnabledBaseline.from_dict("TestBaseline", properties)
    
    # Should produce the same JSON
    assert reconstructed.to_json(validation=False) == json_str