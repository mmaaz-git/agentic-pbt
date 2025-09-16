"""Test demonstrating the empty string validation bug in troposphere.servicecatalogappregistry"""

import troposphere.servicecatalogappregistry as module
from hypothesis import given, strategies as st


@given(st.sampled_from(['', ' ', '  ', '\t', '\n', '   \t   ']))
def test_empty_string_accepted_for_required_fields(empty_value):
    """
    Bug: Required Name fields accept empty/whitespace-only strings.
    
    CloudFormation requires non-empty strings for Name fields, but
    troposphere's validation doesn't enforce this constraint.
    """
    # Application accepts empty/whitespace Name (REQUIRED field)
    app = module.Application('TestApp', Name=empty_value)
    result = app.to_dict()
    
    # This should fail validation but doesn't
    assert result['Properties']['Name'] == empty_value
    assert module.Application.props['Name'][1] == True  # Field is marked as required
    
    # AttributeGroup also accepts empty/whitespace Name (REQUIRED field)
    ag = module.AttributeGroup('TestAG', Name=empty_value, Attributes={'key': 'val'})
    result = ag.to_dict()
    
    assert result['Properties']['Name'] == empty_value
    assert module.AttributeGroup.props['Name'][1] == True  # Field is marked as required


def test_empty_string_bug_minimal_repro():
    """Minimal reproduction of the empty string validation bug"""
    # This should fail but doesn't
    app = module.Application('App', Name='')
    result = app.to_dict()
    
    print(f"Created Application with empty Name: {result}")
    print(f"Name field is required: {module.Application.props['Name'][1]}")
    print("Expected: Validation error for empty required field")
    print("Actual: Silently accepts empty string")
    
    # Real CloudFormation would reject this
    assert result == {
        'Properties': {'Name': ''},
        'Type': 'AWS::ServiceCatalogAppRegistry::Application'
    }


if __name__ == '__main__':
    test_empty_string_bug_minimal_repro()
    print("\nBug confirmed: Required fields accept empty strings without validation error")