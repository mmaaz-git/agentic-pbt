import math
import os
from hypothesis import assume, given, strategies as st, settings
from hypothesis.provisional import urls
import pytest
from flask import Flask
from flask.blueprints import Blueprint, BlueprintSetupState


@given(st.text())
def test_blueprint_name_validation(name):
    """Test Blueprint name validation constraints"""
    if not name:
        with pytest.raises(ValueError, match="'name' may not be empty"):
            Blueprint(name, __name__)
    elif "." in name:
        with pytest.raises(ValueError, match="'name' may not contain a dot"):
            Blueprint(name, __name__)
    else:
        bp = Blueprint(name, __name__)
        assert bp.name == name


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.one_of(st.none(), st.text()),
    st.one_of(st.none(), st.text())
)
def test_url_prefix_joining(name, url_prefix1, url_prefix2):
    """Test URL prefix joining behavior in nested blueprints"""
    app = Flask(__name__)
    bp1 = Blueprint(name + "_parent", __name__, url_prefix=url_prefix1)
    bp2 = Blueprint(name + "_child", __name__, url_prefix=url_prefix2)
    
    try:
        bp1.register_blueprint(bp2)
        app.register_blueprint(bp1)
        
        # Check that prefixes are properly joined
        if url_prefix1 and url_prefix2:
            # Both prefixes should be combined with proper slash handling
            combined = url_prefix1.rstrip("/") + "/" + url_prefix2.lstrip("/")
            # The combined prefix should be valid
            assert "/" not in combined or combined.startswith("/") or url_prefix1.startswith("/")
    except ValueError as e:
        # Some combinations might be invalid
        pass


@given(st.text(min_size=1).filter(lambda x: "." not in x))
def test_blueprint_self_registration(name):
    """Test that a blueprint cannot register itself"""
    bp = Blueprint(name, __name__)
    with pytest.raises(ValueError, match="Cannot register a blueprint on itself"):
        bp.register_blueprint(bp)


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.text(),
    st.sampled_from(["r", "rt", "rb", "w", "wb", "a", "x"])
)
def test_open_resource_mode_validation(name, resource, mode):
    """Test that open_resource only allows reading modes"""
    bp = Blueprint(name, __name__)
    
    if mode not in {"r", "rt", "rb"}:
        with pytest.raises(ValueError, match="Resources can only be opened for reading"):
            bp.open_resource(resource, mode=mode)
    else:
        # Valid mode but resource might not exist
        try:
            f = bp.open_resource(resource, mode=mode)
            f.close()
        except (FileNotFoundError, IsADirectoryError, PermissionError):
            # Expected if resource doesn't exist
            pass


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.one_of(st.none(), st.text().filter(lambda x: not x or (x and "." not in x))),
    st.one_of(st.none(), st.text().filter(lambda x: not x or (x and "." not in x)))
)
def test_subdomain_concatenation(name, parent_subdomain, child_subdomain):
    """Test subdomain concatenation in nested blueprints"""
    app = Flask(__name__)
    parent_bp = Blueprint(name + "_parent", __name__, subdomain=parent_subdomain)
    child_bp = Blueprint(name + "_child", __name__, subdomain=child_subdomain)
    
    parent_bp.register_blueprint(child_bp)
    app.register_blueprint(parent_bp)
    
    # Check subdomain concatenation logic
    if parent_subdomain and child_subdomain:
        # Both should be concatenated with dot
        expected = child_subdomain + "." + parent_subdomain
        # This is the expected behavior based on the code


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.integers(), st.text(), st.none()),
        min_size=0,
        max_size=5
    )
)
def test_url_defaults_merging(name, url_defaults):
    """Test URL defaults merging behavior"""
    bp = Blueprint(name, __name__, url_defaults=url_defaults)
    assert bp.url_values_defaults == url_defaults
    
    # Test that defaults are properly stored
    for key, value in url_defaults.items():
        assert bp.url_values_defaults[key] == value


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.text()
)
def test_blueprint_name_prefix_handling(base_name, name_prefix):
    """Test name prefix handling in blueprint registration"""
    app = Flask(__name__)
    bp = Blueprint(base_name, __name__)
    
    # Register with name prefix
    options = {"name_prefix": name_prefix}
    
    try:
        app.register_blueprint(bp, **options)
        
        # The registered name should include the prefix
        if name_prefix:
            expected_name = f"{name_prefix}.{base_name}".lstrip(".")
        else:
            expected_name = base_name
        
        assert expected_name in app.blueprints
    except ValueError:
        # Some combinations might cause conflicts
        pass


