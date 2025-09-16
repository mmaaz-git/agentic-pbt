import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.rds as rds
import troposphere.validators as validators
import pytest


# Test validate_v2_capacity - half-step increments property
@given(st.floats(min_value=0.5, max_value=128))
def test_v2_capacity_half_step_increments(capacity):
    """
    Property: validate_v2_capacity should only accept values in half-step increments
    (0.5, 1.0, 1.5, 2.0, etc.) according to its docstring and error message.
    """
    # Check if the value is actually in half-step increments
    is_half_step = (capacity * 2).is_integer()
    
    try:
        result = rds.validate_v2_capacity(capacity)
        # If it succeeded, it should be a valid half-step
        assert is_half_step, f"validate_v2_capacity accepted {capacity} which is not a half-step increment"
    except ValueError as e:
        # If it failed, it should NOT be a valid half-step
        if is_half_step:
            # This would be a bug - it rejected a valid half-step value
            raise AssertionError(f"validate_v2_capacity rejected valid half-step value {capacity}: {e}")


# Test validate_v2_capacity - boundary conditions
@given(st.floats())
def test_v2_capacity_boundaries(capacity):
    """
    Property: validate_v2_capacity should accept values in [0.5, 128] and reject others
    """
    try:
        result = rds.validate_v2_capacity(capacity)
        # If it succeeded, capacity should be in valid range
        assert 0.5 <= capacity <= 128, f"validate_v2_capacity accepted out-of-range value {capacity}"
    except ValueError:
        # If it failed, capacity should be out of range OR not a half-step
        if 0.5 <= capacity <= 128 and (capacity * 2).is_integer():
            raise AssertionError(f"validate_v2_capacity rejected valid value {capacity}")


# Test validate_v2_max_capacity consistency with validate_v2_capacity
@given(st.floats())
def test_v2_max_capacity_consistency(capacity):
    """
    Property: validate_v2_max_capacity should accept the same values as validate_v2_capacity
    except it requires capacity >= 1
    """
    # First check what v2_capacity does
    v2_accepts = False
    try:
        rds.validate_v2_capacity(capacity)
        v2_accepts = True
    except ValueError:
        pass
    
    # Now check v2_max_capacity
    try:
        result = rds.validate_v2_max_capacity(capacity)
        # If max succeeded, v2 should have succeeded AND capacity >= 1
        assert v2_accepts, f"v2_max_capacity accepted {capacity} but v2_capacity rejected it"
        assert capacity >= 1, f"v2_max_capacity accepted {capacity} which is < 1"
    except ValueError:
        # If max failed, either v2 should have failed OR capacity < 1
        if v2_accepts and capacity >= 1:
            raise AssertionError(f"v2_max_capacity rejected valid value {capacity}")


# Test validate_backup_retention_period
@given(st.integers())
def test_backup_retention_period_range(days):
    """
    Property: BackupRetentionPeriod must be a positive integer <= 35
    """
    try:
        result = rds.validate_backup_retention_period(days)
        # If it succeeded, days should be in valid range
        assert 0 <= days <= 35, f"validate_backup_retention_period accepted invalid value {days}"
    except (ValueError, TypeError):
        # If it failed, days should be out of range
        if 0 <= days <= 35:
            raise AssertionError(f"validate_backup_retention_period rejected valid value {days}")


# Test validate_iops special zero handling
@given(st.integers(min_value=-1000, max_value=10000))
def test_iops_validation(iops):
    """
    Property: IOPS must be 0 or >= 1000
    """
    try:
        result = rds.validate_iops(iops)
        # If it succeeded, iops should be 0 or >= 1000
        assert iops == 0 or iops >= 1000, f"validate_iops accepted invalid value {iops}"
    except (ValueError, TypeError):
        # If it failed, iops should be invalid
        if iops == 0 or iops >= 1000:
            raise AssertionError(f"validate_iops rejected valid value {iops}")


# Test network_port validation
@given(st.integers())
def test_network_port_range(port):
    """
    Property: network_port must be between -1 and 65535
    """
    try:
        result = validators.network_port(port)
        # If it succeeded, port should be in valid range
        assert -1 <= port <= 65535, f"network_port accepted out-of-range value {port}"
    except (ValueError, TypeError):
        # If it failed, port should be out of range
        if -1 <= port <= 65535:
            raise AssertionError(f"network_port rejected valid value {port}")


# Test integer_range factory function
@given(st.integers(), st.integers(), st.integers())
def test_integer_range_validation(min_val, max_val, test_val):
    """
    Property: integer_range should create a validator that accepts values in [min, max]
    """
    assume(min_val <= max_val)  # Only test valid ranges
    
    validator = validators.integer_range(min_val, max_val)
    
    try:
        result = validator(test_val)
        # If it succeeded, test_val should be in range
        assert min_val <= test_val <= max_val, f"integer_range({min_val}, {max_val}) accepted out-of-range value {test_val}"
    except (ValueError, TypeError):
        # If it failed, test_val should be out of range
        if min_val <= test_val <= max_val:
            raise AssertionError(f"integer_range({min_val}, {max_val}) rejected valid value {test_val}")


# Test for float precision issues in v2_capacity
@given(st.floats(min_value=0.4, max_value=0.6))
def test_v2_capacity_float_precision_near_boundary(capacity):
    """
    Property: Test float precision handling near the 0.5 boundary
    """
    try:
        result = rds.validate_v2_capacity(capacity)
        # Should only succeed if >= 0.5 and is half-step
        assert capacity >= 0.5 and (capacity * 2).is_integer()
    except ValueError:
        # Should fail if < 0.5 or not half-step
        pass


if __name__ == "__main__":
    # Run with increased examples for better coverage
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))