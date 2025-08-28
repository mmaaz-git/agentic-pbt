#!/usr/bin/env python3
"""Property-based tests for troposphere.medialive module"""

import sys
import math
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
from troposphere.medialive import (
    AacSettings, Ac3Settings, Eac3Settings, Eac3AtmosSettings,
    Mp2Settings, WavSettings, AudioNormalizationSettings,
    InputChannelLevel, RemixSettings, BurnInDestinationSettings,
    DvbSubDestinationSettings, EbuTtDDestinationSettings
)

# Test 1: Integer validator should handle various integer-like inputs
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x.is_integer()),
    st.text(min_size=1).filter(lambda s: s.strip().replace('-', '').isdigit())
))
def test_integer_validator_accepts_valid_integers(value):
    """Test that integer validator accepts valid integer representations"""
    try:
        result = validators.integer(value)
        # Should be able to convert result to int
        int(result)
    except ValueError:
        # The validator raised ValueError, which is expected for non-integers
        if isinstance(value, str):
            # For strings, check if they're actually valid integers
            try:
                int(value)
                # If we can convert to int, the validator should have accepted it
                pytest.fail(f"Validator rejected valid integer string: {value}")
            except:
                pass  # Expected rejection

# Test 2: Double validator should handle various float-like inputs
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(min_size=1).filter(lambda s: s.strip().replace('-', '').replace('.', '').isdigit())
))
def test_double_validator_accepts_valid_floats(value):
    """Test that double validator accepts valid float representations"""
    try:
        result = validators.double(value)
        # Should be able to convert result to float
        float(result)
    except ValueError:
        # The validator raised ValueError, check if it should have
        if isinstance(value, (int, float)):
            pytest.fail(f"Validator rejected valid numeric value: {value}")

# Test 3: Boolean validator with edge cases
@given(st.one_of(
    st.sampled_from([True, False, 1, 0, "1", "0", "true", "false", "True", "False"]),
    st.text(min_size=1)
))
def test_boolean_validator_consistency(value):
    """Test that boolean validator consistently handles valid and invalid inputs"""
    try:
        result = validators.boolean(value)
        assert isinstance(result, bool), f"Result should be bool, got {type(result)}"
        
        # Verify consistency: same input should produce same output
        result2 = validators.boolean(value)
        assert result == result2, "Boolean validator not deterministic"
        
        # Check that the mapping is correct
        if value in [True, 1, "1", "true", "True"]:
            assert result is True, f"Expected True for {value}"
        elif value in [False, 0, "0", "false", "False"]:
            assert result is False, f"Expected False for {value}"
            
    except ValueError:
        # Should only raise for invalid values
        assert value not in [True, False, 1, 0, "1", "0", "true", "false", "True", "False"], \
            f"Validator incorrectly rejected valid boolean value: {value}"

# Test 4: Positive integer validator edge cases
@given(st.integers())
def test_positive_integer_validator(value):
    """Test positive_integer validator correctly accepts/rejects values"""
    try:
        result = validators.positive_integer(value)
        # If it succeeds, value should be >= 0
        assert int(value) >= 0, f"Positive integer validator accepted negative: {value}"
    except ValueError:
        # Should only reject negative integers
        assert int(value) < 0, f"Positive integer validator rejected non-negative: {value}"

# Test 5: MediaLive class property validation with integer fields
@given(
    dialnorm=st.one_of(st.integers(), st.text(), st.none()),
    bitrate=st.one_of(st.floats(allow_nan=False, allow_infinity=False), st.text(), st.none())
)
def test_ac3_settings_property_validation(dialnorm, bitrate):
    """Test that Ac3Settings correctly validates integer and double properties"""
    settings = Ac3Settings()
    
    # Test Dialnorm (should be integer)
    if dialnorm is not None:
        try:
            settings.Dialnorm = dialnorm
            # If assignment succeeded, verify we can get it back
            retrieved = settings.Dialnorm
            # Should be able to convert to int
            if not isinstance(dialnorm, str) or dialnorm.strip().replace('-', '').isdigit():
                int(retrieved)
        except (ValueError, TypeError):
            # Expected for invalid values
            pass
    
    # Test Bitrate (should be double)
    if bitrate is not None:
        try:
            settings.Bitrate = bitrate
            # If assignment succeeded, verify we can get it back
            retrieved = settings.Bitrate
            # Should be able to convert to float
            if not isinstance(bitrate, str) or bitrate.strip().replace('-', '').replace('.', '').isdigit():
                float(retrieved)
        except (ValueError, TypeError):
            # Expected for invalid values
            pass

