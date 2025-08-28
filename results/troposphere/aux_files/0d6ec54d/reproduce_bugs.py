"""Minimal reproductions of discovered bugs."""

from troposphere import Tags
from troposphere.route53recoveryreadiness import Cell, ResourceSet


def reproduce_round_trip_bug():
    """Bug 1: from_dict doesn't work with to_dict output."""
    print("Bug 1: Round-trip serialization failure")
    print("-" * 40)
    
    # Create a Cell object
    cell = Cell(
        title="TestCell",
        CellName="MyCell",
        Cells=["Cell1", "Cell2"],
    )
    
    # Convert to dict
    dict_repr = cell.to_dict()
    print(f"to_dict() output: {dict_repr}")
    
    # Try to reconstruct from dict - THIS FAILS
    try:
        reconstructed = Cell.from_dict("TestCell", dict_repr)
        print("✓ Reconstruction succeeded")
    except AttributeError as e:
        print(f"✗ Reconstruction failed: {e}")
    
    print()


def reproduce_tags_concatenation_bug():
    """Bug 2: Tags concatenation doesn't preserve all tags."""
    print("Bug 2: Tags concatenation bug")
    print("-" * 40)
    
    # Create two Tags objects with same key
    t1 = Tags({"Key1": "Value1"})
    t2 = Tags({"Key1": "Value2"})  # Same key, different value
    
    print(f"t1.to_dict(): {t1.to_dict()}")
    print(f"t2.to_dict(): {t2.to_dict()}")
    
    # Concatenate them
    combined = t1 + t2
    combined_dict = combined.to_dict()
    
    print(f"Combined tags: {combined_dict}")
    print(f"Expected length: {len(t1.to_dict()) + len(t2.to_dict())} tags")
    print(f"Actual length: {len(combined_dict)} tags")
    
    if len(combined_dict) != len(t1.to_dict()) + len(t2.to_dict()):
        print("✗ Tags were lost during concatenation!")
    else:
        print("✓ All tags preserved")
    
    print()
    
    # Test with different keys
    t3 = Tags({"Key1": "Value1"})
    t4 = Tags({"Key2": "Value2"})  # Different key
    
    combined2 = t3 + t4
    print(f"t3 + t4 result: {combined2.to_dict()}")
    print(f"Expected: 2 tags, Got: {len(combined2.to_dict())} tags")
    print()


def reproduce_validation_bug():
    """Bug 3: Required properties are not validated."""
    print("Bug 3: Missing validation for required properties")
    print("-" * 40)
    
    # Create ResourceSet without required properties
    resource_set = ResourceSet(
        title="TestResourceSet",
        ResourceSetName="MyResourceSet",
        # Missing required: ResourceSetType and Resources
    )
    
    print(f"Created ResourceSet without required properties")
    print(f"Props definition shows ResourceSetType is required: {ResourceSet.props['ResourceSetType'][1]}")
    print(f"Props definition shows Resources is required: {ResourceSet.props['Resources'][1]}")
    
    # Try to validate - should raise ValueError but doesn't
    try:
        resource_set.validate()
        print("✗ validate() did not raise an error for missing required properties!")
    except ValueError as e:
        print(f"✓ validate() correctly raised: {e}")
    
    print()


def investigate_from_dict():
    """Investigate the from_dict implementation."""
    print("Investigating from_dict expected structure")
    print("-" * 40)
    
    # Let's see what from_dict expects
    cell = Cell(title="Test", CellName="TestCell")
    dict_repr = cell.to_dict()
    
    print(f"to_dict() structure keys: {list(dict_repr.keys())}")
    
    # Try passing just the Properties dict
    if "Properties" in dict_repr:
        try:
            reconstructed = Cell.from_dict("Test", dict_repr["Properties"])
            print("✓ from_dict works when passing just Properties dict")
        except Exception as e:
            print(f"✗ Even passing Properties dict fails: {e}")
    
    print()


if __name__ == "__main__":
    reproduce_round_trip_bug()
    reproduce_tags_concatenation_bug()
    reproduce_validation_bug()
    investigate_from_dict()