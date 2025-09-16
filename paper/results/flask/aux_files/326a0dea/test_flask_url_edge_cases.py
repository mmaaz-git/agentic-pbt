"""Additional property tests exploring Flask URL generation edge cases."""

import string
from hypothesis import given, strategies as st, assume, settings
from flask import Flask
import flask


# Strategy for Flask app names
app_names = st.text(min_size=1, max_size=100).filter(lambda s: '/' not in s and '\\' not in s)

# Strategy for valid Python identifiers (endpoint names)
valid_identifiers = st.text(
    alphabet=string.ascii_letters + string.digits + '_',
    min_size=1,
    max_size=50
).filter(lambda s: s[0].isalpha() or s[0] == '_')


@given(
    app_name=app_names,
    endpoint=valid_identifiers,
    special_chars=st.text(alphabet='<>[]{}|\\^`', min_size=1, max_size=10)
)
def test_url_generation_with_special_chars(app_name, endpoint, special_chars):
    """Test URL generation with special characters that need escaping."""
    
    app = Flask(app_name)
    
    # Create a route that accepts any string
    @app.route('/item/<path:value>')
    def view_func(value):
        return f'Value: {value}'
    
    # Register with custom endpoint name
    app.add_url_rule('/special/<path:data>', endpoint=endpoint, view_func=view_func)
    
    with app.test_request_context():
        # Generate URL with special characters
        url = flask.url_for(endpoint, data=special_chars)
        
        # The URL should be generated (not raise an exception)
        assert isinstance(url, str)
        assert '/special/' in url
        
        # Special characters should be properly encoded
        # < and > should be URL-encoded
        if '<' in special_chars:
            assert '%3C' in url or '<' not in url  # Should be encoded
        if '>' in special_chars:
            assert '%3E' in url or '>' not in url  # Should be encoded


@given(
    app_name=app_names,
    param_name=valid_identifiers,
    int_value=st.integers()
)
def test_url_generation_int_coercion(app_name, param_name, int_value):
    """Test that integer parameters in URL generation are handled correctly."""
    
    app = Flask(app_name)
    
    # Create a route with int converter
    rule = f'/num/<int:{param_name}>'
    
    @app.route(rule)
    def view_func(**kwargs):
        return 'ok'
    
    with app.test_request_context():
        # Generate URL with integer parameter
        url = flask.url_for('view_func', **{param_name: int_value})
        
        # Should contain the string representation of the integer
        assert str(int_value) in url
        assert url.startswith('/num/')


@given(
    app_name=app_names,
    float_value=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_url_generation_float_converter(app_name, float_value):
    """Test URL generation with float converter."""
    
    app = Flask(app_name)
    
    @app.route('/float/<float:value>')
    def float_view(value):
        return f'Float: {value}'
    
    with app.test_request_context():
        url = flask.url_for('float_view', value=float_value)
        
        # URL should be generated
        assert isinstance(url, str)
        assert '/float/' in url
        
        # Check that the float is represented in the URL
        # (May be formatted differently, e.g., scientific notation)
        # But it should be parseable back to a float
        float_part = url.replace('/float/', '')
        try:
            reconstructed = float(float_part)
            # Allow for floating point imprecision
            if abs(float_value) > 1e-10:
                assert abs(reconstructed - float_value) / abs(float_value) < 1e-7
            else:
                assert abs(reconstructed - float_value) < 1e-10
        except ValueError:
            # If we can't parse it back, that might be a bug
            assert False, f"Could not parse float from URL: {float_part}"


@given(
    app_name=app_names,
    unicode_string=st.text(alphabet='αβγδεζηθικλμνξοπρστυφχψω中文字符🎉🦄', min_size=1, max_size=20)
)
def test_url_generation_unicode(app_name, unicode_string):
    """Test URL generation with Unicode characters."""
    
    app = Flask(app_name)
    
    @app.route('/unicode/<path:text>')
    def unicode_view(text):
        return f'Text: {text}'
    
    with app.test_request_context():
        url = flask.url_for('unicode_view', text=unicode_string)
        
        # URL should be generated
        assert isinstance(url, str)
        assert '/unicode/' in url
        
        # Unicode should be properly percent-encoded
        # Non-ASCII characters should be encoded
        for char in unicode_string:
            if ord(char) > 127:
                # Should be percent-encoded
                assert char not in url  # Raw unicode shouldn't appear


@given(
    app_name=app_names,
    endpoint=valid_identifiers,
    num_params=st.integers(min_value=1, max_value=5)
)
def test_url_multiple_converters(app_name, endpoint, num_params):
    """Test URL generation with multiple converters in one route."""
    
    app = Flask(app_name)
    
    # Build a route with multiple parameters
    parts = ['/multi']
    param_names = []
    for i in range(num_params):
        param_name = f'p{i}'
        param_names.append(param_name)
        if i % 2 == 0:
            parts.append(f'<int:{param_name}>')
        else:
            parts.append(f'<{param_name}>')
    
    rule = '/'.join(parts)
    
    def view_func(**kwargs):
        return 'ok'
    
    app.add_url_rule(rule, endpoint=endpoint, view_func=view_func)
    
    with app.test_request_context():
        # Generate URL with all parameters
        kwargs = {}
        for i, param_name in enumerate(param_names):
            if i % 2 == 0:
                kwargs[param_name] = i * 10
            else:
                kwargs[param_name] = f'val{i}'
        
        url = flask.url_for(endpoint, **kwargs)
        
        # All values should appear in the URL
        for i, param_name in enumerate(param_names):
            if i % 2 == 0:
                assert str(i * 10) in url
            else:
                assert f'val{i}' in url


@given(
    app_name=app_names,
    slash_count=st.integers(min_value=0, max_value=5)
)
def test_url_generation_trailing_slashes(app_name, slash_count):
    """Test URL generation with various trailing slash configurations."""
    
    app = Flask(app_name)
    
    # Create route with specific number of trailing slashes
    route = '/test' + '/' * slash_count
    
    @app.route(route)
    def test_view():
        return 'ok'
    
    with app.test_request_context():
        url = flask.url_for('test_view')
        
        # URL should be generated
        assert isinstance(url, str)
        assert url.startswith('/test')
        
        # Check trailing slash behavior
        # Flask typically normalizes these
        if slash_count > 0:
            # Should have exactly one trailing slash
            assert url.endswith('/') or url == '/test'