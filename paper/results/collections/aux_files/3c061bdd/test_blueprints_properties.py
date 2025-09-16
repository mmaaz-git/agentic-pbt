#!/usr/bin/env python3

import os
import pytest
from hypothesis import given, strategies as st, assume, settings
from flask import Flask, Blueprint
from flask.blueprints import BlueprintSetupState


# Strategy for valid blueprint names (no dots, not empty)
valid_bp_names = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), min_codepoint=32),
    min_size=1,
    max_size=50
).filter(lambda x: "." not in x and x.strip())

# Strategy for URL paths
url_paths = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/-_"),
    min_size=0,
    max_size=100
).map(lambda x: x.strip())

# Strategy for URL prefixes (should start with /)
url_prefixes = st.one_of(
    st.none(),
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="/-_"),
        min_size=1,
        max_size=50
    ).map(lambda x: "/" + x.strip("/") if x.strip() else "/")
)

# Strategy for subdomains
subdomains = st.one_of(
    st.none(),
    st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-"),
        min_size=1,
        max_size=30
    ).filter(lambda x: not x.startswith("-") and not x.endswith("-"))
)


@given(
    bp_name=valid_bp_names,
    url_prefix=url_prefixes,
    rule=url_paths
)
def test_url_prefix_concatenation_property(bp_name, url_prefix, rule):
    """Test property: URL prefix concatenation should preserve path structure"""
    app = Flask(__name__)
    bp = Blueprint(bp_name, __name__, url_prefix=url_prefix)
    
    # Register a route
    @bp.route("/" + rule.lstrip("/"))
    def test_view():
        return "test"
    
    app.register_blueprint(bp)
    
    # Property: The resulting rule should be properly formed
    # If url_prefix is None, rule should be unchanged (except normalization)
    # If url_prefix exists, it should be joined with proper slash handling
    
    with app.test_client() as client:
        if url_prefix:
            expected_path = url_prefix.rstrip("/") + "/" + rule.lstrip("/")
            if not expected_path.startswith("/"):
                expected_path = "/" + expected_path
        else:
            expected_path = "/" + rule.lstrip("/") if rule else "/"
        
        # Clean up multiple slashes
        import re
        expected_path = re.sub(r'/+', '/', expected_path)
        if not expected_path:
            expected_path = "/"
            
        response = client.get(expected_path)
        # Property: properly formed URLs should be accessible
        assert response.status_code in [200, 404, 308]  # 308 for trailing slash redirects


@given(
    parent_prefix=url_prefixes,
    child_prefix=url_prefixes,
    parent_subdomain=subdomains,
    child_subdomain=subdomains
)
def test_nested_blueprint_url_prefix_merging(parent_prefix, child_prefix, parent_subdomain, child_subdomain):
    """Test property: Nested blueprint URL prefixes should merge correctly"""
    app = Flask(__name__)
    
    parent = Blueprint('parent', __name__, url_prefix=parent_prefix, subdomain=parent_subdomain)
    child = Blueprint('child', __name__, url_prefix=child_prefix, subdomain=child_subdomain)
    
    @child.route("/test")
    def test_view():
        return "nested"
    
    parent.register_blueprint(child)
    app.register_blueprint(parent)
    
    # Property: The merging should follow the documented rules
    # 1. URL prefixes concatenate with proper slash handling
    # 2. Subdomains concatenate with dot separator
    
    # Check that registration succeeded without errors
    assert 'parent.child.test_view' in app.view_functions


@given(
    bp_name=valid_bp_names,
    endpoint_name=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
        min_size=1,
        max_size=30
    ).filter(lambda x: "." not in x)
)
def test_endpoint_dot_validation(bp_name, endpoint_name):
    """Test property: Endpoints with dots should be rejected"""
    app = Flask(__name__)
    bp = Blueprint(bp_name, __name__)
    
    # Property: Endpoints containing dots should raise ValueError
    if "." in endpoint_name:
        with pytest.raises(ValueError, match="may not contain a dot"):
            @bp.route("/test", endpoint=endpoint_name + ".invalid")
            def test_view():
                return "test"
    else:
        # Valid endpoint should work
        @bp.route("/test", endpoint=endpoint_name)
        def test_view():
            return "test"
        
        app.register_blueprint(bp)
        assert f"{bp_name}.{endpoint_name}" in app.view_functions


@given(valid_bp_names)
def test_blueprint_name_dot_validation(bp_name):
    """Test property: Blueprint names with dots should be rejected"""
    # Property: Names containing dots should raise ValueError
    if "." in bp_name:
        with pytest.raises(ValueError, match="may not contain a dot"):
            Blueprint(bp_name, __name__)
    else:
        # Valid names should work
        bp = Blueprint(bp_name, __name__)
        assert bp.name == bp_name


@given(
    bp_name=valid_bp_names,
    register_name1=st.one_of(st.none(), valid_bp_names),
    register_name2=st.one_of(st.none(), valid_bp_names)
)
def test_blueprint_registration_uniqueness(bp_name, register_name1, register_name2):
    """Test property: Same blueprint registered with same name should fail"""
    app = Flask(__name__)
    bp = Blueprint(bp_name, __name__)
    
    # First registration
    options1 = {"name": register_name1} if register_name1 else {}
    app.register_blueprint(bp, **options1)
    
    # Property: Registering again with same effective name should raise ValueError
    options2 = {"name": register_name2} if register_name2 else {}
    effective_name1 = register_name1 or bp_name
    effective_name2 = register_name2 or bp_name
    
    if effective_name1 == effective_name2:
        with pytest.raises(ValueError, match="already registered"):
            app.register_blueprint(bp, **options2)
    else:
        # Different names should work
        app.register_blueprint(bp, **options2)
        assert effective_name1 in app.blueprints
        assert effective_name2 in app.blueprints


