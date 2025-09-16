"""Property-based testing for troposphere.networkmanager module"""

import math
from hypothesis import assume, given, strategies as st, settings
import troposphere.networkmanager as nm
from troposphere.validators import boolean, double, integer


# Test validator functions
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts documented valid values"""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.data())
def test_boolean_validator_invalid_inputs(data):
    """Test that boolean validator rejects invalid values"""
    # Generate values that should not be valid booleans
    invalid_value = data.draw(st.one_of(
        st.integers().filter(lambda x: x not in [0, 1]),
        st.text(min_size=1).filter(lambda x: x not in ["true", "True", "false", "False", "0", "1"]),
        st.floats(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ))
    
    try:
        boolean(invalid_value)
        assert False, f"boolean() should have raised ValueError for {invalid_value}"
    except ValueError:
        pass  # Expected behavior


@given(st.one_of(
    st.integers(),
    st.text(alphabet="0123456789", min_size=1),
    st.text(alphabet="-0123456789", min_size=1).filter(lambda x: x != "-" and x != "")
))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer representations"""
    try:
        int(value)  # If this works, integer() should work
        result = integer(value)
        assert result == value
    except (ValueError, TypeError):
        # If int() fails, integer() should also fail
        try:
            integer(value)
            assert False, f"integer() should have raised ValueError for {value}"
        except ValueError:
            pass


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text(alphabet="0123456789.-", min_size=1).filter(
        lambda x: x.count('.') <= 1 and x not in ['.', '-', '-.'] and not x.startswith('-..')
    )
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid float representations"""
    try:
        float(value)  # If this works, double() should work
        result = double(value)
        assert result == value
    except (ValueError, TypeError):
        # If float() fails, double() should also fail
        try:
            double(value)
            assert False, f"double() should have raised ValueError for {value}"
        except ValueError:
            pass


# Test round-trip property for NetworkManager objects
@given(
    core_network_id=st.text(min_size=1, max_size=50),
    edge_location=st.text(min_size=1, max_size=50),
    transport_attachment_id=st.text(min_size=1, max_size=50),
    protocol=st.sampled_from(["GRE", "NO_ENCAP"])
)
def test_connect_attachment_round_trip(core_network_id, edge_location, transport_attachment_id, protocol):
    """Test that ConnectAttachment survives to_dict() -> _from_dict() conversion"""
    # Create object with required properties
    original = nm.ConnectAttachment(
        "TestAttachment",
        CoreNetworkId=core_network_id,
        EdgeLocation=edge_location,
        TransportAttachmentId=transport_attachment_id,
        Options=nm.ConnectAttachmentOptions(Protocol=protocol)
    )
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Convert back from dict
    reconstructed = nm.ConnectAttachment._from_dict(
        "TestAttachment",
        **dict_repr["Properties"]
    )
    
    # Verify round-trip
    assert reconstructed.to_dict() == dict_repr


@given(
    global_network_id=st.text(min_size=1, max_size=50),
    description=st.text(min_size=0, max_size=256)
)
def test_global_network_round_trip(global_network_id, description):
    """Test that GlobalNetwork survives to_dict() -> _from_dict() conversion"""
    # Create object
    original = nm.GlobalNetwork(
        "TestGlobalNetwork",
        Description=description
    )
    
    # Note: GlobalNetwork doesn't have required properties in props
    # but we can still test the round-trip with optional properties
    if description:
        original.Description = description
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    if "Properties" in dict_repr:
        # Convert back from dict
        reconstructed = nm.GlobalNetwork._from_dict(
            "TestGlobalNetwork",
            **dict_repr["Properties"]
        )
        
        # Verify round-trip
        assert reconstructed.to_dict() == dict_repr


@given(
    download_speed=st.integers(min_value=0, max_value=10000),
    upload_speed=st.integers(min_value=0, max_value=10000)
)
def test_bandwidth_property_validation(download_speed, upload_speed):
    """Test that Bandwidth property correctly validates integer values"""
    bandwidth = nm.Bandwidth(
        DownloadSpeed=download_speed,
        UploadSpeed=upload_speed
    )
    
    dict_repr = bandwidth.to_dict()
    
    # Verify the values are preserved
    assert dict_repr["DownloadSpeed"] == download_speed
    assert dict_repr["UploadSpeed"] == upload_speed
    
    # Test that invalid types are rejected
    try:
        nm.Bandwidth(DownloadSpeed="not_an_integer")
        assert False, "Should have raised an error for non-integer DownloadSpeed"
    except (TypeError, ValueError):
        pass  # Expected


@given(
    peer_asn=st.floats(min_value=1, max_value=4294967295, allow_nan=False, allow_infinity=False)
)
def test_bgp_options_peer_asn_validation(peer_asn):
    """Test that BgpOptions correctly handles PeerAsn as a double"""
    bgp = nm.BgpOptions(PeerAsn=peer_asn)
    
    dict_repr = bgp.to_dict()
    
    # The value should be preserved
    assert dict_repr["PeerAsn"] == peer_asn


@given(
    address=st.text(max_size=100),
    latitude=st.text(max_size=20),
    longitude=st.text(max_size=20)
)
def test_location_property_all_strings(address, latitude, longitude):
    """Test that Location accepts string values for coordinates as documented"""
    location = nm.Location(
        Address=address,
        Latitude=latitude,
        Longitude=longitude
    )
    
    dict_repr = location.to_dict()
    
    # All values should be preserved as strings
    if address:
        assert dict_repr["Address"] == address
    if latitude:
        assert dict_repr["Latitude"] == latitude
    if longitude:
        assert dict_repr["Longitude"] == longitude


# Test property constraints
@given(
    core_network_id=st.text(min_size=1, max_size=50),
    direct_connect_gateway_arn=st.text(min_size=1, max_size=50),
    edge_locations=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10)
)  
def test_direct_connect_gateway_required_properties(core_network_id, direct_connect_gateway_arn, edge_locations):
    """Test that DirectConnectGatewayAttachment enforces required properties"""
    # Should succeed with all required properties
    attachment = nm.DirectConnectGatewayAttachment(
        "TestDCGAttachment",
        CoreNetworkId=core_network_id,
        DirectConnectGatewayArn=direct_connect_gateway_arn,
        EdgeLocations=edge_locations
    )
    
    dict_repr = attachment.to_dict()
    assert dict_repr["Properties"]["CoreNetworkId"] == core_network_id
    assert dict_repr["Properties"]["DirectConnectGatewayArn"] == direct_connect_gateway_arn
    assert dict_repr["Properties"]["EdgeLocations"] == edge_locations