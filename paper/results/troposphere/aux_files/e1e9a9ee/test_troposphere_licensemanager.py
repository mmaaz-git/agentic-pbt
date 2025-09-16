#!/usr/bin/env python3
"""Property-based tests for troposphere.licensemanager module."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import json

# Import the module under test
from troposphere import licensemanager
from troposphere import validators
from troposphere import BaseAWSObject, AWSObject, AWSProperty


# Test 1: Boolean validator properties
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_idempotence(value):
    """Test that boolean validator is idempotent for valid inputs."""
    result1 = validators.boolean(value)
    result2 = validators.boolean(result1)
    assert result1 == result2
    assert isinstance(result1, bool)


@given(st.one_of(
    st.text(min_size=1),
    st.integers(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs."""
    # Filter out valid values
    if value not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]:
        with pytest.raises(ValueError):
            validators.boolean(value)


# Test 2: Integer validator properties
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.lstrip('-').isdigit()),
))
def test_integer_validator_valid(value):
    """Test that integer validator accepts valid integers."""
    result = validators.integer(value)
    # Should be able to convert result to int
    int_value = int(result)
    assert isinstance(int_value, int)


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: not x.lstrip('-').replace('.', '').isdigit()),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.none()
))
def test_integer_validator_invalid(value):
    """Test that integer validator raises ValueError for non-integer inputs."""
    with pytest.raises(ValueError):
        validators.integer(value)


# Test 3: Title validation for AWS objects
@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1))
def test_valid_title_alphanumeric(title):
    """Test that alphanumeric titles are accepted."""
    # Grant requires several properties, let's test with minimal valid setup
    grant = licensemanager.Grant(title)
    assert grant.title == title


@given(st.text(min_size=1).filter(lambda x: not x.isalnum()))
def test_invalid_title_non_alphanumeric(title):
    """Test that non-alphanumeric titles are rejected."""
    with pytest.raises(ValueError, match="not alphanumeric"):
        licensemanager.Grant(title)


# Test 4: Required property validation
def test_license_missing_required_properties():
    """Test that License raises error when required properties are missing."""
    # License has many required properties
    license_obj = licensemanager.License("TestLicense")
    with pytest.raises(ValueError, match="required in type"):
        license_obj.to_dict()


@given(
    beneficiary=st.text(min_size=1),
    renew_type=st.text(min_size=1),
    name=st.text(min_size=1),
    unit=st.text(min_size=1),
    issuer_name=st.text(min_size=1),
    license_name=st.text(min_size=1),
    product_name=st.text(min_size=1),
    home_region=st.text(min_size=1),
    begin_date=st.text(min_size=1),
    end_date=st.text(min_size=1)
)
def test_license_with_all_required_properties(
    beneficiary, renew_type, name, unit, issuer_name,
    license_name, product_name, home_region, begin_date, end_date
):
    """Test that License with all required properties can be created."""
    license_obj = licensemanager.License(
        "TestLicense",
        Beneficiary=beneficiary,
        ConsumptionConfiguration=licensemanager.ConsumptionConfiguration(
            RenewType=renew_type
        ),
        Entitlements=[
            licensemanager.Entitlement(
                Name=name,
                Unit=unit
            )
        ],
        HomeRegion=home_region,
        Issuer=licensemanager.IssuerData(
            Name=issuer_name
        ),
        LicenseName=license_name,
        ProductName=product_name,
        Validity=licensemanager.ValidityDateFormat(
            Begin=begin_date,
            End=end_date
        )
    )
    # Should not raise when converting to dict
    result = license_obj.to_dict()
    assert isinstance(result, dict)
    assert result["Type"] == "AWS::LicenseManager::License"


# Test 5: Property classes can be instantiated and converted to dict
@given(
    allow_early_checkin=st.booleans(),
    max_time=st.integers(min_value=0, max_value=1000000)
)
def test_borrow_configuration_properties(allow_early_checkin, max_time):
    """Test BorrowConfiguration property class."""
    config = licensemanager.BorrowConfiguration(
        AllowEarlyCheckIn=allow_early_checkin,
        MaxTimeToLiveInMinutes=max_time
    )
    result = config.to_dict()
    assert result["AllowEarlyCheckIn"] == allow_early_checkin
    assert result["MaxTimeToLiveInMinutes"] == max_time


# Test 6: Metadata property with required fields
@given(
    name=st.text(min_size=1),
    value=st.text(min_size=1)
)
def test_metadata_required_fields(name, value):
    """Test that Metadata requires both Name and Value."""
    metadata = licensemanager.Metadata(
        Name=name,
        Value=value
    )
    result = metadata.to_dict()
    assert result["Name"] == name
    assert result["Value"] == value


