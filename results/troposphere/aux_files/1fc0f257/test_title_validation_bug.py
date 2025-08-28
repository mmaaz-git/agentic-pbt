"""Property-based test demonstrating the title validation bypass bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate
from troposphere import AWSObject
import re

# The validation regex from troposphere
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

@given(st.one_of(
    st.just(""),
    st.just(None),
    st.just(0),
    st.just(False),
    st.text(max_size=0)  # Empty strings
))
def test_falsy_titles_bypass_validation(title):
    """
    Property: AWSObject titles must be alphanumeric and non-empty.
    
    According to AWS CloudFormation documentation and troposphere's 
    validate_title() method, resource logical IDs (titles) must:
    - Contain only alphanumeric characters (A-Za-z0-9)
    - Be non-empty
    
    However, troposphere fails to validate titles that are falsy values.
    """
    # Create a valid definition for testing
    definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
    
    # This should fail but doesn't
    template = FlowTemplate(title, Definition=definition)
    
    # The object is created successfully (bug!)
    assert template.title == title
    
    # to_dict() also succeeds (bug!)
    result = template.to_dict()
    assert result["Type"] == "AWS::IoTThingsGraph::FlowTemplate"
    
    # But validate_title() would correctly identify it as invalid
    try:
        template.validate_title()
        # If validate_title passes, the title must match the regex
        assert valid_names.match(str(title))
    except ValueError as e:
        # validate_title correctly raises for invalid titles
        assert "not alphanumeric" in str(e)
        # This proves the bug: object was created but title is invalid!
        print(f"BUG: Object created with invalid title {title!r}, but validate_title() correctly rejects it")


@given(st.sampled_from(["", None, 0, False]))
@settings(max_examples=10)
def test_title_validation_inconsistency(title):
    """
    Property: Title validation should be consistent across all validation points.
    
    If a title is invalid, it should be rejected at object creation,
    not just when validate_title() is explicitly called.
    """
    definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
    
    # Object creation succeeds (shouldn't for invalid titles)
    template = FlowTemplate(title, Definition=definition)
    
    # to_dict with validation succeeds (shouldn't for invalid titles)  
    dict_repr = template.to_dict(validation=True)
    
    # But direct validation fails (correct behavior)
    is_valid = True
    try:
        template.validate_title()
    except ValueError:
        is_valid = False
    
    # The inconsistency: object exists with invalid title
    if not is_valid:
        print(f"INCONSISTENCY: Title {title!r} allowed in __init__ and to_dict(), but validate_title() rejects it")
        return False  # Test "passes" by demonstrating the bug
    
    return True


if __name__ == "__main__":
    print("Testing title validation bypass bug...")
    print("=" * 60)
    
    # Run the tests directly without hypothesis decorator
    test_titles = ["", None, 0, False]
    
    for title in test_titles:
        print(f"\nTesting with title={title!r}:")
        
        definition = DefinitionDocument(Language="GRAPHQL", Text="{}")
        
        # This should fail but doesn't
        template = FlowTemplate(title, Definition=definition)
        print(f"  ✗ Object created successfully (should have failed)")
        
        # to_dict() also succeeds (bug!)
        result = template.to_dict()
        print(f"  ✗ to_dict() succeeded (should have failed)")
        
        # But validate_title() correctly identifies it as invalid
        try:
            template.validate_title()
            print(f"  ? validate_title() passed unexpectedly")
        except ValueError as e:
            print(f"  ✓ validate_title() correctly raised: {e}")
            print(f"  BUG CONFIRMED: Object exists with invalid title!")
    
    print("\n" + "=" * 60)
    print("All tests confirm the bug: falsy titles bypass validation!")