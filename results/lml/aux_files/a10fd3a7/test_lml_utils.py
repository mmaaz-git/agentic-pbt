import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
from lml.utils import PythonObjectEncoder, json_dumps, do_import_class


@given(st.one_of(
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.text(),
    st.integers(),
    st.floats(allow_nan=False),
    st.booleans(),
    st.none()
))
def test_pythonobjectencoder_basic_types_passthrough(obj):
    """Basic types should encode normally without _python_object wrapper"""
    encoder = PythonObjectEncoder()
    result = encoder.default(obj)
    
    # For basic types, the default method should delegate to parent
    # which will raise TypeError since we're calling it directly
    # So let's test via json_dumps instead
    encoded = json_dumps({"key": obj})
    decoded = json.loads(encoded)
    
    # Basic types should not have _python_object wrapper
    assert "_python_object" not in str(decoded["key"])
    

@given(st.builds(object))
def test_pythonobjectencoder_complex_types_wrapper(obj):
    """Non-basic types should get wrapped with _python_object"""
    encoder = PythonObjectEncoder()
    result = encoder.default(obj)
    
    assert isinstance(result, dict)
    assert "_python_object" in result
    assert isinstance(result["_python_object"], str)


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.booleans(),
        st.text(),
        st.none(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
))
def test_json_dumps_round_trip_basic_types(keywords):
    """json_dumps should produce valid JSON that can be decoded for basic types"""
    encoded = json_dumps(keywords)
    decoded = json.loads(encoded)
    
    # For basic types, round-trip should preserve values
    assert decoded == keywords


@given(st.text())
def test_do_import_class_requires_dot(class_path):
    """do_import_class should handle various input strings correctly"""
    # The function uses rsplit(".", 1) which requires at least one dot
    if "." not in class_path:
        # Should raise an error since rsplit needs to split on dot
        try:
            do_import_class(class_path)
            # If it doesn't raise, it means there was a successful import
            # which is unexpected for a string without dots
        except (ValueError, ImportError, AttributeError):
            # Expected - either rsplit fails or import fails
            pass
    else:
        # Has a dot, so rsplit will work
        # But the module/class may not exist
        try:
            result = do_import_class(class_path)
            # If successful, we imported something
            assert result is not None
        except (ImportError, AttributeError):
            # Expected for non-existent modules/classes
            pass


@given(st.text(min_size=1).filter(lambda x: "." not in x))
def test_do_import_class_no_dot_fails(class_path):
    """do_import_class should fail when there's no dot in the path"""
    try:
        do_import_class(class_path)
        # Shouldn't reach here - rsplit should fail to unpack
        assert False, f"Expected ValueError for {class_path!r} but got success"
    except ValueError as e:
        # Expected - rsplit(".", 1) returns single item, can't unpack into two
        assert "unpack" in str(e).lower() or "values" in str(e).lower()
    except (ImportError, AttributeError):
        # Also acceptable if import itself fails
        pass


@given(st.text())
def test_json_dumps_handles_any_input(keywords):
    """json_dumps should never crash, always produce valid JSON"""
    # Test with direct input (not necessarily dict)
    result = json_dumps(keywords)
    
    # Should always produce valid JSON
    decoded = json.loads(result)
    assert decoded is not None


@given(st.dictionaries(
    st.text(),
    st.builds(object)  # Complex objects
))
def test_json_dumps_complex_objects(keywords):
    """json_dumps should handle complex objects by wrapping them"""
    encoded = json_dumps(keywords)
    decoded = json.loads(encoded)
    
    # All values should be wrapped with _python_object
    for key, value in decoded.items():
        assert isinstance(value, dict)
        assert "_python_object" in value