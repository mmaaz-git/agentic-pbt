"""Comprehensive test demonstrating the integer validator bug with floats."""

import sys
import json
from hypothesis import given, strategies as st, settings

# Add the venv site-packages to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.mediapackage import (
    StreamSelection, OriginEndpointCmafEncryption, OriginEndpointHlsManifest,
    OriginEndpointCmafPackage, OriginEndpointDashPackage, OriginEndpointHlsPackage,
    OriginEndpointMssPackage, OriginEndpoint, HlsManifest, CmafPackage,
    DashManifest, DashPackage, HlsPackage, MssPackage
)


@given(
    float_value=st.floats(
        allow_nan=False, 
        allow_infinity=False,
        min_value=-1e10,
        max_value=1e10
    ).filter(lambda x: x != int(x))  # Only non-integer floats
)
@settings(max_examples=20)
def test_integer_properties_accept_floats(float_value):
    """Test that integer properties incorrectly accept and preserve float values."""
    
    # Test StreamSelection integer properties
    stream = StreamSelection()
    stream.MaxVideoBitsPerSecond = float_value
    assert stream.MaxVideoBitsPerSecond == float_value
    assert isinstance(stream.MaxVideoBitsPerSecond, float)
    
    # Test serialization preserves float
    dict_repr = stream.to_dict()
    assert dict_repr["MaxVideoBitsPerSecond"] == float_value
    
    # JSON serialization also preserves float
    json_str = json.dumps(dict_repr)
    reloaded = json.loads(json_str)
    assert reloaded["MaxVideoBitsPerSecond"] == float_value
    assert isinstance(reloaded["MaxVideoBitsPerSecond"], float)
    
    # Test other integer properties
    cmaf_enc = OriginEndpointCmafEncryption(
        SpekeKeyProvider={"ResourceId": "r", "RoleArn": "a", "SystemIds": ["s"], "Url": "u"}
    )
    cmaf_enc.KeyRotationIntervalSeconds = float_value
    assert cmaf_enc.KeyRotationIntervalSeconds == float_value
    
    hls_manifest = OriginEndpointHlsManifest(Id="test")
    hls_manifest.PlaylistWindowSeconds = float_value
    assert hls_manifest.PlaylistWindowSeconds == float_value
    
    # All these should have been integers but are floats
    print(f"Float {float_value} accepted for integer properties")


if __name__ == "__main__":
    # Run the property test
    test_integer_properties_accept_floats()
    
    # Demonstrate specific problematic cases
    print("\nDemonstrating specific problematic cases:")
    
    # Case 1: Financial calculation result
    bitrate = 1000000.0 / 3  # Results in 333333.3333...
    stream = StreamSelection()
    stream.MaxVideoBitsPerSecond = bitrate
    print(f"1. Bitrate calculation: {bitrate}")
    print(f"   Stored as: {stream.MaxVideoBitsPerSecond}")
    print(f"   JSON: {json.dumps(stream.to_dict())}")
    
    # Case 2: Percentage calculation
    duration = 100 * 0.9  # 90.0 - looks like int but is float
    cmaf = OriginEndpointCmafPackage()
    cmaf.SegmentDurationSeconds = duration  
    print(f"\n2. Duration calculation: {duration}")
    print(f"   Type: {type(duration)}")
    print(f"   Stored as: {cmaf.SegmentDurationSeconds}")
    print(f"   JSON: {json.dumps(cmaf.to_dict())}")
    
    # Case 3: Division that happens to be exact
    window = 300.0 / 5.0  # 60.0 - exact division but still float
    hls = OriginEndpointHlsPackage()
    hls.PlaylistWindowSeconds = window
    print(f"\n3. Window calculation: {window}")
    print(f"   Type: {type(window)}")  
    print(f"   Stored as: {hls.PlaylistWindowSeconds}")
    print(f"   JSON: {json.dumps(hls.to_dict())}")
    
    print("\n⚠️ Bug Summary:")
    print("The integer validator accepts floats without converting them to integers.")
    print("This violates AWS CloudFormation's type requirements for integer properties.")
    print("CloudFormation templates generated with float values may fail validation.")