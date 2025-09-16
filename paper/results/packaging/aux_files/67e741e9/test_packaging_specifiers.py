import math
from hypothesis import assume, given, strategies as st, settings
from packaging.specifiers import Specifier, SpecifierSet, InvalidSpecifier
from packaging.version import Version, InvalidVersion
import itertools


# Strategies for generating valid version strings
def version_strategy():
    """Generate valid version strings."""
    # Basic versions like "1.2.3"
    parts = st.integers(min_value=0, max_value=100)
    num_parts = st.integers(min_value=1, max_value=4)
    
    @st.composite
    def make_version(draw):
        n = draw(num_parts)
        version_parts = [str(draw(parts)) for _ in range(n)]
        base = '.'.join(version_parts)
        
        # Sometimes add prerelease
        if draw(st.booleans()):
            prerelease_type = draw(st.sampled_from(['a', 'b', 'rc']))
            prerelease_num = draw(st.integers(min_value=1, max_value=10))
            base = f"{base}{prerelease_type}{prerelease_num}"
        
        return base
    
    return make_version()


# Strategy for valid operators
operator_strategy = st.sampled_from(['==', '!=', '<=', '>=', '<', '>', '~=', '==='])


# Strategy for valid specifier strings
@st.composite
def specifier_string_strategy(draw):
    op = draw(operator_strategy)
    version = draw(version_strategy())
    # Sometimes add whitespace after operator
    if draw(st.booleans()):
        return f"{op} {version}"
    return f"{op}{version}"


# Strategy for SpecifierSet strings (comma-separated specifiers)
@st.composite  
def specifier_set_string_strategy(draw):
    num_specs = draw(st.integers(min_value=1, max_value=5))
    specs = [draw(specifier_string_strategy()) for _ in range(num_specs)]
    return ','.join(specs)


# Test 1: Filter and contains consistency
@given(
    spec_str=specifier_string_strategy(),
    versions=st.lists(version_strategy(), min_size=1, max_size=20)
)
def test_filter_contains_consistency(spec_str, versions):
    """Property: v in spec.filter([v]) iff v in spec"""
    try:
        spec = Specifier(spec_str)
    except InvalidSpecifier:
        assume(False)
    
    for v in versions:
        try:
            version_obj = Version(v)
        except InvalidVersion:
            continue
            
        # Check if version is contained
        is_contained = version_obj in spec
        
        # Check if version appears in filtered list
        filtered = list(spec.filter([v]))
        is_in_filtered = v in filtered
        
        assert is_contained == is_in_filtered, \
            f"Inconsistency for {v} with spec {spec_str}: contained={is_contained}, filtered={is_in_filtered}"


# Test 2: Filter invariant - never increases count
@given(
    spec_str=specifier_string_strategy(),
    versions=st.lists(version_strategy(), min_size=0, max_size=20)
)
def test_filter_count_invariant(spec_str, versions):
    """Property: len(spec.filter(versions)) <= len(versions)"""
    try:
        spec = Specifier(spec_str)
    except InvalidSpecifier:
        assume(False)
    
    filtered = list(spec.filter(versions))
    assert len(filtered) <= len(versions), \
        f"Filter increased count: {len(versions)} -> {len(filtered)}"


# Test 3: SpecifierSet intersection commutativity
@given(
    spec1_str=specifier_string_strategy(),
    spec2_str=specifier_string_strategy(),
    test_version=version_strategy()
)
def test_specifierset_intersection_commutative(spec1_str, spec2_str, test_version):
    """Property: (s1 & s2).contains(v) == (s2 & s1).contains(v)"""
    try:
        s1 = SpecifierSet(spec1_str)
        s2 = SpecifierSet(spec2_str)
        v = Version(test_version)
    except (InvalidSpecifier, InvalidVersion):
        assume(False)
    
    intersection1 = s1 & s2
    intersection2 = s2 & s1
    
    # Test with a specific version
    result1 = v in intersection1
    result2 = v in intersection2
    
    assert result1 == result2, \
        f"Intersection not commutative for {test_version}: {s1} & {s2} vs {s2} & {s1}"


# Test 4: SpecifierSet intersection semantics
@given(
    spec1_str=specifier_string_strategy(),
    spec2_str=specifier_string_strategy(),
    test_version=version_strategy()
)
def test_specifierset_intersection_semantics(spec1_str, spec2_str, test_version):
    """Property: v in (s1 & s2) iff (v in s1 and v in s2)"""
    try:
        s1 = SpecifierSet(spec1_str)
        s2 = SpecifierSet(spec2_str)
        v = Version(test_version)
    except (InvalidSpecifier, InvalidVersion):
        assume(False)
    
    intersection = s1 & s2
    
    in_intersection = v in intersection
    in_both = (v in s1) and (v in s2)
    
    assert in_intersection == in_both, \
        f"Intersection semantics violated for {test_version}: in_intersection={in_intersection}, in_both={in_both}"


