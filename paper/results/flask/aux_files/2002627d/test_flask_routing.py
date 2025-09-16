"""Property-based tests for Flask routing and URL generation"""
import flask
from flask import Flask
from hypothesis import assume, given, strategies as st, settings
import re
from urllib.parse import quote, unquote


# Strategy for valid endpoint names
endpoint_names = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), min_codepoint=97),
    min_size=1,
    max_size=20
).filter(lambda x: x[0].isalpha() and '.' not in x)

# Strategy for URL-safe strings
url_safe_strings = st.text(
    alphabet=st.characters(blacklist_characters='\x00\r\n#?&=/<>%\\', min_codepoint=32, max_codepoint=126),
    min_size=0,
    max_size=20
)


@given(
    endpoint=endpoint_names,
    rule=st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='/_-'),
        min_size=2,
        max_size=30
    ).filter(lambda x: x.startswith('/') and '//' not in x)
)
def test_flask_route_registration(endpoint, rule):
    """Test that routes can be registered and retrieved correctly"""
    app = Flask(__name__)
    
    @app.route(rule, endpoint=endpoint)
    def test_view():
        return "test"
    
    # Route should be registered
    assert endpoint in app.view_functions
    assert app.view_functions[endpoint] == test_view
    
    # Should be in URL map
    rules = list(app.url_map.iter_rules())
    rule_endpoints = [r.endpoint for r in rules]
    assert endpoint in rule_endpoints


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10).filter(lambda x: x.isidentifier()),
        url_safe_strings,
        min_size=0,
        max_size=5
    )
)
def test_flask_url_for_with_params(params):
    """Test url_for with various parameter combinations"""
    app = Flask(__name__)
    
    # Create a route with variable parts
    @app.route('/test/<var>')
    def test_view(var):
        return f"var={var}"
    
    with app.test_request_context():
        if 'var' in params:
            # Should generate URL with the parameter
            url = flask.url_for('test_view', **params)
            assert f"/test/{params['var']}" in url
            
            # Extra params should become query string
            extra_params = {k: v for k, v in params.items() if k != 'var'}
            if extra_params:
                for key, value in extra_params.items():
                    assert f"{key}={value}" in url or f"{key}={quote(str(value))}" in url


@given(st.text(min_size=1, max_size=50))
def test_flask_escape_markup_safety(text):
    """Test that flask.escape properly escapes HTML characters"""
    from markupsafe import Markup, escape
    
    # Flask uses MarkupSafe's escape
    escaped = escape(text)
    
    # Should be a Markup object
    assert isinstance(escaped, Markup)
    
    # HTML special characters should be escaped
    if '<' in text:
        assert '&lt;' in str(escaped)
    if '>' in text:
        assert '&gt;' in str(escaped)
    if '&' in text:
        assert '&amp;' in str(escaped)
    if '"' in text:
        assert '&quot;' in str(escaped) or '&#34;' in str(escaped)
    if "'" in text:
        assert '&#39;' in str(escaped) or '&#x27;' in str(escaped)
    
    # Escaping twice should be safe (idempotent for Markup)
    double_escaped = escape(escaped)
    assert str(double_escaped) == str(escaped)


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=20).filter(lambda x: x.startswith('/') and ' ' not in x),
            endpoint_names
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[1]  # Unique endpoints
    )
)
def test_flask_multiple_routes(routes):
    """Test registering multiple routes"""
    app = Flask(__name__)
    
    # Register all routes
    for rule, endpoint in routes:
        # Skip invalid patterns
        if '<' in rule and '>' not in rule:
            continue
            
        def make_view(ep):
            def view():
                return ep
            return view
        
        app.add_url_rule(rule, endpoint=endpoint, view_func=make_view(endpoint))
    
    # All endpoints should be registered
    for rule, endpoint in routes:
        if '<' in rule and '>' not in rule:
            continue
        assert endpoint in app.view_functions


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda x: x.isupper()),
        st.one_of(
            st.integers(),
            st.text(max_size=100),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=20
    )
)
def test_flask_config_consistency(config_data):
    """Test that Flask config maintains consistency across operations"""
    app = Flask(__name__)
    
    # Set initial config
    for key, value in config_data.items():
        app.config[key] = value
    
    # Get a snapshot
    snapshot1 = dict(app.config)
    
    # Update with same data (should be idempotent)
    app.config.update(config_data)
    snapshot2 = dict(app.config)
    
    # Should be identical
    for key in config_data:
        assert snapshot1[key] == snapshot2[key] == config_data[key]
    
    # Test from_mapping
    app2 = Flask(__name__)
    app2.config.from_mapping(config_data)
    
    for key, value in config_data.items():
        assert app2.config[key] == value


@given(st.integers(100, 599))
def test_flask_abort_status_codes(status_code):
    """Test that flask.abort raises correct HTTP exceptions"""
    from werkzeug.exceptions import HTTPException
    
    try:
        flask.abort(status_code)
        assert False, "abort should have raised an exception"
    except HTTPException as e:
        # Should have the correct status code
        if hasattr(e, 'code'):
            assert e.code == status_code or (status_code not in range(100, 600) and e.code in [500, 404])


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=0, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_flask_session_like_dict(session_data):
    """Test that Flask session object behaves like a dictionary"""
    app = Flask(__name__)
    app.secret_key = 'test_secret_key'
    
    with app.test_request_context():
        session = flask.session
        
        # Should support dictionary operations
        for key, value in session_data.items():
            session[key] = value
        
        # All data should be accessible
        for key, value in session_data.items():
            assert session.get(key) == value
            assert key in session
        
        # Should support update
        session.update(session_data)
        for key, value in session_data.items():
            assert session[key] == value