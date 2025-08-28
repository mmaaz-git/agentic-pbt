"""Targeted test to investigate the numeric key bug in troposphere.evidently"""

from hypothesis import given, strategies as st, settings, example
import troposphere.evidently as evidently
import pytest


def test_numeric_string_key_bug_minimal():
    """Minimal reproduction of the bug with numeric string keys"""
    # This should demonstrate the bug clearly
    with pytest.raises(AttributeError) as exc_info:
        var = evidently.VariationObject(**{'0': None})
    
    assert "does not support attribute 0" in str(exc_info.value)
    print(f"Error message: {exc_info.value}")


def test_various_numeric_keys():
    """Test various numeric-like keys"""
    test_cases = [
        {'0': 'value'},
        {'1': 'value'},
        {'123': 'value'},
        {'00': 'value'},
        {'01': 'value'},
        {'-1': 'value'},  # negative number string
        {'1.0': 'value'},  # float-like string
        {'1e5': 'value'},  # scientific notation
    ]
    
    for kwargs in test_cases:
        print(f"\nTesting with kwargs: {kwargs}")
        try:
            var = evidently.VariationObject(**kwargs)
            print(f"  Success: Created object")
        except AttributeError as e:
            print(f"  Failed with AttributeError: {e}")
        except Exception as e:
            print(f"  Failed with {type(e).__name__}: {e}")


def test_normal_vs_numeric_keys():
    """Compare behavior with normal vs numeric keys"""
    # This should work fine
    try:
        var1 = evidently.VariationObject(VariationName='test', StringValue='hello')
        print(f"Normal kwargs work: {var1.to_dict()}")
    except Exception as e:
        print(f"Normal kwargs failed: {e}")
    
    # This should fail
    try:
        var2 = evidently.VariationObject(**{'VariationName': 'test', '0': 'value'})
        print(f"Mixed with numeric key works: {var2.to_dict()}")
    except AttributeError as e:
        print(f"Mixed with numeric key fails: {e}")


@given(st.text(alphabet='0123456789', min_size=1, max_size=5))
def test_hypothesis_numeric_strings(key):
    """Property test: numeric string keys should either work or fail consistently"""
    try:
        var = evidently.VariationObject(**{key: 'test_value'})
        # If it works, we should be able to convert to dict
        result = var.to_dict()
        # The key should NOT appear in the result (since it's not a valid property)
        assert key not in result
    except AttributeError as e:
        # This is the bug - numeric strings cause AttributeError
        assert "does not support attribute" in str(e)
        assert key in str(e)


def test_other_aws_classes_same_bug():
    """Check if other AWS classes have the same bug"""
    classes_to_test = [
        evidently.EntityOverride,
        evidently.MetricGoalObject,
        evidently.TreatmentToWeight,
        evidently.S3Destination,
    ]
    
    for cls in classes_to_test:
        print(f"\nTesting {cls.__name__}:")
        try:
            obj = cls(**{'0': 'value'})
            print(f"  No error - created {type(obj)}")
        except AttributeError as e:
            print(f"  Same bug! {e}")
        except TypeError as e:
            print(f"  Different error: {e}")


if __name__ == "__main__":
    print("=== Testing numeric string key bug ===")
    test_numeric_string_key_bug_minimal()
    print("\n=== Testing various numeric keys ===")
    test_various_numeric_keys()
    print("\n=== Testing normal vs numeric keys ===")
    test_normal_vs_numeric_keys()
    print("\n=== Testing if other classes have same bug ===")
    test_other_aws_classes_same_bug()