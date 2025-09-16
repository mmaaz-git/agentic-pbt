#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.mediaconvert as mc
from troposphere import Template

# Property 1: Title validation - alphanumeric only
# Evidence: valid_names regex in __init__.py line 70: r"^[a-zA-Z0-9]+$"
@given(title=st.text())
@settings(max_examples=100)
def test_title_validation(title):
    """Test that non-alphanumeric titles are rejected"""
    # Check if title is alphanumeric
    is_alphanumeric = title and title.isalnum()
    
    try:
        jt = mc.JobTemplate(title, SettingsJson={})
        # If we got here, title was accepted
        if not is_alphanumeric:
            print(f"BUG: Non-alphanumeric title accepted: {title!r}")
            return False
    except ValueError as e:
        # Title was rejected
        if is_alphanumeric:
            print(f"BUG: Alphanumeric title rejected: {title!r}")
            return False
        if "alphanumeric" not in str(e):
            print(f"Unexpected error for {title!r}: {e}")
    
    return True

# Property 2: Integer validator edge cases
# Evidence: integer validator in validators/__init__.py allows strings that can convert to int
@given(value=st.one_of(
    st.text(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.booleans()
))
def test_integer_validator_edge_cases(value):
    """Test integer validator with various input types"""
    jt = mc.JobTemplate("Test", SettingsJson={})
    
    # Check if value can be converted to int
    can_convert = False
    try:
        int(value)
        can_convert = True
    except (ValueError, TypeError):
        pass
    
    # Now test setting Priority
    try:
        jt.Priority = value
        if not can_convert:
            print(f"BUG: Non-integer value accepted: {value!r} (type: {type(value).__name__})")
            return False
    except (ValueError, TypeError):
        if can_convert:
            print(f"BUG: Convertible value rejected: {value!r} (type: {type(value).__name__})")
            return False
    
    return True

# Property 3: Required field bypass
# Evidence: validation parameter can disable validation
@given(
    title=st.text(alphabet=st.characters(whitelist_categories=["L", "N"]), min_size=1, max_size=50),
    validation=st.booleans()
)
def test_required_field_bypass(title, validation):
    """Test that validation parameter controls required field checking"""
    
    # Create without required SettingsJson
    jt = mc.JobTemplate(title, validation=validation)
    
    # Try to serialize
    try:
        result = jt.to_dict(validation=validation)
        if validation:
            print(f"BUG: to_dict() succeeded without required field when validation={validation}")
            return False
    except ValueError as e:
        if not validation:
            print(f"BUG: to_dict(validation=False) still enforced required field")
            return False
        if "SettingsJson" not in str(e):
            print(f"Unexpected error: {e}")
            return False
    
    return True

# Property 4: Template attachment
# Evidence: BaseAWSObject.__init__ adds resource to template if provided
@given(title=st.text(alphabet=st.characters(whitelist_categories=["L", "N"]), min_size=1, max_size=50))
def test_template_attachment(title):
    """Test that resources are automatically added to templates"""
    template = Template()
    
    # Create resource with template
    jt = mc.JobTemplate(title, template=template, SettingsJson={})
    
    # Check if resource was added to template
    if title not in template.resources:
        print(f"BUG: Resource {title!r} not added to template")
        return False
    
    if template.resources[title] != jt:
        print(f"BUG: Wrong resource added to template")
        return False
    
    return True

# Property 5: Props type enforcement for lists
# Evidence: __setattr__ checks list types in BaseAWSObject
@given(
    hop_data=st.lists(
        st.one_of(
            st.dictionaries(st.text(), st.text()),  # Valid: dict that becomes HopDestination
            st.text(),  # Invalid: string
            st.integers(),  # Invalid: integer
            st.none()  # Invalid: None
        ),
        min_size=1,
        max_size=5
    )
)
def test_list_property_type_enforcement(hop_data):
    """Test that list properties enforce correct types"""
    
    # Check if all items are valid (dicts or HopDestination objects)
    all_valid = all(isinstance(item, dict) for item in hop_data)
    
    jt = mc.JobTemplate("Test", SettingsJson={})
    
    # Convert valid dicts to HopDestination objects
    if all_valid:
        try:
            hop_objects = []
            for item in hop_data:
                # Only create if dict has valid structure
                if isinstance(item, dict):
                    hop = mc.HopDestination()
                    for k, v in item.items():
                        setattr(hop, k, v)
                    hop_objects.append(hop)
            jt.HopDestinations = hop_objects
            return True
        except:
            # Dict might not have valid structure
            return True
    else:
        # Test with mixed/invalid types
        try:
            jt.HopDestinations = hop_data
            # Find first invalid item
            first_invalid = next(item for item in hop_data if not isinstance(item, dict))
            print(f"BUG: List property accepted invalid type: {type(first_invalid).__name__}")
            return False
        except (TypeError, ValueError, AttributeError):
            # Expected to fail
            pass
    
    return True

# Run all tests
print("Running property-based tests with Hypothesis...")
print("\n1. Testing title validation...")
test_title_validation()

print("\n2. Testing integer validator edge cases...")
test_integer_validator_edge_cases()

print("\n3. Testing required field bypass...")
test_required_field_bypass()

print("\n4. Testing template attachment...")
test_template_attachment()

print("\n5. Testing list property type enforcement...")
test_list_property_type_enforcement()

print("\nAll property tests completed!")