def test_metadata_missing_required_field():
    """Test that Metadata raises error when required field is missing."""
    metadata = licensemanager.Metadata(Name="test")
    with pytest.raises(ValueError, match="Value required"):
        metadata.to_dict()


# Test 7: Entitlement with boolean and integer validators
@given(
    allow_check_in=st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]),
    max_count=st.one_of(st.integers(), st.text().filter(lambda x: x.isdigit())),
    overage=st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]),
    name=st.text(min_size=1),
    unit=st.text(min_size=1)
)
def test_entitlement_with_validators(allow_check_in, max_count, overage, name, unit):
    """Test that Entitlement properly validates boolean and integer fields."""
    entitlement = licensemanager.Entitlement(
        AllowCheckIn=allow_check_in,
        MaxCount=max_count,
        Name=name,
        Overage=overage,
        Unit=unit
    )
    result = entitlement.to_dict()
    # Boolean fields should be normalized to True/False
    assert result["AllowCheckIn"] in [True, False]
    assert result["Overage"] in [True, False]
    # MaxCount should be convertible to int
    int(result["MaxCount"])


# Test 8: to_dict and from_dict round-trip
@given(
    name=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
    grant_name=st.text(min_size=1),
    home_region=st.text(min_size=1),
    license_arn=st.text(min_size=1),
    principals=st.lists(st.text(min_size=1), min_size=1),
    allowed_ops=st.lists(st.text(min_size=1), min_size=1),
    status=st.text(min_size=1)
)
def test_grant_to_dict_from_dict_roundtrip(
    name, grant_name, home_region, license_arn, principals, allowed_ops, status
):
    """Test that Grant can round-trip through to_dict and from_dict."""
    grant1 = licensemanager.Grant(
        name,
        GrantName=grant_name,
        HomeRegion=home_region,
        LicenseArn=license_arn,
        Principals=principals,
        AllowedOperations=allowed_ops,
        Status=status
    )
    
    # Convert to dict
    dict_repr = grant1.to_dict()
    
    # Extract properties (removing Type field)
    props = dict_repr.get("Properties", {})
    
    # Create new object from dict
    grant2 = licensemanager.Grant.from_dict(name, props)
    
    # Compare the two objects
    assert grant1 == grant2
    assert grant1.to_dict() == grant2.to_dict()


# Test 9: Equality properties
@given(
    title1=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
    title2=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1),
    grant_name=st.text(min_size=1),
    status=st.text(min_size=1)
)
def test_grant_equality(title1, title2, grant_name, status):
    """Test equality properties of Grant objects."""
    # Same title and properties should be equal
    grant1 = licensemanager.Grant(title1, GrantName=grant_name, Status=status)
    grant2 = licensemanager.Grant(title1, GrantName=grant_name, Status=status)
    assert grant1 == grant2
    assert not (grant1 != grant2)
    
    # Different titles should not be equal
    if title1 != title2:
        grant3 = licensemanager.Grant(title2, GrantName=grant_name, Status=status)
        assert grant1 != grant3
        assert not (grant1 == grant3)


# Test 10: Test integer range boundaries
@given(st.integers())
def test_max_time_to_live_accepts_any_integer(value):
    """Test that MaxTimeToLiveInMinutes accepts any integer value."""
    # Both BorrowConfiguration and ProvisionalConfiguration have this field
    try:
        config = licensemanager.BorrowConfiguration(
            AllowEarlyCheckIn=True,
            MaxTimeToLiveInMinutes=value
        )
        result = config.to_dict()
        # Should be able to convert back to int
        int(result["MaxTimeToLiveInMinutes"])
    except ValueError:
        # Only should fail if the integer validator fails
        with pytest.raises(ValueError):
            validators.integer(value)


# Test 11: ValidityDateFormat requires both Begin and End
def test_validity_date_format_missing_fields():
    """Test that ValidityDateFormat requires both Begin and End."""
    validity = licensemanager.ValidityDateFormat(Begin="2024-01-01")
    with pytest.raises(ValueError, match="End required"):
        validity.to_dict()
    
    validity2 = licensemanager.ValidityDateFormat(End="2024-12-31")
    with pytest.raises(ValueError, match="Begin required"):
        validity2.to_dict()


@given(
    begin=st.text(min_size=1),
    end=st.text(min_size=1)
)
def test_validity_date_format_with_both_fields(begin, end):
    """Test ValidityDateFormat with both required fields."""
    validity = licensemanager.ValidityDateFormat(Begin=begin, End=end)
    result = validity.to_dict()
    assert result["Begin"] == begin
    assert result["End"] == end