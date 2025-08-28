import json
from hypothesis import given, strategies as st
import troposphere.workspacesweb as target


@given(st.one_of(
    st.binary(min_size=1, max_size=10).filter(lambda b: b.decode('ascii', errors='ignore').replace('.','').replace('-','').isdigit() if b.decode('ascii', errors='ignore') else False),
    st.builds(bytearray, st.binary(min_size=1, max_size=10))
))
def test_double_accepts_bytes_causing_json_serialization_failure(byte_value):
    """double() accepts bytes/bytearray which causes JSON serialization to fail"""
    # Ensure the bytes can be converted to float
    try:
        float(byte_value)
    except (ValueError, TypeError):
        # Skip if float() can't handle it
        return
    
    # double() accepts the bytes
    result = target.double(byte_value)
    assert result == byte_value
    
    # Now use it in InlineRedactionPattern
    pattern = target.InlineRedactionPattern(
        ConfidenceLevel=byte_value,
        RedactionPlaceHolder=target.RedactionPlaceHolder(
            RedactionPlaceHolderType='Text'
        )
    )
    
    # Get the dictionary representation
    pattern_dict = pattern.to_dict()
    assert pattern_dict['ConfidenceLevel'] == byte_value
    
    # This should fail - bytes are not JSON serializable
    try:
        json.dumps(pattern_dict)
        assert False, f"JSON serialization should have failed for bytes value {byte_value!r}"
    except TypeError as e:
        assert "not JSON serializable" in str(e)