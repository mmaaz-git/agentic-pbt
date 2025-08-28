#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

import keyword
import re
from hypothesis import given, strategies as st, settings, assume

from pyatlan.model.utils import (
    to_python_class_name,
    to_camel_case,
    to_snake_case,
    construct_object_key
)


# Property 1: to_python_class_name should always return a valid Python class name or empty string
@given(st.text())
def test_to_python_class_name_returns_valid_or_empty(input_string):
    result = to_python_class_name(input_string)
    
    # Should return either empty string or valid class name
    if result:
        # Must be a valid identifier
        assert result.isidentifier(), f"{result} is not a valid identifier"
        # Must not be a keyword
        assert not keyword.iskeyword(result), f"{result} is a Python keyword"
        # Must start with uppercase (PEP 8 convention for classes)
        assert result[0].isupper(), f"{result} doesn't start with uppercase"


# Property 2: construct_object_key handles slashes consistently
@given(st.text(), st.text())
def test_construct_object_key_slash_handling(prefix, name):
    result = construct_object_key(prefix, name)
    
    # If prefix is empty, should return name as-is
    if not prefix:
        assert result == name
    else:
        # Should never have double slashes in the middle (unless they were in the input)
        # But only check if neither input had double slashes
        if "//" not in prefix and "//" not in name:
            # Allow double slashes at the beginning (for URLs or absolute paths)
            middle_part = result[2:] if result.startswith("//") else result
            assert "//" not in middle_part, f"Double slash found in: {result}"


# Property 3: to_camel_case and to_snake_case roundtrip (for simple cases)
@given(st.from_regex(r"[a-z][a-z0-9]*(_[a-z][a-z0-9]*)*", fullmatch=True))
def test_snake_to_camel_preserves_information(snake_string):
    # Skip special cases with overrides
    assume(snake_string not in ["purpose_atlan_tags", "mapped_atlan_tag_name"])
    
    camel = to_camel_case(snake_string)
    back_to_snake = to_snake_case(camel)
    
    # The round-trip should preserve the original for simple snake_case strings
    assert back_to_snake == snake_string, f"Round-trip failed: {snake_string} -> {camel} -> {back_to_snake}"


# Property 4: to_python_class_name should handle already valid class names unchanged
@given(st.from_regex(r"[A-Z][a-zA-Z0-9]*", fullmatch=True))
def test_to_python_class_name_preserves_valid_names(valid_class_name):
    # Skip Python keywords
    assume(not keyword.iskeyword(valid_class_name))
    
    result = to_python_class_name(valid_class_name)
    
    # Should preserve already valid class names
    assert result == valid_class_name, f"Changed valid class name: {valid_class_name} -> {result}"


# Property 5: construct_object_key should not lose parts of the path
@given(
    st.text(min_size=1).filter(lambda x: x.strip() and x != "/"),
    st.text(min_size=1).filter(lambda x: x.strip() and x != "/")
)
def test_construct_object_key_preserves_content(prefix, name):
    result = construct_object_key(prefix, name)
    
    # The core content should be preserved (after stripping slashes)
    prefix_core = prefix.strip("/")
    name_core = name.strip("/")
    
    # Both parts should appear in the result
    if prefix_core:
        assert prefix_core in result, f"Lost prefix content: {prefix} in {result}"
    if name_core:
        assert name_core in result, f"Lost name content: {name} in {result}"


# Property 6: to_python_class_name should never return invalid identifiers
@given(st.text())
def test_to_python_class_name_never_invalid(input_string):
    result = to_python_class_name(input_string)
    
    # Should never return something that's not empty but also not a valid identifier
    if result:
        # This is stricter - checking the invariant more thoroughly
        try:
            # Try to use it as a class name
            exec(f"class {result}: pass")
        except SyntaxError:
            assert False, f"to_python_class_name returned invalid class name: {result}"




if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])