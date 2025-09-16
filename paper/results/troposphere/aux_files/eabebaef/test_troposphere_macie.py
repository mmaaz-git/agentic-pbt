#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python
"""Property-based tests for troposphere.macie module"""

import json
import re
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the target module
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere import macie
from troposphere.validators import macie as macie_validators


# Test 1: Validator functions should accept valid values and return them unchanged
@given(st.sampled_from(["ARCHIVE", "NOOP"]))
def test_findingsfilter_action_valid(action):
    """Valid actions should pass through unchanged"""
    result = macie_validators.findingsfilter_action(action)
    assert result == action


@given(st.text().filter(lambda x: x not in ["ARCHIVE", "NOOP"]))
def test_findingsfilter_action_invalid(action):
    """Invalid actions should raise ValueError with descriptive message"""
    with pytest.raises(ValueError) as exc:
        macie_validators.findingsfilter_action(action)
    error_msg = str(exc.value)
    assert "Action must be one of" in error_msg
    assert "ARCHIVE" in error_msg
    assert "NOOP" in error_msg


@given(st.sampled_from(["FIFTEEN_MINUTES", "ONE_HOUR", "SIX_HOURS"]))
def test_session_findingpublishingfrequency_valid(frequency):
    """Valid frequencies should pass through unchanged"""
    result = macie_validators.session_findingpublishingfrequency(frequency)
    assert result == frequency


@given(st.text().filter(lambda x: x not in ["FIFTEEN_MINUTES", "ONE_HOUR", "SIX_HOURS"]))
def test_session_findingpublishingfrequency_invalid(frequency):
    """Invalid frequencies should raise ValueError with descriptive message"""
    with pytest.raises(ValueError) as exc:
        macie_validators.session_findingpublishingfrequency(frequency)
    error_msg = str(exc.value)
    assert "FindingPublishingFrequency must be one of" in error_msg
    assert "FIFTEEN_MINUTES" in error_msg
    assert "ONE_HOUR" in error_msg
    assert "SIX_HOURS" in error_msg


@given(st.sampled_from(["ENABLED", "DISABLED"]))
def test_session_status_valid(status):
    """Valid status values should pass through unchanged"""
    result = macie_validators.session_status(status)
    assert result == status


@given(st.text().filter(lambda x: x not in ["ENABLED", "DISABLED"]))
def test_session_status_invalid(status):
    """Invalid status values should raise ValueError with descriptive message"""
    with pytest.raises(ValueError) as exc:
        macie_validators.session_status(status)
    error_msg = str(exc.value)
    assert "Status must be one of" in error_msg
    assert "ENABLED" in error_msg
    assert "DISABLED" in error_msg


# Test 2: Object creation with required and optional properties
@given(
    bucket_name=st.text(min_size=1, max_size=63).filter(lambda x: x.isalnum()),
    object_key=st.text(min_size=1, max_size=1024)
)
def test_s3wordslist_creation(bucket_name, object_key):
    """S3WordsList should be created with required properties"""
    s3_words_list = macie.S3WordsList(
        BucketName=bucket_name,
        ObjectKey=object_key
    )
    
    # Properties should be accessible
    assert s3_words_list.BucketName == bucket_name
    assert s3_words_list.ObjectKey == object_key
    
    # Should convert to dict properly
    result_dict = s3_words_list.to_dict()
    assert result_dict["BucketName"] == bucket_name
    assert result_dict["ObjectKey"] == object_key


@given(
    name=st.text(min_size=1, max_size=128).filter(lambda x: re.match(r'^[a-zA-Z0-9]+$', x)),
    regex_pattern=st.text(min_size=1, max_size=512),
    description=st.text(min_size=0, max_size=512)
)
def test_customdataidentifier_creation(name, regex_pattern, description):
    """CustomDataIdentifier should handle required and optional properties"""
    # Create with required properties only
    cdi = macie.CustomDataIdentifier(
        title="TestCDI",
        Name=name,
        Regex=regex_pattern
    )
    assert cdi.Name == name
    assert cdi.Regex == regex_pattern
    
    # Should serialize to dict correctly
    result = cdi.to_dict()
    assert result["Type"] == "AWS::Macie::CustomDataIdentifier"
    assert result["Properties"]["Name"] == name
    assert result["Properties"]["Regex"] == regex_pattern
    
    # Test with optional description
    if description:
        cdi2 = macie.CustomDataIdentifier(
            title="TestCDI2",
            Name=name,
            Regex=regex_pattern,
            Description=description
        )
        assert cdi2.Description == description
        result2 = cdi2.to_dict()
        assert result2["Properties"]["Description"] == description


