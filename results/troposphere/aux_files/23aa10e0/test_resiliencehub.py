import math
from hypothesis import assume, given, strategies as st
import pytest
import troposphere.resiliencehub as rh


# Test the integer function
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none()
))
def test_integer_function_consistency(x):
    """Property: integer(x) should succeed iff int(x) succeeds, and return x"""
    try:
        result = rh.integer(x)
        # If integer(x) succeeds, int(x) should also succeed
        int_value = int(x)
        # And it should return the original value
        assert result == x
    except ValueError as e:
        # If integer(x) raises ValueError, int(x) should also fail
        with pytest.raises((ValueError, TypeError)):
            int(x)


@given(st.integers())
def test_integer_with_valid_integers(x):
    """Property: integer() should always succeed with actual integers"""
    result = rh.integer(x)
    assert result == x


@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x)))
def test_integer_with_exact_floats(x):
    """Property: integer() should succeed with floats that are exact integers"""
    result = rh.integer(x)
    assert result == x


# Test validate_resiliencypolicy_tier
@given(st.text())
def test_validate_tier_with_strings(tier):
    """Property: validate_resiliencypolicy_tier should only accept specific values"""
    VALID_TIERS = ("MissionCritical", "Critical", "Important", "CoreServices", "NonCritical")
    
    if tier in VALID_TIERS:
        result = rh.validate_resiliencypolicy_tier(tier)
        assert result == tier
    else:
        with pytest.raises(ValueError) as exc_info:
            rh.validate_resiliencypolicy_tier(tier)
        assert "Tier must be one of" in str(exc_info.value)


@given(st.sampled_from(["MissionCritical", "Critical", "Important", "CoreServices", "NonCritical"]))
def test_validate_tier_with_valid_values(tier):
    """Property: All documented valid tiers should be accepted and returned unchanged"""
    result = rh.validate_resiliencypolicy_tier(tier)
    assert result == tier


# Test validate_resiliencypolicy_policy
@given(st.dictionaries(
    keys=st.sampled_from(["Software", "Hardware", "AZ", "Region"]),
    values=st.builds(rh.FailurePolicy,
                    RpoInSecs=st.integers(min_value=0, max_value=2592000),
                    RtoInSecs=st.integers(min_value=0, max_value=2592000))
))
def test_validate_policy_with_valid_structure(policy):
    """Property: Valid policy structure should be accepted and returned unchanged"""
    result = rh.validate_resiliencypolicy_policy(policy)
    assert result == policy


@given(st.dictionaries(
    keys=st.text(),
    values=st.builds(rh.FailurePolicy,
                    RpoInSecs=st.integers(min_value=0, max_value=2592000),
                    RtoInSecs=st.integers(min_value=0, max_value=2592000))
))
def test_validate_policy_key_validation(policy):
    """Property: Only specific keys should be allowed in policy"""
    VALID_KEYS = {"Software", "Hardware", "AZ", "Region"}
    
    if all(k in VALID_KEYS for k in policy.keys()):
        result = rh.validate_resiliencypolicy_policy(policy)
        assert result == policy
    elif policy:  # Non-empty dict with invalid keys
        with pytest.raises(ValueError) as exc_info:
            rh.validate_resiliencypolicy_policy(policy)
        assert "Policy key must be one of" in str(exc_info.value)
    else:  # Empty dict is valid
        result = rh.validate_resiliencypolicy_policy(policy)
        assert result == policy


@given(st.one_of(
    st.none(),
    st.text(),
    st.integers(),
    st.lists(st.integers())
))
def test_validate_policy_type_check(policy):
    """Property: validate_resiliencypolicy_policy should only accept dicts"""
    if not isinstance(policy, dict):
        with pytest.raises(ValueError) as exc_info:
            rh.validate_resiliencypolicy_policy(policy)
        assert "Policy must be a dict" in str(exc_info.value)


# Test FailurePolicy class
@given(
    rpo=st.integers(min_value=-1000000, max_value=1000000),
    rto=st.integers(min_value=-1000000, max_value=1000000)
)
def test_failure_policy_integer_validation(rpo, rto):
    """Property: FailurePolicy should properly validate integer inputs"""
    fp = rh.FailurePolicy(RpoInSecs=rpo, RtoInSecs=rto)
    # Should be able to convert to dict without error if inputs are valid integers
    result = fp.to_dict()
    assert result["RpoInSecs"] == rpo
    assert result["RtoInSecs"] == rto


@given(
    rpo=st.one_of(st.integers(), st.floats(allow_nan=True, allow_infinity=True), st.text()),
    rto=st.one_of(st.integers(), st.floats(allow_nan=True, allow_infinity=True), st.text())
)
def test_failure_policy_validation(rpo, rto):
    """Property: FailurePolicy validation should match integer() function behavior"""
    # Check if both values can be converted to int
    can_convert = True
    try:
        int(rpo)
        int(rto)
    except (ValueError, TypeError):
        can_convert = False
    
    if can_convert:
        # Should successfully create and convert to dict
        fp = rh.FailurePolicy(RpoInSecs=rpo, RtoInSecs=rto)
        result = fp.to_dict()
        assert "RpoInSecs" in result
        assert "RtoInSecs" in result
    else:
        # Should fail validation during construction
        with pytest.raises(ValueError):
            rh.FailurePolicy(RpoInSecs=rpo, RtoInSecs=rto)


# Test round-trip properties for classes
@given(
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    name=st.text(min_size=1),
    tier=st.sampled_from(["MissionCritical", "Critical", "Important", "CoreServices", "NonCritical"]),
    policy_dict=st.dictionaries(
        keys=st.sampled_from(["Software", "Hardware", "AZ", "Region"]),
        values=st.builds(rh.FailurePolicy,
                        RpoInSecs=st.integers(min_value=0, max_value=86400),
                        RtoInSecs=st.integers(min_value=0, max_value=86400)),
        min_size=1
    )
)
def test_resiliency_policy_roundtrip(title, name, tier, policy_dict):
    """Property: ResiliencyPolicy to_dict should produce valid reconstruction data"""
    rp = rh.ResiliencyPolicy(
        title,
        PolicyName=name,
        Tier=tier,
        Policy=policy_dict
    )
    
    # Convert to dict and check structure
    result = rp.to_dict()
    assert "Properties" in result
    assert "Type" in result
    assert result["Type"] == "AWS::ResilienceHub::ResiliencyPolicy"
    
    props = result["Properties"]
    assert props["PolicyName"] == name
    assert props["Tier"] == tier
    assert "Policy" in props
    
    # Create new instance from dict's Properties
    rp2 = rh.ResiliencyPolicy.from_dict("TestPolicy2", props)
    result2 = rp2.to_dict()
    
    # Should produce same properties
    assert result["Properties"]["PolicyName"] == result2["Properties"]["PolicyName"]
    assert result["Properties"]["Tier"] == result2["Properties"]["Tier"]
    assert result["Properties"]["Policy"] == result2["Properties"]["Policy"]