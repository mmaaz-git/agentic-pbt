"""Edge case tests for flask.debughelpers module."""

import flask.debughelpers
from flask.debughelpers import DebugFilesKeyError, _dump_loader_info
from hypothesis import given, strategies as st, assume, settings
from hypothesis import example
from unittest.mock import Mock
from jinja2.loaders import BaseLoader


@given(st.text())
def test_debug_files_key_error_with_special_characters(key):
    """Test DebugFilesKeyError with various special characters in key."""
    request = Mock()
    request.mimetype = "text/html"
    form_mock = Mock()
    form_mock.getlist = lambda k: []
    request.form = form_mock
    
    error = DebugFilesKeyError(request, key)
    result = str(error)
    
    # Property: Should always return a string without failing
    assert isinstance(result, str)
    
    # Property: The formatted message should contain expected parts
    assert "request.files" in result
    assert "multipart/form-data" in result


@given(st.text())
@example("")  # Empty string edge case
@example("\x00")  # Null character
@example("a" * 10000)  # Very long string
def test_debug_files_key_error_extreme_mimetypes(mimetype):
    """Test DebugFilesKeyError with extreme mimetype values."""
    request = Mock()
    request.mimetype = mimetype
    form_mock = Mock()
    form_mock.getlist = lambda k: []
    request.form = form_mock
    
    error = DebugFilesKeyError(request, "test_key")
    result = str(error)
    
    # Property: Should handle any mimetype without crashing
    assert isinstance(result, str)
    
    # Property: repr of mimetype should be in the message
    assert repr(mimetype) in result


@given(st.lists(st.text(), min_size=0, max_size=100))
def test_debug_files_key_error_many_form_matches(form_values):
    """Test DebugFilesKeyError with many form matches."""
    request = Mock()
    request.mimetype = "text/plain"
    form_mock = Mock()
    form_mock.getlist = lambda k: form_values if k == "key" else []
    request.form = form_mock
    
    error = DebugFilesKeyError(request, "key")
    result = str(error)
    
    # Property: Should handle any number of form matches
    assert isinstance(result, str)
    
    # Property: If there are form matches, they should be mentioned
    if form_values:
        assert "browser instead transmitted" in result


@given(st.dictionaries(
    st.text(),
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=True, allow_infinity=True),  # Include NaN and infinity
        st.booleans(),
        st.lists(st.text()),
        st.tuples(st.text()),
        st.dictionaries(st.text(), st.text()),
        st.none(),
    ),
    min_size=0,
    max_size=100
))
def test_dump_loader_info_with_special_values(attrs):
    """Test _dump_loader_info with NaN, infinity, and other special values."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    for key, value in attrs.items():
        setattr(loader, key, value)
    
    # This should not crash regardless of the values
    results = list(_dump_loader_info(loader))
    
    # Property: Should always yield strings
    for item in results:
        assert isinstance(item, str)
    
    # Property: First line should always be class info
    assert len(results) > 0
    assert results[0] == "class: test.TestLoader"


@given(st.lists(st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.booleans(),
    st.none(),
    st.lists(st.text()),  # Nested lists
), min_size=0, max_size=50))
def test_dump_loader_info_nested_structures(values):
    """Test _dump_loader_info with nested data structures."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    loader.nested_list = values
    
    results = list(_dump_loader_info(loader))
    
    # Property: Should handle nested structures without crashing
    assert all(isinstance(item, str) for item in results)
    
    # Property: Non-string lists should not be specially formatted
    if not all(isinstance(x, str) for x in values):
        result_text = '\n'.join(results)
        # Should not have the special list formatting
        if 'nested_list' in result_text:
            assert '  - ' not in result_text


@given(st.text(min_size=0, max_size=1000))
def test_dump_loader_info_attribute_names(attr_name):
    """Test _dump_loader_info with various attribute names."""
    assume(attr_name)  # Skip empty strings
    
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    setattr(loader, attr_name, "test_value")
    
    results = list(_dump_loader_info(loader))
    result_text = '\n'.join(results)
    
    # Property: Private attributes (starting with _) should be filtered
    if attr_name.startswith('_'):
        assert attr_name not in result_text
    else:
        # Public attributes should appear
        assert f"{attr_name}: 'test_value'" in result_text


@given(st.tuples(st.text(), st.text()))
def test_dump_loader_info_tuple_elements(tuple_val):
    """Test _dump_loader_info with tuples containing various strings."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    loader.test_tuple = tuple_val
    
    results = list(_dump_loader_info(loader))
    
    # Property: Should handle tuples without crashing
    assert all(isinstance(item, str) for item in results)
    
    # Property: Tuples of strings should be formatted specially
    result_text = '\n'.join(results)
    if all(isinstance(x, str) for x in tuple_val):
        assert 'test_tuple:' in result_text
        for item in tuple_val:
            assert f"  - {item}" in result_text


@given(st.dictionaries(
    st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=1114111)),
    st.text(),
    min_size=0,
    max_size=50
))
def test_dump_loader_info_unicode_keys(attrs):
    """Test _dump_loader_info with unicode characters in keys."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    for key, value in attrs.items():
        try:
            setattr(loader, key, value)
        except (AttributeError, ValueError):
            # Some unicode characters might not be valid attribute names
            pass
    
    # Should handle unicode without crashing
    results = list(_dump_loader_info(loader))
    
    # Property: All results should be strings
    assert all(isinstance(item, str) for item in results)


@given(st.lists(st.text(alphabet=st.characters(min_codepoint=0, max_codepoint=1114111)), 
                min_size=0, max_size=20))
def test_dump_loader_info_unicode_list_values(values):
    """Test _dump_loader_info with unicode strings in lists."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    loader.unicode_list = values
    
    # Should handle unicode strings in lists without crashing
    results = list(_dump_loader_info(loader))
    result_text = '\n'.join(results)
    
    # Property: All results should be strings
    assert all(isinstance(item, str) for item in results)
    
    # Property: Lists of strings should be specially formatted
    if values and all(isinstance(x, str) for x in values):
        assert 'unicode_list:' in result_text
        for val in values:
            assert f"  - {val}" in result_text


@settings(max_examples=500)
@given(st.floats())
def test_dump_loader_info_float_edge_cases(float_val):
    """Test _dump_loader_info with float edge cases like NaN and infinity."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    loader.float_attr = float_val
    
    results = list(_dump_loader_info(loader))
    
    # Property: Should handle all float values including NaN and infinity
    assert all(isinstance(item, str) for item in results)
    
    # Property: Float values should be represented with repr()
    result_text = '\n'.join(results)
    assert f"float_attr: {float_val!r}" in result_text