# Test 3: Type validation for properties
@given(
    gt_value=st.integers(),
    gte_value=st.integers(),
    lt_value=st.integers(),
    lte_value=st.integers()
)
def test_criterionadditionalproperties_integer_fields(gt_value, gte_value, lt_value, lte_value):
    """CriterionAdditionalProperties should accept integers for comparison fields"""
    cap = macie.CriterionAdditionalProperties(
        gt=gt_value,
        gte=gte_value,
        lt=lt_value,
        lte=lte_value
    )
    
    assert cap.gt == gt_value
    assert cap.gte == gte_value
    assert cap.lt == lt_value
    assert cap.lte == lte_value
    
    # Should serialize correctly
    result = cap.to_dict()
    assert result["gt"] == gt_value
    assert result["gte"] == gte_value
    assert result["lt"] == lt_value
    assert result["lte"] == lte_value


@given(
    eq_values=st.lists(st.text(min_size=1), min_size=1, max_size=10),
    neq_values=st.lists(st.text(min_size=1), min_size=1, max_size=10)
)
def test_criterionadditionalproperties_list_fields(eq_values, neq_values):
    """CriterionAdditionalProperties should accept lists of strings for eq/neq fields"""
    cap = macie.CriterionAdditionalProperties(
        eq=eq_values,
        neq=neq_values
    )
    
    assert cap.eq == eq_values
    assert cap.neq == neq_values
    
    # Should serialize correctly
    result = cap.to_dict()
    assert result["eq"] == eq_values
    assert result["neq"] == neq_values


# Test 4: Session object with validated enum properties
@given(
    frequency=st.sampled_from(["FIFTEEN_MINUTES", "ONE_HOUR", "SIX_HOURS"]),
    status=st.sampled_from(["ENABLED", "DISABLED"])
)
def test_session_with_validators(frequency, status):
    """Session should use validators for its properties"""
    session = macie.Session(
        title="TestSession",
        FindingPublishingFrequency=frequency,
        Status=status
    )
    
    assert session.FindingPublishingFrequency == frequency
    assert session.Status == status
    
    # Should serialize correctly
    result = session.to_dict()
    assert result["Type"] == "AWS::Macie::Session"
    assert result["Properties"]["FindingPublishingFrequency"] == frequency
    assert result["Properties"]["Status"] == status


# Test 5: Invalid type should raise TypeError
@given(st.integers())
def test_s3wordslist_type_validation(invalid_value):
    """S3WordsList should reject non-string values for string properties"""
    with pytest.raises(TypeError) as exc:
        macie.S3WordsList(
            BucketName=invalid_value,  # Should be string
            ObjectKey="valid-key"
        )
    error_msg = str(exc.value)
    assert "BucketName" in error_msg
    assert "expected" in error_msg


# Test 6: Required properties validation
def test_allowlist_requires_criteria():
    """AllowList should require Criteria and Name properties"""
    # Missing Criteria should fail
    with pytest.raises(ValueError) as exc:
        allow_list = macie.AllowList(
            title="TestAllowList",
            Name="TestName"
        )
        allow_list.to_dict()  # Validation happens on serialization
    
    error_msg = str(exc.value)
    assert "required" in error_msg.lower()
    assert "Criteria" in error_msg


# Test 7: Lists properties should reject non-list values
@given(st.text(min_size=1))
def test_customdataidentifier_list_properties(text_value):
    """CustomDataIdentifier should reject non-list values for list properties"""
    with pytest.raises(TypeError) as exc:
        macie.CustomDataIdentifier(
            title="TestCDI",
            Name="TestName",
            Regex=".*",
            Keywords=text_value  # Should be a list
        )
    error_msg = str(exc.value)
    assert "Keywords" in error_msg


# Test 8: MaximumMatchDistance validation (should be integer)
@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()))
def test_customdataidentifier_integer_validation(float_value):
    """CustomDataIdentifier MaximumMatchDistance should only accept integers"""
    with pytest.raises(TypeError) as exc:
        macie.CustomDataIdentifier(
            title="TestCDI",
            Name="TestName",
            Regex=".*",
            MaximumMatchDistance=float_value  # Should be integer
        )
    error_msg = str(exc.value)
    assert "MaximumMatchDistance" in error_msg