import re
from hypothesis import given, strategies as st, assume, settings
from bs4 import BeautifulSoup, Tag, NavigableString
import pytest


# Strategy for generating valid HTML tag names
tag_names = st.sampled_from(['div', 'p', 'span', 'a', 'h1', 'h2', 'h3', 'ul', 'li', 'body', 'html', 'head', 'title', 'b', 'i', 'em', 'strong', 'section', 'article'])

# Strategy for generating valid HTML attribute names
attr_names = st.sampled_from(['id', 'class', 'href', 'title', 'style', 'data-value', 'role', 'aria-label'])

# Strategy for generating safe text content
safe_text = st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs', 'Co'), min_codepoint=32, max_codepoint=126), min_size=1, max_size=50)

# Strategy for generating attribute values (simpler to avoid injection issues)
attr_values = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ ', min_size=1, max_size=30)


@st.composite
def simple_html(draw):
    """Generate simple, valid HTML strings."""
    tag = draw(tag_names)
    text = draw(safe_text)
    
    # Optional attributes
    if draw(st.booleans()):
        attrs = {}
        num_attrs = draw(st.integers(min_value=1, max_value=3))
        for _ in range(num_attrs):
            attr_name = draw(attr_names)
            attr_value = draw(attr_values)
            attrs[attr_name] = attr_value
        
        attr_str = ' '.join([f'{k}="{v}"' for k, v in attrs.items()])
        return f'<{tag} {attr_str}>{text}</{tag}>'
    else:
        return f'<{tag}>{text}</{tag}>'


@st.composite
def nested_html(draw):
    """Generate nested HTML structures."""
    root_tag = draw(tag_names)
    num_children = draw(st.integers(min_value=1, max_value=5))
    
    children = []
    for _ in range(num_children):
        child_tag = draw(tag_names)
        child_text = draw(safe_text)
        children.append(f'<{child_tag}>{child_text}</{child_tag}>')
    
    children_html = ''.join(children)
    return f'<{root_tag}>{children_html}</{root_tag}>'


@given(simple_html())
@settings(max_examples=200)
def test_decode_equals_str(html):
    """Test that decode() always equals str() for any parsed HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.decode() == str(soup)


@given(simple_html())
@settings(max_examples=200)
def test_text_preserved_through_prettify(html):
    """Test that text content is preserved through prettify round-trip."""
    soup = BeautifulSoup(html, 'html.parser')
    original_text = soup.get_text(strip=True)
    
    prettified = soup.prettify()
    soup2 = BeautifulSoup(prettified, 'html.parser')
    new_text = soup2.get_text(strip=True)
    
    assert original_text == new_text


@given(nested_html())
@settings(max_examples=200)
def test_extract_removes_element(html):
    """Test that extracting an element removes it from the tree."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all elements
    all_tags = soup.find_all()
    assume(len(all_tags) > 1)  # Need at least 2 elements (root + child)
    
    # Pick a non-root element to extract
    element_to_extract = all_tags[1]
    tag_name = element_to_extract.name
    
    # Count elements with this tag name before extraction
    count_before = len(soup.find_all(tag_name))
    
    # Extract the element
    extracted = element_to_extract.extract()
    
    # Count elements with this tag name after extraction
    count_after = len(soup.find_all(tag_name))
    
    # Verify properties
    assert extracted.parent is None
    assert count_after == count_before - 1


@given(nested_html())
@settings(max_examples=200)
def test_find_all_vs_select_for_tags(html):
    """Test that find_all and CSS select return same count for simple tag selectors."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get all unique tag names in the soup
    all_tags = soup.find_all()
    tag_names_in_soup = list(set(tag.name for tag in all_tags))
    
    for tag_name in tag_names_in_soup:
        find_all_count = len(soup.find_all(tag_name))
        select_count = len(soup.select(tag_name))
        assert find_all_count == select_count, f"Mismatch for tag {tag_name}: find_all={find_all_count}, select={select_count}"


@given(simple_html())
@settings(max_examples=200)
def test_encode_decode_round_trip(html):
    """Test that encoding and decoding maintains the structure."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Encode to bytes and create new soup from it
    encoded = soup.encode('utf-8')
    soup2 = BeautifulSoup(encoded, 'html.parser')
    
    # The text content should be the same
    assert soup.get_text(strip=True) == soup2.get_text(strip=True)


@given(nested_html())
@settings(max_examples=200) 
def test_append_increases_child_count(html):
    """Test that append increases the child count by 1."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find a tag to append to
    target = soup.find()
    assume(target is not None)
    
    # Count children before
    children_before = len(list(target.children))
    
    # Create and append a new element
    new_tag = soup.new_tag('span')
    new_tag.string = 'appended'
    target.append(new_tag)
    
    # Count children after
    children_after = len(list(target.children))
    
    assert children_after == children_before + 1
    assert new_tag.parent == target


@given(simple_html(), safe_text)
@settings(max_examples=200)
def test_navigable_string_preserves_text(html, text):
    """Test that NavigableString preserves text content exactly."""
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find()
    assume(tag is not None)
    
    # Replace the text with a NavigableString
    tag.string = NavigableString(text)
    
    # The text should be preserved exactly
    assert str(tag.string) == text
    assert tag.get_text() == text


@given(nested_html())
@settings(max_examples=200)
def test_clear_removes_all_children(html):
    """Test that clear() removes all children from a tag."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find a tag with children
    target = soup.find()
    assume(target is not None)
    assume(len(list(target.children)) > 0)
    
    # Clear the tag
    target.clear()
    
    # Should have no children
    assert len(list(target.children)) == 0
    assert target.get_text(strip=True) == ''


if __name__ == '__main__':
    pytest.main([__file__, '-v'])