"""Property-based tests for isort.place module using Hypothesis"""
import re
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from mock_deps import Config, sections

# Import the module we're testing
import place


# Strategy for valid Python module names
def python_module_name():
    """Generate valid Python module/package names."""
    identifier = st.text(
        alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd"), whitelist_characters="_"),
        min_size=1,
        max_size=20
    ).filter(lambda s: s and not s[0].isdigit() and s.isidentifier())
    
    return identifier


def dotted_module_name():
    """Generate dotted module names like 'package.subpackage.module'."""
    return st.lists(python_module_name(), min_size=1, max_size=5).map(lambda parts: ".".join(parts))


def local_module_name():
    """Generate local module names starting with '.'."""
    return st.one_of(
        st.just("."),
        dotted_module_name().map(lambda s: "." + s),
        dotted_module_name().map(lambda s: ".." + s)
    )


# Test 1: Local modules always placed in LOCALFOLDER
@given(name=local_module_name())
def test_local_modules_always_in_localfolder(name):
    """Any module starting with '.' should be placed in LOCALFOLDER section."""
    config = Config()
    result = place.module(name, config)
    assert result == "LOCALFOLDER", f"Module '{name}' starting with '.' should be in LOCALFOLDER, got {result}"


# Test 2: module() and module_with_reason() consistency
@given(
    name=st.one_of(dotted_module_name(), local_module_name()),
    forced_separate=st.lists(st.text(min_size=1, max_size=10), max_size=3)
)
def test_module_and_module_with_reason_consistency(name, forced_separate):
    """module() should return the same section as module_with_reason()[0]."""
    config = Config(forced_separate=forced_separate)
    
    section = place.module(name, config)
    section_with_reason, reason = place.module_with_reason(name, config)
    
    assert section == section_with_reason, (
        f"module() returned {section} but module_with_reason()[0] returned {section_with_reason}"
    )
    assert isinstance(reason, str), "Reason should be a string"
    assert len(reason) > 0, "Reason should not be empty"


# Test 3: Forced separate pattern matching
@given(
    module_name=dotted_module_name(),
    pattern_suffix=st.sampled_from(["", "*"])
)
def test_forced_separate_exact_match(module_name, pattern_suffix):
    """Test that forced_separate patterns match correctly."""
    pattern = module_name + pattern_suffix
    config = Config(forced_separate=[pattern])
    
    result = place.module(module_name, config)
    
    # Should match the forced_separate pattern
    assert result == pattern, f"Module '{module_name}' should match forced_separate pattern '{pattern}'"


# Test 4: Forced separate with wildcards
@given(
    prefix=python_module_name(),
    suffix=python_module_name()
)
def test_forced_separate_wildcard_match(prefix, suffix):
    """Test wildcard matching in forced_separate patterns."""
    module_name = f"{prefix}.{suffix}"
    pattern = f"{prefix}*"
    
    config = Config(forced_separate=[pattern])
    result = place.module(module_name, config)
    
    # Should match since module starts with prefix
    assert result == pattern, f"Module '{module_name}' should match pattern '{pattern}'"


# Test 5: Multiple forced_separate patterns - first match wins
@given(
    module_name=dotted_module_name(),
    patterns=st.lists(python_module_name(), min_size=2, max_size=5, unique=True)
)
def test_forced_separate_first_match_wins(module_name, patterns):
    """When multiple forced_separate patterns could match, the first should win."""
    # Make all patterns match by using wildcards
    wildcard_patterns = [p + "*" for p in patterns]
    
    config = Config(forced_separate=wildcard_patterns)
    result = place.module(module_name, config)
    
    # Should return one of the patterns (if any match)
    if result in wildcard_patterns:
        # Find which pattern matched first
        for pattern in wildcard_patterns:
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if module_name.startswith(prefix) or module_name.startswith("." + prefix):
                    assert result == pattern, f"First matching pattern should be {pattern}, got {result}"
                    break


