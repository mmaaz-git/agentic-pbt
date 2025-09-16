"""Comprehensive test demonstrating the empty title validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import troposphere.frauddetector as fd
from troposphere import Template

# Property test for the bug
@given(
    title=st.sampled_from(["", None]),
    name=st.text(min_size=1, max_size=100)
)
def test_empty_title_bypasses_validation(title, name):
    """Empty or None titles should be rejected but are accepted."""
    # These should raise ValueError but don't
    entity = fd.EntityType(title, Name=name)
    assert entity.title == title  # Bug: accepts invalid title
    
    # Can even generate CloudFormation JSON
    result = entity.to_dict()
    assert "Type" in result
    assert result["Type"] == "AWS::FraudDetector::EntityType"
    
    # Can add to template - causes problems with resource naming
    template = Template()
    template.add_resource(entity)
    
    # The resource key in template is the empty string!
    if title == "":
        assert "" in template.resources
    elif title is None:
        assert None in template.resources

if __name__ == "__main__":
    # Run the property test
    test_empty_title_bypasses_validation()
    print("✓ Property test passed - bug confirmed!")
    
    # Demonstrate the concrete issue
    print("\nDemonstrating the bug:")
    print("-" * 50)
    
    # Create multiple resources with empty titles
    template = Template()
    
    entity1 = fd.EntityType("", Name="Entity1")
    entity2 = fd.EntityType("", Name="Entity2")  
    entity3 = fd.EntityType(None, Name="Entity3")
    
    template.add_resource(entity1)
    template.add_resource(entity2)  # This overwrites entity1!
    template.add_resource(entity3)
    
    print(f"Added 3 entities, but template has {len(template.resources)} resources")
    print(f"Resource keys: {list(template.resources.keys())}")
    
    # The entities overwrite each other!
    for key, resource in template.resources.items():
        print(f"  Key {repr(key)}: {resource.properties}")
    
    print("\nThis causes CloudFormation template corruption!")