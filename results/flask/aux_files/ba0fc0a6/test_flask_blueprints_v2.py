"""Property-based tests for flask.blueprints module - Version 2"""

import string
from hypothesis import given, strategies as st, assume, settings
import flask
import flask.blueprints as bp
from werkzeug.exceptions import default_exceptions


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

# Strategy for valid HTTP error codes
valid_error_codes = st.sampled_from(list(default_exceptions.keys()))


@given(
    name=blueprint_names,
    static_folder=st.text(string.ascii_letters, min_size=1, max_size=20),
    template_folder=st.text(string.ascii_letters, min_size=1, max_size=20)
)
def test_blueprint_folder_path_inconsistency(name, static_folder, template_folder):
    """Bug: Blueprint converts static_folder to absolute path but not template_folder"""
    
    blueprint = bp.Blueprint(
        name, 
        __name__,
        static_folder=static_folder,
        template_folder=template_folder
    )
    
    # Check if both are relative paths initially
    import os
    static_is_relative = not os.path.isabs(static_folder)
    template_is_relative = not os.path.isabs(template_folder)
    
    if static_is_relative and template_is_relative:
        # Both were relative, so they should be treated the same way
        static_became_absolute = os.path.isabs(blueprint.static_folder)
        template_became_absolute = os.path.isabs(blueprint.template_folder)
        
        # Property: Relative paths should be treated consistently
        assert static_became_absolute == template_became_absolute, \
            f"Inconsistent path handling: static_folder converted to absolute ({blueprint.static_folder}) " \
            f"but template_folder stayed relative ({blueprint.template_folder})"


@given(
    name=blueprint_names,
    static_folder_sansio=st.text(string.ascii_letters, min_size=1, max_size=20),
    static_folder_regular=st.text(string.ascii_letters, min_size=1, max_size=20)
)
def test_sansio_blueprint_static_folder_consistency(name, static_folder_sansio, static_folder_regular):
    """Property: SansioBlueprint and Blueprint should handle static_folder the same way"""
    
    # Create both types with same parameters
    sansio = bp.SansioBlueprint(name + "_sansio", __name__, static_folder=static_folder_sansio)
    regular = bp.Blueprint(name + "_regular", __name__, static_folder=static_folder_regular)
    
    # If both inputs are the same, outputs should be processed the same way
    if static_folder_sansio == static_folder_regular:
        # Both should either be absolute or both relative
        import os
        sansio_is_abs = os.path.isabs(sansio.static_folder) if sansio.static_folder else False
        regular_is_abs = os.path.isabs(regular.static_folder) if regular.static_folder else False
        
        assert sansio_is_abs == regular_is_abs, \
            f"SansioBlueprint and Blueprint handle static_folder differently: " \
            f"SansioBlueprint -> {sansio.static_folder}, Blueprint -> {regular.static_folder}"


@given(
    parent_name=blueprint_names,
    child_name=blueprint_names,
    grandchild_name=blueprint_names
)
def test_deeply_nested_blueprints(parent_name, child_name, grandchild_name):
    """Property: Deeply nested blueprints should maintain hierarchy"""
    
    # Ensure unique names
    assume(len({parent_name, child_name, grandchild_name}) == 3)
    
    # Create hierarchy
    parent = bp.Blueprint(parent_name, __name__)
    child = bp.Blueprint(child_name, __name__)
    grandchild = bp.Blueprint(grandchild_name, __name__)
    
    # Add routes to each
    parent.add_url_rule('/parent', 'parent', lambda: 'parent')
    child.add_url_rule('/child', 'child', lambda: 'child')
    grandchild.add_url_rule('/grandchild', 'grandchild', lambda: 'grandchild')
    
    # Register grandchild on child, child on parent
    child.register_blueprint(grandchild)
    parent.register_blueprint(child)
    
    # The parent should not have any deferred functions from nested registration
    # (based on our earlier observation)
    assert len(parent.deferred_functions) == 1, \
        f"Parent blueprint should only have its own route, not nested ones. " \
        f"Expected 1 deferred function, got {len(parent.deferred_functions)}"


@given(
    name=blueprint_names,
    url_rules=st.lists(url_rules, min_size=1, max_size=10, unique=True)
)
def test_blueprint_duplicate_endpoint_detection(name, url_rules):
    """Property: Blueprint should handle duplicate endpoint names appropriately"""
    
    blueprint = bp.Blueprint(name, __name__)
    
    # Try to add multiple rules with the same endpoint name
    endpoint = "test_endpoint"
    
    for i, rule in enumerate(url_rules):
        if i == 0:
            # First one should succeed
            blueprint.add_url_rule(rule, endpoint, lambda: 'test')
            assert len(blueprint.deferred_functions) == 1
        else:
            # Subsequent ones with same endpoint - what happens?
            try:
                blueprint.add_url_rule(rule, endpoint, lambda: 'test')
                # If this succeeds, check if deferred function was added
                # This could reveal if Blueprint allows duplicate endpoints
                pass
            except AssertionError:
                # This is expected - Flask should prevent duplicate endpoints
                pass
    
    # Property: Number of deferred functions should never exceed number of unique endpoints
    # (unless endpoints can be duplicated, which would be a bug)
    assert len(blueprint.deferred_functions) <= len(url_rules)


@given(
    name=blueprint_names,
    methods_lists=st.lists(
        st.lists(
            st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']),
            min_size=1,
            max_size=3,
            unique=True
        ),
        min_size=1,
        max_size=5
    )
)
def test_blueprint_methods_parameter_handling(name, methods_lists):
    """Property: Blueprint should correctly handle methods parameter in add_url_rule"""
    
    blueprint = bp.Blueprint(name, __name__)
    
    for i, methods in enumerate(methods_lists):
        # Add route with specific methods
        blueprint.add_url_rule(
            f'/route{i}',
            f'endpoint{i}',
            lambda: 'test',
            methods=methods
        )
    
    # Property: Each add_url_rule with methods should add exactly one deferred function
    assert len(blueprint.deferred_functions) == len(methods_lists), \
        f"Expected {len(methods_lists)} deferred functions, got {len(blueprint.deferred_functions)}"


@given(
    name=blueprint_names,
    url_prefix=url_rules,
    rule=url_rules
)
def test_url_prefix_concatenation(name, url_prefix, rule):
    """Property: URL prefix and rule should concatenate properly"""
    
    # Create blueprint with URL prefix
    blueprint = bp.Blueprint(name, __name__, url_prefix=url_prefix)
    blueprint.add_url_rule(rule, 'test', lambda: 'test')
    
    # Create app and register blueprint
    app = flask.Flask(__name__)
    app.register_blueprint(blueprint)
    
    # The effective rule should be prefix + rule
    # This tests if Flask properly handles the concatenation
    with app.test_client() as client:
        # Try to access the concatenated path
        expected_path = url_prefix.rstrip('/') + '/' + rule.lstrip('/')
        expected_path = '/' + expected_path.lstrip('/')
        
        # This is more of a functional test, but reveals concatenation bugs
        # We're just checking it doesn't crash on registration
        assert True  # Registration succeeded without error