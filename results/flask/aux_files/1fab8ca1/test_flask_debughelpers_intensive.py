"""Intensive property-based tests to find bugs in flask.debughelpers."""

import flask.debughelpers
from flask.debughelpers import DebugFilesKeyError, _dump_loader_info, FormDataRoutingRedirect
from hypothesis import given, strategies as st, assume, settings, example
from unittest.mock import Mock
from jinja2.loaders import BaseLoader
from werkzeug.routing.exceptions import RequestRedirect


@settings(max_examples=1000)
@given(
    key=st.text(),
    mimetype=st.text(),
    form_values=st.lists(st.text(), min_size=0, max_size=10)
)
def test_debug_files_key_error_comprehensive(key, mimetype, form_values):
    """Comprehensive test for DebugFilesKeyError with many combinations."""
    request = Mock()
    request.mimetype = mimetype
    form_mock = Mock()
    form_mock.getlist = lambda k: form_values if k == key else []
    request.form = form_mock
    
    error = DebugFilesKeyError(request, key)
    result = str(error)
    
    # Property: Should always return a string
    assert isinstance(result, str)
    
    # Property: Key should be represented in the message
    assert repr(key) in result
    
    # Property: Mimetype should be represented in the message
    assert repr(mimetype) in result
    
    # Property: Form values should be mentioned if they exist
    if form_values:
        assert "browser instead transmitted" in result
        # At least one form value should be represented
        assert any(repr(val) in result for val in form_values)


@settings(max_examples=500)
@given(st.dictionaries(
    st.text(min_size=0, max_size=100),
    st.one_of(
        st.lists(st.one_of(
            st.text(),
            st.integers(),
            st.floats(),
            st.booleans(),
            st.none()
        ), min_size=0, max_size=50),
        st.tuples(st.text(), st.text(), st.text()),
        st.text(),
        st.integers(),
        st.floats(),
        st.booleans()
    ),
    min_size=0,
    max_size=20
))
def test_dump_loader_info_complex_attributes(attrs):
    """Test _dump_loader_info with complex attribute combinations."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test.module"
    TestLoader.__name__ = "ComplexLoader"
    
    loader = TestLoader()
    for key, value in attrs.items():
        setattr(loader, key, value)
    
    results = list(_dump_loader_info(loader))
    
    # Property: Should always start with class info
    assert results[0] == "class: test.module.ComplexLoader"
    
    # Property: All results should be strings
    assert all(isinstance(r, str) for r in results)
    
    # Verify formatting for different types
    for key, value in attrs.items():
        if key.startswith('_'):
            # Private attributes should not appear
            assert not any(key in r for r in results)
        elif isinstance(value, (list, tuple)) and all(isinstance(x, str) for x in value):
            # String lists/tuples should have special formatting
            if value:  # Non-empty
                assert any(f"{key}:" in r for r in results)
                for item in value:
                    assert any(f"  - {item}" in r for r in results)
        elif isinstance(value, (str, int, float, bool)):
            # Simple values should appear with repr
            assert any(f"{key}: {value!r}" in r for r in results)


@given(
    url=st.text(min_size=0, max_size=200),
    new_url=st.text(min_size=0, max_size=200),
    base_url=st.text(min_size=0, max_size=200)
)
def test_form_data_routing_redirect_urls(url, new_url, base_url):
    """Test FormDataRoutingRedirect with various URL formats."""
    request = Mock()
    request.url = url
    request.base_url = base_url
    
    # Create a mock routing exception
    routing_exc = Mock(spec=RequestRedirect)
    routing_exc.new_url = new_url
    request.routing_exception = routing_exc
    
    error = FormDataRoutingRedirect(request)
    result = str(error)
    
    # Property: Should always return a string
    assert isinstance(result, str)
    
    # Property: URLs should be in the message
    assert repr(url) in result or url in result
    assert repr(new_url) in result or new_url in result
    
    # Property: Should mention redirect
    assert "redirect" in result.lower()
    
    # Property: Check trailing slash detection
    if f"{base_url}/" == new_url.partition("?")[0]:
        assert "trailing slash" in result


@settings(max_examples=500)
@given(st.lists(
    st.one_of(
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))),
        st.just(''),
        st.text(min_size=1000, max_size=2000),  # Long strings
    ),
    min_size=0,
    max_size=30
))
def test_dump_loader_info_string_list_edge_cases(string_list):
    """Test _dump_loader_info with edge case string lists."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TestLoader"
    
    loader = TestLoader()
    loader.strings = string_list
    
    results = list(_dump_loader_info(loader))
    result_text = '\n'.join(results)
    
    # Property: Should handle all string lists without crashing
    assert all(isinstance(r, str) for r in results)
    
    # Property: String lists should be formatted correctly
    if string_list:
        assert 'strings:' in result_text
        for s in string_list:
            assert f"  - {s}" in result_text