# Test 6: Known patterns with regex
@given(
    module_name=dotted_module_name(),
    pattern_str=st.sampled_from(["test.*", ".*test", "foo", "bar.*"])
)
def test_known_patterns_regex(module_name, pattern_str):
    """Test that known_patterns with regex work correctly."""
    pattern = re.compile(pattern_str)
    placement = "FIRSTPARTY"
    
    config = Config(
        known_patterns=[(pattern, placement)],
        sections={"FIRSTPARTY", "THIRDPARTY", "STDLIB"}
    )
    
    result = place.module(module_name, config)
    
    # Check all possible prefixes of the module name
    parts = module_name.split(".")
    should_match = False
    for i in range(len(parts), 0, -1):
        prefix = ".".join(parts[:i])
        if pattern.match(prefix):
            should_match = True
            break
    
    if should_match:
        assert result == placement, f"Module '{module_name}' should match pattern '{pattern_str}' and be in {placement}"


# Test 7: Default section fallback
@given(
    module_name=dotted_module_name(),
    default_section=st.sampled_from(["STDLIB", "THIRDPARTY", "FIRSTPARTY"])
)
def test_default_section_fallback(module_name, default_section):
    """When no patterns match, should return default_section."""
    # Create config with no patterns that would match
    config = Config(
        forced_separate=[],
        known_patterns=[],
        src_paths=[],  # No source paths
        default_section=default_section
    )
    
    # Skip if it's a local import
    assume(not module_name.startswith("."))
    
    result = place.module(module_name, config)
    assert result == default_section, f"Should fall back to default_section {default_section}, got {result}"


# Test 8: Caching behavior - same inputs return same outputs
@given(
    name=dotted_module_name(),
    forced_separate=st.lists(st.text(min_size=1, max_size=10), max_size=3)
)
@settings(max_examples=50)
def test_caching_determinism(name, forced_separate):
    """Calling module_with_reason multiple times should return the same result."""
    config = Config(forced_separate=forced_separate)
    
    # Clear the cache first
    place.module_with_reason.cache_clear()
    
    # Call multiple times
    result1 = place.module_with_reason(name, config)
    result2 = place.module_with_reason(name, config)
    result3 = place.module_with_reason(name, config)
    
    assert result1 == result2 == result3, "Cached function should return consistent results"
    
    # Check cache is being used (info should show hits)
    cache_info = place.module_with_reason.cache_info()
    assert cache_info.hits >= 2, "Cache should have been hit at least twice"


# Test 9: Pattern matching order (longest to shortest)
@given(st.data())
def test_pattern_matching_order(data):
    """Known patterns should check from longest module name to shortest."""
    # Generate a hierarchical module name
    parts = data.draw(st.lists(python_module_name(), min_size=3, max_size=5))
    full_module = ".".join(parts)
    
    # Create patterns that match different levels
    patterns = []
    for i in range(1, len(parts) + 1):
        partial = ".".join(parts[:i])
        pattern = re.compile(f"^{re.escape(partial)}$")
        section = f"SECTION_{i}"
        patterns.append((pattern, section))
    
    # Add all sections to config
    all_sections = {f"SECTION_{i}" for i in range(1, len(parts) + 1)}
    all_sections.update({"THIRDPARTY", "FIRSTPARTY", "STDLIB"})
    
    config = Config(
        known_patterns=patterns,
        sections=all_sections
    )
    
    result = place.module(full_module, config)
    
    # Should match the longest pattern (which corresponds to the full module name)
    expected = f"SECTION_{len(parts)}"
    assert result == expected, f"Should match longest pattern first, expected {expected}, got {result}"


# Test 10: Edge cases with empty strings and special characters
@given(
    use_empty=st.booleans(),
    num_dots=st.integers(min_value=1, max_value=5)
)
def test_edge_cases_dots(use_empty, num_dots):
    """Test edge cases with dots and empty module names."""
    if use_empty:
        # Module names with just dots
        name = "." * num_dots
    else:
        # Module names starting with multiple dots
        name = "." * num_dots + "module"
    
    config = Config()
    
    # Should not crash
    result = place.module(name, config)
    result_with_reason = place.module_with_reason(name, config)
    
    # Modules starting with dots should be local
    assert result == "LOCALFOLDER", f"Module '{name}' starting with dots should be LOCALFOLDER"
    assert result == result_with_reason[0], "Results should be consistent"