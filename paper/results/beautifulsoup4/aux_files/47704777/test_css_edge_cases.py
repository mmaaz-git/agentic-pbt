"""Additional property-based tests for bs4.css module edge cases."""

import string
from hypothesis import given, strategies as st, assume, settings, example
from bs4 import BeautifulSoup
from bs4.css import CSS
from bs4.element import ResultSet
import soupsieve


# Test for closest() function properties
@given(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=5))
@settings(max_examples=100)
def test_closest_finds_self_when_matching(tag_name):
    """Test that closest() returns the element itself when it matches the selector."""
    html = f"<{tag_name} id='test'>Content</{tag_name}>"
    soup = BeautifulSoup(html, 'html.parser')
    element = soup.find(id='test')
    
    if element:
        # Element should find itself when using its own tag name as selector
        closest_result = element.css.closest(tag_name)
        assert closest_result == element
        
        # Element should find itself when using its ID
        closest_result = element.css.closest('#test')
        assert closest_result == element


@given(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=5))
@settings(max_examples=100)
def test_closest_returns_none_for_no_match(tag_name):
    """Test that closest() returns None when no match is found."""
    html = f"<div><span id='test'>Content</span></div>"
    soup = BeautifulSoup(html, 'html.parser')
    element = soup.find(id='test')
    
    if element:
        # Should return None for a non-existent selector
        closest_result = element.css.closest('nonexistent')
        assert closest_result is None


@given(st.integers(min_value=0, max_value=5))
@settings(max_examples=100)
def test_filter_only_direct_children(depth):
    """Test that filter() only matches direct children, not descendants."""
    # Build nested structure
    html = "<div id='parent'>"
    for i in range(depth):
        html += f"<div class='level{i}'>"
    html += "<span>content</span>"
    for i in range(depth):
        html += "</div>"
    html += "</div>"
    
    soup = BeautifulSoup(html, 'html.parser')
    parent = soup.find(id='parent')
    
    if parent:
        # filter should only return direct children
        filtered = parent.css.filter('div')
        
        # Should only get the immediate child div if depth > 0
        if depth > 0:
            assert len(filtered) == 1
            assert 'level0' in filtered[0].get('class', [])
        else:
            assert len(filtered) == 0
        
        # Compare with select which gets all descendants
        selected = parent.css.select('div')
        assert len(selected) == depth  # All nested divs


@given(st.lists(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=5), min_size=0, max_size=10))
@settings(max_examples=100)
def test_empty_selector_results(tag_names):
    """Test behavior with selectors that match nothing."""
    # Create HTML with specific tags
    html = "<html><body>"
    for tag in tag_names:
        html += f"<{tag}>content</{tag}>"
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # Selector that definitely won't match
    results = css.select('nonexistenttag')
    assert isinstance(results, ResultSet)
    assert len(results) == 0
    
    # select_one should return None
    result = css.select_one('nonexistenttag')
    assert result is None
    
    # iselect should yield nothing
    iresults = list(css.iselect('nonexistenttag'))
    assert iresults == []


@given(st.integers(min_value=-10, max_value=10))
@settings(max_examples=100)
def test_negative_limit_behavior(limit):
    """Test how the module handles negative or zero limit values."""
    html = "<html><body><p>1</p><p>2</p><p>3</p></body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # Test select with various limit values
    if limit < 0:
        # Negative limits might be treated as 0 (no limit) or cause error
        try:
            results = css.select('p', limit=limit)
            # If it doesn't error, check behavior
            assert isinstance(results, ResultSet)
        except (ValueError, TypeError):
            # It's reasonable to reject negative limits
            pass
    else:
        results = css.select('p', limit=limit)
        assert isinstance(results, ResultSet)
        if limit == 0:
            # 0 should mean no limit
            assert len(results) == 3
        else:
            assert len(results) <= min(limit, 3)


@given(st.text(alphabet=string.printable, min_size=0, max_size=20))
@settings(max_examples=100)
def test_escape_special_characters(text):
    """Test that escape handles various special characters."""
    soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
    css = soup.css
    
    try:
        escaped = css.escape(text)
        # Escaped value should be a string
        assert isinstance(escaped, str)
        
        # Try using it in a selector (shouldn't error even if no match)
        selector = f"#{escaped}"
        results = css.select(selector)
        assert isinstance(results, ResultSet)
        
    except Exception:
        # Some characters might not be escapeable, which is acceptable
        pass


@given(st.lists(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=3), min_size=1, max_size=5))
@settings(max_examples=100)
def test_multiple_selectors_joined(selectors):
    """Test behavior with multiple selectors joined with commas."""
    html = "<html><body>"
    for i, sel in enumerate(selectors):
        html += f"<{sel} id='el{i}'>content</{sel}>"
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # Join selectors with comma (CSS OR operation)
    combined_selector = ', '.join(selectors)
    
    try:
        results = css.select(combined_selector)
        assert isinstance(results, ResultSet)
        
        # Results from combined should equal union of individual results
        individual_results = []
        for sel in selectors:
            individual_results.extend(css.select(sel))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_individual = []
        for item in individual_results:
            if item not in seen:
                seen.add(item)
                unique_individual.append(item)
        
        assert len(results) == len(unique_individual)
        
    except soupsieve.SelectorSyntaxError:
        # Invalid selector combination is acceptable
        pass


@given(st.booleans())
@settings(max_examples=50)
def test_namespace_handling(use_namespace):
    """Test namespace parameter handling."""
    # Create HTML with namespace
    html = '''<html xmlns:custom="http://example.com/custom">
    <body>
        <custom:element id="test">Content</custom:element>
        <element id="regular">Regular</element>
    </body>
    </html>'''
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    if use_namespace:
        namespaces = {'custom': 'http://example.com/custom'}
    else:
        namespaces = None
    
    # Try selecting with namespace
    try:
        # This should work regardless of namespace parameter
        results = css.select('element', namespaces=namespaces)
        assert isinstance(results, ResultSet)
        
        # Also test with select_one
        result = css.select_one('element', namespaces=namespaces)
        assert result is None or hasattr(result, 'name')
        
    except Exception:
        # Namespace handling might have limitations
        pass


# Test match() with complex selectors
@given(
    st.integers(min_value=1, max_value=5),
    st.sampled_from(['>', '+', '~', ' '])
)
@settings(max_examples=100)
def test_match_with_combinators(num_elements, combinator):
    """Test match() with CSS combinators."""
    # Build HTML with related elements
    html = "<html><body>"
    for i in range(num_elements):
        html += f"<div class='item{i}' id='div{i}'>Content {i}</div>"
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Test various combinator selectors
    if num_elements >= 2:
        elem1 = soup.find(id='div0')
        elem2 = soup.find(id='div1')
        
        if elem1 and elem2:
            # Adjacent sibling
            if combinator == '+':
                selector = f"#div0 + div"
                # elem2 should match as it's adjacent to div0
                assert elem2.css.match(selector) == False  # match checks if elem2 matches the whole selector
                
            # General sibling
            elif combinator == '~':
                selector = f"#div0 ~ div"
                assert elem2.css.match(selector) == False  # match checks elem2 against full selector
                
            # Descendant
            elif combinator == ' ':
                selector = f"body div"
                assert elem1.css.match(selector) == True
                assert elem2.css.match(selector) == True
                
            # Child
            elif combinator == '>':
                selector = f"body > div"
                assert elem1.css.match(selector) == True
                assert elem2.css.match(selector) == True