@settings(max_examples=500)
@given(
    key1=st.text(min_size=1, max_size=50),
    key2=st.text(min_size=1, max_size=50),
    val1=st.one_of(st.text(), st.integers(), st.floats(), st.booleans()),
    val2=st.lists(st.text(), min_size=0, max_size=10)
)
def test_dump_loader_info_mixed_attributes(key1, key2, val1, val2):
    """Test _dump_loader_info with mixed attribute types."""
    assume(key1 != key2)  # Different keys
    assume(not key1.startswith('_') and not key2.startswith('_'))  # Public attrs
    
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "MixedLoader"
    
    loader = TestLoader()
    setattr(loader, key1, val1)
    setattr(loader, key2, val2)
    
    results = list(_dump_loader_info(loader))
    
    # Property: Both attributes should appear in output
    result_text = '\n'.join(results)
    
    # Simple value should appear with repr
    assert f"{key1}: {val1!r}" in result_text
    
    # List handling
    if all(isinstance(x, str) for x in val2):
        if val2:
            assert f"{key2}:" in result_text
            for item in val2:
                assert f"  - {item}" in result_text
    else:
        # Non-string lists shouldn't have special formatting
        if f"{key2}:" in result_text:
            assert not any(f"  - " in r for r in results)


@settings(max_examples=500)
@given(st.dictionaries(
    st.text(min_size=1, max_size=20).filter(lambda x: not x.startswith('_')),
    st.tuples(
        st.one_of(st.text(), st.integers()),
        st.one_of(st.text(), st.floats()),
        st.one_of(st.text(), st.booleans())
    ),
    min_size=0,
    max_size=10
))
def test_dump_loader_info_tuple_mixed_types(attrs):
    """Test _dump_loader_info with tuples containing mixed types."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = "test"
    TestLoader.__name__ = "TupleLoader"
    
    loader = TestLoader()
    for key, value in attrs.items():
        setattr(loader, key, value)
    
    results = list(_dump_loader_info(loader))
    result_text = '\n'.join(results)
    
    # Property: Mixed-type tuples should not get special formatting
    for key, value in attrs.items():
        if all(isinstance(x, str) for x in value):
            # All strings - should get special formatting
            assert f"{key}:" in result_text
            for item in value:
                assert f"  - {item}" in result_text
        else:
            # Mixed types - no special formatting
            if f"{key}:" in result_text:
                # Should not have the list-style formatting
                for item in value:
                    assert f"  - {item}" not in result_text


@settings(max_examples=1000)
@given(st.data())
def test_dump_loader_info_randomized(data):
    """Fully randomized test for _dump_loader_info."""
    class TestLoader(BaseLoader):
        pass
    
    TestLoader.__module__ = data.draw(st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),  # No surrogates or control chars
        min_size=1, 
        max_size=50
    ))
    TestLoader.__name__ = data.draw(st.text(
        alphabet=st.characters(blacklist_categories=('Cs', 'Cc')),  # No surrogates or control chars
        min_size=1, 
        max_size=50
    ))
    
    loader = TestLoader()
    
    # Add random attributes
    num_attrs = data.draw(st.integers(min_value=0, max_value=20))
    for _ in range(num_attrs):
        key = data.draw(st.text(min_size=1, max_size=30))
        value = data.draw(st.one_of(
            st.text(),
            st.integers(),
            st.floats(allow_nan=True, allow_infinity=True),
            st.booleans(),
            st.lists(st.text(), min_size=0, max_size=10),
            st.tuples(st.text(), st.text()),
            st.dictionaries(st.text(), st.text()),
            st.none()
        ))
        try:
            setattr(loader, key, value)
        except (AttributeError, ValueError):
            pass  # Some keys might not be valid attribute names
    
    # Should never crash
    results = list(_dump_loader_info(loader))
    
    # Property: All results must be strings
    assert all(isinstance(r, str) for r in results)
    
    # Property: First line must be class info
    expected_class = f"class: {TestLoader.__module__}.{TestLoader.__name__}"
    assert results[0] == expected_class