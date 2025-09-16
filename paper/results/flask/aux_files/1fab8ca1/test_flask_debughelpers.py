"""Property-based tests for flask.debughelpers module."""

import flask.debughelpers
from flask.debughelpers import DebugFilesKeyError, _dump_loader_info
from hypothesis import given, strategies as st, assume
from hypothesis import settings
from unittest.mock import Mock
from jinja2.loaders import BaseLoader


@st.composite
def mock_loaders(draw):
    """Generate mock loader objects with various attributes."""
    # Create a custom class instead of trying to modify Mock's __class__
    class TestLoader(BaseLoader):
        pass
    
    # Generate safe module and class names (no null characters)
    module_name = draw(st.text(
        alphabet=st.characters(blacklist_characters='\x00'),
        min_size=1, 
        max_size=50
    ))
    class_name = draw(st.text(
        alphabet=st.characters(blacklist_characters='\x00'),
        min_size=1, 
        max_size=50
    ))
    
    TestLoader.__module__ = module_name
    TestLoader.__name__ = class_name
    
    loader = TestLoader()
    
    # Generate a dictionary of attributes
    num_attrs = draw(st.integers(min_value=0, max_value=10))
    
    for _ in range(num_attrs):
        key = draw(st.text(min_size=1, max_size=20))
        # Generate various types of values
        value_strategy = st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.lists(st.text(), min_size=0, max_size=10),
            st.tuples(st.text(), st.text()),
            st.dictionaries(st.text(), st.text()),
            st.none(),
        )
        value = draw(value_strategy)
        setattr(loader, key, value)
    
    return loader


@given(mock_loaders())
def test_dump_loader_info_yields_only_strings(loader):
    """Test that _dump_loader_info always yields strings."""
    results = list(_dump_loader_info(loader))
    
    # Property: All yielded values should be strings
    for item in results:
        assert isinstance(item, str), f"Expected string, got {type(item)}: {item!r}"


@given(mock_loaders())
def test_dump_loader_info_filters_private_attributes(loader):
    """Test that _dump_loader_info correctly filters private attributes."""
    # Add some private attributes
    setattr(loader, '_private', "should not appear")
    setattr(loader, '__dunder__', "should not appear")
    setattr(loader, 'public', "should appear")
    
    results = list(_dump_loader_info(loader))
    result_text = '\n'.join(results)
    
    # Property: Private attributes should not appear in output
    assert '_private' not in result_text
    assert '__dunder__' not in result_text
    
    # Property: Public simple values should appear
    if isinstance(getattr(loader, 'public', None), (str, int, float, bool)):
        assert 'public' in result_text


@st.composite
def mock_requests(draw):
    """Generate mock request objects for DebugFilesKeyError."""
    request = Mock()
    request.mimetype = draw(st.text(min_size=0, max_size=100))
    
    # Mock form.getlist
    form_mock = Mock()
    # Generate a dict of form values
    form_data = draw(st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.lists(st.text(), min_size=0, max_size=5),
        min_size=0, max_size=10
    ))
    form_mock.getlist = lambda key: form_data.get(key, [])
    request.form = form_mock
    
    return request


@given(mock_requests(), st.text(min_size=0, max_size=100))
def test_debug_files_key_error_str_returns_string(request, key):
    """Test that DebugFilesKeyError.__str__() always returns a string."""
    error = DebugFilesKeyError(request, key)
    result = str(error)
    
    # Property: __str__ should always return a string
    assert isinstance(result, str)
    
    # Property: The key should appear in the error message
    assert key in result or repr(key) in result
    
    # Property: The mimetype should appear in the error message
    assert request.mimetype in result or repr(request.mimetype) in result


@given(
    st.text(min_size=0, max_size=100),
    st.lists(st.text(), min_size=1, max_size=10)
)
def test_debug_files_key_error_with_form_matches(key, form_values):
    """Test DebugFilesKeyError when form contains matching keys."""
    request = Mock()
    request.mimetype = "application/x-www-form-urlencoded"
    form_mock = Mock()
    form_mock.getlist = lambda k: form_values if k == key else []
    request.form = form_mock
    
    error = DebugFilesKeyError(request, key)
    result = str(error)
    
    # Property: When form matches exist, they should be mentioned
    if form_values:
        assert "browser instead transmitted" in result
        # At least one form value should appear in the message
        assert any(repr(val) in result for val in form_values)


@given(st.lists(st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none()
), min_size=0, max_size=20))
def test_dump_loader_info_list_handling(values):
    """Test _dump_loader_info handling of lists with mixed types."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    loader.test_list = values
    
    results = list(_dump_loader_info(loader))
    result_text = '\n'.join(results)
    
    # Property: Lists of all strings should be formatted specially
    if all(isinstance(x, str) for x in values):
        if values:  # Non-empty list of strings
            assert 'test_list:' in result_text
            for val in values:
                assert f"  - {val}" in result_text
    else:
        # Mixed types or non-strings should not use the special formatting
        assert '  - ' not in result_text or 'test_list:' not in result_text


@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.booleans()
    ),
    min_size=0,
    max_size=10
))
def test_dump_loader_info_simple_values(attrs):
    """Test that simple values are properly formatted."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    for key, value in attrs.items():
        setattr(loader, key, value)
    
    results = list(_dump_loader_info(loader))
    
    # First line should always be the class info
    assert results[0].startswith("class: test.TestLoader")
    
    # Property: All simple values should appear with key: value format
    for key, value in attrs.items():
        if not key.startswith('_'):
            expected = f"{key}: {value!r}"
            assert expected in results