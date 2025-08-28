#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Run property-based tests for troposphere.omics."""

import sys
import traceback

# Ensure we use the correct environment
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import troposphere.omics as omics
from troposphere.validators import boolean, double

def run_test(test_func, test_name):
    """Run a single test and report results."""
    print(f"\nRunning: {test_name}")
    try:
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except AssertionError as e:
        print(f"✗ {test_name} failed: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ {test_name} error: {e}")
        traceback.print_exc()
        return False

# Test 1: Boolean validator edge case
print("Testing boolean validator edge cases...")
try:
    # Test with string "1" 
    result = boolean("1")
    print(f"boolean('1') = {result}, expected True")
    assert result is True, f"boolean('1') returned {result}, expected True"
    
    # Test with integer 1
    result = boolean(1)
    print(f"boolean(1) = {result}, expected True")
    assert result is True, f"boolean(1) returned {result}, expected True"
    
    # Test with string "0"
    result = boolean("0")
    print(f"boolean('0') = {result}, expected False")
    assert result is False, f"boolean('0') returned {result}, expected False"
    
    print("✓ Boolean validator basic tests passed")
except AssertionError as e:
    print(f"✗ Boolean validator test failed: {e}")

# Test 2: Double validator edge cases
print("\nTesting double validator edge cases...")
try:
    # Test with various numeric strings
    test_values = ["3.14", "-2.5", "1e10", "0", "-0"]
    for val in test_values:
        result = double(val)
        print(f"double('{val}') = {result}")
        assert result == val, f"double('{val}') returned {result}, expected {val}"
    
    print("✓ Double validator basic tests passed")
except AssertionError as e:
    print(f"✗ Double validator test failed: {e}")

# Test 3: RunGroup round-trip
print("\nTesting RunGroup round-trip property...")
try:
    # Create a RunGroup
    rg = omics.RunGroup("TestRunGroup")
    rg.Name = "MyRunGroup"
    rg.MaxCpus = 100.0
    rg.MaxRuns = 50.0
    
    # Convert to dict
    dict_repr = rg.to_dict()
    print(f"Original dict: {dict_repr}")
    
    # Extract properties
    props = dict_repr.get("Properties", {})
    
    # Create new object from dict
    rg2 = omics.RunGroup._from_dict("TestRunGroup", **props)
    dict_repr2 = rg2.to_dict()
    print(f"Reconstructed dict: {dict_repr2}")
    
    # Compare
    assert dict_repr == dict_repr2, f"Round-trip failed: {dict_repr} != {dict_repr2}"
    print("✓ RunGroup round-trip test passed")
    
except Exception as e:
    print(f"✗ RunGroup round-trip test failed: {e}")
    traceback.print_exc()

# Test 4: Invalid property handling
print("\nTesting invalid property handling...")
try:
    rg = omics.RunGroup("TestRunGroup")
    
    # Try to set an invalid property
    try:
        rg.InvalidProperty = "test"
        # Check if it was actually set (shouldn't be in props)
        if "InvalidProperty" in rg.properties:
            print("✗ Invalid property was accepted (found in properties)")
        else:
            print("✗ Invalid property was silently ignored (not found in properties)")
            # Try to access it
            try:
                val = rg.InvalidProperty
                print(f"✗ Could access invalid property: {val}")
            except AttributeError:
                print("✓ Invalid property access raised AttributeError")
    except AttributeError as e:
        print(f"✓ Setting invalid property raised AttributeError: {e}")
        
except Exception as e:
    print(f"✗ Invalid property test error: {e}")
    traceback.print_exc()

# Test 5: Required properties
print("\nTesting required properties...")
try:
    # AnnotationStore requires Name and StoreFormat
    store = omics.AnnotationStore("TestStore")
    
    # Set only StoreFormat, not Name
    store.StoreFormat = "VCF"
    
    # Try to convert to dict - should work but Name might be missing
    dict_repr = store.to_dict()
    props = dict_repr.get("Properties", {})
    
    print(f"Properties without Name: {props}")
    
    # Now set Name
    store.Name = "MyAnnotationStore"
    dict_repr = store.to_dict()
    props = dict_repr.get("Properties", {})
    
    print(f"Properties with Name: {props}")
    print("✓ Required properties test completed")
    
except Exception as e:
    print(f"✗ Required properties test error: {e}")
    traceback.print_exc()

# Test 6: Nested objects
print("\nTesting nested property objects...")
try:
    # Create SSEConfig
    sse = omics.SseConfig()
    sse.Type = "KMS"
    sse.KeyArn = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    
    # Use in ReferenceStore
    ref_store = omics.ReferenceStore("TestRefStore")
    ref_store.Name = "MyReferenceStore"
    ref_store.SseConfig = sse
    
    # Convert to dict
    dict_repr = ref_store.to_dict()
    props = dict_repr.get("Properties", {})
    
    print(f"Nested structure: {props}")
    
    # Verify nested structure
    assert "SseConfig" in props
    assert props["SseConfig"]["Type"] == "KMS"
    print("✓ Nested objects test passed")
    
except Exception as e:
    print(f"✗ Nested objects test error: {e}")
    traceback.print_exc()

# Test 7: Boolean field in WorkflowParameter
print("\nTesting WorkflowParameter.Optional boolean field...")
try:
    param = omics.WorkflowParameter()
    
    # Test various boolean-like values
    test_values = [True, False, 1, 0, "true", "false", "True", "False"]
    for val in test_values:
        param.Optional = val
        dict_repr = param.to_dict()
        if "Optional" in dict_repr:
            result = dict_repr["Optional"]
            print(f"Optional={val} -> {result} (type: {type(result).__name__})")
            # Should be boolean
            if not isinstance(result, bool):
                print(f"✗ Optional field not converted to bool for {val}")
    
    print("✓ WorkflowParameter.Optional test completed")
    
except Exception as e:
    print(f"✗ WorkflowParameter test error: {e}")
    traceback.print_exc()

print("\n" + "="*50)
print("Test run completed!")