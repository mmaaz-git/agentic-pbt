#!/usr/bin/env python3
"""Run property-based tests for troposphere using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import string
import traceback
from hypothesis import given, settings, strategies as st, assume

import troposphere
from troposphere import (
    AWSObject, AWSProperty, BaseAWSObject, Join, Split, Parameter, Tags, Template,
    encode_to_dict, valid_names
)

print(f"Testing Troposphere version: {troposphere.__version__}\n")
print("=" * 60)

# Store any bugs we find
bugs_found = []

# Test 1: Template resource limits
print("\nTest 1: Testing Template MAX_RESOURCES limit (should be 500)...")
@given(n_resources=st.integers(min_value=495, max_value=510))
@settings(max_examples=20, deadline=None)
def test_resources_limit(n_resources):
    template = Template()
    
    class DummyResource(AWSObject):
        resource_type = "AWS::Dummy::Resource"
        props = {}
    
    for i in range(min(n_resources, 500)):
        resource = DummyResource(f"Resource{i}")
        template.add_resource(resource)
    
    if n_resources > 500:
        try:
            resource = DummyResource(f"Resource{500}")
            template.add_resource(resource) 
            # Bug: Should have raised ValueError
            bugs_found.append(f"BUG: Template allowed {n_resources} resources (limit should be 500)")
        except ValueError as e:
            if "Maximum number of resources 500 reached" not in str(e):
                bugs_found.append(f"BUG: Wrong error message for resource limit: {e}")

try:
    test_resources_limit()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

# Test 2: Parameter title validation  
print("\nTest 2: Testing Parameter title validation (alphanumeric, max 255 chars)...")
@given(title=st.text(min_size=0, max_size=300))
@settings(max_examples=100, deadline=None)
def test_param_title(title):
    is_valid = (
        len(title) > 0 and 
        len(title) <= 255 and 
        valid_names.match(title) is not None
    )
    
    try:
        param = Parameter(title, Type="String")
        if not is_valid:
            bugs_found.append(f"BUG: Invalid title accepted: '{title}' (len={len(title)}, alphanumeric={bool(valid_names.match(title))})")
    except ValueError:
        if is_valid:
            bugs_found.append(f"BUG: Valid title rejected: '{title}'")

try:
    test_param_title()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

# Test 3: Tags addition associativity
print("\nTest 3: Testing Tags addition associativity...")
@given(
    tags1=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        st.text(min_size=0, max_size=20),
        min_size=0,
        max_size=3
    ),
    tags2=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        st.text(min_size=0, max_size=20),
        min_size=0,
        max_size=3
    ),
    tags3=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
        st.text(min_size=0, max_size=20),
        min_size=0,
        max_size=3
    )
)
@settings(max_examples=50, deadline=None)
def test_tags_assoc(tags1, tags2, tags3):
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    t3 = Tags(**tags3)
    
    result1 = (t1 + t2) + t3
    result2 = t1 + (t2 + t3)
    
    if result1.to_dict() != result2.to_dict():
        bugs_found.append(f"BUG: Tags addition not associative: {tags1}, {tags2}, {tags3}")

try:
    test_tags_assoc()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

# Test 4: Template duplicate key detection
print("\nTest 4: Testing Template duplicate key detection...")
@given(key=st.text(min_size=1, max_size=20, alphabet=string.ascii_letters + string.digits))
@settings(max_examples=50, deadline=None)
def test_duplicate_keys(key):
    template = Template()
    
    # Test with parameters
    param1 = Parameter(key, Type="String")
    template.add_parameter(param1)
    
    param2 = Parameter(key, Type="String", Default="default")
    try:
        template.add_parameter(param2)
        bugs_found.append(f"BUG: Template accepted duplicate parameter key: '{key}'")
    except ValueError as e:
        if "duplicate key" not in str(e):
            bugs_found.append(f"BUG: Wrong error for duplicate key: {e}")

try:
    test_duplicate_keys()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

# Test 5: Parameter type validation
print("\nTest 5: Testing Parameter type validation...")
@given(
    param_type=st.sampled_from(["String", "Number"]),
    default_value=st.one_of(
        st.text(min_size=1, max_size=20),
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
    )
)
@settings(max_examples=100, deadline=None)
def test_param_types(param_type, default_value):
    is_valid = False
    if param_type == "String":
        is_valid = isinstance(default_value, str)
    elif param_type == "Number":
        is_valid = isinstance(default_value, (int, float)) and not isinstance(default_value, bool)
    
    try:
        param = Parameter("TestParam", Type=param_type, Default=default_value)
        param.validate()
        if not is_valid:
            bugs_found.append(f"BUG: Invalid default accepted for {param_type}: {default_value} (type={type(default_value).__name__})")
    except (ValueError, TypeError):
        if is_valid:
            bugs_found.append(f"BUG: Valid default rejected for {param_type}: {default_value}")

try:
    test_param_types()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

# Test 6: Join delimiter validation
print("\nTest 6: Testing Join delimiter validation...")
@given(
    delimiter=st.one_of(
        st.none(),
        st.integers(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text()),
        st.text()
    ),
    values=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5)
)
@settings(max_examples=50, deadline=None)
def test_join_delimiter(delimiter, values):
    try:
        join = Join(delimiter, values)
        if not isinstance(delimiter, str):
            bugs_found.append(f"BUG: Join accepted non-string delimiter: {delimiter} (type={type(delimiter).__name__})")
    except ValueError as e:
        if isinstance(delimiter, str):
            bugs_found.append(f"BUG: Join rejected valid string delimiter: '{delimiter}'")
        elif "Delimiter must be a String" not in str(e):
            bugs_found.append(f"BUG: Wrong error message for invalid delimiter: {e}")
    except Exception as e:
        bugs_found.append(f"BUG: Unexpected exception in Join: {e}")

try:
    test_join_delimiter()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

# Test 7: encode_to_dict idempotence
print("\nTest 7: Testing encode_to_dict idempotence...")
@given(
    data=st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1000, max_value=1000),
            st.text(min_size=0, max_size=10),
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=3),
            st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3),
        ),
        max_leaves=10
    )
)
@settings(max_examples=50, deadline=None)
def test_encode_idempotent(data):
    encoded1 = encode_to_dict(data)
    encoded2 = encode_to_dict(encoded1)
    
    if encoded1 != encoded2:
        bugs_found.append(f"BUG: encode_to_dict not idempotent: {data}")

try:
    test_encode_idempotent()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

# Test 8: Template to_json/to_dict consistency
print("\nTest 8: Testing Template JSON serialization...")
@given(
    description=st.text(min_size=0, max_size=50),
    n_params=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=30, deadline=None)  
def test_template_json(description, n_params):
    template = Template(Description=description if description else None)
    
    for i in range(n_params):
        param = Parameter(f"Param{i}", Type="String")
        template.add_parameter(param)
    
    # Test JSON round-trip
    json_str = template.to_json()
    parsed = json.loads(json_str)
    dict_repr = template.to_dict()
    
    if parsed != dict_repr:
        bugs_found.append(f"BUG: Template JSON inconsistent with to_dict")

try:
    test_template_json()
    print("✓ Test passed")
except Exception as e:
    print(f"✗ Test failed with exception: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print(f"\n=== TEST SUMMARY ===")

if bugs_found:
    print(f"\nFound {len(bugs_found)} potential bug(s):\n")
    for i, bug in enumerate(bugs_found[:10], 1):  # Show first 10 bugs
        print(f"{i}. {bug}")
    if len(bugs_found) > 10:
        print(f"\n... and {len(bugs_found) - 10} more")
else:
    print("\nAll tests passed! No bugs found. ✓")

print("\n" + "=" * 60)