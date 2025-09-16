import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.urldispatch as urldispatch
import string
import re


# Strategy for valid route patterns
def valid_route_pattern():
    # Generate ASCII-only patterns to avoid encoding issues
    segment = st.text(alphabet=string.ascii_letters + string.digits + '-_', min_size=1, max_size=20)
    placeholder = st.one_of(
        st.just(''),
        st.builds(lambda name: f'{{{name}}}', segment),
        st.builds(lambda name, regex: f'{{{name}:{regex}}}', segment, st.just(r'\d+')),
    )
    
    path_part = st.one_of(
        segment,
        placeholder,
        st.builds(lambda s, p: s + p, segment, placeholder),
    )
    
    # Build paths with optional star at end
    base_path = st.builds(
        lambda parts: '/' + '/'.join(parts),
        st.lists(path_part, min_size=0, max_size=5)
    )
    
    return st.one_of(
        base_path,
        st.builds(lambda path, name: path + '*' + name, base_path, st.text(alphabet=string.ascii_letters, max_size=10))
    )


# Test 1: Pattern normalization - routes always start with '/'
@given(st.text(alphabet=string.ascii_letters + string.digits + '/{}-_:', min_size=1))
def test_route_pattern_normalization(pattern):
    # The code claims to normalize patterns to start with '/'
    try:
        route = urldispatch.Route('test', pattern)
        # After creation, the pattern should start with '/'
        assert route.pattern.startswith('/'), f"Pattern {route.pattern} doesn't start with '/'"
    except (ValueError, re.error):
        # Some patterns might be invalid regex
        pass


# Test 2: RoutesMapper route replacement
@given(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
    valid_route_pattern(),
    valid_route_pattern()
)
def test_routes_mapper_replacement(name, pattern1, pattern2):
    mapper = urldispatch.RoutesMapper()
    
    # Connect first route
    route1 = mapper.connect(name, pattern1)
    assert route1 in mapper.routelist
    assert mapper.get_route(name) == route1
    
    # Connect second route with same name
    route2 = mapper.connect(name, pattern2)
    
    # Old route should be removed, new route should be present
    assert route1 not in mapper.routelist
    assert route2 in mapper.routelist
    assert mapper.get_route(name) == route2
    assert len([r for r in mapper.routelist if r.name == name]) == 1


# Test 3: Route retrieval invariant
@given(
    st.lists(
        st.tuples(
            st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
            valid_route_pattern()
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]  # Unique names
    )
)
def test_route_retrieval_invariant(routes_data):
    mapper = urldispatch.RoutesMapper()
    
    connected_routes = {}
    for name, pattern in routes_data:
        route = mapper.connect(name, pattern)
        connected_routes[name] = route
    
    # Every route we connected should be retrievable by name
    for name, expected_route in connected_routes.items():
        retrieved = mapper.get_route(name)
        assert retrieved == expected_route, f"Route {name} not retrievable correctly"


# Test 4: Non-ASCII bytestring handling
@given(st.binary(min_size=1).filter(lambda b: any(byte > 127 for byte in b)))
def test_non_ascii_bytestring_raises_error(binary_pattern):
    # The code explicitly states it should raise ValueError for non-ASCII bytestrings
    try:
        matcher, generator = urldispatch._compile_route(binary_pattern)
        # If we get here without exception, check if it was valid ASCII
        binary_pattern.decode('ascii')
        # If decode succeeds, the test assumption was wrong
    except ValueError as e:
        # This is expected for non-ASCII bytestrings
        assert 'non-ASCII' in str(e) or 'Unicode' in str(e)
    except UnicodeDecodeError:
        # This means it truly was non-ASCII, so ValueError should have been raised
        assert False, f"Non-ASCII bytestring {binary_pattern!r} didn't raise ValueError"


# Test 5: Star pattern remainder handling
@given(
    st.text(alphabet=string.ascii_letters + string.digits + '/', min_size=1, max_size=20),
    st.text(alphabet=string.ascii_letters, min_size=0, max_size=10)
)
def test_star_pattern_remainder(base_path, remainder_name):
    # Ensure base_path starts with /
    if not base_path.startswith('/'):
        base_path = '/' + base_path
    
    pattern = base_path + '*' + remainder_name
    
    matcher, generator = urldispatch._compile_route(pattern)
    
    # Test that paths matching the base and having extra segments work
    test_path = base_path + '/extra/segments/here'
    test_path = test_path.replace('//', '/')  # Clean double slashes
    
    match_result = matcher(test_path)
    
    if match_result is not None and remainder_name:
        # The remainder should be captured under the remainder_name key
        assert remainder_name in match_result
        # The remainder should be a list (from split_path_info)
        assert isinstance(match_result[remainder_name], tuple) or isinstance(match_result[remainder_name], list)


# Test 6: Static vs non-static route separation
@given(
    st.lists(
        st.tuples(
            st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
            valid_route_pattern(),
            st.booleans()
        ),
        min_size=1,
        max_size=10,
        unique_by=lambda x: x[0]
    )
)
def test_static_route_separation(routes_data):
    mapper = urldispatch.RoutesMapper()
    
    static_routes = []
    regular_routes = []
    
    for name, pattern, is_static in routes_data:
        route = mapper.connect(name, pattern, static=is_static)
        if is_static:
            static_routes.append(route)
        else:
            regular_routes.append(route)
    
    # Check that get_routes without include_static doesn't return static routes
    retrieved_regular = mapper.get_routes(include_static=False)
    for route in static_routes:
        assert route not in retrieved_regular
    
    # Check that get_routes with include_static returns all routes
    all_routes = mapper.get_routes(include_static=True)
    for route in static_routes + regular_routes:
        assert route in all_routes


# Test 7: Route pattern compilation idempotence
@given(valid_route_pattern())
@settings(max_examples=200)
def test_route_compilation_deterministic(pattern):
    # Compiling the same pattern multiple times should give equivalent results
    matcher1, generator1 = urldispatch._compile_route(pattern)
    matcher2, generator2 = urldispatch._compile_route(pattern)
    
    # Test with a sample path
    test_paths = ['/', '/test', '/test/path', '/123', '/test/123/abc']
    
    for path in test_paths:
        result1 = matcher1(path)
        result2 = matcher2(path)
        assert result1 == result2, f"Matchers differ for path {path} with pattern {pattern}"