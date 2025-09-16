#!/usr/bin/env python3
"""Run the property-based tests directly."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, Verbosity
import troposphere.greengrassv2 as ggv2
from troposphere.validators import boolean, integer, double

print("Running property-based tests for troposphere.greengrassv2...")
print("=" * 60)

# Test 1: Boolean validator
print("\nTest 1: Boolean validator with valid inputs...")
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
@settings(max_examples=100, verbosity=Verbosity.verbose)
def test_boolean_valid(value):
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False

try:
    test_boolean_valid()
    print("✓ Boolean validator valid inputs test passed")
except Exception as e:
    print(f"✗ Boolean validator valid inputs test FAILED: {e}")

# Test 2: Boolean validator invalid inputs
print("\nTest 2: Boolean validator with invalid inputs...")
@given(st.one_of(
    st.text(min_size=1).filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers(min_value=2),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x not in [0.0, 1.0]),
))
@settings(max_examples=100, verbosity=Verbosity.verbose)
def test_boolean_invalid(value):
    try:
        boolean(value)
        assert False, f"Expected ValueError for {value!r}"
    except ValueError:
        pass  # Expected

try:
    test_boolean_invalid()
    print("✓ Boolean validator invalid inputs test passed")
except Exception as e:
    print(f"✗ Boolean validator invalid inputs test FAILED: {e}")

# Test 3: Component construction
print("\nTest 3: ComponentPlatform construction...")
@given(
    name=st.text(min_size=1, max_size=100),
    attributes=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        max_size=5
    )
)
@settings(max_examples=50, verbosity=Verbosity.verbose)
def test_component_platform(name, attributes):
    platform = ggv2.ComponentPlatform(
        Name=name,
        Attributes=attributes
    )
    assert platform.Name == name
    assert platform.Attributes == attributes
    result = platform.to_dict()
    assert isinstance(result, dict)

try:
    test_component_platform()
    print("✓ ComponentPlatform construction test passed")
except Exception as e:
    print(f"✗ ComponentPlatform construction test FAILED: {e}")

# Test 4: SystemResourceLimits with validators
print("\nTest 4: SystemResourceLimits with numeric validators...")
@given(
    cpus=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    memory=st.integers(min_value=0, max_value=10**9)
)
@settings(max_examples=50, verbosity=Verbosity.verbose)
def test_system_limits(cpus, memory):
    limits = ggv2.SystemResourceLimits(
        Cpus=cpus,
        Memory=memory
    )
    result = limits.to_dict()
    assert isinstance(result, dict)
    assert result.get('Cpus') == cpus
    assert result.get('Memory') == memory

try:
    test_system_limits()
    print("✓ SystemResourceLimits test passed")
except Exception as e:
    print(f"✗ SystemResourceLimits test FAILED: {e}")

# Test 5: Required properties
print("\nTest 5: IoTJobAbortCriteria with required properties...")
@given(
    action=st.text(min_size=1, max_size=50),
    failure_type=st.text(min_size=1, max_size=50),
    min_executed=st.integers(min_value=0, max_value=10000),
    threshold=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
)
@settings(max_examples=50, verbosity=Verbosity.verbose)
def test_required_props(action, failure_type, min_executed, threshold):
    criteria = ggv2.IoTJobAbortCriteria(
        Action=action,
        FailureType=failure_type,
        MinNumberOfExecutedThings=min_executed,
        ThresholdPercentage=threshold
    )
    result = criteria.to_dict()
    assert result['Action'] == action
    assert result['FailureType'] == failure_type

try:
    test_required_props()
    print("✓ Required properties test passed")
except Exception as e:
    print(f"✗ Required properties test FAILED: {e}")

print("\n" + "=" * 60)
print("Test run complete!")