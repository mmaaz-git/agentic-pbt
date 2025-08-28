#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

import math
from hypothesis import given, strategies as st, assume, settings
import pytest
from pyatlan.utils import (
    to_camel_case,
    get_parent_qualified_name,
    select_optional_set_fields,
    non_null,
    deep_get,
    validate_required_fields,
    validate_single_required_field,
    get_base_type,
    API
)


@given(st.text(min_size=1, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
def test_to_camel_case_idempotence(s):
    first_conversion = to_camel_case(s)
    second_conversion = to_camel_case(first_conversion)
    assert first_conversion == second_conversion


@given(st.text(min_size=1, alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
def test_to_camel_case_starts_lowercase(s):
    result = to_camel_case(s)
    if result:
        if result[0].isalpha():
            assert result[0].islower()


@given(st.text(min_size=1))
def test_get_parent_qualified_name_is_prefix(qualified_name):
    parent = get_parent_qualified_name(qualified_name)
    if "/" in qualified_name:
        assert qualified_name.startswith(parent)
    else:
        assert parent == ""


@given(st.text(min_size=2).filter(lambda x: "/" in x))
def test_get_parent_qualified_name_transitivity(qualified_name):
    parent = get_parent_qualified_name(qualified_name)
    if "/" in parent:
        grandparent = get_parent_qualified_name(parent)
        parent_of_original = get_parent_qualified_name(qualified_name)
        grandparent_direct = get_parent_qualified_name(parent_of_original)
        assert grandparent == grandparent_direct


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.none(), st.integers(), st.text(), st.booleans())
))
def test_select_optional_fields_no_none_values(params):
    result = select_optional_set_fields(params)
    assert None not in result.values()


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.none(), st.integers(), st.text(), st.booleans())
))
def test_select_optional_fields_subset(params):
    result = select_optional_set_fields(params)
    assert all(key in params for key in result)
    assert all(result[key] == params[key] for key in result)


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.none(), st.integers(), st.text(), st.booleans())
))
def test_select_optional_fields_preserves_non_none(params):
    result = select_optional_set_fields(params)
    for key, value in params.items():
        if value is not None:
            assert key in result
            assert result[key] == value


@given(st.one_of(st.none(), st.integers(), st.text()), st.integers())
def test_non_null_returns_obj_when_not_none(obj, def_value):
    if obj is not None:
        assert non_null(obj, def_value) == obj
    else:
        assert non_null(obj, def_value) == def_value


@given(
    st.recursive(
        st.dictionaries(st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122)), 
                       st.one_of(st.integers(), st.text())),
        lambda children: st.dictionaries(
            st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
            st.one_of(children, st.integers(), st.text())
        ),
        max_leaves=3
    ),
    st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    st.integers()
)
def test_deep_get_with_simple_key(dictionary, key, value):
    if key and "." not in key:
        dictionary[key] = value
        assert deep_get(dictionary, key) == value


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.lists(st.none(), min_size=1, max_size=5)
)
def test_validate_required_fields_raises_on_none(field_names, values):
    assume(len(field_names) == len(values))
    with pytest.raises(ValueError) as exc_info:
        validate_required_fields(field_names, values)
    assert field_names[0] in str(exc_info.value)
    assert "is required" in str(exc_info.value)


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.lists(st.text(min_size=0, max_size=0), min_size=1, max_size=5)
)
def test_validate_required_fields_raises_on_empty_string(field_names, values):
    assume(len(field_names) == len(values))
    assume(all(isinstance(v, str) for v in values))
    with pytest.raises(ValueError) as exc_info:
        validate_required_fields(field_names, values)
    assert "cannot be blank" in str(exc_info.value)


@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),
    st.lists(st.just([]), min_size=1, max_size=5)
)
def test_validate_required_fields_raises_on_empty_list(field_names, values):
    assume(len(field_names) == len(values))
    with pytest.raises(ValueError) as exc_info:
        validate_required_fields(field_names, values)
    assert "cannot be an empty list" in str(exc_info.value)


@given(
    st.lists(st.text(min_size=1), min_size=2, max_size=5)
)
def test_validate_single_required_field_with_all_none(field_names):
    values = [None] * len(field_names)
    with pytest.raises(ValueError) as exc_info:
        validate_single_required_field(field_names, values)
    assert "One of the following parameters are required" in str(exc_info.value)


@given(
    st.lists(st.text(min_size=1), min_size=2, max_size=5)
)
def test_validate_single_required_field_with_multiple_values(field_names):
    values = [f"value_{i}" for i in range(len(field_names))]
    with pytest.raises(ValueError) as exc_info:
        validate_single_required_field(field_names, values)
    assert "Only one of the following parameters are allowed" in str(exc_info.value)


@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122)))
def test_get_base_type_simple_types(attribute_type):
    assume("<" not in attribute_type)
    result = get_base_type(attribute_type)
    assert result == attribute_type


@given(st.text(min_size=1))
def test_get_base_type_result_is_substring(attribute_type):
    result = get_base_type(attribute_type)
    if "<" in attribute_type and ">" in attribute_type:
        assert result in attribute_type
    else:
        assert result == attribute_type


@given(
    st.text(min_size=1),
    st.lists(st.text(min_size=1), min_size=1, max_size=5)
)
def test_api_multipart_urljoin_no_double_slashes(base_path, path_elems):
    result = API.multipart_urljoin(base_path, *path_elems)
    if not base_path.startswith("http://") and not base_path.startswith("https://"):
        assert "//" not in result
    else:
        protocol_end = result.find("://") + 3
        assert "//" not in result[protocol_end:]


@given(
    st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=97, max_codepoint=122)), min_size=1, max_size=3)
)
def test_api_multipart_urljoin_contains_elements(base_path, path_elems):
    result = API.multipart_urljoin(base_path, *path_elems)
    assert base_path.strip("/") in result
    for elem in path_elems:
        if elem.strip("/"):
            assert elem.strip("/") in result


@given(st.text(min_size=1).filter(lambda x: "/" in x))
def test_get_parent_qualified_name_reduces_path_depth(qualified_name):
    parent = get_parent_qualified_name(qualified_name)
    original_parts = qualified_name.count("/")
    parent_parts = parent.count("/") if parent else 0
    assert parent_parts < original_parts or (parent_parts == 0 and original_parts == 1)