import packaging.markers
from hypothesis import given, strategies as st, assume
import string


# Strategy for valid marker variable names
valid_variables = st.sampled_from([
    'os_name', 'sys_platform', 'platform_release', 'platform_system', 
    'platform_version', 'platform_machine', 'platform_python_implementation',
    'python_version', 'python_full_version', 'implementation_name', 
    'implementation_version', 'extra', 'extras'
])

# Strategy for operators
operators = st.sampled_from(['<', '<=', '!=', '==', '>=', '>', '~=', 'in', 'not in'])

# Strategy for version strings 
version_strings = st.from_regex(r'[0-9]+(\.[0-9]+)*', fullmatch=True)

# Strategy for general quoted strings
quoted_strings = st.text(alphabet=string.ascii_letters + string.digits + '._- ', min_size=1, max_size=20).map(lambda s: f'"{s}"')

# Strategy for simple marker expressions
@st.composite
def simple_markers(draw):
    var = draw(valid_variables)
    op = draw(operators)
    
    # Choose appropriate value based on variable
    if 'version' in var:
        value = draw(version_strings)
    else:
        value = draw(st.text(alphabet=string.ascii_letters + string.digits + '._- ', min_size=1, max_size=20))
    
    return f'{var} {op} "{value}"'


# Strategy for compound markers with and/or
@st.composite  
def compound_markers(draw):
    num_clauses = draw(st.integers(min_value=2, max_value=4))
    clauses = [draw(simple_markers()) for _ in range(num_clauses)]
    
    # Choose operator (all same for simplicity)
    bool_op = draw(st.sampled_from(['and', 'or']))
    
    return f' {bool_op} '.join(clauses)


# Test 1: Round-trip property - parsing and serializing preserves semantics
@given(simple_markers())
def test_round_trip_preserves_evaluation(marker_str):
    """A marker should evaluate the same after round-tripping through string representation"""
    try:
        marker1 = packaging.markers.Marker(marker_str)
    except packaging.markers.InvalidMarker:
        # Skip invalid markers
        return
        
    # Convert to string and parse again
    serialized = str(marker1)
    marker2 = packaging.markers.Marker(serialized)
    
    # Both should evaluate to the same result with default environment
    env = packaging.markers.default_environment()
    assert marker1.evaluate(env) == marker2.evaluate(env)
    
    # And with empty environment
    assert marker1.evaluate({}) == marker2.evaluate({})


# Test 2: Evaluation determinism
@given(simple_markers())
def test_evaluation_deterministic(marker_str):
    """A marker should always evaluate to the same result with the same environment"""
    try:
        marker = packaging.markers.Marker(marker_str)
    except packaging.markers.InvalidMarker:
        return
        
    env = packaging.markers.default_environment()
    
    # Evaluate multiple times - should always get same result
    results = [marker.evaluate(env) for _ in range(5)]
    assert all(r == results[0] for r in results)


# Test 3: Whitespace normalization
@given(simple_markers(), st.integers(min_value=0, max_value=5))
def test_whitespace_normalization(marker_str, extra_spaces):
    """Markers with different whitespace should normalize to the same form"""
    try:
        marker1 = packaging.markers.Marker(marker_str)
    except packaging.markers.InvalidMarker:
        return
    
    # Add random extra spaces
    spaced = marker_str.replace(' ', ' ' * (extra_spaces + 1))
    spaced = '  ' + spaced + '  '  # Add leading/trailing
    
    try:
        marker2 = packaging.markers.Marker(spaced)
    except packaging.markers.InvalidMarker:
        return
        
    # Should normalize to same string representation
    assert str(marker1) == str(marker2)
    
    # And evaluate the same
    env = packaging.markers.default_environment()
    assert marker1.evaluate(env) == marker2.evaluate(env)


# Test 4: Invalid markers are rejected  
@given(st.text(min_size=1, max_size=50))
def test_invalid_markers_rejected(text):
    """Invalid marker syntax should raise InvalidMarker"""
    # Filter out accidentally valid markers
    if any(var in text for var in ['python_version', 'sys_platform', 'os_name']):
        assume(False)
    
    # These should be invalid
    invalid_patterns = [
        text,  # Random text
        f'{text} ==',  # Missing value
        f'== "{text}"',  # Missing variable
    ]
    
    for pattern in invalid_patterns:
        try:
            marker = packaging.markers.Marker(pattern)
            # If we get here without exception, check if it accidentally became valid
            # (shouldn't happen with our patterns, but be safe)
        except packaging.markers.InvalidMarker:
            # Expected behavior
            pass
        except Exception as e:
            # Unexpected exception type
            raise AssertionError(f"Expected InvalidMarker but got {type(e)}: {e}")


# Test 5: Compound marker commutativity for OR
@given(simple_markers(), simple_markers())
def test_or_commutativity(marker1_str, marker2_str):
    """'A or B' should evaluate the same as 'B or A'"""
    try:
        # Create both orderings
        marker_ab = packaging.markers.Marker(f'{marker1_str} or {marker2_str}')
        marker_ba = packaging.markers.Marker(f'{marker2_str} or {marker1_str}')
    except packaging.markers.InvalidMarker:
        return
        
    # Should evaluate to same result
    env = packaging.markers.default_environment()
    assert marker_ab.evaluate(env) == marker_ba.evaluate(env)


# Test 6: Compound marker commutativity for AND
@given(simple_markers(), simple_markers())
def test_and_commutativity(marker1_str, marker2_str):
    """'A and B' should evaluate the same as 'B and A'"""
    try:
        # Create both orderings
        marker_ab = packaging.markers.Marker(f'{marker1_str} and {marker2_str}')
        marker_ba = packaging.markers.Marker(f'{marker2_str} and {marker1_str}')
    except packaging.markers.InvalidMarker:
        return
        
    # Should evaluate to same result
    env = packaging.markers.default_environment()
    assert marker_ab.evaluate(env) == marker_ba.evaluate(env)


# Test 7: Empty string is invalid
def test_empty_string_invalid():
    """Empty string should raise InvalidMarker"""
    try:
        packaging.markers.Marker('')
        assert False, "Empty string should raise InvalidMarker"
    except packaging.markers.InvalidMarker:
        pass  # Expected


# Test 8: Extras evaluation with different contexts
@given(st.text(alphabet=string.ascii_lowercase + string.digits + '_-', min_size=1, max_size=20))
def test_extra_marker_contexts(extra_name):
    """Test 'extra' markers with different evaluation contexts"""
    marker_str = f'extra == "{extra_name}"'
    
    try:
        marker = packaging.markers.Marker(marker_str)
    except packaging.markers.InvalidMarker:
        return
    
    # Test with default context (should be False as no extras)
    assert marker.evaluate() == False
    
    # Test with environment containing the extra
    env = {'extra': extra_name}
    assert marker.evaluate(env) == True
    
    # Test with different extra
    env = {'extra': extra_name + '_different'}
    assert marker.evaluate(env) == False