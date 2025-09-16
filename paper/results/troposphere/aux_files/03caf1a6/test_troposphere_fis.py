import json
import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.fis as fis
from troposphere.validators import integer

# Test 1: Integer validator function
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers())
))
def test_integer_validator_property(value):
    """Test that integer validator accepts values convertible to int and rejects others"""
    try:
        int(value)
        should_pass = True
    except (ValueError, TypeError):
        should_pass = False
    
    try:
        result = integer(value)
        assert should_pass, f"integer({value}) should have raised ValueError"
        # If it passes, the result should be the original value
        assert result == value
        # And int(result) should work
        int(result)
    except ValueError as e:
        assert not should_pass, f"integer({value}) raised ValueError unexpectedly: {e}"


# Test 2: Round-trip property for S3Configuration
@given(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
def test_s3_configuration_round_trip(bucket_name, prefix):
    """Test S3Configuration to_dict and from_dict round-trip"""
    props = {"BucketName": bucket_name}
    if prefix is not None:
        props["Prefix"] = prefix
    
    # Create object
    s3_config = fis.S3Configuration(**props)
    
    # Convert to dict
    dict_repr = s3_config.to_dict()
    
    # Create new object from dict
    s3_config2 = fis.S3Configuration._from_dict(**dict_repr)
    
    # They should be equal
    assert s3_config.to_dict() == s3_config2.to_dict()
    assert s3_config == s3_config2


# Test 3: Required property validation
@given(
    st.text(min_size=1, max_size=100),
    st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
def test_required_property_validation(dashboard_id, prefix):
    """Test that required properties are properly validated"""
    # CloudWatchDashboard requires DashboardIdentifier
    try:
        dashboard = fis.CloudWatchDashboard()
        dashboard.to_dict()  # This should trigger validation
        assert False, "Should have raised ValueError for missing required property"
    except ValueError as e:
        assert "required" in str(e).lower()
    
    # With required property, it should work
    dashboard = fis.CloudWatchDashboard(DashboardIdentifier=dashboard_id)
    dict_repr = dashboard.to_dict()
    assert "DashboardIdentifier" in dict_repr
    assert dict_repr["DashboardIdentifier"] == dashboard_id


# Test 4: ExperimentTemplateLogConfiguration integer validation
@given(
    st.one_of(
        st.integers(min_value=-1000, max_value=1000),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans()
    ),
    st.text(min_size=1, max_size=100)
)
def test_log_configuration_integer_property(log_schema_version, bucket_name):
    """Test that LogSchemaVersion property uses integer validator correctly"""
    s3_config = fis.S3Configuration(BucketName=bucket_name)
    
    # Check if the value can be converted to int
    try:
        int(log_schema_version)
        should_pass = True
    except (ValueError, TypeError):
        should_pass = False
    
    try:
        log_config = fis.ExperimentTemplateLogConfiguration(
            LogSchemaVersion=log_schema_version,
            S3Configuration=s3_config
        )
        dict_repr = log_config.to_dict()
        assert should_pass, f"LogSchemaVersion={log_schema_version} should have failed validation"
        assert "LogSchemaVersion" in dict_repr
    except (ValueError, TypeError) as e:
        assert not should_pass, f"LogSchemaVersion={log_schema_version} failed unexpectedly: {e}"


# Test 5: Property equality
@given(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
)
def test_property_equality_symmetric(bucket1, bucket2):
    """Test that equality is symmetric for AWS properties"""
    obj1 = fis.S3Configuration(BucketName=bucket1)
    obj2 = fis.S3Configuration(BucketName=bucket2)
    
    # Equality should be symmetric
    if obj1 == obj2:
        assert obj2 == obj1
    if obj1 != obj2:
        assert obj2 != obj1
    
    # Object should equal itself
    assert obj1 == obj1
    assert obj2 == obj2


# Test 6: ExperimentTemplateTargetFilter Values property
@given(
    st.text(min_size=1, max_size=100),
    st.one_of(
        st.lists(st.text(min_size=1), min_size=1, max_size=10),
        st.text(),
        st.integers(),
        st.none()
    )
)  
def test_target_filter_values_list_property(path, values):
    """Test that Values property must be a list of strings"""
    is_valid_values = isinstance(values, list) and all(isinstance(v, str) for v in values)
    
    try:
        target_filter = fis.ExperimentTemplateTargetFilter(
            Path=path,
            Values=values
        )
        dict_repr = target_filter.to_dict()
        assert is_valid_values or not target_filter.do_validation, \
            f"Values={values} should have failed validation"
        assert "Values" in dict_repr
    except (TypeError, ValueError) as e:
        assert not is_valid_values, f"Values={values} failed unexpectedly: {e}"


# Test 7: Nested property round-trip
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=0, max_size=50)
)
def test_nested_property_round_trip(bucket_name, prefix):
    """Test round-trip for nested properties"""
    # Create nested structure
    s3_config = fis.ExperimentReportS3Configuration(
        BucketName=bucket_name,
        Prefix=prefix if prefix else None
    )
    outputs = fis.Outputs(ExperimentReportS3Configuration=s3_config)
    report_config = fis.ExperimentTemplateExperimentReportConfiguration(
        Outputs=outputs
    )
    
    # Convert to dict
    dict_repr = report_config.to_dict()
    
    # Recreate from dict
    report_config2 = fis.ExperimentTemplateExperimentReportConfiguration._from_dict(**dict_repr)
    
    # Should be equal
    assert report_config.to_dict() == report_config2.to_dict()