import sys
import re
from hypothesis import given, strategies as st, assume
from typing import Any

# Add fixit to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import fixit.rule
import fixit.ftypes as ftypes


# Property 1: LintRule name handling - removes "Rule" suffix
@given(st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
def test_lintrule_name_suffix_removal(class_name):
    """Test that LintRule correctly removes 'Rule' suffix from class names."""
    # Create a dynamic class with the given name
    assume(class_name.isidentifier())  # Must be valid Python identifier
    
    TestClass = type(class_name, (fixit.rule.LintRule,), {})
    instance = TestClass()
    
    # Property: if class name ends with "Rule", instance.name should be without it
    if class_name.endswith("Rule") and len(class_name) > 4:
        assert instance.name == class_name[:-4]
    else:
        assert instance.name == class_name


# Property 2: Tags.parse round-trip and containment logic
@given(st.lists(st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc", "Cs"])), min_size=1, max_size=10))
def test_tags_parse_contains(tag_list):
    """Test Tags parsing and containment behavior."""
    # Create comma-separated string
    tags_str = ",".join(tag_list)
    tags = ftypes.Tags.parse(tags_str)
    
    # Test that parsed tags work with containment
    for tag in tag_list:
        tag_lower = tag.lower().strip()
        if tag_lower and not tag_lower[0] in "!^-":
            # Regular tags should be included
            assert tag_lower in tags or not tags.include
        

# Property 3: is_sequence and is_collection helpers
@given(st.one_of(
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.text(),
    st.binary(),
    st.integers(),
    st.sets(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_is_sequence_is_collection(value):
    """Test that is_sequence and is_collection correctly identify types."""
    is_seq = ftypes.is_sequence(value)
    is_coll = ftypes.is_collection(value)
    
    # Property: strings and bytes should never be considered sequences/collections
    if isinstance(value, (str, bytes)):
        assert not is_seq
        assert not is_coll
    
    # Property: sequences are also collections (if not str/bytes)
    if is_seq:
        assert is_coll
    
    # Property: lists and tuples are sequences
    if isinstance(value, (list, tuple)):
        assert is_seq
        assert is_coll
    
    # Property: sets are collections but not sequences
    if isinstance(value, set):
        assert not is_seq
        assert is_coll


# Property 4: LintIgnoreRegex pattern matching
@given(st.sampled_from(["lint-ignore", "lint-fixme"]),
       st.one_of(st.none(), st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122)), min_size=1, max_size=5)))
def test_lint_ignore_regex(directive, rule_names):
    """Test that LintIgnoreRegex matches valid patterns."""
    # Build a comment string
    if rule_names is None:
        comment = f"# {directive}"
    else:
        names_str = ", ".join(rule_names)
        comment = f"# {directive}: {names_str}"
    
    match = ftypes.LintIgnoreRegex.search(comment)
    
    # Property: valid directives should always match
    assert match is not None
    groups = match.groups()
    assert groups[0] == directive
    
    if rule_names is None:
        assert groups[1] is None
    else:
        # Check that rule names are captured
        assert groups[1] is not None


# Property 5: QualifiedRule string representation
@given(st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
       st.one_of(st.none(), st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122))))
def test_qualified_rule_string_representation(module, name):
    """Test QualifiedRule string representation consistency."""
    assume(module.replace(".", "").replace("_", "").isalnum())  # Basic module name validation
    if name:
        assume(name.replace("_", "").isalnum())
    
    rule = ftypes.QualifiedRule(module=module, name=name)
    str_repr = str(rule)
    
    # Property: string representation should contain module
    assert module in str_repr
    
    # Property: if name exists, it should be after a colon
    if name:
        assert f":{name}" in str_repr
    else:
        assert ":" not in str_repr


# Property 6: QualifiedRule comparison
@given(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
       st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=65, max_codepoint=122)))
def test_qualified_rule_ordering(module1, module2):
    """Test that QualifiedRule ordering is consistent with string representation."""
    assume(module1 != module2)
    assume(module1.replace(".", "").replace("_", "").isalnum())
    assume(module2.replace(".", "").replace("_", "").isalnum())
    
    rule1 = ftypes.QualifiedRule(module=module1)
    rule2 = ftypes.QualifiedRule(module=module2)
    
    # Property: ordering should match string ordering
    if str(rule1) < str(rule2):
        assert rule1 < rule2
    elif str(rule1) > str(rule2):
        assert rule2 < rule1


# Property 7: LintViolation autofixable property
@given(st.one_of(st.none(), st.just("replacement_node")))
def test_lint_violation_autofixable(replacement):
    """Test that LintViolation.autofixable correctly reflects replacement presence."""
    from libcst import Name
    from libcst.metadata import CodeRange, CodePosition
    
    # Create a dummy violation
    violation = ftypes.LintViolation(
        rule_name="TestRule",
        range=CodeRange(
            start=CodePosition(1, 0),
            end=CodePosition(1, 10)
        ),
        message="Test message",
        node=Name("test"),  # dummy node
        replacement=replacement
    )
    
    # Property: autofixable should be true iff replacement exists
    assert violation.autofixable == bool(replacement)


# Property 8: Config path resolution
@given(st.text(min_size=1, max_size=100))
def test_config_path_resolution(path_str):
    """Test that Config resolves paths."""
    from pathlib import Path
    
    # Skip invalid paths
    try:
        path = Path(path_str)
    except (ValueError, OSError):
        assume(False)
    
    config = ftypes.Config(path=path)
    
    # Property: path should be resolved (absolute)
    assert config.path.is_absolute() or str(config.path) == str(path.resolve())


if __name__ == "__main__":
    import traceback
    
    print("Running property-based tests for fixit.rule...")
    
    tests = [
        ("LintRule name suffix removal", test_lintrule_name_suffix_removal),
        ("Tags parse/contains", test_tags_parse_contains),
        ("is_sequence/is_collection helpers", test_is_sequence_is_collection),
        ("LintIgnoreRegex pattern matching", test_lint_ignore_regex),
        ("QualifiedRule string representation", test_qualified_rule_string_representation),
        ("QualifiedRule ordering", test_qualified_rule_ordering),
        ("LintViolation autofixable", test_lint_violation_autofixable),
        ("Config path resolution", test_config_path_resolution),
    ]
    
    failures = []
    for name, test_func in tests:
        print(f"\nTesting: {name}")
        try:
            test_func()
            print(f"  ✓ Passed")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failures.append((name, e, traceback.format_exc()))
    
    if failures:
        print(f"\n\n{'='*60}")
        print(f"FAILURES: {len(failures)} tests failed")
        print('='*60)
        for name, error, tb in failures:
            print(f"\n{name}:")
            print(tb)
    else:
        print(f"\n\nAll {len(tests)} property tests passed ✅")