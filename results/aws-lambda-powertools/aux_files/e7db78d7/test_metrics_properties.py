#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import math
import warnings
from datetime import datetime, timedelta
from unittest.mock import patch

from hypothesis import assume, given, settings, strategies as st
import pytest

from aws_lambda_powertools.metrics import Metrics, MetricUnit, MetricResolution
from aws_lambda_powertools.metrics.exceptions import (
    MetricValueError, 
    SchemaValidationError,
    MetricResolutionError,
    MetricUnitError
)
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.exceptions import MetricNameError
from aws_lambda_powertools.metrics.provider.cloudwatch_emf.cloudwatch import AmazonCloudWatchEMFProvider
from aws_lambda_powertools.metrics.functions import validate_emf_timestamp, extract_cloudwatch_metric_resolution_value


# Test 1: Metric name length validation (must be 1-255 characters)
@given(
    name=st.text(min_size=0, max_size=300).filter(lambda x: len(x.strip()) != len(x) or len(x.strip()) < 1 or len(x.strip()) > 255)
)
def test_invalid_metric_name_length_raises_error(name):
    """Test that metric names outside 1-255 characters after stripping raise MetricNameError"""
    provider = AmazonCloudWatchEMFProvider()
    
    with pytest.raises(MetricNameError):
        provider.add_metric(name=name, unit=MetricUnit.Count, value=1)


@given(
    name=st.text(min_size=1, max_size=255).filter(lambda x: 1 <= len(x.strip()) <= 255)
)
def test_valid_metric_name_length_accepted(name):
    """Test that metric names within 1-255 characters after stripping are accepted"""
    provider = AmazonCloudWatchEMFProvider()
    
    # Should not raise any error
    provider.add_metric(name=name, unit=MetricUnit.Count, value=1)
    assert name.strip() in provider.metric_set


# Test 2: Metric value must be a number
@given(
    value=st.one_of(
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.none(),
        st.booleans()
    )
)
def test_non_numeric_metric_value_raises_error(value):
    """Test that non-numeric metric values raise MetricValueError"""
    assume(not isinstance(value, bool))  # booleans are numbers in Python
    assume(not isinstance(value, (int, float)))
    
    provider = AmazonCloudWatchEMFProvider()
    
    with pytest.raises(MetricValueError):
        provider.add_metric(name="TestMetric", unit=MetricUnit.Count, value=value)


@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    )
)
def test_numeric_metric_value_accepted(value):
    """Test that numeric metric values are accepted and stored as floats"""
    provider = AmazonCloudWatchEMFProvider()
    
    provider.add_metric(name="TestMetric", unit=MetricUnit.Count, value=value)
    assert "TestMetric" in provider.metric_set
    assert float(value) in provider.metric_set["TestMetric"]["Value"]


# Test 3: Maximum dimensions limit
@given(
    dimensions=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
            st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
        ),
        min_size=30,
        max_size=50,
        unique_by=lambda x: x[0]
    )
)
def test_exceeding_max_dimensions_raises_error(dimensions):
    """Test that adding more than 29 dimensions raises SchemaValidationError"""
    provider = AmazonCloudWatchEMFProvider()
    
    # Add dimensions up to the limit
    for i, (name, value) in enumerate(dimensions[:29]):
        provider.add_dimension(name=name, value=value)
    
    # The 30th dimension should raise an error
    if len(dimensions) >= 30:
        with pytest.raises(SchemaValidationError):
            provider.add_dimension(name=dimensions[29][0], value=dimensions[29][1])


# Test 4: Dimension name/value validation
@given(
    name=st.one_of(st.just(""), st.text(min_size=1).map(lambda x: " " * len(x))),
    value=st.text(min_size=1)
)
def test_empty_dimension_name_is_ignored_with_warning(name, value):
    """Test that empty dimension names (after stripping) are ignored with a warning"""
    provider = AmazonCloudWatchEMFProvider()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        provider.add_dimension(name=name, value=value)
        
        # Should have triggered a warning
        assert len(w) == 1
        assert "doesn't meet the requirements" in str(w[0].message)
        
        # Dimension should not be added
        assert name not in provider.dimension_set


@given(
    name=st.text(min_size=1).filter(lambda x: x.strip()),
    value=st.one_of(st.just(""), st.text(min_size=1).map(lambda x: " " * len(x)))
)
def test_empty_dimension_value_is_ignored_with_warning(name, value):
    """Test that empty dimension values (after stripping) are ignored with a warning"""
    provider = AmazonCloudWatchEMFProvider()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        provider.add_dimension(name=name, value=value)
        
        # Should have triggered a warning
        assert len(w) == 1
        assert "doesn't meet the requirements" in str(w[0].message)
        
        # Dimension should not be added
        assert name not in provider.dimension_set


