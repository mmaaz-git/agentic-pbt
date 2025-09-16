import math
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import packaging.tags


# Strategy for valid tag components (no dots or dashes allowed in components)
tag_component = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"),
        whitelist_characters="_"
    ),
    min_size=1,
    max_size=20
).filter(lambda s: not any(c in s for c in ".-"))


@given(
    interpreter=tag_component,
    abi=tag_component,
    platform=tag_component
)
def test_tag_round_trip_simple(interpreter, abi, platform):
    """Test that Tag creation and string representation round-trips correctly."""
    tag = packaging.tags.Tag(interpreter, abi, platform)
    tag_str = str(tag)
    
    # Parse the string back
    parsed = packaging.tags.parse_tag(tag_str)
    
    # Should get exactly one tag back
    assert len(parsed) == 1
    parsed_tag = next(iter(parsed))
    
    # Should be equivalent
    assert parsed_tag == tag
    assert parsed_tag.interpreter == tag.interpreter
    assert parsed_tag.abi == tag.abi
    assert parsed_tag.platform == tag.platform


@given(
    interpreters=st.lists(tag_component, min_size=1, max_size=5, unique=True),
    abis=st.lists(tag_component, min_size=1, max_size=5, unique=True),
    platforms=st.lists(tag_component, min_size=1, max_size=5, unique=True)
)
def test_compressed_tag_expansion_count(interpreters, abis, platforms):
    """Test that compressed tags expand to the correct number of combinations."""
    # Create a compressed tag string
    compressed = f"{'.'.join(interpreters)}-{'.'.join(abis)}-{'.'.join(platforms)}"
    
    # Parse it
    parsed = packaging.tags.parse_tag(compressed)
    
    # Should have exactly the product of all component counts
    expected_count = len(interpreters) * len(abis) * len(platforms)
    assert len(parsed) == expected_count
    
    # Verify all expected combinations are present
    for interp in interpreters:
        for abi in abis:
            for plat in platforms:
                expected_tag = packaging.tags.Tag(interp, abi, plat)
                assert expected_tag in parsed


@given(
    interpreter=st.text(min_size=1, max_size=20).filter(lambda s: not any(c in s for c in ".-")),
    abi=st.text(min_size=1, max_size=20).filter(lambda s: not any(c in s for c in ".-")),
    platform=st.text(min_size=1, max_size=20).filter(lambda s: not any(c in s for c in ".-"))
)
def test_tag_case_normalization(interpreter, abi, platform):
    """Test that tags normalize to lowercase."""
    # Create tags with different cases
    tag_lower = packaging.tags.Tag(interpreter.lower(), abi.lower(), platform.lower())
    tag_upper = packaging.tags.Tag(interpreter.upper(), abi.upper(), platform.upper())
    tag_mixed = packaging.tags.Tag(interpreter, abi, platform)
    
    # All should be equal
    assert tag_lower == tag_upper
    assert tag_lower == tag_mixed
    assert tag_upper == tag_mixed
    
    # All should have same hash
    assert hash(tag_lower) == hash(tag_upper)
    assert hash(tag_lower) == hash(tag_mixed)
    
    # All should have lowercase components
    for tag in [tag_lower, tag_upper, tag_mixed]:
        assert tag.interpreter == interpreter.lower()
        assert tag.abi == abi.lower()
        assert tag.platform == platform.lower()


@given(
    interpreter1=tag_component,
    abi1=tag_component,
    platform1=tag_component,
    interpreter2=tag_component,
    abi2=tag_component,
    platform2=tag_component
)
def test_tag_equality_hash_consistency(interpreter1, abi1, platform1, interpreter2, abi2, platform2):
    """Test that tag equality and hashing are consistent."""
    tag1 = packaging.tags.Tag(interpreter1, abi1, platform1)
    tag2 = packaging.tags.Tag(interpreter2, abi2, platform2)
    
    # If tags are equal, hashes must be equal
    if tag1 == tag2:
        assert hash(tag1) == hash(tag2)
    
    # Create identical tag to tag1
    tag1_copy = packaging.tags.Tag(interpreter1, abi1, platform1)
    assert tag1 == tag1_copy
    assert hash(tag1) == hash(tag1_copy)
    
    # Test that string representation is consistent
    if tag1 == tag2:
        assert str(tag1) == str(tag2)


@given(
    components=st.lists(
        st.lists(tag_component, min_size=1, max_size=3, unique=True),
        min_size=3,
        max_size=3
    )
)
def test_parse_tag_ordering_invariant(components):
    """Test that parsing compressed tags maintains expected properties regardless of order."""
    interpreters, abis, platforms = components
    
    # Create compressed tag
    compressed = f"{'.'.join(interpreters)}-{'.'.join(abis)}-{'.'.join(platforms)}"
    parsed = packaging.tags.parse_tag(compressed)
    
    # Create the same tag with components in different order within each section
    import random
    shuffled_interp = list(interpreters)
    shuffled_abi = list(abis)
    shuffled_plat = list(platforms)
    random.shuffle(shuffled_interp)
    random.shuffle(shuffled_abi)
    random.shuffle(shuffled_plat)
    
    compressed_shuffled = f"{'.'.join(shuffled_interp)}-{'.'.join(shuffled_abi)}-{'.'.join(shuffled_plat)}"
    parsed_shuffled = packaging.tags.parse_tag(compressed_shuffled)
    
    # Both should produce the same set of tags
    assert parsed == parsed_shuffled


# Strategy for valid tag strings
valid_tag_str = st.builds(
    lambda i, a, p: f"{i}-{a}-{p}",
    i=st.text(min_size=1, max_size=10).filter(lambda s: "-" not in s and s),
    a=st.text(min_size=1, max_size=10).filter(lambda s: "-" not in s and s),
    p=st.text(min_size=1, max_size=10).filter(lambda s: "-" not in s and s)
)

@given(tag_str=valid_tag_str)
def test_parse_tag_robustness(tag_str):
    """Test that parse_tag handles various inputs without crashing."""
    try:
        result = packaging.tags.parse_tag(tag_str)
        # If it succeeds, result should be a frozenset of Tag objects
        assert isinstance(result, frozenset)
        for tag in result:
            assert isinstance(tag, packaging.tags.Tag)
    except (ValueError, AttributeError):
        # These are acceptable failures for malformed input
        pass


@given(
    interpreter=tag_component,
    abi=tag_component,
    platform=tag_component
)
def test_tag_string_format(interpreter, abi, platform):
    """Test that Tag string representation follows the expected format."""
    tag = packaging.tags.Tag(interpreter, abi, platform)
    tag_str = str(tag)
    
    # Should be in format: interpreter-abi-platform
    parts = tag_str.split("-")
    assert len(parts) == 3
    assert parts[0] == interpreter.lower()
    assert parts[1] == abi.lower()
    assert parts[2] == platform.lower()
    
    # Test that parsing this string gives us back the same tag
    parsed = packaging.tags.parse_tag(tag_str)
    assert len(parsed) == 1
    assert tag in parsed