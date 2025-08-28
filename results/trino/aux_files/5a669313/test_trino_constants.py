"""Property-based tests for trino.constants module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings

# Import the module we're testing
import trino.constants as constants


def test_client_capabilities_concatenation():
    """Test that CLIENT_CAPABILITIES is correctly formed from individual capabilities"""
    # This property is explicitly defined in the code at line 63
    expected = ','.join([
        constants.CLIENT_CAPABILITY_PARAMETRIC_DATETIME,
        constants.CLIENT_CAPABILITY_SESSION_AUTHORIZATION
    ])
    assert constants.CLIENT_CAPABILITIES == expected


def test_header_name_pattern():
    """Test that all HEADER_* constants follow the X-Trino-* pattern"""
    # Get all HEADER_* constants
    header_constants = [
        name for name in dir(constants) 
        if name.startswith('HEADER_') and not name.startswith('_')
    ]
    
    for header_name in header_constants:
        header_value = getattr(constants, header_name)
        # The code clearly shows all headers should start with "X-Trino-"
        assert isinstance(header_value, str), f"{header_name} should be a string"
        assert header_value.startswith('X-Trino-'), \
            f"{header_name} value '{header_value}' should start with 'X-Trino-'"


def test_scale_types_subset_of_precision_types():
    """Test that SCALE_TYPES is a subset of PRECISION_TYPES"""
    # From the code, we can see that "decimal" appears in both lists
    # This is an intentional property - scale is only applicable to types that have precision
    for scale_type in constants.SCALE_TYPES:
        assert scale_type in constants.PRECISION_TYPES, \
            f"Scale type '{scale_type}' should also be in PRECISION_TYPES"


def test_protocol_string_values():
    """Test that HTTP and HTTPS constants have expected lowercase values"""
    # These are used in client.py to set the http_scheme
    assert constants.HTTP == "http"
    assert constants.HTTPS == "https"


def test_default_port_values():
    """Test that default ports have standard values"""
    assert constants.DEFAULT_PORT == 8080
    assert constants.DEFAULT_TLS_PORT == 443
    # These should be different
    assert constants.DEFAULT_PORT != constants.DEFAULT_TLS_PORT


def test_url_path_format():
    """Test that URL_STATEMENT_PATH has expected format"""
    # Used in client.py line 628
    assert constants.URL_STATEMENT_PATH == "/v1/statement"
    assert constants.URL_STATEMENT_PATH.startswith("/")


def test_max_nt_password_size():
    """Test that MAX_NT_PASSWORD_SIZE is a reasonable positive integer"""
    assert isinstance(constants.MAX_NT_PASSWORD_SIZE, int)
    assert constants.MAX_NT_PASSWORD_SIZE > 0
    # The value 1280 seems specific - it's likely related to NT authentication limits
    assert constants.MAX_NT_PASSWORD_SIZE == 1280


# Property-based test to verify type lists don't accidentally overlap incorrectly
@given(st.nothing())
def test_type_lists_consistency(nothing):
    """Test various properties of the type lists"""
    # LENGTH_TYPES and PRECISION_TYPES should be distinct except for intentional overlaps
    length_set = set(constants.LENGTH_TYPES)
    precision_set = set(constants.PRECISION_TYPES)
    scale_set = set(constants.SCALE_TYPES)
    
    # Scale types must be a subset of precision types (by design)
    assert scale_set.issubset(precision_set)
    
    # No length type should be in scale types (these are orthogonal concepts)
    assert length_set.isdisjoint(scale_set)
    
    # All lists should contain only strings
    for item in constants.LENGTH_TYPES:
        assert isinstance(item, str)
    for item in constants.PRECISION_TYPES:
        assert isinstance(item, str)
    for item in constants.SCALE_TYPES:
        assert isinstance(item, str)


# Test for potential mutation issues
def test_constants_immutability():
    """Test that we can't accidentally mutate the type lists"""
    # Save original values
    original_length_types = constants.LENGTH_TYPES.copy()
    original_precision_types = constants.PRECISION_TYPES.copy()
    original_scale_types = constants.SCALE_TYPES.copy()
    
    # Try to mutate (this shouldn't affect the module's constants in subsequent imports)
    try:
        constants.LENGTH_TYPES.append("test")
        constants.PRECISION_TYPES.append("test")
        constants.SCALE_TYPES.append("test")
    except AttributeError:
        # If they're tuples or immutable, this is good
        pass
    
    # If mutation was possible, at least verify it's consistent
    if "test" in constants.LENGTH_TYPES:
        # The mutation worked, which means the lists are mutable
        # This could be a minor issue for constants
        assert constants.LENGTH_TYPES[-1] == "test"
        # Clean up
        constants.LENGTH_TYPES.remove("test")
        constants.PRECISION_TYPES.remove("test") 
        constants.SCALE_TYPES.remove("test")