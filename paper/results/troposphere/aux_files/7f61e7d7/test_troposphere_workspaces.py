"""Property-based tests for troposphere.workspaces module"""

import troposphere.workspaces as ws
from hypothesis import given, strategies as st, assume
import pytest


# Test 1: Round-trip property for AWSObject classes (to_dict/from_dict)
@given(
    bundle_id=st.text(min_size=1, max_size=100),
    directory_id=st.text(min_size=1, max_size=100),
    username=st.text(min_size=1, max_size=100),
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier())
)
def test_workspace_roundtrip_to_dict_from_dict(bundle_id, directory_id, username, title):
    """Test that Workspace.from_dict(title, workspace.to_dict()) recreates the workspace"""
    # Create original workspace
    original = ws.Workspace(
        title,
        BundleId=bundle_id,
        DirectoryId=directory_id,
        UserName=username
    )
    
    # Convert to dict
    ws_dict = original.to_dict()
    
    # Try to recreate from dict - this should work but doesn't!
    # The bug is that to_dict wraps in 'Properties' but from_dict expects unwrapped
    try:
        # This should work according to round-trip property
        recreated = ws.Workspace.from_dict(title + '_new', ws_dict)
        
        # Verify properties match
        assert recreated.BundleId == original.BundleId
        assert recreated.DirectoryId == original.DirectoryId
        assert recreated.UserName == original.UserName
    except ValueError as e:
        # This reveals the bug - from_dict can't read to_dict output
        if "does not have a Properties property" in str(e):
            # Extract just the Properties part for from_dict
            if 'Properties' in ws_dict:
                recreated = ws.Workspace.from_dict(title + '_new', ws_dict['Properties'])
                # This works, but shows the round-trip is broken
                assert False, f"Round-trip property violated: to_dict() output not compatible with from_dict() input"


# Test 2: ConnectionAlias round-trip
@given(
    connection_string=st.text(min_size=1, max_size=100),
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier())
)
def test_connection_alias_roundtrip(connection_string, title):
    """Test ConnectionAlias round-trip property"""
    original = ws.ConnectionAlias(
        title,
        ConnectionString=connection_string
    )
    
    alias_dict = original.to_dict()
    
    try:
        recreated = ws.ConnectionAlias.from_dict(title + '_new', alias_dict)
        assert recreated.ConnectionString == original.ConnectionString
    except ValueError as e:
        if "does not have a Properties property" in str(e):
            assert False, f"Round-trip property violated: to_dict() output not compatible with from_dict() input"


# Test 3: Integer function property - should it return int?
@given(value=st.one_of(
    st.integers(),
    st.text(min_size=1).map(str),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x))
))
def test_integer_function_return_type(value):
    """Test that integer() function validates but preserves original type"""
    try:
        # Convert to something that should be valid
        if isinstance(value, float):
            value = int(value)
        
        result = ws.integer(value)
        
        # The function name suggests it returns an integer
        # but it actually returns the original value unchanged
        assert result == value  # It returns original, not int
        
        # This could be a semantic bug - function named 'integer' 
        # but doesn't ensure integer type
        if not isinstance(result, int) and str(value).isdigit():
            # String digits are accepted but not converted
            assert isinstance(result, str)
    except ValueError:
        # Should only raise for invalid inputs
        try:
            int(value)
            assert False, f"integer() rejected valid integer-convertible value: {value}"
        except (ValueError, TypeError):
            pass  # Expected to fail


# Test 4: Boolean function validation
@given(value=st.one_of(
    st.just(True), st.just(False),
    st.just(1), st.just(0),
    st.just("1"), st.just("0"),
    st.just("true"), st.just("false"),
    st.just("True"), st.just("False")
))
def test_boolean_function_known_values(value):
    """Test that boolean() correctly handles all documented values"""
    result = ws.boolean(value)
    
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False
    else:
        assert False, f"boolean() didn't handle documented value: {value}"


# Test 5: WorkspacesPool round-trip with required fields
@given(
    bundle_id=st.text(min_size=1, max_size=100),
    directory_id=st.text(min_size=1, max_size=100),
    pool_name=st.text(min_size=1, max_size=100),
    desired_sessions=st.integers(min_value=0, max_value=1000),
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier())
)
def test_workspaces_pool_roundtrip(bundle_id, directory_id, pool_name, desired_sessions, title):
    """Test WorkspacesPool round-trip property"""
    capacity = ws.Capacity(DesiredUserSessions=desired_sessions)
    
    original = ws.WorkspacesPool(
        title,
        BundleId=bundle_id,
        DirectoryId=directory_id,
        PoolName=pool_name,
        Capacity=capacity
    )
    
    pool_dict = original.to_dict()
    
    try:
        recreated = ws.WorkspacesPool.from_dict(title + '_new', pool_dict)
        assert recreated.BundleId == original.BundleId
    except ValueError as e:
        if "does not have a Properties property" in str(e):
            assert False, f"Round-trip property violated for WorkspacesPool"


# Test 6: Property validation with integer fields
@given(
    size=st.one_of(
        st.integers(min_value=0, max_value=10000),
        st.text().filter(lambda x: x.isdigit()),
        st.floats(min_value=0, max_value=10000).filter(lambda x: x == int(x))
    )
)
def test_workspace_properties_integer_fields(size):
    """Test that WorkspaceProperties correctly handles integer-like values"""
    try:
        props = ws.WorkspaceProperties(
            RootVolumeSizeGib=size,
            UserVolumeSizeGib=size
        )
        
        # These fields use the integer() validator
        # Check that values are preserved
        assert props.RootVolumeSizeGib == size
        assert props.UserVolumeSizeGib == size
        
        # Round-trip through dict should work
        props_dict = props.to_dict()
        new_props = ws.WorkspaceProperties.from_dict('test', props_dict)
        assert new_props.RootVolumeSizeGib == props.RootVolumeSizeGib
        assert new_props.UserVolumeSizeGib == props.UserVolumeSizeGib
        
    except ValueError:
        # Should only fail for non-integer-convertible values
        try:
            int(size)
            assert False, f"WorkspaceProperties rejected valid integer: {size}"
        except (ValueError, TypeError):
            pass  # Expected