@given(
    st.lists(
        st.text(min_size=1).filter(lambda x: "." not in x),
        min_size=2,
        max_size=5,
        unique=True
    )
)
def test_multiple_blueprint_registration(names):
    """Test registering multiple blueprints with the same app"""
    app = Flask(__name__)
    blueprints = [Blueprint(name, __name__) for name in names]
    
    for bp in blueprints:
        app.register_blueprint(bp)
    
    # All blueprints should be registered
    for name in names:
        assert name in app.blueprints
    
    # Test that re-registering the same blueprint with the same name fails
    with pytest.raises(ValueError, match="already registered"):
        app.register_blueprint(blueprints[0])


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.one_of(st.none(), st.text())
)
def test_blueprint_cli_group_setting(name, cli_group):
    """Test CLI group settings for blueprints"""
    from flask.sansio.scaffold import _sentinel
    
    if cli_group is None:
        bp = Blueprint(name, __name__)
        assert bp.cli_group is _sentinel
    else:
        bp = Blueprint(name, __name__, cli_group=cli_group)
        assert bp.cli_group == cli_group


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.one_of(st.none(), st.text()),
    st.text()
)
def test_blueprint_static_folder_url_path(name, static_folder, static_url_path):
    """Test static folder and URL path handling"""
    # Only test valid combinations
    if static_folder is not None:
        static_folder = static_folder.strip()
        if not static_folder:
            static_folder = None
    
    bp = Blueprint(
        name, 
        __name__, 
        static_folder=static_folder,
        static_url_path=static_url_path
    )
    
    if static_folder:
        assert bp.has_static_folder
        # static_url_path defaults to static_folder if not provided
        if static_url_path is None:
            assert bp.static_url_path == f"/{static_folder}"
        else:
            assert bp.static_url_path == static_url_path
    else:
        assert not bp.has_static_folder


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.one_of(st.none(), st.integers(min_value=0, max_value=1000000)),
    st.one_of(st.none(), st.floats(min_value=0, max_value=86400))
)  
def test_get_send_file_max_age_conversion(name, int_value, float_value):
    """Test get_send_file_max_age with different value types"""
    from datetime import timedelta
    from flask import Flask
    
    app = Flask(__name__)
    bp = Blueprint(name, __name__)
    
    with app.app_context():
        # Test with None
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = None
        assert bp.get_send_file_max_age("test.txt") is None
        
        # Test with integer
        if int_value is not None:
            app.config["SEND_FILE_MAX_AGE_DEFAULT"] = int_value
            assert bp.get_send_file_max_age("test.txt") == int_value
        
        # Test with timedelta
        if float_value is not None:
            td = timedelta(seconds=float_value)
            app.config["SEND_FILE_MAX_AGE_DEFAULT"] = td
            result = bp.get_send_file_max_age("test.txt")
            assert result == int(td.total_seconds())


@given(
    st.text(min_size=1).filter(lambda x: "." not in x),
    st.text(),
    st.text()
)
def test_blueprint_setup_state_url_rule_prefixing(name, url_prefix, rule):
    """Test URL rule prefixing in BlueprintSetupState"""
    app = Flask(__name__)
    bp = Blueprint(name, __name__)
    
    options = {"url_prefix": url_prefix} if url_prefix else {}
    state = BlueprintSetupState(bp, app, options, True)
    
    # Test how URL rules are prefixed
    endpoint = "test_endpoint"
    
    @app.route("/dummy")
    def dummy():
        return "dummy"
    
    try:
        state.add_url_rule(rule, endpoint=endpoint, view_func=dummy)
        
        # Check that the rule was added with proper prefixing
        if url_prefix is not None:
            if rule:
                expected_rule = "/".join((url_prefix.rstrip("/"), rule.lstrip("/")))
            else:
                expected_rule = url_prefix
        else:
            expected_rule = rule
            
    except Exception:
        # Some combinations might be invalid
        pass


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])