# Test 6: Test opacity fields that should be integers (0-255 range typical)
@given(
    background_opacity=st.integers(min_value=-1000, max_value=1000),
    font_opacity=st.integers(min_value=-1000, max_value=1000),
    shadow_opacity=st.integers(min_value=-1000, max_value=1000)
)
def test_burn_in_settings_opacity_fields(background_opacity, font_opacity, shadow_opacity):
    """Test BurnInDestinationSettings opacity fields accept integer values"""
    settings = BurnInDestinationSettings()
    
    # These should accept integer values (though AWS might have range limits)
    # The troposphere library should at least validate they're integers
    try:
        settings.BackgroundOpacity = background_opacity
        assert settings.BackgroundOpacity == background_opacity
    except (ValueError, TypeError) as e:
        pytest.fail(f"Failed to set BackgroundOpacity to integer {background_opacity}: {e}")
    
    try:
        settings.FontOpacity = font_opacity
        assert settings.FontOpacity == font_opacity
    except (ValueError, TypeError) as e:
        pytest.fail(f"Failed to set FontOpacity to integer {font_opacity}: {e}")
        
    try:
        settings.ShadowOpacity = shadow_opacity
        assert settings.ShadowOpacity == shadow_opacity
    except (ValueError, TypeError) as e:
        pytest.fail(f"Failed to set ShadowOpacity to integer {shadow_opacity}: {e}")

# Test 7: Test InputChannelLevel with required integer fields
@given(
    gain=st.integers(min_value=-1000, max_value=1000),
    input_channel=st.integers(min_value=-1000, max_value=1000)
)
def test_input_channel_level_integers(gain, input_channel):
    """Test InputChannelLevel correctly handles integer properties"""
    level = InputChannelLevel()
    
    # Both Gain and InputChannel should accept integers
    try:
        level.Gain = gain
        assert level.Gain == gain
    except (ValueError, TypeError) as e:
        pytest.fail(f"Failed to set Gain to integer {gain}: {e}")
    
    try:
        level.InputChannel = input_channel
        assert level.InputChannel == input_channel
    except (ValueError, TypeError) as e:
        pytest.fail(f"Failed to set InputChannel to integer {input_channel}: {e}")

# Test 8: Test RemixSettings channels fields
@given(
    channels_in=st.integers(min_value=-100, max_value=100),
    channels_out=st.integers(min_value=-100, max_value=100)
)
def test_remix_settings_channels(channels_in, channels_out):
    """Test RemixSettings channel count fields accept integers"""
    settings = RemixSettings()
    
    try:
        settings.ChannelsIn = channels_in
        assert settings.ChannelsIn == channels_in
    except (ValueError, TypeError) as e:
        pytest.fail(f"Failed to set ChannelsIn to integer {channels_in}: {e}")
    
    try:
        settings.ChannelsOut = channels_out
        assert settings.ChannelsOut == channels_out
    except (ValueError, TypeError) as e:
        pytest.fail(f"Failed to set ChannelsOut to integer {channels_out}: {e}")

# Test 9: Test serialization round-trip for objects with validators
@given(
    bitrate=st.floats(min_value=0, max_value=1000000, allow_nan=False, allow_infinity=False),
    sample_rate=st.floats(min_value=8000, max_value=48000, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_aac_settings_serialization(bitrate, sample_rate):
    """Test that AacSettings can be created and serialized to dict"""
    settings = AacSettings()
    settings.Bitrate = bitrate
    settings.SampleRate = sample_rate
    
    # Should be able to convert to dict
    try:
        result = settings.to_dict()
        assert isinstance(result, dict)
        
        # Values should be preserved
        if 'Bitrate' in result:
            assert float(result['Bitrate']) == pytest.approx(bitrate)
        if 'SampleRate' in result:
            assert float(result['SampleRate']) == pytest.approx(sample_rate)
    except Exception as e:
        pytest.fail(f"Failed to serialize AacSettings: {e}")

# Test 10: Edge case - what happens with infinity/NaN for doubles?
@given(value=st.sampled_from([float('inf'), float('-inf'), float('nan')]))
def test_double_validator_special_floats(value):
    """Test how double validator handles special float values"""
    try:
        result = validators.double(value)
        # If it accepts these, we found interesting behavior
        if math.isnan(value):
            assert math.isnan(float(result)), "NaN not preserved"
        elif math.isinf(value):
            assert math.isinf(float(result)), "Infinity not preserved"
    except (ValueError, TypeError):
        # It might reject these, which is also valid
        pass

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])