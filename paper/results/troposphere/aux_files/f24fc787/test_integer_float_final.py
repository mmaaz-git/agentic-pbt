"""Demonstrates the integer validator bug that accepts floats."""

import sys
import json

# Add the venv site-packages to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.mediapackage import (
    StreamSelection, OriginEndpointCmafEncryption, OriginEndpointHlsManifest,
    OriginEndpointCmafPackage, OriginEndpointDashPackage, OriginEndpointHlsPackage,
    OriginEndpointMssPackage, OriginEndpoint, OriginEndpointSpekeKeyProvider,
    OriginEndpointDashEncryption, DashManifest
)


def demonstrate_integer_float_bug():
    """Demonstrate that integer properties accept and serialize float values."""
    
    print("=== Integer Validator Float Bug Demonstration ===\n")
    
    # Test 1: StreamSelection with float values
    print("Test 1: StreamSelection with float values")
    stream = StreamSelection()
    stream.MaxVideoBitsPerSecond = 1000000.5  # Should be integer
    stream.MinVideoBitsPerSecond = 500000.25  # Should be integer
    
    dict_repr = stream.to_dict()
    json_repr = json.dumps(dict_repr)
    
    print(f"  MaxVideoBitsPerSecond = 1000000.5")
    print(f"  Type stored: {type(stream.MaxVideoBitsPerSecond)}")
    print(f"  JSON output: {json_repr}")
    print(f"  ❌ CloudFormation expects Integer, got Float\n")
    
    # Test 2: OriginEndpointCmafEncryption with float KeyRotationIntervalSeconds
    print("Test 2: OriginEndpointCmafEncryption with float rotation interval")
    speke = OriginEndpointSpekeKeyProvider(
        ResourceId="resource-1",
        RoleArn="arn:aws:iam::123456789012:role/test",
        SystemIds=["system-1"],
        Url="https://example.com/keyserver"
    )
    cmaf_enc = OriginEndpointCmafEncryption(SpekeKeyProvider=speke)
    cmaf_enc.KeyRotationIntervalSeconds = 3600.75  # Should be integer
    
    dict_repr = cmaf_enc.to_dict()
    json_repr = json.dumps(dict_repr)
    
    print(f"  KeyRotationIntervalSeconds = 3600.75")
    print(f"  Type stored: {type(cmaf_enc.KeyRotationIntervalSeconds)}")
    print(f"  JSON output: {json_repr}")
    print(f"  ❌ CloudFormation expects Integer, got Float\n")
    
    # Test 3: OriginEndpointHlsManifest with float window seconds
    print("Test 3: OriginEndpointHlsManifest with float window")
    hls_manifest = OriginEndpointHlsManifest(Id="manifest-1")
    hls_manifest.PlaylistWindowSeconds = 300.5  # Should be integer
    hls_manifest.ProgramDateTimeIntervalSeconds = 60.25  # Should be integer
    
    dict_repr = hls_manifest.to_dict()
    json_repr = json.dumps(dict_repr)
    
    print(f"  PlaylistWindowSeconds = 300.5")
    print(f"  ProgramDateTimeIntervalSeconds = 60.25")
    print(f"  JSON output: {json_repr}")
    print(f"  ❌ CloudFormation expects Integer properties, got Floats\n")
    
    # Test 4: Real-world scenario - calculation results
    print("Test 4: Real-world calculation scenario")
    
    # Common scenario: dividing total bitrate among streams
    total_bitrate = 5000000
    num_streams = 3
    per_stream_bitrate = total_bitrate / num_streams  # Results in float!
    
    stream2 = StreamSelection()
    stream2.MaxVideoBitsPerSecond = per_stream_bitrate
    
    print(f"  Calculation: {total_bitrate} / {num_streams} = {per_stream_bitrate}")
    print(f"  Type: {type(per_stream_bitrate)}")
    print(f"  Stored value: {stream2.MaxVideoBitsPerSecond}")
    print(f"  JSON: {json.dumps(stream2.to_dict())}")
    print(f"  ❌ CloudFormation will reject: 1666666.6666666667 is not an integer\n")
    
    # Test 5: Edge case - float that looks like integer
    print("Test 5: Float that appears to be integer")
    
    duration = 10.0  # Common from calculations
    cmaf_package = OriginEndpointCmafPackage()
    cmaf_package.SegmentDurationSeconds = duration
    
    print(f"  Value: {duration} (type: {type(duration)})")
    print(f"  JSON: {json.dumps(cmaf_package.to_dict())}")
    print(f"  ⚠️  Even 10.0 is serialized as float, not integer\n")
    
    # Test 6: Verify through full template generation
    print("Test 6: Full CloudFormation template generation")
    
    from troposphere import Template
    
    template = Template()
    template.set_version("2010-09-09")
    template.set_description("Template with float integer properties")
    
    endpoint = OriginEndpoint(
        "TestEndpoint",
        ChannelId="test-channel",
        Id="test-endpoint"
    )
    endpoint.StartoverWindowSeconds = 86400.5  # Should be integer!
    endpoint.TimeDelaySeconds = 30.25  # Should be integer!
    
    template.add_resource(endpoint)
    
    # Generate the template
    template_json = template.to_json(indent=2)
    template_dict = json.loads(template_json)
    
    properties = template_dict["Resources"]["TestEndpoint"]["Properties"]
    print(f"  StartoverWindowSeconds in template: {properties.get('StartoverWindowSeconds')}")
    print(f"  TimeDelaySeconds in template: {properties.get('TimeDelaySeconds')}")
    print(f"  ❌ Template contains float values for integer properties\n")
    
    print("=" * 50)
    print("BUG SUMMARY:")
    print("=" * 50)
    print("The integer validator function in troposphere accepts float values")
    print("but does not convert them to integers. This causes:")
    print("1. Float values are stored in properties expecting integers")
    print("2. JSON/CloudFormation templates contain floats instead of integers")
    print("3. CloudFormation deployment will fail with type validation errors")
    print("\nAffected properties: All properties using the 'integer' validator")
    print("Impact: High - Templates will fail CloudFormation validation")


if __name__ == "__main__":
    demonstrate_integer_float_bug()