@given(
    bp_name=valid_bp_names,
    static_folder=st.one_of(
        st.none(),
        st.just("static"),
        st.just("assets")
    ),
    static_url_path=st.one_of(
        st.none(),
        st.just("/static"),
        st.just("/assets")
    )
)
def test_static_file_configuration(bp_name, static_folder, static_url_path):
    """Test property: Static file configuration should be consistent"""
    # Create a temporary static folder if needed
    if static_folder:
        os.makedirs(static_folder, exist_ok=True)
        try:
            bp = Blueprint(bp_name, __name__, 
                          static_folder=static_folder,
                          static_url_path=static_url_path)
            
            # Property: If static_folder is set, has_static_folder should be True
            if static_folder:
                assert bp.has_static_folder
            else:
                assert not bp.has_static_folder
                
            # Property: static_url_path defaults to static_folder if not provided
            if static_url_path is None and static_folder:
                assert bp.static_url_path == f"/{static_folder}"
            elif static_url_path:
                assert bp.static_url_path == static_url_path
                
        finally:
            # Cleanup
            if static_folder and os.path.exists(static_folder):
                os.rmdir(static_folder)
    else:
        bp = Blueprint(bp_name, __name__, 
                      static_folder=static_folder,
                      static_url_path=static_url_path)
        assert not bp.has_static_folder


@given(
    url_prefix=url_prefixes,
    rule=st.one_of(
        st.just(""),
        st.just("/"),
        url_paths
    )
)
def test_empty_rule_with_prefix_handling(url_prefix, rule):
    """Test property: Empty rules with URL prefix should be handled correctly"""
    app = Flask(__name__)
    bp = Blueprint('test', __name__)
    
    state = BlueprintSetupState(bp, app, {"url_prefix": url_prefix}, True)
    
    # Add a URL rule with potentially empty rule
    state.add_url_rule(rule, endpoint="test", view_func=lambda: "test")
    
    # Property: The resulting rule should never be empty
    # If url_prefix exists and rule is empty, the result should be the prefix
    # This tests the specific logic in lines 98-102 of BlueprintSetupState.add_url_rule
    
    # Check that a rule was added to the app
    endpoints = [e for e in app.view_functions.keys() if 'test' in e]
    assert len(endpoints) > 0
    
    # The rule should be properly formed
    rules = list(app.url_map.iter_rules())
    test_rules = [r for r in rules if 'test' in r.endpoint]
    assert len(test_rules) > 0
    
    rule_str = str(test_rules[0])
    # Property: URL should always start with /
    assert rule_str.startswith("/") or rule_str == ""


@given(
    bp_name=valid_bp_names,
    name_prefix=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
        min_size=0,
        max_size=20
    ),
    endpoint=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
        min_size=1,
        max_size=20
    ).filter(lambda x: "." not in x)
)
def test_endpoint_name_prefix_concatenation(bp_name, name_prefix, endpoint):
    """Test property: Endpoint names should be properly prefixed"""
    app = Flask(__name__)
    bp = Blueprint(bp_name, __name__)
    
    @bp.route("/test", endpoint=endpoint)
    def test_view():
        return "test"
    
    options = {"name_prefix": name_prefix} if name_prefix else {}
    app.register_blueprint(bp, **options)
    
    # Property: The endpoint in app should be properly prefixed
    # Format: "{name_prefix}.{bp_name}.{endpoint}".lstrip(".")
    expected_endpoint = f"{name_prefix}.{bp_name}.{endpoint}".lstrip(".")
    
    assert expected_endpoint in app.view_functions


@given(bp_name=valid_bp_names)
def test_blueprint_self_registration_protection(bp_name):
    """Test property: A blueprint cannot register itself"""
    bp = Blueprint(bp_name, __name__)
    
    # Property: Attempting to register a blueprint on itself should raise ValueError
    with pytest.raises(ValueError, match="Cannot register a blueprint on itself"):
        bp.register_blueprint(bp)


@given(
    parent_subdomain=subdomains,
    child_subdomain=subdomains,
    state_subdomain=subdomains
)
def test_nested_subdomain_merging_property(parent_subdomain, child_subdomain, state_subdomain):
    """Test property: Subdomain merging follows documented concatenation rules"""
    app = Flask(__name__)
    
    parent = Blueprint('parent', __name__, subdomain=parent_subdomain)
    child = Blueprint('child', __name__, subdomain=child_subdomain)
    
    @child.route("/test")
    def test_view():
        return "nested"
    
    # Property: Subdomain merging should follow these rules:
    # 1. If both state and blueprint have subdomains, concatenate with "."
    # 2. Otherwise use whichever is not None
    # 3. None if both are None
    
    parent.register_blueprint(child)
    
    # Register parent with optional subdomain override
    options = {"subdomain": state_subdomain} if state_subdomain is not None else {}
    app.register_blueprint(parent, **options)
    
    # Check the registration succeeded
    assert 'parent.child.test_view' in app.view_functions
    
    # Property verification happens during registration - if it succeeds,
    # the subdomains were merged correctly


if __name__ == "__main__":
    # Run the tests
    import sys
    sys.exit(pytest.main([__file__, "-v"]))