# Test 5: Prerelease filtering consistency
@given(
    spec_str=specifier_string_strategy(),
    versions=st.lists(version_strategy(), min_size=1, max_size=20)
)
def test_prerelease_filtering(spec_str, versions):
    """Property: With prereleases=False, no prerelease versions should pass"""
    try:
        spec = Specifier(spec_str)
    except InvalidSpecifier:
        assume(False)
    
    # Filter without prereleases
    filtered_no_pre = list(spec.filter(versions, prereleases=False))
    
    # Check that no filtered version is a prerelease
    for v_str in filtered_no_pre:
        try:
            v = Version(v_str)
            assert not v.is_prerelease, \
                f"Prerelease {v_str} passed filter with prereleases=False"
        except InvalidVersion:
            pass


# Test 6: Operator semantics for >=
@given(
    base_version=version_strategy(),
    test_versions=st.lists(version_strategy(), min_size=1, max_size=20)
)
def test_gte_operator_semantics(base_version, test_versions):
    """Property: >= operator should match all versions >= base"""
    try:
        base = Version(base_version)
        spec = Specifier(f">={base_version}")
    except (InvalidVersion, InvalidSpecifier):
        assume(False)
    
    for v_str in test_versions:
        try:
            v = Version(v_str)
            
            # Skip prereleases for cleaner test
            if v.is_prerelease or base.is_prerelease:
                continue
                
            should_match = v >= base
            does_match = v in spec
            
            assert should_match == does_match, \
                f">= semantics violated: {v_str} >= {base_version} is {should_match}, but spec match is {does_match}"
        except InvalidVersion:
            pass


# Test 7: != operator excludes exactly one version
@given(
    excluded_version=version_strategy(),
    test_versions=st.lists(version_strategy(), min_size=1, max_size=20)
)
def test_ne_operator_semantics(excluded_version, test_versions):
    """Property: != operator should exclude exactly the specified version"""
    try:
        spec = Specifier(f"!={excluded_version}")
        excluded = Version(excluded_version)
    except (InvalidSpecifier, InvalidVersion):
        assume(False)
    
    # The excluded version should not match
    assert excluded not in spec, f"!= operator failed to exclude {excluded_version}"
    
    # All other versions should match (except prereleases by default)
    for v_str in test_versions:
        if v_str == excluded_version:
            continue
        try:
            v = Version(v_str)
            if not v.is_prerelease:
                assert v in spec, f"!= operator incorrectly excluded {v_str}"
        except InvalidVersion:
            pass


# Test 8: SpecifierSet with contradictory constraints
@given(
    version=version_strategy()
)
def test_contradictory_constraints(version):
    """Property: Contradictory constraints should result in no matches"""
    try:
        v = Version(version)
        # Create contradictory constraints
        spec_set = SpecifierSet(f"=={version},!={version}")
    except (InvalidVersion, InvalidSpecifier):
        assume(False)
    
    # Version cannot both equal and not equal itself
    assert v not in spec_set, \
        f"Contradictory constraints (=={version},!={version}) incorrectly matched"


# Test 9: Filter preserves order
@given(
    spec_str=specifier_string_strategy(),
    versions=st.lists(version_strategy(), min_size=2, max_size=10, unique=True)
)
def test_filter_preserves_order(spec_str, versions):
    """Property: filter() should preserve the order of input versions"""
    try:
        spec = Specifier(spec_str)
    except InvalidSpecifier:
        assume(False)
    
    filtered = list(spec.filter(versions))
    
    # Check that filtered items appear in the same relative order
    filtered_indices = []
    for item in filtered:
        if item in versions:
            filtered_indices.append(versions.index(item))
    
    # Indices should be strictly increasing
    for i in range(1, len(filtered_indices)):
        assert filtered_indices[i] > filtered_indices[i-1], \
            f"Filter changed order: {filtered} from {versions}"


# Test 10: Empty SpecifierSet accepts everything (except prereleases by default)
@given(versions=st.lists(version_strategy(), min_size=1, max_size=20))
def test_empty_specifierset(versions):
    """Property: Empty SpecifierSet should accept all non-prerelease versions"""
    spec_set = SpecifierSet("")  # Empty specifier set
    
    for v_str in versions:
        try:
            v = Version(v_str)
            if not v.is_prerelease:
                assert v in spec_set, f"Empty SpecifierSet rejected non-prerelease {v_str}"
        except InvalidVersion:
            pass