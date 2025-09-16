import re
from hypothesis import given, strategies as st, assume, settings
from bs4.filter import (
    MatchRule, AttributeValueMatchRule, StringMatchRule, 
    TagNameMatchRule, SoupStrainer
)
from bs4 import BeautifulSoup, Tag


# Test Property 1: MatchRule with exclude_everything=True always returns False
@given(st.one_of(st.none(), st.text()))
def test_matchrule_exclude_everything_always_false(s):
    rule = MatchRule(exclude_everything=True)
    assert rule.matches_string(s) == False


# Test Property 2: MatchRule with present=True returns True for non-None strings
@given(st.text())
def test_matchrule_present_true_matches_non_none(s):
    rule = MatchRule(present=True)
    assert rule.matches_string(s) == True
    assert rule.matches_string(None) == False


# Test Property 3: MatchRule with present=False only matches None
@given(st.one_of(st.none(), st.text()))
def test_matchrule_present_false_only_matches_none(s):
    rule = MatchRule(present=False)
    if s is None:
        assert rule.matches_string(s) == True
    else:
        assert rule.matches_string(s) == False


# Test Property 4: MatchRule string exact match round-trip
@given(st.text())
def test_matchrule_string_exact_match_roundtrip(s):
    rule = MatchRule(string=s)
    assert rule.matches_string(s) == True
    
    # Also test that different strings don't match
    if s != "different":
        assert rule.matches_string("different") == False


# Test Property 5: MatchRule regex pattern matching
@given(st.text(min_size=1))
def test_matchrule_pattern_matching(s):
    # Create a pattern that should match the string
    pattern = re.compile(re.escape(s))
    rule = MatchRule(pattern=pattern)
    assert rule.matches_string(s) == True
    assert rule.matches_string(None) == False


# Test Property 6: AttributeValueMatchRule and StringMatchRule consistency
@given(
    st.one_of(st.none(), st.text()),
    st.one_of(st.none(), st.text()),
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_attribute_and_string_matchrule_consistency(test_string, rule_string, present, exclude_everything, use_pattern):
    if use_pattern and rule_string:
        pattern = re.compile(re.escape(rule_string))
        attr_rule = AttributeValueMatchRule(pattern=pattern, present=present if not use_pattern else None, 
                                           exclude_everything=exclude_everything)
        str_rule = StringMatchRule(pattern=pattern, present=present if not use_pattern else None,
                                  exclude_everything=exclude_everything)
    else:
        attr_rule = AttributeValueMatchRule(string=rule_string, present=present, 
                                           exclude_everything=exclude_everything)
        str_rule = StringMatchRule(string=rule_string, present=present,
                                  exclude_everything=exclude_everything)
    
    # Both should behave identically
    assert attr_rule.matches_string(test_string) == str_rule.matches_string(test_string)


# Test Property 7: SoupStrainer with only string rules cannot match Tags
@given(st.text())
def test_soupstrainer_string_only_no_tag_match(string_to_match):
    # Create a strainer with only string rules
    strainer = SoupStrainer(string=string_to_match)
    
    # Create a tag
    soup = BeautifulSoup('<p>test</p>', 'html.parser')
    tag = soup.find('p')
    
    # According to the code, a strainer with only string rules cannot match a Tag
    assert strainer.matches_tag(tag) == False


# Test Property 8: TagNameMatchRule matches both string and tag consistently
@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1))
def test_tagname_matchrule_consistency(tag_name):
    # Ensure valid tag name (lowercase letters only for simplicity)
    rule = TagNameMatchRule(string=tag_name)
    
    # Test string matching
    assert rule.matches_string(tag_name) == True
    
    # Create a tag with that name and test tag matching
    soup = BeautifulSoup(f'<{tag_name}></{tag_name}>', 'html.parser')
    tag = soup.find(tag_name)
    if tag:
        assert rule.matches_tag(tag) == True


# Test Property 9: SoupStrainer attribute matching consistency
@given(
    st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1),
    st.text(),
    st.text()
)
def test_soupstrainer_attribute_matching(tag_name, attr_name, attr_value):
    assume(attr_name and attr_name.replace('-', '').replace('_', '').isalnum())
    
    # Create a strainer that looks for specific attribute value
    strainer = SoupStrainer(attrs={attr_name: attr_value})
    
    # Create a tag with that attribute
    soup = BeautifulSoup(f'<{tag_name} {attr_name}="{attr_value}"></{tag_name}>', 'html.parser')
    tag = soup.find(tag_name)
    
    if tag:
        # Tag should match if it has the exact attribute value
        assert strainer.matches_tag(tag) == True
        
    # Create a tag without that attribute
    soup2 = BeautifulSoup(f'<{tag_name}></{tag_name}>', 'html.parser')
    tag2 = soup2.find(tag_name)
    
    if tag2:
        # Tag should not match if it lacks the attribute
        assert strainer.matches_tag(tag2) == False


# Test Property 10: Empty SoupStrainer behavior
@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1))
def test_empty_soupstrainer_behavior(tag_name):
    # Create an empty strainer (no rules)
    strainer = SoupStrainer()
    
    # Create a tag
    soup = BeautifulSoup(f'<{tag_name}>content</{tag_name}>', 'html.parser')
    tag = soup.find(tag_name)
    
    if tag:
        # Based on code comment: "If there are no rules at all, let anything through"
        # But actual implementation returns False when no name_rules and no attribute_rules
        result = strainer.matches_tag(tag)
        # The actual behavior is to return False, not True as the comment suggests
        assert result == False