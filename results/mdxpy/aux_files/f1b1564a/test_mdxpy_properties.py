#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/mdxpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import mdxpy
from mdxpy import Member, MdxTuple, normalize, Order, ElementType
from mdxpy.mdx import DescFlag


@given(st.text())
def test_normalize_idempotence(s):
    """The normalize function should be idempotent: f(f(x)) = f(x)"""
    normalized_once = normalize(s)
    normalized_twice = normalize(normalize(s))
    assert normalized_once == normalized_twice


@given(st.text(min_size=1), st.text(min_size=1), st.text(min_size=1))
def test_member_round_trip(dimension, hierarchy, element):
    """Creating a Member from parts and getting its unique_name should be consistent"""
    # Avoid edge cases with special characters in the unique name format
    assume("].[" not in dimension)
    assume("].[" not in hierarchy)
    assume("].[" not in element)
    assume("[" not in dimension)
    assume("[" not in element)
    assume("[" not in hierarchy)
    assume("]" not in dimension)
    assume("]" not in element)
    assume("]" not in hierarchy)
    
    member = Member(dimension, hierarchy, element)
    unique_name = member.unique_name
    
    # Parse the unique name back
    member_from_unique = Member.from_unique_name(unique_name)
    
    # The normalized versions should match
    assert normalize(member.dimension) == normalize(member_from_unique.dimension)
    assert normalize(member.hierarchy) == normalize(member_from_unique.hierarchy)
    assert normalize(member.element) == normalize(member_from_unique.element)


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_mdx_tuple_length(member_names):
    """MdxTuple length should match the number of members added"""
    # Create members with simple unique names
    members = []
    for i, name in enumerate(member_names):
        # Avoid problematic characters
        assume("].[" not in name)
        assume("[" not in name)
        assume("]" not in name)
        members.append(Member(f"dim{i}", f"dim{i}", name))
    
    tuple_obj = MdxTuple(members)
    assert len(tuple_obj) == len(members)
    assert len(tuple_obj.members) == len(members)


@given(st.sampled_from(["self", "after", "before", "SELF", "AFTER", "BEFORE", 
                        "self_and_after", "SELF_AND_AFTER", "selfandafter",
                        "before_and_after", "BEFORE_AND_AFTER", "beforeandafter"]))
def test_desc_flag_parsing(flag_str):
    """DescFlag should parse string values correctly (case-insensitive, space-insensitive)"""
    parsed = DescFlag._missing_(flag_str)
    assert parsed is not None
    assert isinstance(parsed, DescFlag)


@given(st.sampled_from(["asc", "desc", "basc", "bdesc", "ASC", "DESC", "BASC", "BDESC"]))
def test_order_parsing(order_str):
    """Order enum should parse string values correctly (case-insensitive)"""
    parsed = Order._missing_(order_str)
    assert parsed is not None
    assert isinstance(parsed, Order)


@given(st.text(min_size=1), st.text(min_size=1), st.text(min_size=1))
def test_member_unique_name_components(dimension, hierarchy, element):
    """Test that Member correctly extracts components from unique names"""
    # Avoid edge cases with special characters
    assume("].[" not in dimension)
    assume("].[" not in hierarchy) 
    assume("].[" not in element)
    assume("[" not in dimension)
    assume("[" not in element)
    assume("[" not in hierarchy)
    assume("]" not in dimension.replace("]]", ""))
    assume("]" not in element.replace("]]", ""))
    assume("]" not in hierarchy.replace("]]", ""))
    
    # Create a member
    member = Member(dimension, hierarchy, element)
    unique_name = member.unique_name
    
    # Extract components using static methods
    extracted_dim = Member.dimension_name_from_unique_name(unique_name)
    extracted_elem = Member.element_name_from_unique_name(unique_name)
    
    # The extracted components should match the normalized originals
    assert extracted_dim == normalize(dimension)
    assert extracted_elem == normalize(element)
    
    # If the unique name has 3 parts, test hierarchy extraction
    if unique_name.count("].[") == 2:
        extracted_hier = Member.hierarchy_name_from_unique_name(unique_name)
        assert extracted_hier == normalize(hierarchy)


@given(st.lists(st.text(min_size=1), min_size=0, max_size=5))
def test_mdx_tuple_empty_status(member_names):
    """Test that MdxTuple correctly reports empty status"""
    members = []
    for i, name in enumerate(member_names):
        # Avoid problematic characters
        assume("].[" not in name)
        assume("[" not in name)
        assume("]" not in name)
        members.append(Member(f"dim{i}", f"dim{i}", name))
    
    tuple_obj = MdxTuple(members)
    
    if len(members) == 0:
        assert tuple_obj.is_empty()
    else:
        assert not tuple_obj.is_empty()


@given(st.sampled_from(["numeric", "string", "consolidated", "NUMERIC", "STRING", "CONSOLIDATED"]))
def test_element_type_parsing(type_str):
    """ElementType enum should parse string values correctly (case-insensitive)"""
    parsed = ElementType._missing_(type_str)
    assert parsed is not None
    assert isinstance(parsed, ElementType)


@given(st.text())
def test_normalize_preserves_double_brackets(s):
    """Test that normalize correctly handles ']' by replacing with ']]'"""
    # Count the original ']' characters (not counting those that are already doubled)
    original_single_brackets = s.replace("]]", "").count("]")
    
    normalized = normalize(s)
    
    # After normalization:
    # - All spaces should be removed
    # - All text should be lowercase
    # - Each original ']' should become ']]'
    
    # Verify no spaces
    assert " " not in normalized
    
    # Verify lowercase
    assert normalized == normalized.lower()
    
    # Count ']' in the normalized string
    # Every ']' should be part of a ']]' pair
    if "]" in normalized:
        # Split by ']]' - if properly normalized, there should be no lone ']'
        parts = normalized.split("]]")
        for part in parts[:-1]:  # Don't check the last part
            assert "]" not in part


@given(st.integers(min_value=0, max_value=100))
def test_mdx_axis_head_tail_values(count):
    """Test that head and tail values are preserved in MDX generation"""
    from mdxpy.mdx import MdxAxis, MdxHierarchySet
    
    axis = MdxAxis()
    # Add a simple set
    dim_set = MdxHierarchySet.from_str("TestDim", "TestHier", "{[TestDim].[TestHier].Members}")
    axis.add_set(dim_set)
    
    # Generate MDX with head
    mdx_with_head = axis.to_mdx(head=count)
    if count is not None:
        assert f"HEAD(" in mdx_with_head
        assert f", {count})" in mdx_with_head
    
    # Generate MDX with tail
    mdx_with_tail = axis.to_mdx(tail=count)
    if count is not None:
        assert f"TAIL(" in mdx_with_tail
        assert f", {count})" in mdx_with_tail


if __name__ == "__main__":
    # Run with pytest
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    print(result.stderr)
    exit(result.returncode)