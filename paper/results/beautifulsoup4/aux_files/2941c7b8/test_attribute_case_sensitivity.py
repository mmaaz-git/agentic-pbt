from hypothesis import given, strategies as st, assume
from bs4 import BeautifulSoup
from bs4.filter import SoupStrainer

# Test for attribute case sensitivity bug
@given(
    st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=1, max_size=10),  # Uppercase letters
    st.text(max_size=50)
)
def test_soupstrainer_attribute_case_sensitivity(attr_name_upper, attr_value):
    """Test that SoupStrainer handles case-insensitive attribute matching correctly.
    
    HTML parsers convert attribute names to lowercase, but SoupStrainer
    performs case-sensitive matching, causing uppercase attribute names
    in strainers to never match parsed HTML.
    """
    # Only test valid attribute names
    assume(attr_name_upper.isalpha())
    
    # Create a strainer looking for uppercase attribute
    strainer = SoupStrainer(attrs={attr_name_upper: attr_value})
    
    # Create HTML with the uppercase attribute (parser will convert to lowercase)
    html = f'<div {attr_name_upper}="{attr_value}"></div>'
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('div')
    
    # The tag will have lowercase attributes due to HTML parser
    assert attr_name_upper.lower() in tag.attrs
    assert tag.attrs[attr_name_upper.lower()] == attr_value
    
    # But the strainer won't match because it's looking for uppercase
    result = strainer.matches_tag(tag)
    
    # This should be True for usability, but it's False due to case sensitivity
    assert result == False  # Current (buggy) behavior
    # assert result == True  # Expected behavior


if __name__ == "__main__":
    # Run a simple example
    test_soupstrainer_attribute_case_sensitivity("CLASS", "test-class")
    print("Test passed - confirming the case sensitivity issue exists")