# Test 5: Serialization validation
def test_serialize_empty_metrics_raises_error():
    """Test that serializing with no metrics raises SchemaValidationError"""
    provider = AmazonCloudWatchEMFProvider(namespace="TestNamespace")
    
    with pytest.raises(SchemaValidationError, match="Must contain at least one metric"):
        provider.serialize_metric_set()


def test_serialize_without_namespace_raises_error():
    """Test that serializing without namespace raises SchemaValidationError"""
    provider = AmazonCloudWatchEMFProvider()
    provider.add_metric(name="TestMetric", unit=MetricUnit.Count, value=1)
    
    with pytest.raises(SchemaValidationError, match="Must contain a metric namespace"):
        provider.serialize_metric_set()


# Test 6: Timestamp validation
@given(
    days_offset=st.integers(min_value=-30, max_value=-15)
)
def test_timestamp_too_far_in_past_is_invalid(days_offset):
    """Test that timestamps more than 14 days in the past are invalid"""
    timestamp = datetime.now() + timedelta(days=days_offset)
    assert not validate_emf_timestamp(timestamp)


@given(
    hours_offset=st.floats(min_value=2.1, max_value=100)
)
def test_timestamp_too_far_in_future_is_invalid(hours_offset):
    """Test that timestamps more than 2 hours in the future are invalid"""
    timestamp = datetime.now() + timedelta(hours=hours_offset)
    assert not validate_emf_timestamp(timestamp)


@given(
    days_offset=st.floats(min_value=-14, max_value=0),
    hours_offset=st.floats(min_value=0, max_value=2)
)
def test_timestamp_within_valid_range_is_valid(days_offset, hours_offset):
    """Test that timestamps within valid range are accepted"""
    # Create timestamp within valid range
    timestamp = datetime.now() + timedelta(days=days_offset, hours=hours_offset)
    
    # Ensure we're not going into the future beyond 2 hours
    max_future = datetime.now() + timedelta(hours=2)
    if timestamp > max_future:
        timestamp = max_future - timedelta(minutes=1)
    
    assert validate_emf_timestamp(timestamp)


# Test 7: Metric resolution validation
@given(
    resolution=st.integers().filter(lambda x: x not in [1, 60])
)
def test_invalid_resolution_raises_error(resolution):
    """Test that invalid resolution values raise MetricResolutionError"""
    metric_resolutions = [1, 60]
    
    with pytest.raises(MetricResolutionError):
        extract_cloudwatch_metric_resolution_value(metric_resolutions, resolution)


@given(
    resolution=st.sampled_from([1, 60])
)
def test_valid_resolution_accepted(resolution):
    """Test that valid resolution values (1 or 60) are accepted"""
    provider = AmazonCloudWatchEMFProvider()
    
    provider.add_metric(name="TestMetric", unit=MetricUnit.Count, value=1, resolution=resolution)
    assert provider.metric_set["TestMetric"]["StorageResolution"] == resolution


# Test 8: Duplicate dimension warning
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    value1=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    value2=st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
)
def test_duplicate_dimension_warns_and_overwrites(name, value1, value2):
    """Test that adding duplicate dimensions warns and overwrites the value"""
    provider = AmazonCloudWatchEMFProvider()
    
    # Add first dimension
    provider.add_dimension(name=name, value=value1)
    assert provider.dimension_set[name] == value1
    
    # Add duplicate dimension
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        provider.add_dimension(name=name, value=value2)
        
        # Should have triggered a warning about overwriting
        assert len(w) == 1
        assert "already been added" in str(w[0].message)
        
        # Value should be overwritten
        assert provider.dimension_set[name] == value2


# Test 9: Non-string dimension values are converted
@given(
    name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    value=st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False))
)
def test_non_string_dimension_values_converted_to_string(name, value):
    """Test that non-string dimension values are converted to strings"""
    provider = AmazonCloudWatchEMFProvider()
    
    provider.add_dimension(name=name, value=value)
    
    # Value should be converted to string
    assert provider.dimension_set[name] == str(value)
    assert isinstance(provider.dimension_set[name], str)


# Test 10: Metrics accumulation and auto-flush at 100 metrics
@given(
    metric_names=st.lists(
        st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        min_size=100,
        max_size=105,
        unique=True
    )
)
def test_metrics_auto_flush_at_100_limit(metric_names):
    """Test that metrics are automatically flushed when reaching 100 metrics"""
    provider = AmazonCloudWatchEMFProvider(namespace="TestNamespace")
    
    with patch('builtins.print') as mock_print:
        # Add 99 metrics
        for i in range(99):
            provider.add_metric(name=metric_names[i], unit=MetricUnit.Count, value=i)
        
        # The 100th metric should trigger a flush
        provider.add_metric(name=metric_names[99], unit=MetricUnit.Count, value=99)
        
        # Verify flush was called (print was called with JSON)
        assert mock_print.called
        
        # After flush, metric set should be cleared
        assert len(provider.metric_set) == 0