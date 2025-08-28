import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.efs as efs
from troposphere.validators.efs import (
    provisioned_throughput_validator,
    throughput_mode_validator,
    validate_backup_policy,
    Bursting, Elastic, Provisioned
)
# Validators use regular ValueError, not a custom ValidationError


# Test 1: provisioned_throughput_validator property
@given(st.floats(min_value=0.0, max_value=1e10))
def test_provisioned_throughput_accepts_non_negative(throughput):
    """Property: provisioned_throughput_validator accepts all values >= 0.0 and returns them unchanged"""
    result = provisioned_throughput_validator(throughput)
    assert result == throughput  # Should return the input unchanged


@given(st.floats(max_value=-0.001, min_value=-1e10))
def test_provisioned_throughput_rejects_negative(throughput):
    """Property: provisioned_throughput_validator rejects all values < 0.0"""
    try:
        provisioned_throughput_validator(throughput)
        assert False, f"Should have raised ValueError for {throughput}"
    except ValueError as e:
        assert "must be greater than or equal to 0.0" in str(e)


# Test 2: throughput_mode_validator property
@given(st.sampled_from([Bursting, Elastic, Provisioned]))
def test_throughput_mode_accepts_valid_modes(mode):
    """Property: throughput_mode_validator accepts valid modes and returns them unchanged"""
    result = throughput_mode_validator(mode)
    assert result == mode


@given(st.text(min_size=1).filter(lambda x: x not in [Bursting, Elastic, Provisioned]))
def test_throughput_mode_rejects_invalid_modes(mode):
    """Property: throughput_mode_validator rejects all non-valid mode strings"""
    try:
        throughput_mode_validator(mode)
        assert False, f"Should have raised ValueError for {mode}"
    except ValueError as e:
        assert "ThroughputMode must be one of" in str(e)


# Test 3: BackupPolicy validation property
@given(st.sampled_from(["DISABLED", "DISABLING", "ENABLED", "ENABLING"]))
def test_backup_policy_accepts_valid_status(status):
    """Property: BackupPolicy accepts valid status values"""
    backup_policy = efs.BackupPolicy(Status=status)
    backup_policy.validate()  # Should not raise


@given(st.text(min_size=1).filter(lambda x: x not in ["DISABLED", "DISABLING", "ENABLED", "ENABLING"]))
def test_backup_policy_rejects_invalid_status(status):
    """Property: BackupPolicy rejects invalid status values"""
    backup_policy = efs.BackupPolicy(Status=status)
    try:
        backup_policy.validate()
        assert False, f"Should have raised ValueError for Status={status}"
    except ValueError as e:
        assert "must be one of" in str(e)


# Test 4: Round-trip property for FileSystem
@given(
    st.booleans(),  # Encrypted
    st.booleans(),  # BypassPolicyLockoutSafetyCheck
    st.sampled_from([None, "generalPurpose", "maxIO"]),  # PerformanceMode
    st.sampled_from([None, Bursting, Elastic, Provisioned])  # ThroughputMode
)
def test_filesystem_roundtrip(encrypted, bypass, perf_mode, throughput_mode):
    """Property: FileSystem to_dict and from_dict should preserve data"""
    fs = efs.FileSystem(title="TestFS")
    
    if encrypted:
        fs.Encrypted = encrypted
    if bypass:
        fs.BypassPolicyLockoutSafetyCheck = bypass
    if perf_mode:
        fs.PerformanceMode = perf_mode
    if throughput_mode:
        fs.ThroughputMode = throughput_mode
    
    # Convert to dict and back
    dict_repr = fs.to_dict()
    fs_recovered = efs.FileSystem.from_dict("TestFS", dict_repr)
    dict_recovered = fs_recovered.to_dict()
    
    # The round-trip should preserve the data
    assert dict_repr == dict_recovered


# Test 5: Edge case for provisioned throughput at exactly 0.0
def test_provisioned_throughput_zero_edge_case():
    """Property: provisioned_throughput_validator accepts exactly 0.0"""
    result = provisioned_throughput_validator(0.0)
    assert result == 0.0


# Test 6: Case sensitivity for backup policy status
@given(st.sampled_from(["disabled", "DISABLED", "Disabled", "enabling", "ENABLING", "Enabling"]))
def test_backup_policy_case_sensitivity(status):
    """Property: BackupPolicy status validation is case sensitive"""
    backup_policy = efs.BackupPolicy(Status=status)
    if status in ["DISABLED", "DISABLING", "ENABLED", "ENABLING"]:
        backup_policy.validate()  # Should succeed
    else:
        try:
            backup_policy.validate()
            assert False, f"Should have raised ValueError for Status={status}"
        except ValueError:
            pass  # Expected to fail for non-uppercase versions