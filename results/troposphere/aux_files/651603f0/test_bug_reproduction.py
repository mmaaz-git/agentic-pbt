"""Minimal reproduction of the API inconsistency bug in troposphere.proton"""

import troposphere.proton as proton


def test_properties_key_inconsistency():
    """
    Bug: to_dict() inconsistently includes/excludes the 'Properties' key.
    
    When a template has no properties set, to_dict() omits the 'Properties' key entirely.
    When properties are set, to_dict() includes the 'Properties' key.
    
    This inconsistency makes the API unpredictable and can break code that expects
    the 'Properties' key to always be present in the dictionary representation.
    """
    # Case 1: Template with no properties
    empty_template = proton.EnvironmentTemplate('EmptyTemplate')
    empty_dict = empty_template.to_dict()
    
    # This will raise KeyError because Properties is missing
    try:
        properties = empty_dict['Properties']
        print("ERROR: Should have raised KeyError but didn't")
    except KeyError:
        print("✓ KeyError raised as expected - Properties key is missing")
    
    # Case 2: Template with properties
    template_with_props = proton.EnvironmentTemplate(
        'TemplateWithProps',
        Name='TestTemplate'
    )
    props_dict = template_with_props.to_dict()
    
    # This works because Properties exists
    try:
        properties = props_dict['Properties']
        print("✓ Properties key exists when properties are set")
    except KeyError:
        print("ERROR: Properties key should exist but doesn't")
    
    # Demonstrate the inconsistency
    print("\nInconsistency demonstrated:")
    print(f"  Empty template has 'Properties': {'Properties' in empty_dict}")
    print(f"  Template with props has 'Properties': {'Properties' in props_dict}")
    
    # This breaks the round-trip property for code that expects Properties
    print("\nRound-trip issue:")
    print("  Code expecting dict['Properties'] will fail unpredictably")
    print("  Must use dict.get('Properties', {}) defensively everywhere")
    
    return empty_dict, props_dict


if __name__ == "__main__":
    empty_dict, props_dict = test_properties_key_inconsistency()
    
    print("\nActual dict outputs:")
    print(f"  Empty template: {empty_dict}")
    print(f"  With properties: {props_dict}")