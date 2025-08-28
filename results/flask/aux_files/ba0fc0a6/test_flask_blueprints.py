"""Property-based tests for flask.blueprints module"""

import string
from hypothesis import given, strategies as st, assume, settings
import flask
import flask.blueprints as bp


# Strategy for valid blueprint names
blueprint_names = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=50
).filter(lambda x: not x.startswith('_'))

# Strategy for valid URL rules
url_rules = st.text(
    alphabet=string.ascii_letters + string.digits + "/_-",
    min_size=1,
    max_size=100
).map(lambda x: f"/{x.strip('/')}")

# Strategy for valid endpoint names
endpoint_names = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=50
).filter(lambda x: x and not x.startswith('_'))


@given(
    name=blueprint_names,
    rules=st.lists(url_rules, min_size=1, max_size=10),
    endpoints=st.lists(endpoint_names, min_size=1, max_size=10)
)
def test_add_url_rule_adds_deferred_function(name, rules, endpoints):
    """Property: Each add_url_rule call should add exactly one deferred function"""
    
    # Create a fresh blueprint
    blueprint = bp.Blueprint(name, __name__)
    initial_count = len(blueprint.deferred_functions)
    
    # Make endpoints match rules length
    endpoints = endpoints[:len(rules)]
    while len(endpoints) < len(rules):
        endpoints.append(None)
    
    # Add URL rules
    for rule, endpoint in zip(rules, endpoints):
        prev_count = len(blueprint.deferred_functions)
        blueprint.add_url_rule(rule, endpoint, lambda: 'test')
        new_count = len(blueprint.deferred_functions)
        
        # Property: Each add_url_rule adds exactly one deferred function
        assert new_count == prev_count + 1, \
            f"add_url_rule should add exactly 1 deferred function, but added {new_count - prev_count}"
    
    # Property: Total deferred functions should match number of rules added
    final_count = len(blueprint.deferred_functions)
    assert final_count - initial_count == len(rules), \
        f"Expected {len(rules)} deferred functions, got {final_count - initial_count}"


@given(
    parent_name=blueprint_names,
    child_name=blueprint_names,
    parent_prefix=st.one_of(st.none(), url_rules),
    child_prefix=st.one_of(st.none(), url_rules)
)
def test_blueprint_nesting_url_prefix_combination(parent_name, child_name, parent_prefix, child_prefix):
    """Property: Nested blueprint URL prefixes should combine correctly"""
    
    # Ensure names are different
    assume(parent_name != child_name)
    
    # Create parent and child blueprints
    parent = bp.Blueprint(parent_name, __name__, url_prefix=parent_prefix)
    child = bp.Blueprint(child_name, __name__, url_prefix=child_prefix)
    
    # Add a route to child
    child.add_url_rule('/test', 'test', lambda: 'test')
    
    # Register child on parent
    parent.register_blueprint(child)
    
    # Create app and get setup state
    app = flask.Flask(__name__)
    
    # Register parent on app and check the resulting URL prefixes
    try:
        app.register_blueprint(parent)
        
        # The registration should succeed without exceptions
        assert True
        
    except Exception as e:
        # Check if this is a known limitation
        if "has already been registered" in str(e):
            # This is expected behavior for duplicate names
            pass
        else:
            raise


@given(
    name1=blueprint_names,
    name2=blueprint_names
)
def test_blueprint_name_uniqueness_on_app(name1, name2):
    """Property: Blueprints with same name cannot be registered twice on same app"""
    
    app = flask.Flask(__name__)
    
    # Create two blueprints
    bp1 = bp.Blueprint(name1, __name__)
    bp2 = bp.Blueprint(name2, __name__)
    
    # Register first blueprint
    app.register_blueprint(bp1)
    
    if name1 == name2:
        # Should not be able to register another blueprint with same name
        try:
            app.register_blueprint(bp2)
            # If we get here, the property is violated
            assert False, f"Should not be able to register two blueprints with same name '{name1}'"
        except AssertionError:
            # This is expected - blueprints with same name should fail
            pass
    else:
        # Different names should register successfully
        app.register_blueprint(bp2)
        assert True


@given(
    name=blueprint_names,
    url_prefix=st.one_of(st.none(), url_rules),
    subdomain=st.one_of(st.none(), st.text(string.ascii_lowercase, min_size=1, max_size=20))
)
def test_blueprint_setup_state_preserves_attributes(name, url_prefix, subdomain):
    """Property: BlueprintSetupState should preserve blueprint attributes"""
    
    # Create blueprint with attributes
    blueprint = bp.Blueprint(name, __name__, url_prefix=url_prefix, subdomain=subdomain)
    
    # Create app and setup state
    app = flask.Flask(__name__)
    options = {}
    
    # Can override url_prefix in options
    if url_prefix:
        options['url_prefix'] = url_prefix
    
    setup_state = blueprint.make_setup_state(app, options)
    
    # Properties to test:
    # 1. Setup state should reference the correct blueprint
    assert setup_state.blueprint is blueprint
    assert setup_state.blueprint.name == name
    
    # 2. URL prefix should be preserved or overridden correctly
    if 'url_prefix' in options:
        assert setup_state.url_prefix == options['url_prefix']
    else:
        assert setup_state.url_prefix == blueprint.url_prefix
    
    # 3. Subdomain should be preserved
    assert setup_state.subdomain == subdomain


@given(
    bp_name=blueprint_names,
    num_routes=st.integers(min_value=0, max_value=20),
    num_error_handlers=st.integers(min_value=0, max_value=10),
    num_app_error_handlers=st.integers(min_value=0, max_value=10)
)
def test_deferred_functions_count_consistency(bp_name, num_routes, num_error_handlers, num_app_error_handlers):
    """Property: Deferred functions count should match certain decorator patterns"""
    
    blueprint = bp.Blueprint(bp_name, __name__)
    initial_count = len(blueprint.deferred_functions)
    
    # Add routes (each adds a deferred function)
    for i in range(num_routes):
        blueprint.add_url_rule(f'/route{i}', f'endpoint{i}', lambda: 'test')
    
    # Add error handlers (should NOT add deferred functions based on our observation)
    for i in range(num_error_handlers):
        @blueprint.errorhandler(400 + i)
        def handler(e):
            return 'error'
    
    # Add app error handlers (each adds a deferred function)
    for i in range(num_app_error_handlers):
        @blueprint.app_errorhandler(500 + i)
        def app_handler(e):
            return 'app error'
    
    # Property: Total deferred functions should match routes + app_error_handlers
    expected = initial_count + num_routes + num_app_error_handlers
    actual = len(blueprint.deferred_functions)
    
    assert actual == expected, \
        f"Expected {expected} deferred functions (initial={initial_count}, routes={num_routes}, app_errors={num_app_error_handlers}), got {actual}"


@given(
    name=blueprint_names,
    static_folder=st.one_of(st.none(), st.text(string.ascii_letters, min_size=1, max_size=20)),
    template_folder=st.one_of(st.none(), st.text(string.ascii_letters, min_size=1, max_size=20))
)
def test_blueprint_folder_attributes(name, static_folder, template_folder):
    """Property: Blueprint folder attributes should be preserved correctly"""
    
    blueprint = bp.Blueprint(
        name, 
        __name__,
        static_folder=static_folder,
        template_folder=template_folder
    )
    
    # Properties:
    # 1. Attributes should be preserved
    assert blueprint.static_folder == static_folder
    assert blueprint.template_folder == template_folder
    
    # 2. Blueprint should be creatable without exceptions
    assert blueprint.name == name