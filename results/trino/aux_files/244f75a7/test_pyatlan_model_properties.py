import keyword
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

from pyatlan.model.utils import (
    to_python_class_name,
    to_camel_case,
    to_snake_case,
    construct_object_key
)

# Test 1: to_python_class_name should always produce valid Python class names or empty string
@given(st.text())
def test_to_python_class_name_always_valid(s):
    result = to_python_class_name(s)
    
    # Result should either be empty or a valid Python class name
    if result:
        # Must be a valid identifier
        assert result.isidentifier(), f"'{result}' is not a valid identifier"
        
        # Must not be a keyword
        assert not keyword.iskeyword(result), f"'{result}' is a Python keyword"
        
        # Must start with uppercase (PEP 8 convention for classes)
        assert result[0].isupper(), f"'{result}' doesn't start with uppercase"


# Test 2: to_python_class_name idempotence - valid class names should remain unchanged
@given(st.from_regex(r"[A-Z][a-zA-Z0-9]*", fullmatch=True))
def test_to_python_class_name_idempotent_for_valid_names(valid_class_name):
    assume(not keyword.iskeyword(valid_class_name))
    result = to_python_class_name(valid_class_name)
    assert result == valid_class_name, f"Valid class name '{valid_class_name}' was changed to '{result}'"


# Test 3: to_camel_case should always produce non-empty strings for non-empty input
@given(st.text(min_size=1))
def test_to_camel_case_non_empty(s):
    result = to_camel_case(s)
    assert len(result) > 0, f"to_camel_case returned empty string for input '{s}'"


# Test 4: to_camel_case should handle known overrides correctly
@given(st.sampled_from([
    "index_type_es_fields",
    "source_url",
    "source_embed_url",
    "sql_dbt_sources",
    "purpose_atlan_tags",
    "mapped_atlan_tag_name",
    "has_lineage",
    "atlan_tags"
]))
def test_to_camel_case_overrides(override_key):
    expected = {
        "index_type_es_fields": "IndexTypeESFields",
        "source_url": "sourceURL",
        "source_embed_url": "sourceEmbedURL",
        "sql_dbt_sources": "sqlDBTSources",
        "purpose_atlan_tags": "purposeClassifications",
        "mapped_atlan_tag_name": "mappedClassificationName",
        "has_lineage": "__hasLineage",
        "atlan_tags": "classifications",
    }[override_key]
    
    result = to_camel_case(override_key)
    assert result == expected, f"Override '{override_key}' returned '{result}' instead of '{expected}'"


# Test 5: to_snake_case should handle known special cases
@given(st.sampled_from(["purposeClassifications", "mappedClassificationName"]))
def test_to_snake_case_special_cases(special_case):
    expected = {
        "purposeClassifications": "purpose_atlan_tags",
        "mappedClassificationName": "mapped_atlan_tag_name"
    }[special_case]
    
    result = to_snake_case(special_case)
    assert result == expected, f"Special case '{special_case}' returned '{result}' instead of '{expected}'"


# Test 6: construct_object_key should preserve single slashes and remove duplicates
@given(
    st.text(alphabet=st.characters(blacklist_characters="/\x00"), min_size=0, max_size=100),
    st.text(alphabet=st.characters(blacklist_characters="/\x00"), min_size=1, max_size=100)
)
def test_construct_object_key_slash_handling(prefix, name):
    result = construct_object_key(prefix, name)
    
    # Should not have double slashes (unless empty prefix)
    if prefix:
        assert "//" not in result, f"Result '{result}' contains double slashes"
        
        # Should join with exactly one slash between prefix and name
        if prefix and name:
            # The result should contain both prefix and name parts
            assert prefix.rstrip("/") in result or prefix == "", f"Prefix '{prefix}' not found in result '{result}'"
            assert name.strip("/") in result, f"Name '{name}' not found in result '{result}'"


# Test 7: construct_object_key with empty prefix should return name as-is
@given(st.text(min_size=1))
def test_construct_object_key_empty_prefix(name):
    result = construct_object_key("", name)
    assert result == name, f"Empty prefix should return name as-is, got '{result}' for name '{name}'"


# Test 8: Round-trip property for simple snake_case strings
@given(st.from_regex(r"[a-z]+(_[a-z]+)*", fullmatch=True))
def test_snake_to_camel_partial_roundtrip(snake_str):
    # Skip special overrides
    assume(snake_str not in ["purpose_atlan_tags", "mapped_atlan_tag_name", "has_lineage", "atlan_tags"])
    assume(snake_str not in ["index_type_es_fields", "source_url", "source_embed_url", "sql_dbt_sources"])
    
    camel = to_camel_case(snake_str)
    back_to_snake = to_snake_case(camel)
    
    # Due to information loss (e.g., acronyms), we can't guarantee perfect round-trip
    # But we can check that the result is snake_case
    assert "_" not in back_to_snake or all(c.islower() or c == "_" for c in back_to_snake), \
        f"Result '{back_to_snake}' is not valid snake_case"


# Test 9: to_camel_case should handle prefixes correctly
@given(st.text(min_size=1))
def test_to_camel_case_alpha_prefixes(suffix):
    # Test alpha_dq prefix
    input_str = f"alpha_dq_{suffix}"
    result = to_camel_case(input_str)
    assert result.startswith("alpha_dq"), f"Result '{result}' doesn't preserve 'alpha_dq' prefix"
    
    # Test alpha_asset prefix  
    input_str = f"alpha_asset_{suffix}"
    result = to_camel_case(input_str)
    assert result.startswith("alpha_asset"), f"Result '{result}' doesn't preserve 'alpha_asset' prefix"


# Test 10: to_python_class_name should handle the documented examples correctly
def test_to_python_class_name_documented_examples():
    test_cases = [
        ("AtlasGlossaryPreferredTerm", "AtlasGlossaryPreferredTerm"),
        ("hello-world-123", "HelloWorld123"),
        ("my.email@address.com", "MyEmailAddressCom"),
        ("123_start_with_number", "StartWithNumber"),
        ("class", "Class_"),
    ]
    
    for input_val, expected in test_cases:
        result = to_python_class_name(input_val)
        assert result == expected, f"Example '{input_val}' returned '{result}' instead of '{expected}'"


if __name__ == "__main__":
    # Run a quick test to ensure imports work
    print("Testing pyatlan.model.utils functions...")
    test_to_python_class_name_documented_examples()
    print("Basic tests passed!")