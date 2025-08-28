#!/usr/bin/env python3
import sys
import re
from hypothesis import given, assume, strategies as st, settings
import pytest

# Add the site-packages path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.opensearchservice import (
    WindowStartTime,
    validate_search_service_engine_version,
    AppConfig,
    DataSource,
    NodeConfig,
    ZoneAwarenessConfig
)
from troposphere.validators.opensearchservice import validate_search_service_engine_version as validator_func

# Property 1: validate_search_service_engine_version regex bug
# The regex uses an unescaped dot which matches any character, not just a literal dot
@given(st.text(min_size=1, max_size=100))
def test_engine_version_regex_should_only_accept_dots(version_string):
    """Test that the regex properly validates version strings with actual dots"""
    # The function should reject strings that have characters other than dots between numbers
    # but the regex bug allows any character because the dot is not escaped
    
    # Create versions with non-dot separators that should be rejected but aren't
    if re.match(r"^(OpenSearch_|Elasticsearch_)\d{1,5}.\d{1,5}", version_string):
        # Check if this matches with the buggy regex but shouldn't with correct regex
        correct_regex = re.compile(r"^(OpenSearch_|Elasticsearch_)\d{1,5}\.\d{1,5}")
        if not correct_regex.match(version_string):
            # This means the buggy regex accepts something it shouldn't
            try:
                result = validate_search_service_engine_version(version_string)
                # If we get here, the function accepted an invalid version
                assert False, f"Function accepted invalid version: {version_string}"
            except ValueError:
                # This is expected for invalid versions
                pass

# Property 2: Test specific invalid versions that exploit the regex bug
@given(
    prefix=st.sampled_from(["OpenSearch_", "Elasticsearch_"]),
    major=st.integers(min_value=0, max_value=99999),
    separator=st.sampled_from(["X", "#", "!", "@", "A", "B", " ", "-", "+"]),
    minor=st.integers(min_value=0, max_value=99999)
)
def test_invalid_separator_should_be_rejected(prefix, major, separator, minor):
    """Test that version strings with non-dot separators are rejected"""
    version_string = f"{prefix}{major}{separator}{minor}"
    
    # The buggy regex will match this because . matches any character
    buggy_regex = re.compile(r"^(OpenSearch_|Elasticsearch_)\d{1,5}.\d{1,5}")
    correct_regex = re.compile(r"^(OpenSearch_|Elasticsearch_)\d{1,5}\.\d{1,5}")
    
    if buggy_regex.match(version_string) and not correct_regex.match(version_string):
        # This version should be rejected but the bug allows it
        try:
            result = validate_search_service_engine_version(version_string)
            # Bug found: Invalid version accepted
            print(f"BUG: Invalid version accepted: {version_string}")
            assert False, f"Invalid version accepted: {version_string}"
        except ValueError:
            # Unexpected: the function correctly rejected it
            pass

# Property 3: Valid versions should always be accepted
@given(
    prefix=st.sampled_from(["OpenSearch_", "Elasticsearch_"]),
    major=st.integers(min_value=0, max_value=99999),
    minor=st.integers(min_value=0, max_value=99999)
)
def test_valid_versions_accepted(prefix, major, minor):
    """Test that valid version strings are accepted"""
    version_string = f"{prefix}{major}.{minor}"
    result = validate_search_service_engine_version(version_string)
    assert result == version_string

# Property 4: WindowStartTime hours and minutes validation
# These should be bounded but there's no validation
@given(
    hours=st.integers(),
    minutes=st.integers()
)
def test_window_start_time_accepts_invalid_times(hours, minutes):
    """Test WindowStartTime accepts invalid hour/minute values"""
    # WindowStartTime should validate that hours are 0-23 and minutes are 0-59
    # but it doesn't have any validation
    try:
        window = WindowStartTime(Hours=hours, Minutes=minutes)
        # Check if these are valid time values
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            # Bug: Invalid time values accepted
            print(f"BUG: WindowStartTime accepted invalid time: {hours}:{minutes}")
            assert False, f"WindowStartTime accepted invalid hours={hours}, minutes={minutes}"
    except (ValueError, TypeError) as e:
        # If it raises an error for invalid values, that's good
        pass

# Property 5: Test edge cases for WindowStartTime
@given(
    hours=st.one_of(
        st.integers(min_value=-1000, max_value=-1),
        st.integers(min_value=24, max_value=1000)
    ),
    minutes=st.one_of(
        st.integers(min_value=-1000, max_value=-1),
        st.integers(min_value=60, max_value=1000)
    )
)
def test_window_start_time_edge_cases(hours, minutes):
    """Test WindowStartTime with clearly invalid values"""
    window = WindowStartTime(Hours=hours, Minutes=minutes)
    # If we get here without error, it's a bug
    print(f"BUG: WindowStartTime accepted clearly invalid time: {hours}:{minutes}")
    assert False, f"WindowStartTime should reject hours={hours}, minutes={minutes}"

# Property 6: Test that property dictionaries maintain their structure
@given(
    count=st.integers(),
    enabled=st.booleans(),
    node_type=st.text()
)
def test_node_config_properties(count, enabled, node_type):
    """Test NodeConfig accepts any integer count without validation"""
    # NodeConfig Count should probably be non-negative but isn't validated
    node = NodeConfig(Count=count, Enabled=enabled, Type=node_type)
    
    if count < 0:
        # Bug: Negative node counts accepted
        print(f"BUG: NodeConfig accepted negative count: {count}")
        assert False, f"NodeConfig should reject negative count={count}"

# Property 7: ZoneAwarenessConfig should validate availability zone count
@given(az_count=st.integers())
def test_zone_awareness_config_az_count(az_count):
    """Test ZoneAwarenessConfig accepts invalid availability zone counts"""
    # AWS typically supports 2 or 3 AZs, max is usually 3-6 depending on region
    # Negative or very large values should be rejected
    config = ZoneAwarenessConfig(AvailabilityZoneCount=az_count)
    
    if az_count < 0 or az_count > 99:
        # Bug: Invalid AZ counts accepted
        print(f"BUG: ZoneAwarenessConfig accepted invalid AZ count: {az_count}")
        assert False, f"ZoneAwarenessConfig should validate AZ count={az_count}"

if __name__ == "__main__":
    # Run with increased examples for better coverage
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))