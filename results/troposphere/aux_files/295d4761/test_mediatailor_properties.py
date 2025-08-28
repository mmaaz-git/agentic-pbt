import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.mediatailor as mediatailor
import troposphere.validators as validators
from troposphere import AWSProperty, AWSObject
import json
import math


# Test 1: Boolean validator round-trip property
@given(st.one_of(
    st.booleans(),
    st.sampled_from([0, 1, "0", "1", "true", "True", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """The boolean validator should correctly handle all documented valid inputs"""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    
    # Check that the conversion follows documented rules
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """The boolean validator should raise ValueError for invalid inputs"""
    try:
        validators.boolean(value)
        assert False, f"Expected ValueError for {value}"
    except ValueError:
        pass  # Expected


# Test 2: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(st.characters(whitelist_categories=["Nd"])).filter(lambda x: x and not x.startswith('0') or x == '0')
))
def test_integer_validator_valid_inputs(value):
    """The integer validator should accept integers and numeric strings"""
    try:
        result = validators.integer(value)
        # If it doesn't raise, the value should be convertible to int
        int(result)
    except ValueError:
        # For strings, only valid integer strings should pass
        if isinstance(value, str):
            try:
                int(value)
                assert False, f"integer() raised ValueError for valid string {value}"
            except ValueError:
                pass  # String wasn't a valid integer, so validator was correct


@given(st.one_of(
    st.floats().filter(lambda x: not x.is_integer() and not math.isnan(x) and not math.isinf(x)),
    st.text(alphabet=st.characters(blacklist_categories=["Nd", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf"])).filter(lambda x: x),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))  
def test_integer_validator_invalid_inputs(value):
    """The integer validator should raise ValueError for non-integer inputs"""
    try:
        validators.integer(value)
        # Check if the value is actually convertible to int
        try:
            int(value)
            # If it is, the validator was correct not to raise
        except (ValueError, TypeError):
            assert False, f"integer() should have raised ValueError for {value}"
    except ValueError:
        pass  # Expected


# Test 3: Double validator property  
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().map(lambda _: st.sampled_from(["1.5", "2.0", "-3.14", "0.0", "1e10", "-2.5e-3"]).example())
))
def test_double_validator_valid_inputs(value):
    """The double validator should accept floats, integers, and numeric strings"""
    try:
        result = validators.double(value)
        # If it doesn't raise, the value should be convertible to float
        float(result)
    except ValueError:
        # Check if input was actually valid
        if isinstance(value, (int, float)):
            assert False, f"double() raised ValueError for valid numeric {value}"
        elif isinstance(value, str):
            try:
                float(value)
                assert False, f"double() raised ValueError for valid string {value}"
            except ValueError:
                pass  # String wasn't valid, so validator was correct


# Test 4: Required property validation
@given(
    channel_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"])),
    playback_mode=st.sampled_from(["LOOP", "LINEAR"])
)
def test_channel_required_properties(channel_name, playback_mode):
    """Channel class should enforce its required properties"""
    # Test that we can create a valid Channel with all required props
    outputs = [mediatailor.RequestOutputItem(
        ManifestName="test",
        SourceGroup="test"
    )]
    
    channel = mediatailor.Channel(
        "TestChannel",
        ChannelName=channel_name,
        PlaybackMode=playback_mode,
        Outputs=outputs
    )
    
    # Should not raise during validation
    channel.to_dict()
    
    # Test that missing required properties raises ValueError
    try:
        bad_channel = mediatailor.Channel("BadChannel")
        bad_channel.to_dict()
        assert False, "Should have raised ValueError for missing required properties"
    except ValueError as e:
        assert "required" in str(e).lower()


# Test 5: Round-trip serialization property
@given(
    channel_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"])),
    playback_mode=st.sampled_from(["LOOP", "LINEAR"]),
    tier=st.one_of(st.none(), st.sampled_from(["BASIC", "STANDARD"]))
)  
def test_channel_round_trip_serialization(channel_name, playback_mode, tier):
    """to_dict and from_dict should form a proper round-trip"""
    outputs = [mediatailor.RequestOutputItem(
        ManifestName="manifest1",
        SourceGroup="source1"
    )]
    
    original = mediatailor.Channel(
        "TestChannel",
        ChannelName=channel_name,
        PlaybackMode=playback_mode,
        Outputs=outputs
    )
    
    if tier:
        original.Tier = tier
    
    # Serialize to dict
    dict_repr = original.to_dict()
    
    # Deserialize back
    reconstructed = mediatailor.Channel.from_dict("TestChannel", dict_repr["Properties"])
    
    # Should be equivalent
    assert original.to_dict() == reconstructed.to_dict()


# Test 6: LogConfiguration PercentEnabled validation
@given(percent=st.integers())
def test_log_configuration_percent_enabled(percent):
    """LogConfiguration should validate PercentEnabled is an integer"""
    try:
        config = mediatailor.LogConfiguration(PercentEnabled=percent)
        # Should succeed for any integer
        config.to_dict()
    except (ValueError, TypeError) as e:
        # The validators.integer function should not raise for integers
        assert False, f"Unexpected error for integer {percent}: {e}"


# Test 7: Property type validation
@given(
    value=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.booleans()
    )
)
def test_manifest_window_seconds_type_validation(value):
    """DashPlaylistSettings ManifestWindowSeconds should only accept doubles"""
    try:
        settings = mediatailor.DashPlaylistSettings(ManifestWindowSeconds=value)
        settings.to_dict()
        
        # If it succeeded, value should be convertible to float
        try:
            float(value)
        except (ValueError, TypeError):
            assert False, f"DashPlaylistSettings accepted non-numeric value: {value}"
    except (ValueError, TypeError):
        # Should only reject non-numeric values
        try:
            float(value)
            if not isinstance(value, bool):  # bool is technically numeric in Python
                assert False, f"DashPlaylistSettings rejected valid numeric value: {value}"
        except (ValueError, TypeError):
            pass  # Correctly rejected non-numeric


# Test 8: HTTP configuration BaseUrl required property
@given(
    base_url=st.one_of(
        st.none(),
        st.text(min_size=1).filter(lambda x: "http" in x.lower()),
        st.text(min_size=1).filter(lambda x: "http" not in x.lower())
    )
)
def test_http_configuration_base_url_required(base_url):
    """HttpConfiguration should require BaseUrl property"""
    if base_url is None:
        try:
            config = mediatailor.HttpConfiguration()
            config.to_dict()
            assert False, "Should require BaseUrl"
        except (ValueError, TypeError):
            pass  # Expected
    else:
        try:
            config = mediatailor.HttpConfiguration(BaseUrl=base_url)
            config.to_dict()
            # Should succeed with any non-None BaseUrl
        except ValueError as e:
            if "required" in str(e).lower():
                assert False, f"Rejected valid BaseUrl: {base_url}"