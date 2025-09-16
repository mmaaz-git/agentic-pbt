import json
import sys
import pytest
from hypothesis import given, strategies as st, assume, settings
import math

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators
from troposphere.fms import PortRange, IcmpTypeCode, NetworkAclEntry
from troposphere.validators.fms import validate_json_checker


# Test 1: json_checker round-trip property
@given(st.dictionaries(
    st.text(min_size=1), 
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ),
        lambda children: st.one_of(
            st.lists(children),
            st.dictionaries(st.text(min_size=1), children)
        ),
        max_leaves=10
    )
))
def test_json_checker_dict_round_trip(input_dict):
    """Test that json_checker converts dicts to JSON strings and back correctly"""
    result = validators.json_checker(input_dict)
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed == input_dict


@given(st.dictionaries(
    st.text(min_size=1),
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ),
        lambda children: st.one_of(
            st.lists(children),
            st.dictionaries(st.text(min_size=1), children)
        ),
        max_leaves=10
    )
))
def test_json_checker_string_idempotent(input_dict):
    """Test that json_checker on valid JSON strings is idempotent"""
    json_str = json.dumps(input_dict)
    result = validators.json_checker(json_str)
    assert result == json_str
    # Verify it's valid JSON
    json.loads(result)


# Test 2: boolean validator property
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts documented valid inputs"""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.data())
def test_boolean_validator_invalid_inputs(data):
    """Test that boolean validator rejects invalid inputs"""
    # Generate values that should be invalid
    invalid = data.draw(st.one_of(
        st.integers().filter(lambda x: x not in [0, 1]),
        st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
        st.floats(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ))
    
    with pytest.raises(ValueError):
        validators.boolean(invalid)


# Test 3: integer validator property
@given(st.integers())
def test_integer_validator_accepts_integers(value):
    """Test that integer validator accepts all integers"""
    result = validators.integer(value)
    assert result == value
    assert int(result) == value


@given(st.text(alphabet="0123456789-", min_size=1).filter(lambda x: x != "-"))
def test_integer_validator_accepts_numeric_strings(value):
    """Test that integer validator accepts numeric strings"""
    try:
        int(value)  # Only test if it's a valid integer string
        result = validators.integer(value)
        assert result == value
    except ValueError:
        pass  # Skip invalid numeric strings


# Test 4: network_port validator property
@given(st.integers(min_value=-1, max_value=65535))
def test_network_port_valid_range(port):
    """Test that network_port accepts ports in valid range [-1, 65535]"""
    result = validators.network_port(port)
    assert result == port


@given(st.one_of(
    st.integers(max_value=-2),
    st.integers(min_value=65536)
))
def test_network_port_invalid_range(port):
    """Test that network_port rejects ports outside valid range"""
    with pytest.raises(ValueError, match="network port .* must been between 0 and 65535"):
        validators.network_port(port)


# Test 5: PortRange class property
@given(
    st.integers(min_value=0, max_value=65535),
    st.integers(min_value=0, max_value=65535)
)
def test_portrange_valid_ports(from_port, to_port):
    """Test that PortRange accepts valid port numbers"""
    port_range = PortRange(From=from_port, To=to_port)
    assert port_range.properties["From"] == from_port
    assert port_range.properties["To"] == to_port
    
    # Test to_dict works
    d = port_range.to_dict()
    assert d["From"] == from_port
    assert d["To"] == to_port


# Test 6: IcmpTypeCode class property
@given(
    st.integers(min_value=-255, max_value=255),
    st.integers(min_value=-255, max_value=255)
)
def test_icmptypecode_accepts_integers(code, icmp_type):
    """Test that IcmpTypeCode accepts integer values for Code and Type"""
    icmp = IcmpTypeCode(Code=code, Type=icmp_type)
    assert icmp.properties["Code"] == code
    assert icmp.properties["Type"] == icmp_type
    
    # Test to_dict works
    d = icmp.to_dict()
    assert d["Code"] == code
    assert d["Type"] == icmp_type


# Test 7: NetworkAclEntry with PortRange property
@given(
    st.integers(min_value=0, max_value=65535),
    st.integers(min_value=0, max_value=65535),
    st.sampled_from(["tcp", "udp", "icmp", "6", "17", "1", "-1"]),
    st.sampled_from(["allow", "deny"]),
    st.booleans()
)
def test_network_acl_entry_with_portrange(from_port, to_port, protocol, rule_action, egress):
    """Test NetworkAclEntry can be created with PortRange"""
    port_range = PortRange(From=from_port, To=to_port)
    entry = NetworkAclEntry(
        PortRange=port_range,
        Protocol=protocol,
        RuleAction=rule_action,
        Egress=egress
    )
    
    d = entry.to_dict()
    assert d["PortRange"]["From"] == from_port
    assert d["PortRange"]["To"] == to_port
    assert d["Protocol"] == protocol
    assert d["RuleAction"] == rule_action
    assert d["Egress"] == egress


# Test 8: validate_json_checker is just an alias
@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.none(), st.booleans(), st.integers(), st.text())
))
def test_validate_json_checker_alias(input_dict):
    """Test that validate_json_checker behaves identically to json_checker"""
    result1 = validate_json_checker(input_dict)
    result2 = validators.json_checker(input_dict)
    assert result1 == result2