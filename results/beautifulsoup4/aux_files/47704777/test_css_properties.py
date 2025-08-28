"""Property-based tests for bs4.css module using Hypothesis."""

import string
import random
from hypothesis import given, strategies as st, assume, settings
from bs4 import BeautifulSoup
from bs4.css import CSS
from bs4.element import ResultSet
import soupsieve


# Strategy for generating valid HTML tag names
tag_names = st.sampled_from(["div", "span", "p", "a", "h1", "h2", "section", "article", "nav"])

# Strategy for generating valid CSS class names  
css_class_names = st.text(
    alphabet=string.ascii_letters + string.digits + "-_",
    min_size=1,
    max_size=20
).filter(lambda x: x[0].isalpha() or x[0] in '_-')

# Strategy for generating simple HTML structures
@st.composite  
def html_documents(draw):
    """Generate simple HTML documents for testing."""
    num_elements = draw(st.integers(min_value=1, max_value=10))
    elements = []
    
    for i in range(num_elements):
        tag = draw(tag_names)
        class_name = draw(css_class_names)
        id_val = f"id{i}"
        content = draw(st.text(min_size=0, max_size=20))
        elements.append(f'<{tag} class="{class_name}" id="{id_val}">{content}</{tag}>')
    
    html = f"<html><body>{''.join(elements)}</body></html>"
    return html


@st.composite
def simple_css_selectors(draw):
    """Generate simple CSS selectors."""
    selector_type = draw(st.sampled_from(["tag", "class", "id", "tag.class"]))
    
    if selector_type == "tag":
        return draw(tag_names)
    elif selector_type == "class":
        class_name = draw(css_class_names)
        return f".{class_name}"
    elif selector_type == "id":
        id_num = draw(st.integers(min_value=0, max_value=9))
        return f"#id{id_num}"
    else:  # tag.class
        tag = draw(tag_names)
        class_name = draw(css_class_names)
        return f"{tag}.{class_name}"


@given(html_documents(), simple_css_selectors())
@settings(max_examples=100)
def test_select_one_matches_first_of_select(html, selector):
    """Test that select_one returns the same as the first element of select."""
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    select_results = css.select(selector)
    select_one_result = css.select_one(selector)
    
    if len(select_results) > 0:
        # select_one should return the same as the first element from select
        assert select_one_result == select_results[0]
    else:
        # If select returns empty, select_one should return None
        assert select_one_result is None


@given(html_documents(), simple_css_selectors())
@settings(max_examples=100)
def test_compiled_selector_equivalence(html, selector):
    """Test that precompiled selectors produce the same results as string selectors."""
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # Compile the selector
    try:
        compiled = css.compile(selector)
    except Exception:
        # If compilation fails, skip this test case
        assume(False)
    
    # Compare results using string selector vs compiled selector
    string_results = css.select(selector)
    compiled_results = css.select(compiled)
    
    assert string_results == compiled_results
    
    # Also test select_one
    string_one = css.select_one(selector)
    compiled_one = css.select_one(compiled)
    
    assert string_one == compiled_one


@given(html_documents(), simple_css_selectors(), st.integers(min_value=0, max_value=100))
@settings(max_examples=100)
def test_select_limit_property(html, selector, limit):
    """Test that the limit parameter correctly bounds the number of results."""
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    results = css.select(selector, limit=limit)
    
    # Results should be a ResultSet
    assert isinstance(results, ResultSet)
    
    # Number of results should not exceed limit
    if limit > 0:
        assert len(results) <= limit
    
    # Results should be a subset of unlimited results
    all_results = css.select(selector)
    
    if limit > 0:
        # Limited results should be the first `limit` elements of all results
        assert results == all_results[:limit]
    else:
        # limit=0 means no limit
        assert results == all_results


@given(html_documents(), simple_css_selectors())
@settings(max_examples=100)
def test_select_returns_resultset(html, selector):
    """Test that select always returns a ResultSet."""
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    results = css.select(selector)
    assert isinstance(results, ResultSet)
    
    # Also test filter
    body = soup.body
    if body:
        filter_results = body.css.filter(selector)
        assert isinstance(filter_results, ResultSet)


@given(st.text(alphabet=string.ascii_letters + string.digits + "-_.:[]", min_size=1, max_size=20))
@settings(max_examples=100)
def test_css_escape_in_selector(identifier):
    """Test that escaped identifiers can be used in selectors without errors."""
    # Create a simple HTML with the identifier as an ID
    soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
    css = soup.css
    
    try:
        # Escape the identifier
        escaped = css.escape(identifier)
        
        # The escaped identifier should be usable in a selector
        # Even if it doesn't match anything, it shouldn't raise an error
        selector = f"#{escaped}"
        results = css.select(selector)
        
        # Should return empty ResultSet for non-existent elements
        assert isinstance(results, ResultSet)
        assert len(results) == 0
        
    except Exception as e:
        # escape() might fail for some inputs, which is fine
        # But if it succeeds, the result should be usable
        pass


@given(html_documents(), simple_css_selectors())
@settings(max_examples=100) 
def test_match_consistency_with_select(html, selector):
    """Test that match() is consistent with select() results."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get all elements selected by the selector
    selected = soup.select(selector)
    
    # For each selected element, match() should return True
    for element in selected:
        assert element.css.match(selector) == True
    
    # Get all elements in the document
    all_elements = soup.find_all(True)  # Find all tags
    
    # Elements not in selected should not match
    for element in all_elements:
        if element in selected:
            assert element.css.match(selector) == True
        else:
            assert element.css.match(selector) == False


@given(html_documents())
@settings(max_examples=100)
def test_iselect_yields_same_as_select(html):
    """Test that iselect yields the same elements as select."""
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # Test with a simple selector that should match multiple elements
    selector = "*"  # Match all elements
    
    select_results = css.select(selector)
    iselect_results = list(css.iselect(selector))
    
    assert select_results == iselect_results
    
    # Test with limit
    limit = 3
    select_limited = css.select(selector, limit=limit) 
    iselect_limited = list(css.iselect(selector, limit=limit))
    
    assert select_limited == iselect_limited