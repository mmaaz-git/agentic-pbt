import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/mdxpy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
from mdxpy import (
    normalize, Member, Order, ElementType, MdxTuple, 
    MdxHierarchySet, DimensionProperty
)
from mdxpy.mdx import MdxAxis, DescFlag


@given(st.text())
def test_normalize_idempotence(s):
    """normalize() should be idempotent - normalizing twice equals normalizing once"""
    normalized_once = normalize(s)
    normalized_twice = normalize(normalized_once)
    assert normalized_once == normalized_twice


@given(st.text(min_size=1).filter(lambda x: '.' not in x and '[' not in x and ']' not in x))
def test_member_unique_name_round_trip(element_name):
    """Creating a Member and getting its unique name should preserve structure"""
    # Test with same dimension and hierarchy (SHORT_NOTATION=False case)
    original_short_notation = Member.SHORT_NOTATION
    try:
        Member.SHORT_NOTATION = False
        member = Member("TestDim", "TestDim", element_name)
        unique_name = member.unique_name
        
        # Parse back from unique name
        parsed_member = Member.from_unique_name(unique_name)
        
        # Should have same components
        assert parsed_member.dimension.lower() == "testdim"
        assert parsed_member.hierarchy.lower() == "testdim"
        assert parsed_member.element.lower() == element_name.lower().replace(" ", "")
        assert parsed_member.unique_name == unique_name
    finally:
        Member.SHORT_NOTATION = original_short_notation


@given(st.sampled_from(["asc", "ASC", "Asc", "desc", "DESC", "Desc", "basc", "BASC", "bdesc", "BDESC"]))
def test_order_enum_case_insensitive(order_str):
    """Order enum should parse strings case-insensitively"""
    parsed = Order(order_str)
    assert parsed.name.lower() == order_str.lower()


@given(st.sampled_from(["numeric", "NUMERIC", "Numeric", "string", "STRING", "String", 
                        "consolidated", "CONSOLIDATED", "Consolidated"]))
def test_element_type_enum_case_insensitive(type_str):
    """ElementType enum should parse strings case-insensitively"""
    parsed = ElementType(type_str)
    assert parsed.name.lower() == type_str.lower()


@given(st.lists(st.text(min_size=1).filter(lambda x: '.' not in x and '[' not in x and ']' not in x), 
                min_size=0, max_size=10))
def test_mdx_tuple_length(element_names):
    """MdxTuple length should match number of members added"""
    tuple_obj = MdxTuple.empty()
    assert len(tuple_obj) == 0
    
    for i, element_name in enumerate(element_names):
        member = Member("Dim", "Hier", element_name)
        tuple_obj.add_member(member)
        assert len(tuple_obj) == i + 1


@given(st.lists(st.text(min_size=1), min_size=0, max_size=5),
       st.lists(st.text(min_size=1), min_size=0, max_size=5))
def test_mdx_axis_emptiness_invariant(tuple_elements, set_dims):
    """MdxAxis is empty iff it has no tuples and no sets"""
    axis = MdxAxis.empty()
    assert axis.is_empty()
    
    # Add tuples
    for element in tuple_elements:
        try:
            member = Member("TestDim", "TestHier", element)
            tuple_obj = MdxTuple.of(member)
            axis.add_tuple(tuple_obj)
        except:
            # Skip invalid inputs
            pass
    
    # Try to add sets (should fail if tuples exist)
    if not tuple_elements:
        for dim in set_dims:
            try:
                hierarchy_set = MdxHierarchySet.from_str(dim, dim, "{}")
                axis.add_set(hierarchy_set) 
            except:
                # Expected to fail if tuples exist
                pass
    
    # Check emptiness invariant
    has_content = bool(axis.tuples) or bool(axis.dim_sets)
    assert axis.is_empty() == (not has_content)


@given(st.text(min_size=1))
def test_dimension_property_unique_name_round_trip(attribute_name):
    """DimensionProperty should round-trip through unique names"""
    assume('.' not in attribute_name and '[' not in attribute_name and ']' not in attribute_name)
    
    prop = DimensionProperty("TestDim", "TestHier", attribute_name)
    unique_name = prop.unique_name
    
    parsed_prop = DimensionProperty.from_unique_name(unique_name)
    
    assert parsed_prop.dimension.lower() == "testdim"
    assert parsed_prop.hierarchy.lower() == "testhier"
    assert parsed_prop.element.lower() == attribute_name.lower().replace(" ", "")


@given(st.sampled_from(["self", "SELF", "after", "AFTER", "before", "BEFORE", 
                        "beforeandafter", "BEFOREANDAFTER", "selfandafter", "SELFANDAFTER",
                        "selfandbefore", "SELFANDBEFORE", "selfbeforeafter", "SELFBEFOREAFTER",
                        "leaves", "LEAVES"]))
def test_desc_flag_enum_case_insensitive(flag_str):
    """DescFlag enum should parse strings case-insensitively, ignoring spaces"""
    parsed = DescFlag(flag_str)
    assert parsed.name.replace("_", "").lower() == flag_str.replace(" ", "").lower()


@given(st.integers(min_value=0, max_value=100), 
       st.integers(min_value=0, max_value=100))
def test_mdx_hierarchy_subset_length(start, length):
    """SubsetHierarchySet should correctly encode start and length in MDX"""
    base_set = MdxHierarchySet.from_str("TestDim", "TestHier", "{[TestDim].[TestHier].Members}")
    subset = base_set.subset(start, length)
    
    mdx = subset.to_mdx()
    assert f"SUBSET(" in mdx
    assert f",{start},{length})" in mdx


@given(st.integers(min_value=1, max_value=100))
def test_mdx_hierarchy_head_tail(n):
    """Head and Tail operations should encode correctly in MDX"""
    base_set = MdxHierarchySet.from_str("TestDim", "TestHier", "{[TestDim].[TestHier].Members}")
    
    head_set = base_set.head(n)
    head_mdx = head_set.to_mdx()
    assert f"HEAD(" in head_mdx
    assert f",{n})" in head_mdx
    
    tail_set = base_set.tail(n)
    tail_mdx = tail_set.to_mdx()
    assert f"TAIL(" in tail_mdx
    assert f",{n})" in tail_mdx