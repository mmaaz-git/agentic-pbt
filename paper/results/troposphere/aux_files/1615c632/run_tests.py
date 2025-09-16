#!/usr/bin/env python3
"""Run the property-based tests"""

import sys
import traceback

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, Verbosity
import troposphere.networkmanager as nm
from troposphere.validators import boolean, double, integer

print("Running property-based tests for troposphere.networkmanager...")
print("=" * 60)

# Test 1: Boolean validator with valid inputs
print("\nTest 1: Boolean validator with valid inputs")
try:
    @given(st.one_of(
        st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
        st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
    ))
    @settings(max_examples=100)
    def test_boolean_valid(value):
        result = boolean(value)
        assert isinstance(result, bool)
        if value in [True, 1, "1", "true", "True"]:
            assert result is True
        else:
            assert result is False
    
    test_boolean_valid()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 2: Boolean validator with invalid inputs
print("\nTest 2: Boolean validator with invalid inputs")
try:
    @given(st.integers().filter(lambda x: x not in [0, 1]))
    @settings(max_examples=50)
    def test_boolean_invalid(value):
        try:
            boolean(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass
    
    test_boolean_invalid()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 3: Integer validator
print("\nTest 3: Integer validator")
try:
    @given(st.one_of(st.integers(), st.text(alphabet="0123456789-", min_size=1)))
    @settings(max_examples=100)
    def test_integer_validator(value):
        try:
            int_val = int(value)
            result = integer(value)
            assert result == value
        except (ValueError, TypeError):
            try:
                integer(value)
                assert False, f"integer() should have raised ValueError"
            except ValueError:
                pass
    
    test_integer_validator()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 4: Double validator
print("\nTest 4: Double validator")
try:
    @given(st.one_of(
        st.floats(allow_nan=False, allow_infinity=False),
        st.integers()
    ))
    @settings(max_examples=100)
    def test_double_validator(value):
        result = double(value)
        assert result == value
    
    test_double_validator()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 5: ConnectAttachment round-trip
print("\nTest 5: ConnectAttachment round-trip property")
try:
    @given(
        core_network_id=st.text(min_size=1, max_size=50),
        edge_location=st.text(min_size=1, max_size=50),
        transport_attachment_id=st.text(min_size=1, max_size=50),
        protocol=st.sampled_from(["GRE", "NO_ENCAP"])
    )
    @settings(max_examples=20)
    def test_connect_attachment_roundtrip(core_network_id, edge_location, transport_attachment_id, protocol):
        original = nm.ConnectAttachment(
            "TestAttachment",
            CoreNetworkId=core_network_id,
            EdgeLocation=edge_location,
            TransportAttachmentId=transport_attachment_id,
            Options=nm.ConnectAttachmentOptions(Protocol=protocol)
        )
        
        dict_repr = original.to_dict()
        reconstructed = nm.ConnectAttachment._from_dict(
            "TestAttachment",
            **dict_repr["Properties"]
        )
        
        assert reconstructed.to_dict() == dict_repr
    
    test_connect_attachment_roundtrip()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 6: BgpOptions PeerAsn as double
print("\nTest 6: BgpOptions PeerAsn validation")
try:
    @given(peer_asn=st.floats(min_value=1, max_value=4294967295, allow_nan=False, allow_infinity=False))
    @settings(max_examples=50)
    def test_bgp_peer_asn(peer_asn):
        bgp = nm.BgpOptions(PeerAsn=peer_asn)
        dict_repr = bgp.to_dict()
        assert dict_repr["PeerAsn"] == peer_asn
    
    test_bgp_peer_asn()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 7: Location with string coordinates
print("\nTest 7: Location with string coordinates")
try:
    @given(
        latitude=st.text(max_size=20),
        longitude=st.text(max_size=20)
    )
    @settings(max_examples=50)
    def test_location_strings(latitude, longitude):
        location = nm.Location(
            Latitude=latitude,
            Longitude=longitude
        )
        dict_repr = location.to_dict()
        if latitude:
            assert dict_repr["Latitude"] == latitude
        if longitude:
            assert dict_repr["Longitude"] == longitude
    
    test_location_strings()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

# Test 8: Bandwidth integer validation
print("\nTest 8: Bandwidth integer property validation")
try:
    @given(
        download=st.integers(min_value=0, max_value=10000),
        upload=st.integers(min_value=0, max_value=10000)
    )
    @settings(max_examples=50)
    def test_bandwidth(download, upload):
        bandwidth = nm.Bandwidth(
            DownloadSpeed=download,
            UploadSpeed=upload
        )
        dict_repr = bandwidth.to_dict()
        assert dict_repr["DownloadSpeed"] == download
        assert dict_repr["UploadSpeed"] == upload
    
    test_bandwidth()
    print("✓ Passed")
except Exception as e:
    print(f"✗ Failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing complete!")