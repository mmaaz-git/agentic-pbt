import sys
import os
from datetime import timedelta
import random
import string
from hypothesis import given, strategies as st, assume, settings
import pytest
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'venv/lib/python3.13/site-packages'))

import flask
from flask import Flask
from flask.app import _make_timedelta
from werkzeug.datastructures import Headers


# Test 1: _make_timedelta round-trip property
@given(st.integers(min_value=-2147483648, max_value=2147483647))
def test_make_timedelta_int_conversion(seconds):
    """Test that _make_timedelta converts integers to timedelta correctly"""
    result = _make_timedelta(seconds)
    assert isinstance(result, timedelta)
    assert result.total_seconds() == seconds


@given(st.one_of(st.none(), st.timedeltas()))
def test_make_timedelta_passthrough(value):
    """Test that _make_timedelta passes through None and timedelta unchanged"""
    result = _make_timedelta(value)
    assert result is value


# Test 2: Flask.make_response tuple handling invariants
@given(st.text(min_size=1), st.integers(min_value=100, max_value=599))
def test_make_response_tuple_status(body, status_code):
    """Test that make_response correctly handles (body, status) tuples"""
    app = Flask(__name__)
    with app.test_request_context():
        response = app.make_response((body, status_code))
        assert response.get_data(as_text=True) == body
        assert response.status_code == status_code


@given(st.text(min_size=1), st.dictionaries(st.text(min_size=1), st.text()))
def test_make_response_tuple_headers(body, headers):
    """Test that make_response correctly handles (body, headers) tuples"""
    app = Flask(__name__)
    with app.test_request_context():
        headers_list = list(headers.items())
        response = app.make_response((body, headers_list))
        assert response.get_data(as_text=True) == body
        for key, value in headers.items():
            assert response.headers.get(key) == value


@given(
    st.text(min_size=1),
    st.integers(min_value=100, max_value=599),
    st.dictionaries(st.text(min_size=1), st.text())
)
def test_make_response_triple_tuple(body, status, headers):
    """Test that make_response correctly handles (body, status, headers) tuples"""
    app = Flask(__name__)
    with app.test_request_context():
        headers_list = list(headers.items())
        response = app.make_response((body, status, headers_list))
        assert response.get_data(as_text=True) == body
        assert response.status_code == status
        for key, value in headers.items():
            assert response.headers.get(key) == value


# Test 3: URL generation properties
@given(st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=50))
def test_url_for_endpoint_dots(endpoint_suffix):
    """Test that url_for with dot-prefixed endpoints works correctly"""
    app = Flask(__name__)
    
    @app.route(f'/test/{endpoint_suffix}')
    def test_view():
        return 'test'
    
    # Register the endpoint
    app.add_url_rule(f'/test/{endpoint_suffix}', endpoint=endpoint_suffix, view_func=test_view)
    
    with app.test_request_context():
        # Generate URL without dot prefix
        url1 = app.url_for(endpoint_suffix)
        # Should generate the same URL with explicit endpoint
        url2 = app.url_for(f'.{endpoint_suffix}')
        
        # Without a blueprint, dot-prefix should be stripped
        assert url1 == url2


# Test 4: Response handling invariants
@given(st.lists(st.integers()))
def test_make_response_list_json(data):
    """Test that lists are jsonified correctly"""
    app = Flask(__name__)
    with app.test_request_context():
        response = app.make_response(data)
        assert response.is_json
        assert response.get_json() == data


@given(st.dictionaries(st.text(min_size=1), st.one_of(st.integers(), st.text(), st.none())))
def test_make_response_dict_json(data):
    """Test that dicts are jsonified correctly"""
    app = Flask(__name__)
    with app.test_request_context():
        response = app.make_response(data)
        assert response.is_json
        assert response.get_json() == data


# Test 5: Invalid tuple sizes should raise errors
@given(st.lists(st.text(), min_size=4, max_size=10))
def test_make_response_invalid_tuple_size(items):
    """Test that tuples with invalid sizes raise TypeError"""
    app = Flask(__name__)
    with app.test_request_context():
        with pytest.raises(TypeError, match="did not return a valid response tuple"):
            app.make_response(tuple(items))


@given(st.tuples())
def test_make_response_empty_tuple():
    """Test that empty tuple raises TypeError"""
    app = Flask(__name__)
    with app.test_request_context():
        with pytest.raises(TypeError, match="did not return a valid response tuple"):
            app.make_response(())


@given(st.tuples(st.text()))
def test_make_response_single_element_tuple(t):
    """Test that single element tuple raises TypeError"""
    app = Flask(__name__)
    with app.test_request_context():
        with pytest.raises(TypeError, match="did not return a valid response tuple"):
            app.make_response(t)


# Test 6: Config handling properties
@given(st.dictionaries(
    st.text(alphabet=string.ascii_uppercase + "_", min_size=1, max_size=20),
    st.one_of(st.integers(), st.text(), st.none(), st.booleans())
))
def test_flask_config_update_preserves_keys(config_dict):
    """Test that updating Flask config preserves all keys"""
    app = Flask(__name__)
    original_keys = set(app.config.keys())
    
    app.config.update(config_dict)
    
    # All original keys should still be present
    assert original_keys.issubset(set(app.config.keys()))
    
    # All new keys should be present
    for key, value in config_dict.items():
        assert app.config[key] == value


# Test 7: Testing edge cases with URL anchors
@given(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    st.text(min_size=1)
)
def test_url_for_with_anchor(endpoint_name, anchor_text):
    """Test URL generation with anchors"""
    app = Flask(__name__)
    
    @app.route(f'/{endpoint_name}')
    def view():
        return 'test'
    
    app.add_url_rule(f'/{endpoint_name}', endpoint=endpoint_name, view_func=view)
    
    with app.test_request_context():
        url = app.url_for(endpoint_name, _anchor=anchor_text)
        # URL should end with the anchor
        from urllib.parse import quote
        expected_anchor = quote(anchor_text, safe="%!#$&'()*+,/:;=?@")
        assert url.endswith(f'#{expected_anchor}')


# Test 8: Test status code setting with different types
@given(st.integers(min_value=100, max_value=599))
def test_make_response_status_int(status_code):
    """Test that integer status codes are set correctly"""
    app = Flask(__name__)
    with app.test_request_context():
        response = app.make_response(("test", status_code))
        assert response.status_code == status_code


@given(st.text().filter(lambda x: any(c.isdigit() for c in x) and len(x) >= 3))
def test_make_response_status_string(status_string):
    """Test that string status codes are handled"""
    app = Flask(__name__)
    with app.test_request_context():
        # String status should be set as status
        response = app.make_response(("test", 200))
        response.status = status_string
        assert response.status == status_string


if __name__ == "__main__":
    print("Running property-based tests for flask.app module...")
    pytest.main([__file__, "-v", "--tb=short"])