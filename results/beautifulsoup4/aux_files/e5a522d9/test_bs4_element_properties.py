"""Property-based tests for bs4.element module using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, assume, settings
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString, PageElement
import string


# Strategies for generating test data
@st.composite
def tag_strategy(draw):
    """Generate a Tag with a valid name."""
    name = draw(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10))
    return Tag(name=name)


@st.composite
def navigable_string_strategy(draw):
    """Generate a NavigableString with valid content."""
    content = draw(st.text(min_size=0, max_size=100))
    return NavigableString(content)


@st.composite
def page_element_strategy(draw):
    """Generate either a Tag or NavigableString."""
    if draw(st.booleans()):
        return draw(tag_strategy())
    else:
        return draw(navigable_string_strategy())


# Property 1: Insert position invariant
@given(
    tag=tag_strategy(),
    elements=st.lists(navigable_string_strategy(), min_size=1, max_size=10),
    position=st.integers(min_value=0)
)
def test_insert_position_invariant(tag, elements, position):
    """After inserting at position i, the element should be at position i in contents."""
    # First add some initial content
    initial_content = [NavigableString(f"initial{i}") for i in range(3)]
    for content in initial_content:
        tag.append(content)
    
    # Clamp position to valid range
    position = min(position, len(tag.contents))
    
    # Insert a single element
    element_to_insert = elements[0]
    original_length = len(tag.contents)
    
    # Insert the element
    tag.insert(position, element_to_insert)
    
    # Check the invariant: element should be at the position we specified
    assert tag.contents[position] is element_to_insert
    assert len(tag.contents) == original_length + 1


# Property 2: Append adds to end
@given(
    tag=tag_strategy(),
    element=navigable_string_strategy()
)
def test_append_adds_to_end(tag, element):
    """After append, the element should be the last in contents."""
    # Add some initial content
    for i in range(3):
        tag.append(NavigableString(f"content{i}"))
    
    # Append the new element
    tag.append(element)
    
    # Check that it's at the end
    assert tag.contents[-1] is element


# Property 3: Parent-child relationship invariant
@given(
    parent_tag=tag_strategy(),
    child_element=page_element_strategy(),
    position=st.integers(min_value=0, max_value=5)
)
def test_parent_child_relationship(parent_tag, child_element, position):
    """After insert/append, the element's parent should be the tag."""
    # Ensure element doesn't already have a parent
    assume(child_element.parent is None)
    
    # Add some initial content
    for i in range(3):
        parent_tag.append(NavigableString(f"content{i}"))
    
    # Clamp position
    position = min(position, len(parent_tag.contents))
    
    # Insert the element
    parent_tag.insert(position, child_element)
    
    # Check parent-child relationship
    assert child_element.parent is parent_tag
    assert child_element in parent_tag.contents


# Property 4: Multiple insert maintains order
@given(
    tag=tag_strategy(),
    elements=st.lists(navigable_string_strategy(), min_size=2, max_size=5),
    position=st.integers(min_value=0, max_value=3)
)
def test_multiple_insert_maintains_order(tag, elements, position):
    """When inserting multiple elements, they should appear in order."""
    # Add initial content
    for i in range(2):
        tag.append(NavigableString(f"initial{i}"))
    
    # Clamp position
    position = min(position, len(tag.contents))
    
    # Insert multiple elements at once
    tag.insert(position, *elements)
    
    # Check that elements appear in order starting at position
    for i, element in enumerate(elements):
        assert tag.contents[position + i] is element


# Property 5: Extend adds elements in order
@given(
    tag=tag_strategy(),
    elements=st.lists(navigable_string_strategy(), min_size=1, max_size=5)
)
def test_extend_adds_in_order(tag, elements):
    """Extend should add all elements to the end in order."""
    # Add initial content
    initial_content = [NavigableString(f"initial{i}") for i in range(2)]
    for content in initial_content:
        tag.append(content)
    
    original_length = len(tag.contents)
    
    # Extend with new elements
    tag.extend(elements)
    
    # Check all elements were added in order at the end
    assert len(tag.contents) == original_length + len(elements)
    for i, element in enumerate(elements):
        assert tag.contents[original_length + i] is element


# Property 6: Extract and re-insert round-trip
@given(
    tag=tag_strategy(),
    elements=st.lists(navigable_string_strategy(), min_size=3, max_size=5)
)
def test_extract_insert_roundtrip(tag, elements):
    """Extracting an element and re-inserting it should preserve structure."""
    # Build initial structure
    for element in elements:
        tag.append(element)
    
    # Skip if too few elements
    assume(len(tag.contents) >= 2)
    
    # Extract an element from the middle
    extract_index = len(tag.contents) // 2
    extracted = tag.contents[extract_index]
    original_content = str(extracted)
    
    # Extract it
    extracted.extract()
    
    # Verify it's gone
    assert extracted not in tag.contents
    assert extracted.parent is None
    
    # Re-insert at same position
    tag.insert(extract_index, extracted)
    
    # Verify it's back
    assert tag.contents[extract_index] is extracted
    assert extracted.parent is tag
    assert str(extracted) == original_content


# Property 7: Index method finds correct position
@given(
    tag=tag_strategy(),
    elements=st.lists(navigable_string_strategy(), min_size=1, max_size=5)
)
def test_index_finds_correct_position(tag, elements):
    """Tag.index should return the correct position of an element."""
    # Add all elements
    for element in elements:
        tag.append(element)
    
    # Check index for each element
    for i, element in enumerate(elements):
        assert tag.index(element) == i


# Property 8: Clear removes all children
@given(
    tag=tag_strategy(),
    elements=st.lists(navigable_string_strategy(), min_size=1, max_size=5)
)
def test_clear_removes_all_children(tag, elements):
    """Clear should remove all children from the tag."""
    # Add elements
    for element in elements:
        tag.append(element)
    
    # Verify they're there
    assert len(tag.contents) == len(elements)
    
    # Clear
    tag.clear()
    
    # Verify they're gone
    assert len(tag.contents) == 0
    assert tag.contents == []
    
    # Verify parent relationships are broken
    for element in elements:
        assert element.parent is None


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v"])